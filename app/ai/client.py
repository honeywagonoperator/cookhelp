import os
import json
import logging
from typing import Any, Optional
from dataclasses import dataclass

import httpx
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
    content: str
    tokens_used: int
    model: str
    finish_reason: str


class OpenRouterClient:
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set in environment")
        
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
            http_client=httpx.AsyncClient(timeout=60.0),
        )
        
        self.default_model = "nvidia/llama-nemotron-embed-vl-1b-v2:free"
        self.chat_model = "anthropic/claude-3.5-sonnet"
        self.embedding_model = settings.embedding_model

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    )
    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        response_format: Optional[dict] = None,
    ) -> AIResponse:
        model = model or self.chat_model
        
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if response_format:
            kwargs["response_format"] = response_format
        
        try:
            response = await self.client.chat.completions.create(**kwargs)
            
            choice = response.choices[0]
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            logger.info(
                "OpenRouter completion",
                extra={
                    "model": model,
                    "tokens": tokens_used,
                    "finish_reason": choice.finish_reason,
                },
            )
            
            return AIResponse(
                content=choice.message.content or "",
                tokens_used=tokens_used,
                model=model,
                finish_reason=choice.finish_reason or "unknown",
            )
        except Exception as e:
            logger.error(f"OpenRouter error: {e}")
            raise

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    )
    async def create_embedding(self, text: str, model: Optional[str] = None) -> list[float]:
        model = model or self.embedding_model
        
        try:
            response = await self.client.embeddings.create(
                model=model,
                input=text,
            )
            
            embedding = response.data[0].embedding
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            logger.info(
                "OpenRouter embedding",
                extra={
                    "model": model,
                    "tokens": tokens_used,
                    "dimension": len(embedding),
                },
            )
            
            return embedding
        except Exception as e:
            logger.error(f"OpenRouter embedding error: {e}")
            raise

    async def close(self):
        await self.client.close()


_openrouter_client: Optional[OpenRouterClient] = None


def get_ai_client() -> OpenRouterClient:
    global _openrouter_client
    if _openrouter_client is None:
        _openrouter_client = OpenRouterClient()
    return _openrouter_client


async def close_ai_client():
    global _openrouter_client
    if _openrouter_client:
        await _openrouter_client.close()
        _openrouter_client = None