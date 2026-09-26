class TokenManager:

    def __init__(self, max_tokens=4000):
        self._max_tokens = max_tokens

    def estimate_tokens(self, text):
        return max(1, len(text) // 4)

    def trim_messages(self, messages):
        system_message = messages[0]
        recent_messages = messages[1:]

        total_tokens = self.estimate_tokens(
            system_message['content']
        )

        selected_messages = []

        for message in reversed(recent_messages):
            message_tokens = self.estimate_tokens(
                message['content']
            )

            if total_tokens + message_tokens > self._max_tokens:
                break

            selected_messages.append(message)
            total_tokens += message_tokens

        return [
            system_message,
            *reversed(selected_messages),
        ]

