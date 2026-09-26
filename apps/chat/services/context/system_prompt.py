class SystemPromptService:

    def get_system_prompt(self):
        return {
            'role': 'system',
            'content': (
                'You are a helpful AI assistant. '
                'Answer clearly and accurately.'
            ),
        }