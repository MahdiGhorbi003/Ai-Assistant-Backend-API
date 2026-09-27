import os
import logging
import openai

from apps.chat.services.llm.exceptions import LLMException

logger = logging.getLogger(__name__)


class LLMClient:

    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.getenv('OPENROUTER_API_KEY'),
            base_url='https://openrouter.ai/api/v1',
        )

        self.model = 'nvidia/nemotron-3-ultra-550b-a55b:free'

    def send_message(self, messages):

        try:
            logger.info('sending request to LLM')

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )

            return response.choices[0].message.content

        except openai.APITimeoutError:
            logger.error('LLM request timed out')
            raise LLMException(
                'LLM request timed out.'
            )

        except openai.APIConnectionError:
            logger.error('Failed to connect to LLM')
            raise LLMException(
                'Failed to connect to LLM.'
            )

        except openai.RateLimitError:
            logger.error('LLM rate limit exceeded')
            raise LLMException(
                'LLM rate limit exceeded.'
            )

        except openai.APIStatusError as exception:

            if exception.status_code == 401:
                raise LLMException(
                    'LLM authentication failed.'
                )

            elif exception.status_code == 404:
                raise LLMException(
                    'LLM resource not found.'
                )

            elif exception.status_code >= 500:
                raise LLMException(
                    'LLM server error.'
                )

            else:
                raise LLMException(
                    'LLM API returned an error.'
                )

    def stream_messages(self, messages):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )

        for chunk in response:
            content = chunk.choices[0].delta.content

            if content:
                yield content
