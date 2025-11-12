import base64
import json
import re
from typing import List, Dict
from groq import Groq
from ..config import GROQ_API_KEY, VISION_MODEL, CHAT_MODEL

_client: Groq | None = None

def _get_client() -> Groq:
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not set. Set environment variable GROQ_API_KEY.")
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def analyze_image_with_vision(image_bytes: bytes, prompt: str) -> str:
    client = _get_client()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                    },
                ],
            }
        ],
        model=VISION_MODEL,
        temperature=0.7,
        max_tokens=1024,
    )

    return completion.choices[0].message.content


def make_autonomous_decision(image_bytes: bytes, goal: str, previous_actions: List[str]) -> Dict:
    client = _get_client()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    action_context = ""
    if previous_actions:
        action_context = f"\n\nPrevious actions: {', '.join(previous_actions[-5:])}"

    prompt = f"""You are controlling a robot with a camera. Your goal is: {goal}

Analyze the image and decide the NEXT SINGLE ACTION the robot should take.

Available actions:
- forward: Move forward
- backward: Move backward
- left: Turn left
- right: Turn right
- stop: Stop moving
- complete: Goal is achieved

Respond in this EXACT JSON format:
{{
    "action": "forward|backward|left|right|stop|complete",
    "reasoning": "Brief explanation of why you chose this action",
    "observation": "What you see in the image",
    "progress": "How close are we to the goal (percentage)"
}}
{action_context}

Be decisive and choose ONE action. Consider safety - stop if you see obstacles very close."""

    completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                    },
                ],
            }
        ],
        model=VISION_MODEL,
        temperature=0.5,
        max_tokens=512,
    )

    response_text = completion.choices[0].message.content

    # Try extracting JSON block
    match = re.search(r"\{.*\}", response_text, re.DOTALL)
    if match:
        try:
            return {"success": True, "decision": json.loads(match.group())}
        except json.JSONDecodeError:
            pass

    # Fallback if parsing fails
    return {
        "success": True,
        "decision": {
            "action": "stop",
            "reasoning": "Could not parse decision JSON",
            "observation": response_text,
            "progress": "0%",
        },
    }
