import io
import numpy as np
import cv2
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from ..services.dnn_face import detect_faces, count_faces

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


@router.post("/check_person")
async def check_person_endpoint(image: UploadFile = File(...)):
    """Check if a person (face) is detected in the image."""
    if not image:
        raise HTTPException(status_code=400, detail="No image uploaded")

    image_bytes = await image.read()
    npimg = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image format")

    face_count = count_faces(frame)

    return {
        "person_detected": face_count > 0,
        "face_count": face_count
    }

