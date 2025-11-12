import cv2
import numpy as np
from typing import Tuple
from ..config import MODEL_PATH, PROTO_PATH

# Load the DNN model once at import time
_net = cv2.dnn.readNetFromCaffe(str(PROTO_PATH), str(MODEL_PATH))


def detect_faces(image: np.ndarray, conf_threshold: float = 0.5) -> np.ndarray:
    """Detect faces on a BGR image and draw rectangles.

    Args:
        image: BGR image (np.ndarray)
        conf_threshold: minimum confidence to draw boxes
    Returns:
        image with rectangles drawn over detected faces
    """
    (h, w) = image.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 1.0,
                                 (300, 300), (104.0, 177.0, 123.0))
    _net.setInput(blob)
    detections = _net.forward()

    for i in range(0, detections.shape[2]):
        confidence = float(detections[0, 0, i, 2])
        if confidence >= conf_threshold:
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (x1, y1, x2, y2) = box.astype("int")
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    return image
