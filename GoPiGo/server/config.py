import os
from pathlib import Path
from dotenv import load_dotenv

# Project root (GoPiGo folder)
ROOT_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(ROOT_DIR / ".env")

# Model paths
MODEL_PATH = ROOT_DIR / "res10_300x300_ssd_iter_140000_fp16.caffemodel"
PROTO_PATH = ROOT_DIR / "deploy.prototxt"

# GROQ API key (prefer environment variable)
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_KEY")

# Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyASRw-7JjA6A65-oUDvqGIKjwd_wMm6RLo")

# Defaults for models
CHAT_MODEL = os.getenv("GROQ_CHAT_MODEL", "llama-3.3-70b-versatile")
VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
WHISPER_MODEL = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3-turbo")

# Gemini model for robotics vision
GEMINI_VISION_MODEL = os.getenv("GEMINI_VISION_MODEL", "gemini-robotics-er-1.5-preview")

# Server options
DEBUG = os.getenv("SERVER_DEBUG", "false").lower() == "true"
HOST = os.getenv("SERVER_HOST", "0.0.0.0")
PORT = int(os.getenv("SERVER_PORT", "8000"))
