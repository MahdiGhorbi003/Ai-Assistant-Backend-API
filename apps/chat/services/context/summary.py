from apps.chat.models import Message
from apps.chat.services.llm.client import LLMClient


class SummaryService:

    def __init__(self):
        self.llm_client = LLMClient()

    def get_messages_for_summary(
            self,
            conversation,
            limit=20,
    ):
        messages = (
            Message.objects
            .filter(conversation=conversation)
            .order_by('created_at')[
                conversation.summary_message_count:
                conversation.summary_message_count + limit
            ]
        )

        return [
            {
                'role': message.role,
                'content': message.content,
            }
            for message in messages
        ]

    def generate_summary(
            self,
            conversation,
    ):
        messages = self.get_messages_for_summary(
            conversation
        )

        if not messages:
            return conversation.summary

        summary_prompt = {
            'role': 'system',
            'content': (
                'Create an updated summary of the conversation. '
                'Preserve important facts, user preferences, '
                'goals, decisions, and relevant context.'
            ),
        }

        summary_context = [
            summary_prompt,
        ]

        if conversation.summary:
            summary_context.append({
                'role': 'system',
                'content': (
                    f'Previous summary:\n'
                    f'{conversation.summary}'
                ),
            })

        summary_context.extend(messages)

        response = self.llm_client.send_message(
            messages=summary_context,
        )

        conversation.summary = response
        conversation.summary_message_count += len(messages)

        conversation.save(
            update_fields=[
                'summary',
                'summary_message_count',
                'updated_at',
            ],
        )

        return response

    def should_update_summary(
            self,
            conversation,
            threshold=20,
    ):
        unsummarized_count = (
                conversation.messages.count()
                - conversation.summary_message_count
        )

        return unsummarized_count >= threshold