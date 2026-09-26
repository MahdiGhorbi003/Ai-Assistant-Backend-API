from apps.chat.models import Message


class RecentMessagesService:
    def __init__(self, limit=10):
        self._limit = limit

    def get_recent_messages(self, conversation):
        messages = (
            Message.objects
            .filter(conversation=conversation)
            .order_by("-created_at")[:self._limit]
        )

        return [

            {
                'role': message.role,
                'content': message.content,
            }
            for message in reversed(messages)
        ]