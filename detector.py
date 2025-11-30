import io
import numpy as np
from PIL import Image, ImageChops
import cv2

# -------------------------
# Helper: Extract EXIF metadata
# -------------------------
def extract_exif(image: Image.Image):
    try:
        exif = image.getexif()
        if not exif or len(exif) == 0:
            return False, None, None, None, None

        exif_dict = {image.getexif().get_ifd(0).get(tag): val for tag, val in exif.items()}
        software = exif_dict.get(305) if exif_dict else None   # "Software"
        dt_original = exif_dict.get(36867) if exif_dict else None
        dt_digitized = exif_dict.get(36868) if exif_dict else None
        dt_generic = exif_dict.get(306) if exif_dict else None  # DateTime

        return True, software, dt_original, dt_digitized, dt_generic

    except Exception:
        return False, None, None, None, None


# -------------------------
# Helper: Error Level Analysis (ELA)
# -------------------------
def error_level_analysis(image: Image.Image):
    ela_temp = io.BytesIO()
    image.save(ela_temp, "JPEG", quality=95)
    ela_temp.seek(0)

    recompressed = Image.open(ela_temp)
    ela = ImageChops.difference(image, recompressed)

    ela_arr = np.array(ela.convert("L"))
    mean_ela = float(np.mean(ela_arr))
    hot_fraction = float(np.mean(ela_arr > 40))

    return mean_ela, hot_fraction


# -------------------------
# Helper: High-frequency (texture) analysis
# AI-regenerated images tend to lack micro-textures.
# -------------------------
def high_frequency_score(np_img):
    gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    return float(laplacian.var())


# -------------------------
# Helper: RGB correlation (GAN signature)
# AI images often have overly correlated color channels.
# -------------------------
def rgb_correlation(np_img):
    r, g, b = np_img[:, :, 0], np_img[:, :, 1], np_img[:, :, 2]
    corr_rg = np.corrcoef(r.flatten(), g.flatten())[0, 1]
    corr_gb = np.corrcoef(g.flatten(), b.flatten())[0, 1]
    corr_rb = np.corrcoef(r.flatten(), b.flatten())[0, 1]
    return float(corr_rg), float(corr_gb), float(corr_rb)


# -------------------------
# MAIN FUNCTION
# -------------------------
def analyze_image_bytes(image_bytes: bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    np_img = np.array(image)

    # -------------------------
    # Extract EXIF
    # -------------------------
    exif_present, software_tag, dt_orig, dt_dig, dt_gen = extract_exif(image)

    # -------------------------
    # ELA
    # -------------------------
    mean_ela, hot_fraction = error_level_analysis(image)

    # -------------------------
    # Texture score
    # -------------------------
    hf = high_frequency_score(np_img)

    # -------------------------
    # Color correlation
    # -------------------------
    corr_rg, corr_gb, corr_rb = rgb_correlation(np_img)

    # -------------------------
    # Scoring logic
    # -------------------------
    score = 0.0
    explanation_parts = []

    # 1. Missing EXIF
    if not exif_present:
        score += 0.25
        explanation_parts.append("EXIF metadata missing")

    # 2. Software tag suspicious (Photoshop, Snapseed, Gemini, etc.)
    if software_tag:
        st = software_tag.lower()
        if "photoshop" in st or "gemini" in st or "snapseed" in st or "edit" in st:
            score += 0.3
            explanation_parts.append(f"Software tag indicates editing: {software_tag}")

    # 3. ELA anomalies (local edits)
    if mean_ela > 10 or hot_fraction > 0.02:
        score += 0.35
        explanation_parts.append("ELA hotspots detected (local edits likely)")

    # 4. High-frequency too LOW (AI regeneration)
    if hf < 35:
        score += 0.30
        explanation_parts.append("Very low high-frequency detail (AI-regenerated image likely)")

    # 5. RGB correlations too high (GAN signature)
    if corr_rg > 0.985 and corr_gb > 0.985 and corr_rb > 0.985:
        score += 0.30
        explanation_parts.append("Abnormally high RGB channel correlation (AI signature)")

    # 6. Strong synthetic indicator: no EXIF + low ELA + low HF
    if not exif_present and mean_ela < 4 and hf < 35:
        score = max(score, 0.75)
        explanation_parts.append("Strong evidence of fully synthetic or AI-modified image")

    # Normalize score
    score = max(0.0, min(score, 1.0))

    # Labels
    if score < 0.30:
        recommendation = "auto_approve_ok"
    elif score < 0.60:
        recommendation = "low_priority_manual_review"
    else:
        recommendation = "high_priority_manual_review"

    explanation = " | ".join(explanation_parts) if explanation_parts else "No tampering signals detected."

    return {
        "tampering_score": round(score, 3),
        "recommendation": recommendation,
        "signals": {
            "exif_present": exif_present,
            "software_tag": software_tag,
            "datetime_original": dt_orig,
            "datetime_digitized": dt_dig,
            "datetime_generic": dt_gen,
            "mean_ela": round(mean_ela, 3),
            "hot_fraction": round(hot_fraction, 3),
            "high_freq_variance": round(hf, 3),
            "corr_rg": round(corr_rg, 4),
            "corr_gb": round(corr_gb, 4),
            "corr_rb": round(corr_rb, 4),
        },
        "explanation": explanation,
    }
