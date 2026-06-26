import logging
import time
from collections.abc import Sequence
from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_groq import ChatGroq
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import Settings
from app.core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "agents" / "prompts"

INTENT_HINTS: dict[str, str] = {
    "content": "Focus on LinkedIn content: posts, carousels, video scripts, hooks, campaigns.",
    "networking": (
        "Focus on networking: profile SWOT, icebreakers, connection requests (≤300 chars)."
    ),
    "profile": "Focus on profile optimization: headline, about, experience, skills.",
    "advisor": "Focus on daily/weekly advisor: briefing, post performance, outreach plan.",
    "strategy": "Focus on personal branding strategy: narrative, competitors, content calendar.",
    "general": "Provide general LinkedIn personal branding guidance.",
}


def load_base_prompt() -> str:
    return (PROMPTS_DIR / "base.md").read_text(encoding="utf-8")


class LLMService:
    def __init__(self, settings: Settings, chat_model: BaseChatModel | None = None) -> None:
        self.settings = settings
        self._chat_model = chat_model

    def _ensure_api_key(self) -> None:
        if not self.settings.groq_api_key:
            raise ConfigurationError(
                "GROQ_API_KEY is not configured. Add it to your .env file."
            )

    @property
    def chat_model(self) -> BaseChatModel:
        if self._chat_model is None:
            self._ensure_api_key()
            self._chat_model = ChatGroq(
                model=self.settings.groq_model,
                api_key=self.settings.groq_api_key,
                temperature=0.4,
            )
        return self._chat_model

    @retry(
        retry=retry_if_exception_type(ValidationError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True,
    )
    async def structured_invoke(
        self,
        messages: Sequence[BaseMessage],
        schema: type[BaseModel],
    ) -> BaseModel:
        start = time.perf_counter()
        structured_llm = self.chat_model.with_structured_output(schema)
        result = await structured_llm.ainvoke(list(messages))
        if not isinstance(result, schema):
            result = schema.model_validate(result)

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "LLM structured call model=%s schema=%s latency_ms=%d",
            self.settings.groq_model,
            schema.__name__,
            elapsed_ms,
        )
        return result

    def build_system_prompt(self, intent: str, user_context: dict | None = None) -> str:
        base = load_base_prompt()
        hint = INTENT_HINTS.get(intent, INTENT_HINTS["general"])
        context_block = ""
        if user_context:
            context_block = f"\n\n## User Context\n{user_context}"
        return f"{base}\n\n## Current Focus\n{hint}{context_block}"
