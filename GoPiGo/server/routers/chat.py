from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from ..services import chat as chat_service
from ..services.vision import _get_client  # for audio transcription
from ..config import WHISPER_MODEL

router = APIRouter()

class TextMessage(BaseModel):
    message: str
    reset_history: bool = False

@router.post("/chat/text")
async def chat_text(message: TextMessage):
    if message.reset_history:
        chat_service.reset_history()

    text = message.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        response = chat_service.get_ai_response(text)
        return JSONResponse({
            "user_message": text,
            "ai_response": response,
            "conversation_length": len(chat_service.get_history())
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/audio")
async def chat_audio(audio: UploadFile = File(...)):
    if not audio:
        raise HTTPException(status_code=400, detail="No audio file uploaded")

    try:
        client = _get_client()
        audio_bytes = await audio.read()
        transcription = client.audio.transcriptions.create(
            file=(audio.filename or "audio.wav", audio_bytes),
            model=WHISPER_MODEL,
            response_format="text",
        )

        user_message = transcription.strip()
        if not user_message:
            raise HTTPException(status_code=400, detail="Could not transcribe audio")

        ai_response = chat_service.get_ai_response(user_message)
        return JSONResponse({
            "transcribed_text": user_message,
            "ai_response": ai_response,
            "conversation_length": len(chat_service.get_history())
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")

@router.post("/chat/reset")
async def reset_conversation():
    chat_service.reset_history()
    return JSONResponse({"message": "Conversation history reset successfully"})

@router.get("/chat/history")
async def get_history():
    return JSONResponse({
        "history": chat_service.get_history(),
        "message_count": len(chat_service.get_history())
    })
