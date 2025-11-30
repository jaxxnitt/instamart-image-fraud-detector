**Instamart Image Fraud Detector (Prototype)**

Live Demo
https://jaxxnitt.github.io/instamart-image-fraud-detector/

Backend API
https://instamart-image-fraud-detector.onrender.com/analyze

**Overview**

Quick-commerce platforms like Swiggy Instamart rely on customer-uploaded images for refunds. With modern tools (Gemini, ChatGPT, Photoshop, Snapseed), customers can edit or regenerate images to falsely claim damage.

This prototype detects possible image tampering or AI involvement. It returns a tampering score (0 to 1) and a recommendation that can support refund decisions.

**What the System Does**

Accepts an uploaded proof image.

Runs several digital forensics and AI-detection checks.

Produces a tampering score.

Returns a clear recommendation:


auto_approve_ok

low_priority_manual_review

high_priority_manual_review

Returns a readable explanation and raw signal values.

**Detection Methods**

The detector uses a combination of lightweight, explainable techniques:

1. EXIF Metadata

Checks for EXIF data, timestamps, and software tags.
Missing EXIF or editing software indicates manipulation or AI origin.

2. Error Level Analysis (ELA)

Detects local modifications by comparing the original image to a recompressed version.
Higher ELA or hotspot regions indicate possible edits.

3. Texture Analysis

Measures the high-frequency variance using a Laplacian operator.
AI-regenerated images tend to be overly smooth.

4. RGB Channel Correlation

GAN-generated images often have unusually high correlation between R, G, and B channels.
Real camera sensors usually have more independent channel noise.

5. Combined Scoring

Each signal adds to a final tampering score:

Below 0.30: auto approve

0.30 to 0.60: manual review

Above 0.60: high-priority review

A special rule increases the score if the image simultaneously lacks EXIF, has low ELA, and has low texture. This captures the case where users upload real images to Gemini/ChatGPT and regenerate them with artificial damage.

**Architecture**

docs/index.html: Frontend (GitHub Pages)

app.py: FastAPI backend

detector.py: Image forensics logic

requirements.txt: Dependencies

**Limitations**

Not trained on Instamart-specific data.

Uses heuristic forensic methods (not a learned model).

Very high-quality regenerated images can bypass the detector.

Best used as a supplementary signal and not a final decision-maker.

**Future Improvements**

Train a supervised model
Use real Instamart refund images (genuine and fraudulent) to train a lightweight classifier.
This would significantly improve accuracy compared to heuristic methods.

Add noise-pattern analysis
Mobile cameras have unique sensor noise (Photo Response Non-Uniformity).
Comparing this pattern to a reference can detect AI regeneration or image splicing.

Add JPEG quantization table checks
AI-generated images often use non-standard JPEG tables.
Extracting and comparing these provides another strong signal of manipulation.

Add background consistency checks
Use segmentation to compare texture, color, and lighting consistency across regions.
Helps detect when only the product area is edited.

**Local Development**
pip install -r requirements.txt
uvicorn app:app --reload


Open: http://127.0.0.1:8000/docs

Frontend: open docs/index.html in a browser.
