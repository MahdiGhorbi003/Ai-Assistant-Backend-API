from django.http import StreamingHttpResponse
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from .services.llm_service import LLMService
from .services.llm.exceptions import LLMException


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Conversation.objects.filter(
            user=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user
        )


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (
        SearchFilter,
        DjangoFilterBackend,
    )

    filterset_fields = ('role',)
    search_fields = ('content',)

    def get_queryset(self):
        return Message.objects.filter(
            conversation__user=self.request.user
        ).order_by('created_at')

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        conversation = get_object_or_404(
            Conversation,
            id=serializer.validated_data['conversation'].id,
            user=request.user,
        )

        content = serializer.validated_data['content']

        service = LLMService()

        try:
            response = service.send_message(
                conversation=conversation,
                content=content,
            )

        except LLMException as exception:
            return Response(
                {
                    'detail': str(exception),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {
                'response': response,
            },
            status=status.HTTP_200_OK,
        )

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
