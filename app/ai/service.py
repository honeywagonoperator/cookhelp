import json
import logging
from pathlib import Path
from typing import Any
from uuid import UUID

from app.ai.client import AIResponse, get_ai_client
from app.schemas.recipe import RecipeCreate, RecipeSource

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.txt"
    return path.read_text(encoding="utf-8")


class AIService:
    def __init__(self):
        self.client = get_ai_client()
        self._prompts = {}

    def _get_prompt(self, name: str) -> str:
        if name not in self._prompts:
            self._prompts[name] = load_prompt(name)
        return self._prompts[name]

    async def extract_recipe(self, text: str) -> RecipeCreate:
        prompt = self._get_prompt("extract_recipe")
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Extract recipe from:\n\n{text}"},
        ]
        
        response = await self.client.chat_completion(
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        
        data = json.loads(response.content)
        data["source"] = RecipeSource(type="text", url=None)
        
        return RecipeCreate(**data)

    async def normalize_recipe(self, recipe_data: dict[str, Any]) -> RecipeCreate:
        prompt = self._get_prompt("normalize_recipe")
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(recipe_data, ensure_ascii=False)},
        ]
        
        response = await self.client.chat_completion(
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        
        data = json.loads(response.content)
        data["source"] = recipe_data.get("source", {"type": "text", "url": None})
        
        return RecipeCreate(**data)

    async def classify_intent(self, text: str) -> dict[str, Any]:
        prompt = self._get_prompt("classify_intent")
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ]
        
        response = await self.client.chat_completion(
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        
        return json.loads(response.content)

    async def edit_recipe(self, recipe: dict[str, Any], instruction: str) -> dict[str, Any]:
        prompt = self._get_prompt("edit_recipe")
        recipe_json = json.dumps(recipe, ensure_ascii=False)
        user_content = prompt.replace("{{recipe_json}}", recipe_json).replace("{{instruction}}", instruction)
        
        messages = [
            {"role": "system", "content": "You are a recipe editing expert. Return only JSON with modified recipe."},
            {"role": "user", "content": user_content},
        ]
        
        response = await self.client.chat_completion(
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        
        return json.loads(response.content)

    async def rerank_search_results(
        self,
        query: str,
        candidates: list[dict[str, Any]],
    ) -> list[str]:
        if not candidates:
            return []
        
        prompt = self._get_prompt("rerank_search")
        candidates_json = json.dumps(
            [
                {
                    "id": str(c["id"]),
                    "title": c["title"],
                    "description": c.get("description"),
                    "tags": c.get("tags", []),
                    "ingredients": c.get("ingredients", [])[:5],
                }
                for c in candidates
            ],
            ensure_ascii=False,
        )
        
        user_content = prompt.replace("{{query}}", query).replace("{{candidates_json}}", candidates_json)
        
        messages = [
            {"role": "system", "content": "You are a recipe search reranker. Return only JSON array of recipe IDs."},
            {"role": "user", "content": user_content},
        ]
        
        response = await self.client.chat_completion(
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            logger.warning("Failed to parse rerank response, returning original order")
            return [str(c["id"]) for c in candidates]

    async def generate_tags(self, recipe: dict[str, Any]) -> list[str]:
        prompt = self._get_prompt("generate_tags")
        recipe_json = json.dumps(recipe, ensure_ascii=False)
        user_content = prompt.replace("{{recipe_json}}", recipe_json)
        
        messages = [
            {"role": "system", "content": "You are a recipe tagging expert. Return only JSON array of tags."},
            {"role": "user", "content": user_content},
        ]
        
        response = await self.client.chat_completion(
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        
        try:
            tags = json.loads(response.content)
            return tags if isinstance(tags, list) else []
        except json.JSONDecodeError:
            logger.warning("Failed to parse tags response")
            return []

    async def generate_embedding(self, text: str) -> list[float]:
        return await self.client.create_embedding(text)

    async def generate_embedding_for_recipe(self, recipe: dict[str, Any]) -> list[float]:
        parts = [
            recipe.get("title", ""),
            recipe.get("description", ""),
            " ".join(recipe.get("ingredients", [])),
            " ".join(recipe.get("tags", [])),
        ]
        text = "\n".join(filter(None, parts))
        return await self.generate_embedding(text)


_ai_service = None


def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service