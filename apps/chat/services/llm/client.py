import os
import logging

from groq import (
    Groq,
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    APIStatusError,
)

from apps.chat.services.llm.exceptions import LLMException

logger = logging.getLogger(__name__)


class LLMClient:

    def __init__(self):
        self.client = Groq(
            api_key=os.getenv('GROQ_API_KEY'),
        )

    def send_message(self, messages):

        try:
            logger.info('sending request to LLM')

            response = self.client.chat.completions.create(
                model='openai/gpt-oss-120b',
                messages=messages,
            )

            return response.choices[0].message.content

        except APITimeoutError:
            logger.error('LLM request timed out')
            raise LLMException(
                'LLM request timed out.'
            )

        except APIConnectionError:
            raise LLMException(
                'Failed to connect to LLM.'
            )

        except RateLimitError:
            raise LLMException(
                'LLM rate limit exceeded.'
            )

        except APIStatusError as exception:

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
