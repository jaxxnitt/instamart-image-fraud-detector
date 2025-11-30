from io import BytesIO
from typing import Dict, Any
from PIL import Image, ImageChops, ExifTags
import numpy as np

SUSPICIOUS_SOFTWARE_KEYWORDS = [
    "photoshop", "gemini", "stable diffusion", "midjourney", "gimp", "ai"
]


def _get_exif_dict(image: Image.Image) -> Dict[str, Any]:
    exif_data = getattr(image, "_getexif", lambda: None)()
    if not exif_data:
        return {}

    exif = {}
    for tag_id, value in exif_data.items():
        tag = ExifTags.TAGS.get(tag_id, tag_id)
        exif[tag] = value
    return exif


def _compute_ela_features(image: Image.Image, quality: int = 90):
    image = image.convert("RGB")
    buffer = BytesIO()
    image.save(buffer, "JPEG", quality=quality)
    buffer.seek(0)
    resaved = Image.open(buffer).convert("RGB")

    diff = ImageChops.difference(image, resaved)
    diff_arr = np.asarray(diff).astype("float32")

    intensity = diff_arr.mean(axis=2)

    mean_ela = float(intensity.mean())
    threshold = 25.0
    hot_pixels = (intensity > threshold).sum()
    total_pixels = intensity.size
    hot_fraction = float(hot_pixels) / float(total_pixels)

    return mean_ela, hot_fraction


def analyze_image_bytes(image_bytes: bytes) -> Dict[str, Any]:
    image = Image.open(BytesIO(image_bytes))

    exif = _get_exif_dict(image)
    exif_present = len(exif) > 0

    software_tag = str(exif.get("Software", "")).lower()
    suspicious_software = any(k in software_tag for k in SUSPICIOUS_SOFTWARE_KEYWORDS)

    dt_original = exif.get("DateTimeOriginal")
    dt_digitized = exif.get("DateTimeDigitized")
    dt_generic = exif.get("DateTime")

    mean_ela, hot_fraction = _compute_ela_features(image)

    mean_ela_norm = min(mean_ela / 255.0, 1.0)

    score = 0.0
    reasons = []

    score += 0.4 * mean_ela_norm
    if mean_ela_norm > 0.15:
        reasons.append(f"Elevated ELA mean ({mean_ela:.2f}).")

    score += 0.3 * min(hot_fraction * 3.0, 1.0)
    if hot_fraction > 0.05:
        reasons.append(f"High ELA hotspot fraction ({hot_fraction:.3f}).")

    if not exif_present:
        score += 0.2
        reasons.append("EXIF metadata missing.")

    if suspicious_software:
        score += 0.1
        reasons.append(f"Editing software detected: '{software_tag}'.")

    tampering_score = max(0.0, min(score, 1.0))

    if tampering_score < 0.3:
        recommendation = "auto_approve_ok"
    elif tampering_score < 0.6:
        recommendation = "low_priority_manual_review"
    else:
        recommendation = "high_priority_manual_review"

    if not reasons:
        reasons.append("No major tampering signals.")

    return {
        "tampering_score": round(tampering_score, 3),
        "recommendation": recommendation,
        "signals": {
            "exif_present": exif_present,
            "software_tag": software_tag or None,
            "datetime_original": dt_original,
            "datetime_digitized": dt_digitized,
            "datetime_generic": dt_generic,
            "mean_ela": round(mean_ela, 3),
            "hot_fraction": round(hot_fraction, 4),
        },
        "explanation": " ".join(reasons),
    }
