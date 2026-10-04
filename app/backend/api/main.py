from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.backend.ml.predict import predict_image


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

RESULTS_DIR = PROJECT_ROOT / "results"
UPLOADS_DIR = RESULTS_DIR / "uploads"
GRADCAM_DIR = RESULTS_DIR / "gradcam"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
GRADCAM_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="CancerLens API",
    description="AI-assisted oral image screening research API",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STATIC RESULTS
# ============================================================

# Allows the frontend to access generated Grad-CAM images.
app.mount(
    "/results",
    StaticFiles(directory=str(RESULTS_DIR)),
    name="results",
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "name": "CancerLens",
        "status": "ONLINE",
        "message": "CancerLens AI screening API is running.",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "CancerLens API",
    }


# ============================================================
# ANALYZE IMAGE
# ============================================================

@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):

    # --------------------------------------------------------
    # Validate file type
    # --------------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided.",
        )

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }

    extension = Path(file.filename).suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported image format. "
                "Please upload JPG, JPEG, PNG or WEBP."
            ),
        )

    # --------------------------------------------------------
    # Read uploaded file
    # --------------------------------------------------------

    try:
        contents = await file.read()

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to read uploaded image: {exc}",
        )

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty.",
        )

    # --------------------------------------------------------
    # Create unique filename
    # --------------------------------------------------------

    unique_id = uuid4().hex

    saved_filename = f"{unique_id}{extension}"

    saved_path = UPLOADS_DIR / saved_filename

    # --------------------------------------------------------
    # Save image
    # --------------------------------------------------------

    try:

        with open(saved_path, "wb") as output_file:
            output_file.write(contents)

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Unable to save uploaded image: {exc}",
        )

    # --------------------------------------------------------
    # Run AI prediction
    # --------------------------------------------------------

    try:

        result = predict_image(str(saved_path))

    except TypeError:

        # Some implementations accept a Path instead of string.
        try:
            result = predict_image(saved_path)

        except Exception as exc:

            raise HTTPException(
                status_code=500,
                detail=f"AI prediction failed: {exc}",
            )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"AI prediction failed: {exc}",
        )

    # --------------------------------------------------------
    # Convert Grad-CAM filesystem path into browser URL
    # --------------------------------------------------------

    if isinstance(result, dict):

        if result.get("gradcam"):

            gradcam_path = Path(result["gradcam"])

            result["gradcam"] = (
                f"/results/gradcam/{gradcam_path.name}"
            )

        result["original_filename"] = file.filename

        return result

    # --------------------------------------------------------
    # Safety fallback
    # --------------------------------------------------------

    return {
        "status": "ANALYZED",
        "prediction": result,
        "original_filename": file.filename,
        "note": (
            "This is an AI-assisted research screening output "
            "and not a medical diagnosis."
        ),
    }