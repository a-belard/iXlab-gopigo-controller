from typing import List, Dict
from groq import Groq
from ..config import GROQ_API_KEY, CHAT_MODEL

# Simple in-memory conversation store
_conversation_history: List[Dict[str, str]] = []

# Initialize Groq client lazily
_client: Groq | None = None

def _get_client() -> Groq:
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not set. Set environment variable GROQ_API_KEY.")
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def reset_history() -> None:
    global _conversation_history
    _conversation_history = []


def get_history() -> List[Dict[str, str]]:
    return _conversation_history


def get_ai_response(user_message: str, temperature: float = 0.7, max_tokens: int = 500) -> str:
    """Generate assistant reply and update history."""
    global _conversation_history

    if not _conversation_history:
        _conversation_history.append({
            "role": "system",
            "content": (
                "You are a helpful robot assistant. Be concise, clear, and practical."
            )
        })

    _conversation_history.append({"role": "user", "content": user_message})

    client = _get_client()
    messages = _conversation_history[-11:] if len(_conversation_history) > 11 else _conversation_history

    completion = client.chat.completions.create(
        messages=messages,
        model=CHAT_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    ai_response = completion.choices[0].message.content

    _conversation_history.append({"role": "assistant", "content": ai_response})
    return ai_response
