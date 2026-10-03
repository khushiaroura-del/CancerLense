# CancerLense

### AI-Assisted Oral Lesion Screening Research Prototype

CancerLense is an AI-assisted research prototype for exploring image-based screening of oral lesions using deep learning and computer vision.

The system analyzes an uploaded or camera-captured image, checks basic image quality, generates a model-based screening signal, provides confidence and class scores, and uses Grad-CAM to visualize regions that influenced the model prediction.

> ⚠️ **Research Disclaimer:** CancerLense is a research and educational prototype. It is not a medical diagnostic system and must not be used to diagnose cancer or replace professional clinical examination.

---

## ✨ Features

- 🧠 MobileNetV3-based image classification
- 📸 Image upload and live camera capture
- 🔍 Image quality analysis
- 📊 Model confidence and class scores
- 🔥 Grad-CAM explainability
- 👤 Patient research context
- 🚩 Red-flag context review
- ⚡ FastAPI backend
- 💻 React + Vite frontend
- 🧪 Model evaluation pipeline
- 🎯 Research-oriented screening workflow

---

## 🧠 How It Works

```text
Image Upload / Camera
        ↓
Image Quality Analysis
        ↓
MobileNetV3 Classification
        ↓
Confidence + Class Scores
        ↓
Grad-CAM Explainability
        ↓
Research Screening Output
        ↓
Patient Context & Red-Flag Review
```

---

## 🔬 AI Model

CancerLense currently uses:

- **Architecture:** MobileNetV3 Small
- **Framework:** PyTorch
- **Computer Vision:** OpenCV
- **Explainability:** Grad-CAM
- **Classes:**
  - Cancer
  - Non-Cancer

The model output is presented as a **screening signal**, not a diagnosis.

---

## 📊 Current Evaluation

The current local test evaluation contains **17 test images**.

| Metric | Result |
|---|---:|
| Accuracy | 88.24% |
| Sensitivity | 90.00% |
| Specificity | 85.71% |
| True Positives | 9 |
| True Negatives | 6 |
| False Positives | 1 |
| False Negatives | 1 |

These results represent the current local test split and should not be interpreted as clinical performance or real-world diagnostic accuracy.

---

## 🔍 Image Quality Analysis

CancerLense evaluates basic image properties before processing the image, including:

- Image resolution
- Brightness
- Sharpness
- Overall image quality status

This helps identify whether an image is suitable for the current research pipeline.

---

## 🔥 Grad-CAM Explainability

CancerLense generates a Grad-CAM visualization showing image regions that contributed to the model's prediction.

Grad-CAM is used for model explainability and does not represent a clinically validated lesion boundary or diagnosis.

---

## 📸 Camera & Image Upload

CancerLense supports:

- Image upload
- Drag-and-drop image selection
- Live camera capture
- Captured image preview
- Retake functionality
- AI analysis of the selected image

---

## 👤 Patient Research Context

The interface allows optional research context such as:

- Age group
- Tobacco exposure
- Alcohol exposure
- Previous oral lesion
- Previous oral cancer
- Dental history
- Symptoms
- Symptom duration
- Additional notes

Patient context is kept separate from the image-based model prediction.

---

## 🚩 Red-Flag Context Review

CancerLense can surface research-oriented review prompts based on user-provided information, including:

- Persistent or non-healing lesion
- Bleeding
- White or red patch
- Lump or thickening
- Difficulty swallowing
- Numbness
- Tobacco exposure
- Alcohol exposure
- Previous oral lesion or cancer
- Symptom duration

These are **research context flags**, not diagnostic risk scores.

---

## 🛠️ Tech Stack

### Machine Learning

- Python
- PyTorch
- Torchvision
- MobileNetV3
- OpenCV
- Pillow
- Grad-CAM
- NumPy
- Pandas
- Scikit-learn

### Backend

- FastAPI
- Uvicorn
- Pydantic

### Frontend

- React
- Vite
- Axios
- Lucide React
- CSS

---

## 📁 Project Structure

```text
CancerLense/
│
├── app/
│   └── backend/
│       ├── api/
│       │   └── main.py
│       │
│       └── ml/
│           ├── dataset.py
│           ├── evaluate.py
│           ├── grad_cam.py
│           ├── image_processor.py
│           ├── mobilenet_model.py
│           ├── predict.py
│           └── train.py
│
├── frontend/
│   ├── public/
│   │   └── hero-medical.png
│   │
│   ├── src/
│   │   ├── components/
│   │   │   ├── PatientContext.jsx
│   │   │   └── RedFlagPanel.jsx
│   │   │
│   │   ├── App.jsx
│   │   └── App.css
│   │
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/khushiaroura-del/CancerLense.git
cd CancerLense
```

### 2. Create virtual environment

```powershell
python -m venv .venv
```

### 3. Activate environment

```powershell
.\.venv\Scripts\activate
```

### 4. Install Python dependencies

```powershell
pip install -r requirements.txt
```

### 5. Start FastAPI backend

```powershell
python -m uvicorn app.backend.api.main:app --reload
```

### 6. Start frontend

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

---

## 🔌 API

The main image analysis endpoint is:

```text
POST /analyze
```

Example response:

```json
{
  "status": "ANALYZED",
  "prediction_class": "cancer",
  "model_confidence": 93.78,
  "class_scores": {
    "cancer": 93.78,
    "non_cancer": 6.22
  },
  "quality": {
    "width": 744,
    "height": 557,
    "brightness": 134.42,
    "sharpness": 106.97,
    "quality_status": "ACCEPTABLE"
  },
  "gradcam": "/results/gradcam/example_gradcam.jpg"
}
```

---

## 🔐 Privacy & Repository Safety

The following directories are intentionally excluded from Git:

```text
datasets/
models/
results/
```

Generated uploads and Grad-CAM outputs are also excluded.

This helps prevent research images, model artifacts, and generated runtime data from being committed to the public repository.

---

## 🧪 Research Direction

Future development may explore:

- Multi-condition oral lesion classification
- Model uncertainty estimation
- Out-of-distribution detection
- Abstention / "I don't know" mode
- Multi-view image analysis
- Lesion location mapping
- Image-based lesion measurement with calibration
- Before/after lesion comparison
- Lesion evolution timeline
- Smart image capture guidance
- Professional review workflow
- Research report generation
- Model version and reproducibility tracking
- Offline research workflows

These capabilities require appropriate datasets, validation, and implementation before being considered functional clinical features.

---

## ⚠️ Medical Disclaimer

CancerLense is an **AI-assisted research screening prototype**.

Its output:

- Is not a medical diagnosis
- Does not confirm or rule out cancer
- Should not replace professional medical examination
- Should not be used as the sole basis for medical decisions
- Has not been presented as clinically validated

Model confidence represents the model's output for an input image. It does not represent clinical certainty.

For any concerning oral lesion or persistent symptom, professional clinical evaluation should be sought.

---

## 👩‍💻 Author

**Khushi Aroura**

BTech IT Student  
Developer in Progress • Video Editor • CMO @ TIFO India

GitHub:  
https://github.com/khushiaroura-del

---

## 📌 Project Status

**Research Prototype — Actively Developed**

CancerLense is being developed as an experimental AI + computer vision project for research, learning, and hackathon development.

---

## 📄 License

This project is currently provided for research and educational purposes.
