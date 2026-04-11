import os

import httpx
from dotenv import dotenv_values, find_dotenv

MODEL = "openai/gpt-oss-120b"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"

# Read from .env file first (dev), fall back to os.environ (Docker / CI)
_dotenv_path = find_dotenv(usecwd=True)
_file_env = dotenv_values(_dotenv_path) if _dotenv_path else {}


def get_api_key() -> str:
    api_key = _file_env.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not set in .env or environment")
    return api_key


async def chat_completion(api_key: str, messages: list[dict], **kwargs) -> str:
    """Call the OpenRouter chat completions endpoint and return the response content."""
    payload = {"model": MODEL, "messages": messages, **kwargs}
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{OPENROUTER_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
