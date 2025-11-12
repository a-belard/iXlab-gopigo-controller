import io
import numpy as np
import cv2
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from ..services.dnn_face import detect_faces

router = APIRouter()

@router.post("/detect")
async def detect_endpoint(image: UploadFile = File(...)):
    if not image:
        raise HTTPException(status_code=400, detail="No image uploaded")

    image_bytes = await image.read()
    npimg = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image format")

    processed = detect_faces(frame)

    _, img_encoded = cv2.imencode(".jpg", processed)
    return StreamingResponse(io.BytesIO(img_encoded.tobytes()), media_type="image/jpeg")
