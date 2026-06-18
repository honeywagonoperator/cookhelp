import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import AsyncOpenAI
import httpx


async def main():
    import os
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    print(f"API Key: {'set' if api_key else 'NOT SET'}")

    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        http_client=httpx.AsyncClient(timeout=60.0, trust_env=False),
    )

    try:
        response = await client.embeddings.create(
            model="nvidia/llama-nemotron-embed-vl-1b-v2:free",
            input="Тестовый запрос",
        )
        embedding = response.data[0].embedding
        print(f"Dimension: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
