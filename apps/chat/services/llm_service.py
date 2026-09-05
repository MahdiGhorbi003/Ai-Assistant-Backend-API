from apps.chat.models import Message
from apps.chat.services.llm.client import LLMClient
from django.db import transaction

class LLMService:

    def __init__(self):
        self.client = LLMClient()

    def build_history(self, conversation):

        messages = conversation.messages.order_by(
            'created_at'
        )

        return [
            {
                'role': msg.role,
                'content': msg.content,
            }
            for msg in messages
        ]

    def send_message(self, conversation, content):

        with transaction.atomic():
            Message.objects.create(
                conversation=conversation,
                role='user',
                content=content,
            )

            history = self.build_history(
                conversation
            )

            response = self.client.send_message(
                messages=history
            )

            Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=response,
            )

            return response