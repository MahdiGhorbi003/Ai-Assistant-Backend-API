from .recent_messages import RecentMessagesService
from .system_prompt import SystemPromptService
from .token_manager import TokenManager


class ContextManager:

    def __init__(self):
        self.recent_messages_service = RecentMessagesService()
        self.system_prompt_service = SystemPromptService()
        self.token_manager = TokenManager()

    def build_context(self, conversation):
        system_prompt = self.system_prompt_service.get_system_prompt()

        recent_messages = (
            self.recent_messages_service
            .get_recent_messages(conversation)
        )

        context = [
            system_prompt,
        ]

        if conversation.summary:
            context.append({
                'role': 'system',
                'content': f'conversation summary:{conversation.summary}',
            })

        context.extend(recent_messages)

        return self.token_manager.trim_messages(context)
