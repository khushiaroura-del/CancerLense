import {
  Activity,
  AlertCircle,
  ArrowRight,
  Camera,
  CheckCircle2,
  CircleAlert,
  Clock3,
  FileImage,
  FolderOpen,
  Info,
  Loader2,
  Microscope,
  RefreshCcw,
  ScanSearch,
  ShieldCheck,
  Sparkles,
  Upload,
  UserRound,
  X,
} from "lucide-react";
import axios from "axios";
import { useEffect, useRef, useState } from "react";

import PatientContext from "./components/PatientContext";
import RedFlagPanel from "./components/RedFlagPanel";

import "./App.css";

const API_URL = "http://127.0.0.1:8000";

const initialPatientContext = {
  ageGroup: "",
  tobaccoExposure: "",
  alcoholExposure: "",
  previousOralLesion: "",
  previousOralCancer: "",
  dentalHistory: "",
  symptoms: [],
  symptomDuration: "",
  symptomNotes: "",
};

function App() {
  // ============================================================
  // IMAGE STATE
  // ============================================================

  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [imageSource, setImageSource] = useState("");
  const [dragActive, setDragActive] = useState(false);

  // ============================================================
  // CAMERA STATE
  // ============================================================

  const [cameraOpen, setCameraOpen] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const [capturedPreview, setCapturedPreview] = useState("");

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  // ============================================================
  // ANALYSIS STATE
  // ============================================================

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  // ============================================================
  // UI STATE
  // ============================================================

  const [activeExplainability, setActiveExplainability] =
    useState("original");

  const [showPatientContext, setShowPatientContext] =
    useState(false);

  const [patientContext, setPatientContext] = useState(
    initialPatientContext
  );

  // ============================================================
  // CAMERA CLEANUP
  // ============================================================

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        track.stop();
      });

      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setCameraReady(false);
  };

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  // ============================================================
  // PREVIEW CLEANUP
  // ============================================================

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  // ============================================================
  // START CAMERA
  // ============================================================

  const startCamera = async () => {
    setCameraError("");
    setCapturedPreview("");
    setCameraOpen(true);

    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error(
          "Camera access is not supported by this browser."
        );
      }

      const stream =
        await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: "environment",
            width: {
              ideal: 1280,
            },
            height: {
              ideal: 720,
            },
          },
          audio: false,
        });

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;

        await videoRef.current.play();

        setCameraReady(true);
      }
    } catch (cameraAccessError) {
      console.error(cameraAccessError);

      setCameraError(
        "Camera access was blocked or unavailable. Please allow camera permission and try again."
      );

      stopCamera();
    }
  };

  // ============================================================
  // CLOSE CAMERA
  // ============================================================

  const closeCamera = () => {
    stopCamera();

    setCameraOpen(false);
    setCameraError("");
    setCapturedPreview("");
  };

  // ============================================================
  // CAPTURE PHOTO
  // ============================================================

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) {
      return;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;

    const width = video.videoWidth;
    const height = video.videoHeight;

    if (!width || !height) {
      setCameraError(
        "Camera is not ready yet. Please wait a moment and try again."
      );

      return;
    }

    canvas.width = width;
    canvas.height = height;

    const context = canvas.getContext("2d");

    context.drawImage(
      video,
      0,
      0,
      width,
      height
    );

    canvas.toBlob(
      (blob) => {
        if (!blob) {
          setCameraError(
            "Unable to capture the image. Please try again."
          );

          return;
        }

        const timestamp = new Date()
          .toISOString()
          .replace(/[:.]/g, "-");

        const file = new File(
          [blob],
          `cancerlense-camera-${timestamp}.jpg`,
          {
            type: "image/jpeg",
          }
        );

        const url = URL.createObjectURL(file);

        setSelectedFile(file);
        setImageSource("camera");
        setResult(null);
        setError("");

        setPreviewUrl((oldUrl) => {
          if (oldUrl) {
            URL.revokeObjectURL(oldUrl);
          }

          return url;
        });

        setCapturedPreview(url);
      },
      "image/jpeg",
      0.95
    );
  };

  // ============================================================
  // RETAKE
  // ============================================================

  const retakePhoto = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    setSelectedFile(null);
    setCapturedPreview("");
    setPreviewUrl("");
    setImageSource("");
    setError("");
    setResult(null);

    if (videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;
    }
  };

  // ============================================================
  // USE PHOTO
  // ============================================================

  const useCapturedPhoto = () => {
    stopCamera();

    setCameraOpen(false);
    setCapturedPreview("");
  };

  // ============================================================
  // HANDLE FILE
  // ============================================================

  const handleFile = (file) => {
    if (!file) {
      return;
    }

    if (!file.type.startsWith("image/")) {
      setError("Please select a valid image file.");
      return;
    }

    const maxSize = 15 * 1024 * 1024;

    if (file.size > maxSize) {
      setError(
        "Image is too large. Please choose an image below 15 MB."
      );

      return;
    }

    const url = URL.createObjectURL(file);

    setSelectedFile(file);
    setImageSource("device");
    setError("");
    setResult(null);

    setPreviewUrl((oldUrl) => {
      if (oldUrl) {
        URL.revokeObjectURL(oldUrl);
      }

      return url;
    });
  };

  // ============================================================
  // FILE INPUT
  // ============================================================

  const handleFileInput = (event) => {
    const file = event.target.files?.[0];

    handleFile(file);

    event.target.value = "";
  };

  // ============================================================
  // DRAG & DROP
  // ============================================================

  const handleDragEnter = (event) => {
    event.preventDefault();
    event.stopPropagation();

    setDragActive(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    event.stopPropagation();

    setDragActive(false);
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    event.stopPropagation();

    setDragActive(true);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    event.stopPropagation();

    setDragActive(false);

    const file = event.dataTransfer.files?.[0];

    handleFile(file);
  };

  // ============================================================
  // NORMALIZE API RESULT
  // ============================================================

  const normalizeResult = (data) => {
    if (!data) {
      return null;
    }

    return {
      ...data,

      prediction_class:
        data.prediction_class ||
        data.prediction ||
        "unknown",

      model_confidence:
        Number(
          data.model_confidence ??
            data.confidence ??
            0
        ),

      class_scores: data.class_scores || {},

      quality: data.quality || {},

      recommendation:
        data.recommendation ||
        "Professional clinical evaluation is recommended.",

      note:
        data.note ||
        "This is an AI-assisted research screening output and not a medical diagnosis.",

      gradcam: data.gradcam || null,
    };
  };

  // ============================================================
  // ANALYZE
  // ============================================================

  const analyzeImage = async () => {
    if (!selectedFile) {
      setError("Please select or capture an image first.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);
    setActiveExplainability("original");

    try {
      const formData = new FormData();

      formData.append("file", selectedFile);

      const response = await axios.post(
        `${API_URL}/analyze`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      const normalized = normalizeResult(
        response.data
      );

      setResult(normalized);
    } catch (requestError) {
      console.error(requestError);

      if (requestError.response?.data?.detail) {
        setError(
          typeof requestError.response.data.detail ===
            "string"
            ? requestError.response.data.detail
            : "The backend rejected the image."
        );
      } else if (requestError.request) {
        setError(
          "CancerLense backend is not reachable. Make sure FastAPI is running on port 8000."
        );
      } else {
        setError(
          "Something went wrong while analyzing the image."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // RESET
  // ============================================================

  const resetCase = () => {
    stopCamera();

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    setCameraOpen(false);
    setCameraError("");
    setCapturedPreview("");

    setSelectedFile(null);
    setPreviewUrl("");
    setImageSource("");

    setResult(null);
    setError("");

    setPatientContext(initialPatientContext);

    setActiveExplainability("original");
  };

  // ============================================================
  // PATIENT CONTEXT
  // ============================================================

  const handlePatientContextSave = (data) => {
    setPatientContext(data);
    setShowPatientContext(false);
  };

  // ============================================================
  // RESULT HELPERS
  // ============================================================

  const predictionClass =
    result?.prediction_class?.toLowerCase() || "";

  const isCancer =
    predictionClass === "cancer";

  const isNonCancer =
    predictionClass === "non_cancer" ||
    predictionClass === "non-cancer" ||
    predictionClass === "noncancer";

  const confidence = Number(
    result?.model_confidence || 0
  );

  const cancerScore = Number(
    result?.class_scores?.cancer || 0
  );

  const nonCancerScore = Number(
    result?.class_scores?.non_cancer ??
      result?.class_scores?.["non-cancer"] ??
      0
  );

  const gradcamUrl = result?.gradcam
    ? result.gradcam.startsWith("http")
      ? result.gradcam
      : `${API_URL}${result.gradcam}`
    : "";

  // ============================================================
  // TIMELINE
  // ============================================================

  const timeline = [
    {
      title: "Image received",
      detail:
        selectedFile?.name ||
        "No image selected",
      icon: FileImage,
      complete: Boolean(selectedFile),
    },
    {
      title: "Image quality checked",
      detail:
        result?.quality?.quality_status ||
        "Waiting for analysis",
      icon: ScanSearch,
      complete: Boolean(result),
    },
    {
      title: "AI screening completed",
      detail: result
        ? `${confidence.toFixed(2)}% model confidence`
        : "Waiting for analysis",
      icon: Sparkles,
      complete: Boolean(result),
    },
    {
      title: "Explainability generated",
      detail: result?.gradcam
        ? "Attention map available"
        : "Waiting for analysis",
      icon: Microscope,
      complete: Boolean(result?.gradcam),
    },
  ];

  const sourceLabel =
    imageSource === "camera"
      ? "CAMERA CAPTURE"
      : imageSource === "device"
        ? "DEVICE / DATASET"
        : "NO IMAGE";

  // ============================================================
  // UI
  // ============================================================

  return (
    <div className="app-shell">

      {/* ======================================================
          NAVBAR
          ====================================================== */}

      <header className="top-nav">

        <div className="brand">

          <div className="brand-mark">
            <ScanSearch size={19} />
          </div>

          <div className="brand-copy">
            <strong>CANCERLENSE</strong>
            <span>AI RESEARCH SCREENING</span>
          </div>

        </div>

        <div className="nav-status">
          <span className="status-dot" />
          LOCAL RESEARCH MODE
        </div>

      </header>

      {/* ======================================================
          MAIN
          ====================================================== */}

      <main className="main-container">

        {/* ====================================================
            HERO
            ==================================================== */}

        <section className="hero-section">

          <div className="hero-copy">

            <div className="hero-eyebrow">
              <span className="eyebrow-line" />
              AI-ASSISTED ORAL IMAGE SCREENING
            </div>

            <h1>
              See beyond
              <br />
              <span>the visible.</span>
            </h1>

            <p className="hero-description">
              CancerLense analyzes oral images using a
              research-oriented computer vision pipeline,
              image quality assessment and visual
              explainability.
            </p>

            <div className="hero-meta">

              <div>
                <ShieldCheck size={15} />
                <span>RESEARCH-FIRST</span>
              </div>

              <div>
                <Activity size={15} />
                <span>IMAGE-BASED</span>
              </div>

              <div>
                <Microscope size={15} />
                <span>EXPLAINABLE</span>
              </div>

            </div>

          </div>

          {/* ==================================================
              HERO VISUAL
              ================================================== */}

          <div className="hero-visual-card">

            <div className="visual-grid" />

            <div className="visual-orbit orbit-one" />
            <div className="visual-orbit orbit-two" />

            {/* ATMOSPHERE */}

            <div className="hero-medical-visual">

              <div className="hero-medical-glow" />

              <img
                src="/hero-medical.png"
                alt="CancerLense oral imaging visualization"
                className="hero-medical-image"
              />

              <div className="medical-scan-ring ring-one" />
              <div className="medical-scan-ring ring-two" />

            </div>

            {/* HUD SCAN FRAME */}

            <div className="scan-frame">

              <span className="frame-corner frame-top-left" />
              <span className="frame-corner frame-top-right" />
              <span className="frame-corner frame-bottom-left" />
              <span className="frame-corner frame-bottom-right" />

              <div className="scan-center">

                <ScanSearch
                  size={30}
                  strokeWidth={1.2}
                />

                <span>READY</span>

              </div>

              <div className="scan-label scan-label-top">
                CANCERLENSE / VISION CORE
              </div>

              <div className="scan-label scan-label-bottom">
                IMAGE → SIGNAL → EXPLANATION
              </div>

            </div>

            <div className="visual-side-label">
              <span>01</span>
              <span>VISION</span>
            </div>

          </div>

        </section>

        {/* ====================================================
            IMAGE INPUT
            ==================================================== */}

        <section className="workspace-section">

          <div className="section-heading">

            <div>

              <span className="section-kicker">
                01 / IMAGE INPUT
              </span>

              <h2>
                Choose how you want to provide the image.
              </h2>

            </div>

            <span className="section-index">
              INPUT
            </span>

          </div>

          <div className="source-options">

            {/* UPLOAD */}

            <label
              className={`source-card ${
                imageSource === "device"
                  ? "source-card-active"
                  : ""
              }`}
              onDragEnter={handleDragEnter}
              onDragLeave={handleDragLeave}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
            >

              <input
                type="file"
                accept="image/*"
                onChange={handleFileInput}
                hidden
              />

              <div className="source-card-icon">
                <FolderOpen size={23} />
              </div>

              <div className="source-card-content">

                <div className="source-card-top">

                  <span>
                    UPLOAD / DATASET
                  </span>

                  {imageSource === "device" && (
                    <CheckCircle2 size={16} />
                  )}

                </div>

                <h3>
                  Choose an image
                </h3>

                <p>
                  Upload an image from your computer
                  or use a research dataset image.
                </p>

                <span className="source-card-action">
                  Browse files
                  <ArrowRight size={15} />
                </span>

              </div>

            </label>

            {/* CAMERA */}

            <button
              type="button"
              className={`source-card source-card-button ${
                imageSource === "camera"
                  ? "source-card-active"
                  : ""
              }`}
              onClick={startCamera}
            >

              <div className="source-card-icon camera-icon">
                <Camera size={23} />
              </div>

              <div className="source-card-content">

                <div className="source-card-top">

                  <span>
                    LIVE CAMERA
                  </span>

                  {imageSource === "camera" && (
                    <CheckCircle2 size={16} />
                  )}

                </div>

                <h3>
                  Capture an image
                </h3>

                <p>
                  Use your device camera to capture
                  a new image for research screening.
                </p>

                <span className="source-card-action">
                  Open camera
                  <ArrowRight size={15} />
                </span>

              </div>

            </button>

          </div>

          {/* DRAG DROP */}

          <div
            className={`upload-zone ${
              dragActive
                ? "upload-zone-active"
                : ""
            }`}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >

            <Upload size={18} />

            <span>
              Drag &amp; drop an image here
            </span>

            <small>
              JPG, JPEG, PNG · Maximum 15 MB
            </small>

          </div>

          {/* SELECTED IMAGE */}

          {selectedFile && previewUrl && (

            <div className="selected-image-panel">

              <div className="selected-image-preview">

                <img
                  src={previewUrl}
                  alt="Selected oral image"
                />

                <div className="selected-image-source">

                  <span className="source-live-dot" />

                  SOURCE · {sourceLabel}

                </div>

              </div>

              <div className="selected-image-info">

                <div className="selected-image-heading">

                  <div>

                    <span className="section-kicker">
                      IMAGE READY
                    </span>

                    <h3>
                      {selectedFile.name}
                    </h3>

                  </div>

                  <button
                    type="button"
                    className="remove-image-button"
                    onClick={resetCase}
                    aria-label="Remove image"
                  >
                    <X size={17} />
                  </button>

                </div>

                <div className="selected-image-meta">

                  <div>
                    <span>TYPE</span>
                    <strong>
                      {selectedFile.type ||
                        "IMAGE"}
                    </strong>
                  </div>

                  <div>
                    <span>SIZE</span>
                    <strong>
                      {(
                        selectedFile.size /
                        1024 /
                        1024
                      ).toFixed(2)}{" "}
                      MB
                    </strong>
                  </div>

                  <div>
                    <span>SOURCE</span>
                    <strong>
                      {sourceLabel}
                    </strong>
                  </div>

                </div>

                <button
                  type="button"
                  className="analyze-button"
                  onClick={analyzeImage}
                  disabled={loading}
                >

                  {loading ? (
                    <>
                      <Loader2
                        size={18}
                        className="spin"
                      />
                      Analyzing image...
                    </>
                  ) : (
                    <>
                      Analyze image
                      <ArrowRight size={18} />
                    </>
                  )}

                </button>

              </div>

            </div>

          )}

          {error && (

            <div className="error-message">

              <CircleAlert size={17} />

              <span>
                {error}
              </span>

            </div>

          )}

        </section>

        {/* ====================================================
            CASE CONTEXT
            ==================================================== */}

        <section className="case-context-strip">

          <div className="case-context-copy">

            <div className="case-context-icon">
              <UserRound size={18} />
            </div>

            <div>

              <span>
                OPTIONAL / CASE CONTEXT
              </span>

              <h3>
                Add patient history &amp; symptoms
              </h3>

              <p>
                Add research context without changing
                the image model prediction.
              </p>

            </div>

          </div>

          <button
            type="button"
            className="context-launch-button"
            onClick={() =>
              setShowPatientContext(true)
            }
          >

            <UserRound size={15} />

            {patientContext.symptoms?.length ||
            patientContext.ageGroup ||
            patientContext.tobaccoExposure
              ? "Edit Case Context"
              : "Add Case Context"}

          </button>

        </section>

        {/* ====================================================
            RESULTS
            ==================================================== */}

        {result && (

          <section className="results-section">

            <div className="result-header">

              <div>

                <span className="section-kicker">
                  02 / SCREENING OUTPUT
                </span>

                <h2>
                  Analysis complete.
                </h2>

                <p>
                  The following output is generated by
                  the CancerLense research screening
                  pipeline.
                </p>

              </div>

              <button
                type="button"
                className="reset-button"
                onClick={resetCase}
              >
                <RefreshCcw size={15} />
                New analysis
              </button>

            </div>

            {/* STATUS */}

            <div className="result-summary-grid">

              <div className="result-summary-card">

                <div className="result-summary-icon">
                  <CheckCircle2 size={19} />
                </div>

                <div>
                  <span>STATUS</span>
                  <strong>
                    {result.status ||
                      "ANALYZED"}
                  </strong>
                </div>

              </div>

              <div className="result-summary-card">

                <div className="result-summary-icon">
                  <ScanSearch size={19} />
                </div>

                <div>
                  <span>QUALITY</span>
                  <strong>
                    {result.quality
                      ?.quality_status ||
                      "ASSESSED"}
                  </strong>
                </div>

              </div>

              <div className="result-summary-card">

                <div className="result-summary-icon">
                  <Clock3 size={19} />
                </div>

                <div>
                  <span>SOURCE</span>
                  <strong>
                    {sourceLabel}
                  </strong>
                </div>

              </div>

            </div>

            {/* TIMELINE */}

            <div className="analysis-timeline-panel">

              <div className="panel-heading">

                <div>

                  <span className="section-kicker">
                    ANALYSIS PIPELINE
                  </span>

                  <h3>
                    What CancerLense processed
                  </h3>

                </div>

              </div>

              <div className="analysis-timeline">

                {timeline.map((item, index) => {

                  const Icon = item.icon;

                  return (
                    <div
                      className={`timeline-item ${
                        item.complete
                          ? "timeline-complete"
                          : ""
                      }`}
                      key={item.title}
                    >

                      <div className="timeline-marker">

                        {item.complete ? (
                          <CheckCircle2 size={17} />
                        ) : (
                          <Icon size={17} />
                        )}

                      </div>

                      <div className="timeline-content">

                        <span>
                          0{index + 1}
                        </span>

                        <div>

                          <strong>
                            {item.title}
                          </strong>

                          <p>
                            {item.detail}
                          </p>

                        </div>

                      </div>

                    </div>
                  );
                })}

              </div>

            </div>

            {/* AI FINDINGS */}

            <div className="ai-findings-panel">

              <div className="panel-heading">

                <div>

                  <span className="section-kicker">
                    AI FINDINGS
                  </span>

                  <h3>
                    Screening signal
                  </h3>

                </div>

                <Sparkles size={19} />

              </div>

              <div className="ai-finding-main">

                <div
                  className={`finding-status ${
                    isCancer
                      ? "finding-cancer"
                      : isNonCancer
                        ? "finding-noncancer"
                        : ""
                  }`}
                >

                  <div className="finding-status-dot" />

                  <span>
                    {result.screening_signal ||
                      "MODEL SCREENING SIGNAL"}
                  </span>

                </div>

                <p>
                  CancerLense identified a
                  model-class signal from the
                  submitted image.
                </p>

              </div>

            </div>

            {/* RED FLAGS */}

            <RedFlagPanel
              patientContext={patientContext}
            />

            {/* PREDICTION */}

            <div className="prediction-card">

              <div className="prediction-card-header">

                <div>

                  <span className="section-kicker">
                    MODEL OUTPUT
                  </span>

                  <h3>
                    Predicted class
                  </h3>

                </div>

                <span className="prediction-model">
                  MobileNetV3 Small
                </span>

              </div>

              <div
                className={`prediction-result ${
                  isCancer
                    ? "prediction-cancer"
                    : isNonCancer
                      ? "prediction-noncancer"
                      : ""
                }`}
              >

                <div>

                  <span>
                    SCREENING CLASS
                  </span>

                  <strong>
                    {predictionClass
                      ? predictionClass
                          .replace("_", " ")
                          .toUpperCase()
                      : "UNKNOWN"}
                  </strong>

                </div>

                <div className="confidence-block">

                  <span>
                    MODEL CONFIDENCE
                  </span>

                  <strong>
                    {confidence.toFixed(2)}%
                  </strong>

                </div>

              </div>

              <div className="class-scores">

                <div className="score-row">

                  <div className="score-label">

                    <span>
                      Cancer class
                    </span>

                    <strong>
                      {cancerScore.toFixed(2)}%
                    </strong>

                  </div>

                  <div className="score-track">

                    <div
                      className="score-fill score-cancer"
                      style={{
                        width: `${Math.min(
                          cancerScore,
                          100
                        )}%`,
                      }}
                    />

                  </div>

                </div>

                <div className="score-row">

                  <div className="score-label">

                    <span>
                      Non-cancer class
                    </span>

                    <strong>
                      {nonCancerScore.toFixed(2)}%
                    </strong>

                  </div>

                  <div className="score-track">

                    <div
                      className="score-fill score-noncancer"
                      style={{
                        width: `${Math.min(
                          nonCancerScore,
                          100
                        )}%`,
                      }}
                    />

                  </div>

                </div>

              </div>

            </div>

            {/* QUALITY + RECOMMENDATION */}

            <div className="result-two-column">

              <div className="result-panel">

                <div className="panel-heading">

                  <div>

                    <span className="section-kicker">
                      IMAGE QUALITY
                    </span>

                    <h3>
                      Input assessment
                    </h3>

                  </div>

                  <ScanSearch size={18} />

                </div>

                <div className="quality-grid">

                  <div>
                    <span>WIDTH</span>
                    <strong>
                      {result.quality?.width ||
                        "—"}{" "}
                      px
                    </strong>
                  </div>

                  <div>
                    <span>HEIGHT</span>
                    <strong>
                      {result.quality?.height ||
                        "—"}{" "}
                      px
                    </strong>
                  </div>

                  <div>
                    <span>BRIGHTNESS</span>
                    <strong>
                      {Number(
                        result.quality
                          ?.brightness || 0
                      ).toFixed(2)}
                    </strong>
                  </div>

                  <div>
                    <span>SHARPNESS</span>
                    <strong>
                      {Number(
                        result.quality
                          ?.sharpness || 0
                      ).toFixed(2)}
                    </strong>
                  </div>

                </div>

              </div>

              <div className="result-panel recommendation-panel">

                <div className="panel-heading">

                  <div>

                    <span className="section-kicker">
                      NEXT STEP
                    </span>

                    <h3>
                      Research interpretation
                    </h3>

                  </div>

                  <AlertCircle size={18} />

                </div>

                <p>
                  {result.recommendation}
                </p>

              </div>

            </div>

            {/* EXPLAINABILITY */}

            <div className="gradcam-card">

              <div className="panel-heading">

                <div>

                  <span className="section-kicker">
                    EXPLAINABILITY
                  </span>

                  <h3>
                    Where did the model look?
                  </h3>

                  <p>
                    Grad-CAM highlights image
                    regions that influenced the
                    model prediction. It is not a
                    clinical lesion boundary.
                  </p>

                </div>

                <Microscope size={19} />

              </div>

              {gradcamUrl ? (
                <>

                  <div className="explainability-tabs">

                    <button
                      type="button"
                      className={
                        activeExplainability ===
                        "original"
                          ? "active"
                          : ""
                      }
                      onClick={() =>
                        setActiveExplainability(
                          "original"
                        )
                      }
                    >
                      Original
                    </button>

                    <button
                      type="button"
                      className={
                        activeExplainability ===
                        "attention"
                          ? "active"
                          : ""
                      }
                      onClick={() =>
                        setActiveExplainability(
                          "attention"
                        )
                      }
                    >
                      Attention
                    </button>

                    <button
                      type="button"
                      className={
                        activeExplainability ===
                        "blend"
                          ? "active"
                          : ""
                      }
                      onClick={() =>
                        setActiveExplainability(
                          "blend"
                        )
                      }
                    >
                      Blend
                    </button>

                  </div>

                  <div className="explainability-viewer">

                    {activeExplainability ===
                      "original" && (
                      <img
                        src={previewUrl}
                        alt="Original submitted image"
                        className="explainability-image"
                      />
                    )}

                    {activeExplainability ===
                      "attention" && (
                      <img
                        src={gradcamUrl}
                        alt="Grad-CAM attention map"
                        className="explainability-image"
                      />
                    )}

                    {activeExplainability ===
                      "blend" && (
                      <div className="blend-view">

                        <img
                          src={previewUrl}
                          alt="Original submitted image"
                          className="explainability-image"
                        />

                        <img
                          src={gradcamUrl}
                          alt="Grad-CAM overlay"
                          className="explainability-image blend-overlay"
                        />

                      </div>
                    )}

                  </div>

                </>
              ) : (
                <div className="gradcam-status">

                  <Info size={17} />

                  Explainability output was not
                  generated for this case.

                </div>
              )}

            </div>

            {/* RESEARCH NOTE */}

            <div className="research-note">

              <Info size={18} />

              <div>

                <strong>
                  Research-only interpretation
                </strong>

                <p>
                  CancerLense provides AI-assisted
                  image screening signals for
                  research purposes. Model confidence
                  is not clinical certainty. The output
                  does not establish a diagnosis.
                  Professional clinical assessment
                  remains separate from this research
                  result.
                </p>

              </div>

            </div>

          </section>

        )}

      </main>

      {/* ======================================================
          FOOTER
          ====================================================== */}

      <footer className="app-footer">

        <div>

          <strong>
            CANCERLENSE
          </strong>

          <span>
            AI-assisted oral image screening
            research prototype.
          </span>

        </div>

        <span>
          NOT A MEDICAL DIAGNOSIS
        </span>

      </footer>

      {/* ======================================================
          CAMERA MODAL
          ====================================================== */}

      {cameraOpen && (

        <div className="camera-overlay">

          <div className="camera-modal">

            <div className="camera-modal-header">

              <div>

                <span className="section-kicker">
                  CANCERLENSE / CAMERA
                </span>

                <h2>
                  Capture research image
                </h2>

                <p>
                  Position the area clearly inside
                  the frame before capturing.
                </p>

              </div>

              <button
                type="button"
                className="camera-close-button"
                onClick={closeCamera}
                aria-label="Close camera"
              >
                <X size={19} />
              </button>

            </div>

            <div className="camera-stage">

              {!capturedPreview ? (
                <>

                  <video
                    ref={videoRef}
                    className="camera-video"
                    autoPlay
                    playsInline
                    muted
                  />

                  <div className="camera-frame">

                    <span className="camera-corner camera-corner-tl" />
                    <span className="camera-corner camera-corner-tr" />
                    <span className="camera-corner camera-corner-bl" />
                    <span className="camera-corner camera-corner-br" />

                    <div className="camera-frame-label">
                      POSITION IMAGE INSIDE FRAME
                    </div>

                  </div>

                  {!cameraReady &&
                    !cameraError && (
                      <div className="camera-loading">

                        <Loader2
                          size={27}
                          className="spin"
                        />

                        <span>
                          Starting camera...
                        </span>

                      </div>
                    )}

                  {cameraError && (

                    <div className="camera-error">

                      <AlertCircle size={22} />

                      <p>
                        {cameraError}
                      </p>

                      <button
                        type="button"
                        onClick={startCamera}
                      >
                        Try again
                      </button>

                    </div>

                  )}

                </>
              ) : (

                <div className="camera-captured">

                  <img
                    src={capturedPreview}
                    alt="Captured camera preview"
                  />

                  <div className="captured-label">

                    <CheckCircle2 size={16} />

                    PHOTO CAPTURED

                  </div>

                </div>

              )}

            </div>

            <canvas
              ref={canvasRef}
              style={{
                display: "none",
              }}
            />

            <div className="camera-modal-footer">

              <div className="camera-source-info">

                <Camera size={16} />

                <span>
                  Camera images are processed
                  through the same CancerLense
                  analysis pipeline.
                </span>

              </div>

              <div className="camera-actions">

                {!capturedPreview ? (
                  <>

                    <button
                      type="button"
                      className="camera-secondary-button"
                      onClick={closeCamera}
                    >
                      Cancel
                    </button>

                    <button
                      type="button"
                      className="camera-capture-button"
                      onClick={capturePhoto}
                      disabled={!cameraReady}
                    >

                      <Camera size={18} />

                      Capture Photo

                    </button>

                  </>
                ) : (
                  <>

                    <button
                      type="button"
                      className="camera-secondary-button"
                      onClick={retakePhoto}
                    >

                      <RefreshCcw size={16} />

                      Retake

                    </button>

                    <button
                      type="button"
                      className="camera-capture-button"
                      onClick={useCapturedPhoto}
                    >

                      <CheckCircle2 size={17} />

                      Use This Photo

                    </button>

                  </>
                )}

              </div>

            </div>

          </div>

        </div>

      )}

      {/* ======================================================
          PATIENT CONTEXT MODAL
          ====================================================== */}

      {showPatientContext && (

        <PatientContext
          initialData={patientContext}
          onSave={handlePatientContextSave}
          onClose={() =>
            setShowPatientContext(false)
          }
        />

      )}

    </div>
  );
}

export default App;