from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from detector import analyze_image_bytes
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="Instamart AI Image Fraud Detector (Prototype)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (or restrict later)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Upload an image file.")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(400, "File is empty.")

    result = analyze_image_bytes(image_bytes)
    return JSONResponse(content=result)
