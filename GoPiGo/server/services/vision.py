import base64
import json
import re
from typing import List, Dict
from groq import Groq
from ..config import GROQ_API_KEY, VISION_MODEL, CHAT_MODEL

_client: Groq | None = None

# Compact system context for faster processing
VISION_SYSTEM_CONTEXT = """Robot camera context:
- Ground robot with camera ~10-15 cm above the floor, angled slightly upward.
- Most of the frame is floor; objects appear from base upward.
- Lighting and shadows may vary; assume indoor navigation.
Focus on spatial layout, open path, and nearby obstacles."""

# Compact autonomous instruction (CACHED in Gemini for speed)
AUTONOMOUS_SYSTEM = """Autonomous navigation system for a ground robot.

Camera:
- Positioned ~10-15 cm high with slight upward tilt.
- Floor dominates lower frame; obstacles appear from base upward.

Sensors:
- Forward distance sensor (auto-stop if <25 cm).

Available actions:
- forward(50cm, fast)
- backward(30cm)
- left(30°) - turn left to explore left side
- right(30°) - turn right to explore right side
- stop
- complete (goal achieved)

Behavior rules:
1. Avoid tight spaces, gaps under furniture, or areas with low clearance.
2. If overhead furniture or ceiling appears closer or passage narrows, STOP or TURN.
3. If unsure about exit path, stop instead of entering.
4. Prioritize turning over reversing when avoiding obstacles.
5. Always trust sensors and act decisively.

IMPROVED SPATIAL ANALYSIS:
- Analyze LEFT EDGE of frame: Is there open space? Can robot turn left and explore?
- Analyze CENTER: Is forward path clear? Any obstacles blocking?
- Analyze RIGHT EDGE of frame: Is there open space? Can robot turn right and explore?
- If left or right side shows WIDE OPEN space (no walls, furniture, obstacles), consider turning toward that direction.
- If center is blocked but sides are open, TURN instead of going forward into obstacle.
- Use peripheral vision to detect alternative paths.

Navigation strategy:
- If center clear: go forward
- If center blocked + left open: turn left
- If center blocked + right open: turn right
- If center blocked + both sides unclear: backward or stop
- Prefer exploring open sides over forcing through narrow center

Objective:
Maintain safe, efficient motion by actively scanning and choosing the most open path."""


def _get_client() -> Groq:
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not set. Set environment variable GROQ_API_KEY.")
        _client = Groq(api_key=GROQ_API_KEY)
    return _client

# Caching disabled due to API compatibility issues
# def _get_or_create_cached_content() -> types.CachedContent:
#     """
#     Get or create Gemini cached content for autonomous system instructions.
#     This caches the system prompt to reduce latency and costs.
#     Cache lasts 1 hour by default.
#     """
#     global _cached_content
#     
#     if _cached_content is None:
#         client = _get_gemini_client()
#         
#         try:
#             # Create cached content with system instructions
#             _cached_content = client.caches.create(
#                 model=GEMINI_VISION_MODEL,
#                 contents=[
#                     types.Content(
#                         role="user",
#                         parts=[types.Part.from_text(text=AUTONOMOUS_SYSTEM)],
#                     )
#                 ],
#                 ttl="3600s",  # Cache for 1 hour
#                 display_name="robot_autonomous_system",
#             )
#             print(f"Created Gemini cache: {_cached_content.name}")
#         except Exception as e:
#             print(f"Warning: Could not create cache ({e}), will proceed without caching")
#             return None
#     
#     return _cached_content


def analyze_image_with_vision(image_bytes: bytes, prompt: str) -> str:
    client = _get_client()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": VISION_SYSTEM_CONTEXT
            },
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

    # Compact action history (last 3 only)
    action_context = ""
    if previous_actions:
        recent = previous_actions[-3:]
        action_context = f" Recent: {','.join(recent)}."

    # Improved spatial prompt for Groq
    user_prompt = f"""{AUTONOMOUS_SYSTEM}\n\nGoal: {goal}{action_context}\n\nDETAILED SPATIAL ANALYSIS:\n\nLEFT SIDE of frame:\n- Is there open floor space on the left edge?\n- Any obstacles/walls blocking left turn?\n- How wide/clear is the left pathway?\n\nCENTER of frame:\n- Is forward path clear and obstacle-free?\n- Any furniture/objects blocking straight ahead?\n- Is passage wide enough to continue forward?\n\nRIGHT SIDE of frame:\n- Is there open floor space on the right edge?\n- Any obstacles/walls blocking right turn?\n- How wide/clear is the right pathway?\n\nOVERHEAD check:\n- Any low-hanging objects (tables, chairs) getting closer?\n- Is vertical clearance safe?\n\nDECISION PRIORITY:\n1. If center is clear and wide: go FORWARD\n2. If center blocked but LEFT SIDE very open: turn LEFT\n3. If center blocked but RIGHT SIDE very open: turn RIGHT\n4. If center blocked and BOTH SIDES open: turn toward the MORE open side\n5. If all directions risky: STOP or BACKWARD\n\nRespond ONLY in JSON with your decision:\n{{\n"action": "forward|backward|left|right|stop|complete",\n"reasoning": "Explain left/center/right analysis and why this direction chosen",\n"observation": "Describe what you see: left side, center, right side openness",\n"progress": "percentage estimate toward goal (e.g., 60%)"\n}}"""

    completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": VISION_SYSTEM_CONTEXT
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                    },
                ],
            }
        ],
        model=VISION_MODEL,
        temperature=0.3,
        max_tokens=256,
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
