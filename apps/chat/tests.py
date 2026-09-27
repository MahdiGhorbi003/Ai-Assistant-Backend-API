from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import CustomUser
from .models import Conversation, Message
from .services.llm.exceptions import LLMException
from .services.llm_service import LLMService
from .services.context.recent_messages import RecentMessagesService
from .services.context.manager import ContextManager
from .services.context.summary import SummaryService
from apps.chat.services.llm.client import LLMClient


class ConversationAPITests(APITestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='user_test@gmail.com',
            password='StrongPass123!',
        )

        self.client.force_authenticate(
            user=self.user,
        )

        self.list_url = reverse(
            'chat:conversation-list'
        )

    def test_create_conversation(self):
        data = {
            'title': 'test_title',
        }

        response = self.client.post(
            self.list_url,
            data=data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            Conversation.objects.count(),
            1,
        )

        conversation = Conversation.objects.get()

        self.assertEqual(
            conversation.user,
            self.user,
        )

        self.assertEqual(
            conversation.title,
            data['title'],
        )

    def test_list_only_own_conversations(self):
        Conversation.objects.create(
            user=self.user,
            title='First conversation',
        )

        Conversation.objects.create(
            user=self.user,
            title='Second conversation',
        )

        other_user = CustomUser.objects.create_user(
            email='other_user@gmail.com',
            password='StrongPass123!',
        )

        Conversation.objects.create(
            user=other_user,
            title='Other user conversation',
        )

        response = self.client.get(
            self.list_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            2,
        )

    def test_retrieve_own_conversation(self):
        conversation = Conversation.objects.create(
            user=self.user,
            title='Test conversation',
        )

        url = reverse(
            'chat:conversation-detail',
            args=[conversation.pk],
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['id'],
            conversation.id,
        )

        self.assertEqual(
            response.data['title'],
            conversation.title,
        )

    def test_cannot_retrieve_other_user_conversation(self):
        other_user = CustomUser.objects.create_user(
            email='other_user@gmail.com',
            password='StrongPass123!',
        )

        conversation = Conversation.objects.create(
            user=other_user,
            title='Private conversation',
        )

        url = reverse(
            'chat:conversation-detail',
            args=[conversation.pk],
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_update_own_conversation(self):
        conversation = Conversation.objects.create(
            user=self.user,
            title='Old title',
        )

        url = reverse(
            'chat:conversation-detail',
            args=[conversation.pk],
        )

        data = {
            'title': 'Updated title',
        }

        response = self.client.patch(
            url,
            data=data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        conversation.refresh_from_db()

        self.assertEqual(
            conversation.title,
            data['title'],
        )

    def test_delete_own_conversation(self):
        conversation = Conversation.objects.create(
            user=self.user,
            title='Delete me',
        )

        url = reverse(
            'chat:conversation-detail',
            args=[conversation.pk],
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Conversation.objects.filter(
                pk=conversation.pk
            ).exists()
        )

    def test_unauthenticated_user_cannot_access_conversations(self):
        self.client.force_authenticate(
            user=None
        )

        response = self.client.get(
            self.list_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


class MessageModelTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='user_test@gmail.com',
            password='StrongPass123!',
        )

        self.conversation = Conversation.objects.create(
            user=self.user,
            title='Test Conversation',
        )

    def test_create_message(self):
        message = Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='hi',
        )

        self.assertEqual(
            message.conversation,
            self.conversation,
        )

        self.assertEqual(
            message.role,
            'user',
        )

        self.assertEqual(
            message.content,
            'hi',
        )

        self.assertEqual(
            Message.objects.count(),
            1,
        )


class MessageAPITests(APITestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='user_test@gmail.com',
            password='StrongPass123!',
        )

        self.client.force_authenticate(
            user=self.user,
        )

        self.conversation = Conversation.objects.create(
            user=self.user,
            title='Test Conversation',
        )

        self.list_url = reverse(
            'chat:message-list'
        )

    @patch(
        'apps.chat.services.llm_service.LLMClient.send_message'
    )
    def test_create_message(
            self,
            mock_send_message,
    ):
        mock_send_message.return_value = 'Hello from AI'

        data = {
            'conversation': self.conversation.id,
            'content': 'hello django',
        }

        response = self.client.post(
            self.list_url,
            data=data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['response'],
            'Hello from AI',
        )

        self.assertEqual(
            Message.objects.count(),
            2,
        )

        user_message = Message.objects.get(
            role='user'
        )

        assistant_message = Message.objects.get(
            role='assistant'
        )

        self.assertEqual(
            user_message.content,
            'hello django',
        )

        self.assertEqual(
            assistant_message.content,
            'Hello from AI',
        )

        self.assertEqual(
            user_message.conversation,
            self.conversation,
        )

        self.assertEqual(
            assistant_message.conversation,
            self.conversation,
        )

        mock_send_message.assert_called_once()

    @patch(
        'apps.chat.services.llm_service.LLMService.stream_message'
    )
    def test_stream_message(
            self,
            mock_stream_message,
    ):
        mock_stream_message.return_value = iter([
            'Hello',
            ' world',
        ])

        data = {
            'conversation': self.conversation.id,
            'content': 'hello django',
        }

        stream_url = reverse(
            'chat:message-stream'
        )

        response = self.client.post(
            stream_url,
            data=data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        content = b''.join(
            response.streaming_content
        ).decode()

        self.assertEqual(
            content,
            'Hello world',
        )

        mock_stream_message.assert_called_once()

    @patch(
        'apps.chat.services.llm_service.LLMService.stream_message'
    )
    def test_stream_message_error(
            self,
            mock_stream_message,
    ):
        def stream_error(*args, **kwargs):
            yield 'Hello'
            raise LLMException('LLM server error.')

        mock_stream_message.return_value = stream_error()

        data = {
            'conversation': self.conversation.id,
            'content': 'hello django',
        }

        stream_url = reverse(
            'chat:message-stream'
        )

        response = self.client.post(
            stream_url,
            data=data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        content = b''.join(
            response.streaming_content
        ).decode()

        self.assertEqual(
            content,
            'HelloError: LLM server error.',
        )

        mock_stream_message.assert_called_once()

    def test_list_only_own_messages(self):
        Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='My message',
        )

        other_user = CustomUser.objects.create_user(
            email='other_user@gmail.com',
            password='StrongPass123!',
        )

        other_conversation = Conversation.objects.create(
            user=other_user,
            title='Other Conversation',
        )

        Message.objects.create(
            conversation=other_conversation,
            role='user',
            content='Other user message',
        )

        response = self.client.get(
            self.list_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]['content'],
            'My message',
        )

    def test_retrieve_own_message(self):
        message = Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='Test message',
        )

        url = reverse(
            'chat:message-detail',
            args=[message.pk],
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['id'],
            message.id,
        )

        self.assertEqual(
            response.data['content'],
            message.content,
        )

    def test_cannot_retrieve_other_user_message(self):
        other_user = CustomUser.objects.create_user(
            email='other_user@gmail.com',
            password='StrongPass123!',
        )

        other_conversation = Conversation.objects.create(
            user=other_user,
            title='Other Conversation',
        )

        message = Message.objects.create(
            conversation=other_conversation,
            role='user',
            content='Private message',
        )

        url = reverse(
            'chat:message-detail',
            args=[message.pk],
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_update_own_message(self):
        message = Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='Old message',
        )

        url = reverse(
            'chat:message-detail',
            args=[message.pk],
        )

        data = {
            'content': 'Updated message',
        }

        response = self.client.patch(
            url,
            data=data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        message.refresh_from_db()

        self.assertEqual(
            message.content,
            data['content'],
        )

        self.assertEqual(
            message.role,
            'user',
        )

    def test_delete_own_message(self):
        message = Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='Delete me',
        )

        url = reverse(
            'chat:message-detail',
            args=[message.pk],
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Message.objects.filter(
                pk=message.pk
            ).exists()
        )

    def test_unauthenticated_user_cannot_access_messages(self):
        self.client.force_authenticate(
            user=None
        )

        response = self.client.get(
            self.list_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


class LLMServiceTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='llm_test@gmail.com',
            password='StrongPass123!',
        )

        self.conversation = Conversation.objects.create(
            user=self.user,
            title='LLM Test Conversation',
        )

    @patch(
        'apps.chat.services.llm_service.LLMClient.send_message'
    )
    def test_send_message_creates_user_and_assistant_messages(
            self,
            mock_send_message,
    ):
        mock_send_message.return_value = 'this is response'

        service = LLMService()

        response = service.send_message(
            self.conversation,
            'Hello AI',
        )

        self.assertEqual(
            response,
            'this is response',
        )

        self.assertEqual(
            Message.objects.count(),
            2,
        )

        user_message = Message.objects.get(
            role='user'
        )

        assistant_message = Message.objects.get(
            role='assistant'
        )

        self.assertEqual(
            user_message.content,
            'Hello AI',
        )

        self.assertEqual(
            assistant_message.content,
            'this is response',
        )

        self.assertEqual(
            user_message.conversation,
            self.conversation,
        )

        self.assertEqual(
            assistant_message.conversation,
            self.conversation,
        )

        mock_send_message.assert_called_once()

    @patch(
        'apps.chat.services.llm_service.LLMClient.send_message'
    )
    def test_send_message_passes_context_to_llm(
            self,
            mock_send_message,
    ):
        mock_send_message.return_value = 'new response'

        Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='Old question',
        )

        Message.objects.create(
            conversation=self.conversation,
            role='assistant',
            content='Old answer',
        )

        service = LLMService()

        service.send_message(
            self.conversation,
            'New question',
        )

        mock_send_message.assert_called_once_with(
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'You are a helpful AI assistant. '
                        'Answer clearly and accurately.'
                    ),
                },
                {
                    'role': 'user',
                    'content': 'Old question',
                },
                {
                    'role': 'assistant',
                    'content': 'Old answer',
                },
                {
                    'role': 'user',
                    'content': 'New question',
                },
            ]
        )

    @patch(
        'apps.chat.services.llm_service.SummaryService.generate_summary'
    )
    @patch(
        'apps.chat.services.llm_service.LLMClient.send_message'
    )
    def test_send_message_updates_summary_after_threshold(
            self,
            mock_send_message,
            mock_generate_summary,
    ):
        mock_send_message.return_value = 'new response'

        for index in range(19):
            Message.objects.create(
                conversation=self.conversation,
                role='user',
                content=f'Message {index}',
            )

        service = LLMService()

        service.send_message(
            self.conversation,
            'Message 19',
        )

        mock_generate_summary.assert_called_once_with(
            self.conversation
        )

    @patch('apps.chat.services.llm_service.LLMClient.stream_messages')
    def test_stream_message(
            self,
            mock_stream_messages,
    ):
        mock_stream_messages.return_value = iter([
            'Hello',
            ' world',
        ])

        service = LLMService()

        result = list(
            service.stream_message(
                self.conversation,
                'Hello',
            )
        )

        self.assertEqual(
            result,
            ['Hello', ' world'],
        )

        messages = Message.objects.filter(
            conversation=self.conversation,
        ).order_by('created_at')

        self.assertEqual(messages.count(), 2)

        self.assertEqual(
            messages[0].role,
            'user',
        )
        self.assertEqual(
            messages[0].content,
            'Hello',
        )

        self.assertEqual(
            messages[1].role,
            'assistant',
        )
        self.assertEqual(
            messages[1].content,
            'Hello world',
        )

        mock_stream_messages.assert_called_once()


class RecentMessagesServiceTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='recent_messages_test@gmail.com',
            password='StrongPass123!',
        )

        self.conversation = Conversation.objects.create(
            user=self.user,
            title='Recent Messages Test',
        )

    def test_get_recent_messages(self):
        Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='Hello',
        )

        Message.objects.create(
            conversation=self.conversation,
            role='assistant',
            content='Hi!',
        )

        service = RecentMessagesService()

        result = service.get_recent_messages(
            self.conversation
        )

        self.assertEqual(
            result,
            [
                {
                    'role': 'user',
                    'content': 'Hello',
                },
                {
                    'role': 'assistant',
                    'content': 'Hi!',
                },
            ],
        )

    def test_get_recent_messages_only_from_conversation(self):
        Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='My message',
        )

        other_user = CustomUser.objects.create_user(
            email='other_recent_messages@gmail.com',
            password='StrongPass123!',
        )

        other_conversation = Conversation.objects.create(
            user=other_user,
            title='Other Conversation',
        )

        Message.objects.create(
            conversation=other_conversation,
            role='user',
            content='Other message',
        )

        service = RecentMessagesService()

        result = service.get_recent_messages(
            self.conversation
        )

        self.assertEqual(
            result,
            [
                {
                    'role': 'user',
                    'content': 'My message',
                },
            ],
        )

    def test_get_recent_messages_respects_limit(self):
        for index in range(12):
            Message.objects.create(
                conversation=self.conversation,
                role='user',
                content=f'Message {index}',
            )

        service = RecentMessagesService(limit=10)

        result = service.get_recent_messages(
            self.conversation
        )

        self.assertEqual(
            len(result),
            10,
        )

        self.assertEqual(
            result[0]['content'],
            'Message 2',
        )

        self.assertEqual(
            result[-1]['content'],
            'Message 11',
        )


class ContextManagerTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='context_manager_test@gmail.com',
            password='StrongPass123!',
        )

        self.conversation = Conversation.objects.create(
            user=self.user,
            title='Context Manager Test',
        )

    def test_build_context(self):
        Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='Hello',
        )

        Message.objects.create(
            conversation=self.conversation,
            role='assistant',
            content='Hi!',
        )

        manager = ContextManager()

        context = manager.build_context(
            self.conversation
        )

        self.assertEqual(
            context,
            [
                {
                    'role': 'system',
                    'content': (
                        'You are a helpful AI assistant. '
                        'Answer clearly and accurately.'
                    ),
                },
                {
                    'role': 'user',
                    'content': 'Hello',
                },
                {
                    'role': 'assistant',
                    'content': 'Hi!',
                },
            ],
        )

    def test_build_context_with_summary(self):
        self.conversation.summary = 'User likes Python.'
        self.conversation.save()

        manager = ContextManager()

        context = manager.build_context(
            self.conversation
        )

        self.assertEqual(
            context,
            [
                {
                    'role': 'system',
                    'content': (
                        'You are a helpful AI assistant. '
                        'Answer clearly and accurately.'
                    ),
                },
                {
                    'role': 'system',
                    'content': (
                        'conversation summary:'
                        'User likes Python.'
                    ),
                },
            ],
        )


class SummaryServiceTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='summary_test@gmail.com',
            password='StrongPass123!',
        )

        self.conversation = Conversation.objects.create(
            user=self.user,
            title='Summary Test',
        )

    def test_get_messages_for_summary(self):
        Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='Hello',
        )

        Message.objects.create(
            conversation=self.conversation,
            role='assistant',
            content='Hi!',
        )

        service = SummaryService()

        result = service.get_messages_for_summary(
            self.conversation
        )

        self.assertEqual(
            result,
            [
                {
                    'role': 'user',
                    'content': 'Hello',
                },
                {
                    'role': 'assistant',
                    'content': 'Hi!',
                },
            ],
        )

    def test_get_messages_for_summary_skips_summarized_messages(self):
        for index in range(5):
            Message.objects.create(
                conversation=self.conversation,
                role='user',
                content=f'Message {index}',
            )

        self.conversation.summary_message_count = 3
        self.conversation.save()

        service = SummaryService()

        result = service.get_messages_for_summary(
            self.conversation
        )

        self.assertEqual(
            result,
            [
                {
                    'role': 'user',
                    'content': 'Message 3',
                },
                {
                    'role': 'user',
                    'content': 'Message 4',
                },
            ],
        )

    def test_should_update_summary(self):
        for index in range(20):
            Message.objects.create(
                conversation=self.conversation,
                role='user',
                content=f'Message {index}',
            )

        service = SummaryService()

        self.assertTrue(
            service.should_update_summary(
                self.conversation
            )
        )

    def test_should_not_update_summary(self):
        for index in range(19):
            Message.objects.create(
                conversation=self.conversation,
                role='user',
                content=f'Message {index}',
            )

        service = SummaryService()

        self.assertFalse(
            service.should_update_summary(
                self.conversation
            )
        )

    @patch(
        'apps.chat.services.context.summary.LLMClient.send_message'
    )
    def test_generate_summary(self, mock_send_message):
        mock_send_message.return_value = (
            'User is learning backend development.'
        )

        Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='I am learning Django.',
        )

        Message.objects.create(
            conversation=self.conversation,
            role='assistant',
            content='Django is a Python framework.',
        )

        service = SummaryService()

        result = service.generate_summary(
            self.conversation
        )

        self.conversation.refresh_from_db()

        self.assertEqual(
            result,
            'User is learning backend development.',
        )

        self.assertEqual(
            self.conversation.summary,
            'User is learning backend development.',
        )

        self.assertEqual(
            self.conversation.summary_message_count,
            2,
        )

        mock_send_message.assert_called_once()

    @patch(
        'apps.chat.services.context.summary.LLMClient.send_message'
    )
    def test_generate_summary_with_previous_summary(
            self,
            mock_send_message,
    ):
        mock_send_message.return_value = (
            'Updated conversation summary.'
        )

        self.conversation.summary = 'User is learning Python.'
        self.conversation.summary_message_count = 0
        self.conversation.save()

        Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='I am now learning Django.',
        )

        service = SummaryService()

        result = service.generate_summary(
            self.conversation
        )

        self.conversation.refresh_from_db()

        self.assertEqual(
            result,
            'Updated conversation summary.',
        )

        self.assertEqual(
            self.conversation.summary,
            'Updated conversation summary.',
        )

        self.assertEqual(
            self.conversation.summary_message_count,
            1,
        )

        mock_send_message.assert_called_once()

        call_args = mock_send_message.call_args

        messages = call_args.kwargs['messages']

        self.assertEqual(
            messages[0]['role'],
            'system',
        )

        self.assertEqual(
            messages[1]['role'],
            'system',
        )

        self.assertIn(
            'User is learning Python.',
            messages[1]['content'],
        )


class LLMClientTests(TestCase):

    @patch('apps.chat.services.llm.client.openai.OpenAI')
    def test_stream_messages(self, mock_openai):
        mock_response = [
            MagicMock(
                choices=[
                    MagicMock(
                        delta=MagicMock(content='Hello')
                    )
                ]
            ),
            MagicMock(
                choices=[
                    MagicMock(
                        delta=MagicMock(content=' world')
                    )
                ]
            ),
        ]

        mock_openai.return_value.chat.completions.create.return_value = (
            mock_response
        )

        client = LLMClient()

        result = list(
            client.stream_messages(
                messages=[
                    {
                        'role': 'user',
                        'content': 'Hello',
                    }
                ]
            )
        )

        self.assertEqual(
            result,
            ['Hello', ' world'],
        )

        mock_openai.return_value.chat.completions.create.assert_called_once_with(
            model=client.model,
            messages=[
                {
                    'role': 'user',
                    'content': 'Hello',
                }
            ],
            stream=True,
        )
