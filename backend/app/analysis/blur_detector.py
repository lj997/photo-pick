import cv2
import numpy as np


def detect_blur(filepath: str, threshold: float = 100.0) -> tuple[float, bool]:
    """Detect blur using Laplacian variance. Returns (score, is_blurry)."""
    try:
        img = cv2.imread(filepath)
        if img is None:
            return 0.0, False

        # Resize for consistent analysis speed
        h, w = img.shape[:2]
        if max(h, w) > 1000:
            scale = 1000 / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)))

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        # Normalize score to 0-1 range (higher = sharper)
        score = min(laplacian_var / 500.0, 1.0)
        is_blurry = laplacian_var < threshold

        return score, is_blurry
    except Exception:
        return 0.0, False
