from django.db import transaction

from apps.chat.models import Message
from apps.chat.services.llm.client import LLMClient
from apps.chat.services.context.manager import ContextManager
from apps.chat.services.context.summary import SummaryService


class LLMService:

    def __init__(self):
        self.client = LLMClient()
        self.context_manager = ContextManager()
        self.summary_service = SummaryService()

    def send_message(self, conversation, content):
        with transaction.atomic():
            Message.objects.create(
                conversation=conversation,
                role='user',
                content=content,
            )

            context = self.context_manager.build_context(conversation)

            response = self.client.send_message(
                messages=context,
            )

            Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=response,
            )

        if self.summary_service.should_update_summary(conversation):
            self.summary_service.generate_summary(conversation)

        return response
