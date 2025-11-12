from fastapi import FastAPI
from .routers.detect import router as detect_router
from .routers.chat import router as chat_router
from .routers.vision import router as vision_router
from .routers.autonomous import router as autonomous_router
from .config import HOST, PORT, DEBUG

app = FastAPI()

# Include routers
app.include_router(detect_router)
app.include_router(chat_router)
app.include_router(vision_router)
app.include_router(autonomous_router)

# For direct run: python -m server.main
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT, log_level="debug" if DEBUG else "info")
