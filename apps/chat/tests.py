from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.test import TestCase

from apps.accounts.models import CustomUser

from .models import Conversation, Message


class ConversationAPITests(APITestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='user_test@gmail.com',
            password='StrongPass123!',
        )

        self.client.force_authenticate(user=self.user)

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
        self.client.force_authenticate(user=None)

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

    def test_create_message(self):
        data = {
            'conversation': self.conversation.id,
            'role': 'user',
            'content': 'hello django',
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
            Message.objects.count(),
            1,
        )

        message = Message.objects.get()

        self.assertEqual(
            message.conversation,
            self.conversation,
        )

        self.assertEqual(
            message.role,
            data['role'],
        )

        self.assertEqual(
            message.content,
            data['content'],
        )

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