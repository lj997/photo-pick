import json
import cv2
import numpy as np


def analyze_exposure(filepath: str) -> tuple[float, bool, str]:
    """
    Analyze exposure using histogram analysis.
    Returns (score, has_issue, result_data_json).
    Score: 0.5 = well exposed, <0.3 = underexposed, >0.7 = overexposed.
    """
    try:
        img = cv2.imread(filepath)
        if img is None:
            return 0.5, False, "{}"

        # Resize for speed
        h, w = img.shape[:2]
        if max(h, w) > 1000:
            scale = 1000 / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)))

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        total_pixels = gray.shape[0] * gray.shape[1]

        # Calculate histogram
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()

        # Check clipped shadows (0-5)
        clipped_shadows = hist[:6].sum() / total_pixels
        # Check clipped highlights (250-255)
        clipped_highlights = hist[250:].sum() / total_pixels

        # Overall brightness
        mean_brightness = gray.mean() / 255.0

        # Determine issue
        is_underexposed = mean_brightness < 0.2 or clipped_shadows > 0.15
        is_overexposed = mean_brightness > 0.8 or clipped_highlights > 0.15
        has_issue = is_underexposed or is_overexposed

        result_data = json.dumps({
            "mean_brightness": round(float(mean_brightness), 3),
            "clipped_shadows_pct": round(float(clipped_shadows * 100), 2),
            "clipped_highlights_pct": round(float(clipped_highlights * 100), 2),
            "is_underexposed": is_underexposed,
            "is_overexposed": is_overexposed,
        })

        return float(mean_brightness), has_issue, result_data
    except Exception:
        return 0.5, False, "{}"
