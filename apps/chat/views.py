import hashlib
import json
import uuid
import redis
from django.conf import settings

from django.http import StreamingHttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.core.cache import cache

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.throttling import ScopedRateThrottle

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from .services.llm_service import LLMService
from .services.llm.exceptions import LLMException

idempotency_redis = redis.Redis.from_url(
    settings.CACHES['default']['LOCATION'],
    decode_responses=True,
)

IDEMPOTENCY_TTL = 60 * 5
IDEMPOTENCY_LOCK_TTL = 60 * 5

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Conversation.objects.filter(
            user=self.request.user
        )

    def _bump_conversation_cache_version(self, user_id):
        version_key = f'conversations:user:{user_id}:version'

        if not cache.add(version_key, 1, timeout=None):
            cache.incr(version_key)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        self._bump_conversation_cache_version(self.request.user.id)

    def perform_update(self, serializer):
        serializer.save()
        self._bump_conversation_cache_version(self.request.user.id)

    def perform_destroy(self, instance):
        instance.delete()
        self._bump_conversation_cache_version(self.request.user.id)

    def list(self, request, *args, **kwargs):
        version_key = f'conversations:user:{request.user.id}:version'

        cache.add(version_key, 1, timeout=None)
        version = cache.get(version_key, 1)

        cache_key = (
            f'conversations:user:{request.user.id}:'
            f'v{version}:{request.query_params.urlencode()}'
        )

        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)

        cache.set(cache_key, response.data, 60)

        return response


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'message'

    filter_backends = (
        SearchFilter,
        DjangoFilterBackend,
        OrderingFilter,
    )

    filterset_fields = ('role',)
    search_fields = ('content',)
    ordering_fields = ('created_at',)
    ordering = ('created_at',)

    def get_queryset(self):
        return Message.objects.filter(
            conversation__user=self.request.user
        )

    def get_throttles(self):
        if self.action == 'stream':
            self.throttle_scope = 'stream'
        else:
            self.throttle_scope = 'message'

        return [ScopedRateThrottle()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        conversation = get_object_or_404(
            Conversation,
            id=serializer.validated_data['conversation'].id,
            user=request.user,
        )
        content = serializer.validated_data['content']

        idempotency_key = request.headers.get('Idempotency-Key')

        if not idempotency_key:
            try:
                response = LLMService().send_message(
                    conversation=conversation,
                    content=content,
                )
            except LLMException as exception:
                return Response(
                    {'detail': str(exception)},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            return Response(
                {'response': response},
                status=status.HTTP_200_OK,
            )

        key_hash = hashlib.sha256(
            idempotency_key.encode()
        ).hexdigest()

        key_prefix = f'idempotency:user:{request.user.id}:{key_hash}'
        result_key = f'{key_prefix}:result'
        lock_key = f'{key_prefix}:lock'

        fingerprint = hashlib.sha256(
            json.dumps(
                {
                    'conversation_id': conversation.id,
                    'content': content,
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()

        def get_cached_response():
            cached_data = idempotency_redis.get(result_key)

            if cached_data is None:
                return None

            result = json.loads(cached_data)

            if result['fingerprint'] != fingerprint:
                return Response(
                    {
                        'detail': (
                            'Idempotency-Key was used with different data.'
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            return Response(
                result['response'],
                status=status.HTTP_200_OK,
            )

        cached_response = get_cached_response()

        if cached_response is not None:
            return cached_response

        owner_token = uuid.uuid4().hex

        lock_acquired = idempotency_redis.set(
            lock_key,
            owner_token,
            nx=True,
            ex=IDEMPOTENCY_LOCK_TTL,
        )

        if not lock_acquired:
            cached_response = get_cached_response()

            if cached_response is not None:
                return cached_response

            return Response(
                {'detail': 'A request with this key is already processing.'},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            cached_response = get_cached_response()

            if cached_response is not None:
                return cached_response

            response = LLMService().send_message(
                conversation=conversation,
                content=content,
            )

            result = {
                'fingerprint': fingerprint,
                'response': {'response': response},
            }

            idempotency_redis.set(
                result_key,
                json.dumps(result),
                ex=IDEMPOTENCY_TTL,
            )

            return Response(
                result['response'],
                status=status.HTTP_200_OK,
            )

        except LLMException as exception:
            return Response(
                {'detail': str(exception)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        finally:
            try:
                idempotency_redis.eval(
                    """
                    if redis.call("GET", KEYS[1]) == ARGV[1] then
                        return redis.call("DEL", KEYS[1])
                    end
                    return 0
                    """,
                    1,
                    lock_key,
                    owner_token,
                )
            except redis.exceptions.RedisError:
                pass

    @action(detail=False, methods=['post'], url_path='stream')
    def stream(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        conversation = get_object_or_404(
            Conversation,
            id=serializer.validated_data['conversation'].id,
            user=request.user,
        )

        content = serializer.validated_data['content']
        service = LLMService()

        def generate():
            try:
                for chunk in service.stream_message(
                        conversation=conversation,
                        content=content,
                ):
                    yield chunk

            except LLMException as exception:
                yield f'Error: {str(exception)}'

        return StreamingHttpResponse(
            generate(),
            content_type='text/plain',
        )
