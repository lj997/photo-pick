import cv2
import numpy as np


def detect_closed_eyes(filepath: str) -> tuple[float, bool]:
    """
    Detect closed eyes using OpenCV face/eye cascade classifiers.
    Returns (score, has_closed_eyes).
    Score: ratio of faces with detected open eyes (1.0 = all eyes open).
    """
    try:
        img = cv2.imread(filepath)
        if img is None:
            return 1.0, False

        h, w = img.shape[:2]
        if max(h, w) > 1000:
            scale = 1000 / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)))

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye.xml"
        )

        faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))

        if len(faces) == 0:
            return 1.0, False

        faces_with_open_eyes = 0
        for (x, y, fw, fh) in faces:
            roi_gray = gray[y:y + fh, x:x + fw]
            # Search in upper half of face for eyes
            upper_half = roi_gray[:fh // 2, :]
            eyes = eye_cascade.detectMultiScale(upper_half, 1.1, 3, minSize=(15, 15))

            if len(eyes) >= 2:
                faces_with_open_eyes += 1

        score = faces_with_open_eyes / len(faces) if len(faces) > 0 else 1.0
        has_closed_eyes = score < 1.0 and len(faces) > 0

        return score, has_closed_eyes
    except Exception:
        return 1.0, False
