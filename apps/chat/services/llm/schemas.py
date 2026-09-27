from pydantic import BaseModel


class AIResponse(BaseModel):
    answer: str
    confidence: float