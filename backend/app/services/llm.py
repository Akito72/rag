from typing import Sequence

from openai import OpenAI

from backend.app.models.domain import ChatMessage
from backend.app.schemas.document import SourceChunk


SYSTEM_PROMPT = """You are a precise enterprise RAG assistant.
Answer only from the provided context and recent conversation.
If the answer is not supported by the context, say that the information is not available in the uploaded documents.
Cite relevant source names in the answer when possible.
Keep answers concise but complete."""


class LLMService:
    def __init__(self, api_key: str | None, model_name: str) -> None:
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.model_name = model_name

    def generate_answer(
        self,
        question: str,
        sources: Sequence[SourceChunk],
        chat_history: Sequence[ChatMessage],
    ) -> str:
        context_block = "\n\n".join(
            [
                f"[Source: {source.source_name} | score={source.score:.3f}]\n{source.text}"
                for source in sources
            ]
        )
        history_block = "\n".join([f"{message.role}: {message.content}" for message in chat_history[-6:]])

        if not self.client:
            if not sources:
                return "I could not find relevant information in the uploaded documents."
            return (
                "Grounded answer based on retrieved context:\n\n"
                f"{sources[0].text[:1200]}\n\n"
                "Configure OPENAI_API_KEY to enable generative answers."
            )

        response = self.client.responses.create(
            model=self.model_name,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Conversation history:\n{history_block or 'No prior history.'}\n\n"
                        f"Retrieved context:\n{context_block or 'No retrieved context.'}\n\n"
                        f"User question: {question}"
                    ),
                },
            ],
        )
        return response.output_text.strip()
