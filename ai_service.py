import os
import json
import re
import httpx
from typing import Any, List, Dict

# ---------------------------------------------------------------------------
# Helper to extract JSON from LLM markdown responses
# ---------------------------------------------------------------------------
def _extract_json(text: str) -> str:
    m = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?\s*```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()

# ---------------------------------------------------------------------------
# Core inference call – single place for timeout, auth, error handling
# ---------------------------------------------------------------------------
async def _call_inference(messages: List[Dict[str, str]], max_tokens: int = 512) -> Any:
    api_key = os.getenv("DIGITALOCEAN_INFERENCE_KEY", "")
    model = os.getenv("DO_INFERENCE_MODEL", "openai-gpt-oss-120b")
    url = "https://inference.do-ai.run/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": messages,
        "max_completion_tokens": max_tokens,
    }
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            # Expected OpenAI‑compatible response format
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content:
                raise ValueError("Empty content from inference API")
            json_str = _extract_json(content)
            return json.loads(json_str)
    except Exception as exc:
        # Fallback – callers will interpret the dict
        return {"note": f"AI service unavailable: {str(exc)}"}

# ---------------------------------------------------------------------------
# Public wrapper for flashcard generation
# ---------------------------------------------------------------------------
async def generate_flashcards(text: str, max_cards: int) -> List[Dict[str, str]]:
    system_prompt = (
        "You are a flashcard generation assistant. Given a block of educational text, "
        "create up to the requested number of concise question/answer pairs that capture "
        "the most important concepts. Return a JSON array where each element has the keys "
        "'question' and 'answer'. Do not include any additional explanation or markdown."
    )
    user_prompt = f"Text:\n{text}\n\nGenerate at most {max_cards} flashcards."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    result = await _call_inference(messages, max_tokens=512)
    # If the service returned a fallback dict with a note, propagate it as empty list
    if isinstance(result, dict) and result.get("note"):
        return []
    if isinstance(result, list):
        return result
    # Unexpected format – treat as empty
    return []