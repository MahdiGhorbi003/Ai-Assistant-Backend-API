from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import CustomUser

from .models import Conversation


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