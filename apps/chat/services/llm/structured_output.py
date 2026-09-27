import json

from apps.chat.services.llm.client import LLMClient
from apps.chat.services.llm.schemas import AIResponse


class StructuredOutputService:

    def __init__(self):
        self.client = LLMClient()

    def get_response(self, messages) -> AIResponse:
        response = self.client.send_json_message(messages)

        data = json.loads(response)

        return AIResponse.model_validate(data)