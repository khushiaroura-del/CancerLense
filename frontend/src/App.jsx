import { useEffect, useRef, useState } from "react";
import axios from "axios";

import {
  LayoutDashboard,
  ScanLine,
  History,
  BarChart3,
  FlaskConical,
  Settings,
  CircleUserRound,
  ChevronRight,
  Activity,
  ShieldCheck,
  Upload,
  Camera,
  Image as ImageIcon,
  X,
  RotateCcw,
  Play,
  CheckCircle2,
  AlertTriangle,
  Info,
  BrainCircuit,
  Sparkles,
  Ruler,
  Eye,
  FileImage,
  UserRound,
  MapPin,
  Clock3,
  Stethoscope,
} from "lucide-react";

import "./App.css";


/* =========================================================
   CONFIG
========================================================= */

const API_URL = "http://127.0.0.1:8000";


/* =========================================================
   CONSTANTS
========================================================= */

const lesionLocations = [
  "Tongue — Left Side",
  "Tongue — Right Side",
  "Tongue — Top Surface",
  "Tongue — Underside",
  "Floor of Mouth",
  "Inner Cheek — Left",
  "Inner Cheek — Right",
  "Upper Gum",
  "Lower Gum",
  "Hard Palate",
  "Soft Palate",
  "Upper Lip — Inner",
  "Lower Lip — Inner",
  "Other / Unspecified",
];


const symptomOptions = [
  "Persistent mouth sore",
  "Pain or discomfort",
  "Bleeding",
  "Non-healing lesion",
  "Lump or thickening",
  "White or red patch",
  "Difficulty chewing",
  "Difficulty swallowing",
  "Numbness",
  "Voice changes",
];


/* =========================================================
   APP
========================================================= */

function App() {

  const [activePage, setActivePage] =
    useState("Dashboard");

  const [selectedFile, setSelectedFile] =
    useState(null);

  const [previewUrl, setPreviewUrl] =
    useState("");

  const [dragActive, setDragActive] =
    useState(false);

  const [cameraOpen, setCameraOpen] =
    useState(false);

  const [cameraStream, setCameraStream] =
    useState(null);

  const [analysisResult, setAnalysisResult] =
    useState(null);

  const [isAnalyzing, setIsAnalyzing] =
    useState(false);

  const [errorMessage, setErrorMessage] =
    useState("");

  const [lesionLocation, setLesionLocation] =
    useState("");

  const [patientContext, setPatientContext] =
    useState({
      ageGroup: "",
      tobacco: "",
      alcohol: "",
      previousOralLesion: "",
      previousOralCancer: "",
      dentalHistory: "",
      symptoms: [],
      symptomDuration: "",
      notes: "",
    });

  const [showContext, setShowContext] =
    useState(false);

  const videoRef = useRef(null);

  const canvasRef = useRef(null);

  const fileInputRef = useRef(null);

  const cameraInputRef = useRef(null);


  /* =======================================================
     NAVIGATION
  ======================================================= */

  const navigation = [
    {
      label: "Dashboard",
      icon: LayoutDashboard,
    },
    {
      label: "Screen",
      icon: ScanLine,
    },
    {
      label: "History",
      icon: Clock3,
    },
    {
      label: "Analytics",
      icon: BarChart3,
    },
    {
      label: "Research",
      icon: FlaskConical,
    },
    {
      label: "Settings",
      icon: Settings,
    },
  ];


  const pageTitles = {
    Dashboard: "Dashboard",
    Screen: "Capture & Screen",
    History: "Scan History",
    Analytics: "Analytics",
    Research: "Research & Model",
    Settings: "Settings",
  };


  /* =======================================================
     FILE PREVIEW
  ======================================================= */

  useEffect(() => {

    if (!selectedFile) {
      setPreviewUrl("");
      return;
    }

    const url =
      URL.createObjectURL(selectedFile);

    setPreviewUrl(url);

    return () => {
      URL.revokeObjectURL(url);
    };

  }, [selectedFile]);


  /* =======================================================
     CAMERA CLEANUP
  ======================================================= */

  useEffect(() => {

    return () => {

      if (cameraStream) {

        cameraStream
          .getTracks()
          .forEach((track) =>
            track.stop()
          );

      }

    };

  }, [cameraStream]);


  /* =======================================================
     FILE SELECT
  ======================================================= */

  const handleFileSelect = (file) => {

    if (!file) return;

    if (!file.type.startsWith("image/")) {

      setErrorMessage(
        "Please select a valid image file."
      );

      return;
    }

    setErrorMessage("");

    setAnalysisResult(null);

    setSelectedFile(file);
  };


  /* =======================================================
     FILE INPUT
  ======================================================= */

  const handleFileInput = (event) => {

    const file =
      event.target.files?.[0];

    handleFileSelect(file);

    event.target.value = "";
  };


  /* =======================================================
     DRAG & DROP
  ======================================================= */

  const handleDragOver = (event) => {

    event.preventDefault();

    setDragActive(true);
  };


  const handleDragLeave = (event) => {

    event.preventDefault();

    setDragActive(false);
  };


  const handleDrop = (event) => {

    event.preventDefault();

    setDragActive(false);

    const file =
      event.dataTransfer.files?.[0];

    handleFileSelect(file);
  };


  /* =======================================================
     CAMERA
  ======================================================= */

  const openCamera = async () => {

    setErrorMessage("");

    try {

      if (
        !navigator.mediaDevices ||
        !navigator.mediaDevices.getUserMedia
      ) {
        throw new Error(
          "Camera access is not supported by this browser."
        );
      }

      const stream =
        await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: "environment",
          },
          audio: false,
        });

      setCameraStream(stream);

      setCameraOpen(true);

      setTimeout(() => {

        if (videoRef.current) {

          videoRef.current.srcObject =
            stream;

        }

      }, 100);

    } catch (error) {

      console.error(error);

      setErrorMessage(
        "Camera access could not be started. Please allow camera permission or upload an image instead."
      );

    }

  };


  const closeCamera = () => {

    if (cameraStream) {

      cameraStream
        .getTracks()
        .forEach((track) =>
          track.stop()
        );

    }

    setCameraStream(null);

    setCameraOpen(false);
  };


  const capturePhoto = () => {

    if (
      !videoRef.current ||
      !canvasRef.current
    ) {
      return;
    }

    const video =
      videoRef.current;

    const canvas =
      canvasRef.current;

    canvas.width =
      video.videoWidth;

    canvas.height =
      video.videoHeight;

    const context =
      canvas.getContext("2d");

    context.drawImage(
      video,
      0,
      0,
      canvas.width,
      canvas.height
    );

    canvas.toBlob(
      (blob) => {

        if (!blob) return;

        const file =
          new File(
            [blob],
            `cancerlense-camera-${Date.now()}.jpg`,
            {
              type: "image/jpeg",
            }
          );

        handleFileSelect(file);

        closeCamera();

      },
      "image/jpeg",
      0.94
    );
  };


  /* =======================================================
     CONTEXT
  ======================================================= */

  const toggleSymptom = (symptom) => {

    setPatientContext((previous) => {

      const exists =
        previous.symptoms.includes(symptom);

      return {
        ...previous,
        symptoms: exists
          ? previous.symptoms.filter(
              (item) => item !== symptom
            )
          : [
              ...previous.symptoms,
              symptom,
            ],
      };

    });

  };


  /* =======================================================
     RED FLAG / CONTEXT FLAGS
  ======================================================= */

  const getContextFlags = () => {

    const flags = [];

    const {
      symptoms,
      symptomDuration,
      tobacco,
      alcohol,
      previousOralLesion,
      previousOralCancer,
    } = patientContext;


    if (
      symptoms.includes(
        "Persistent mouth sore"
      )
    ) {
      flags.push(
        "Persistent mouth sore reported"
      );
    }


    if (
      symptoms.includes(
        "Non-healing lesion"
      )
    ) {
      flags.push(
        "Non-healing lesion reported"
      );
    }


    if (
      symptoms.includes("Bleeding")
    ) {
      flags.push(
        "Bleeding reported"
      );
    }


    if (
      symptoms.includes(
        "White or red patch"
      )
    ) {
      flags.push(
        "White or red patch reported"
      );
    }


    if (
      symptoms.includes(
        "Lump or thickening"
      )
    ) {
      flags.push(
        "Lump or thickening reported"
      );
    }


    if (
      symptoms.includes(
        "Difficulty swallowing"
      )
    ) {
      flags.push(
        "Difficulty swallowing reported"
      );
    }


    if (
      symptoms.includes("Numbness")
    ) {
      flags.push(
        "Numbness reported"
      );
    }


    if (
      symptomDuration &&
      symptomDuration !== "Not sure"
    ) {
      flags.push(
        `Symptoms reported for ${symptomDuration}`
      );
    }


    if (tobacco === "Current") {
      flags.push(
        "Current tobacco exposure reported"
      );
    }


    if (alcohol === "Regular") {
      flags.push(
        "Regular alcohol exposure reported"
      );
    }


    if (
      previousOralLesion === "Yes"
    ) {
      flags.push(
        "Previous oral lesion reported"
      );
    }


    if (
      previousOralCancer === "Yes"
    ) {
      flags.push(
        "Previous oral cancer reported"
      );
    }


    return flags;
  };


  /* =======================================================
     ANALYZE
  ======================================================= */

  const analyzeImage = async () => {

    if (!selectedFile) {

      setErrorMessage(
        "Please upload or capture an oral image first."
      );

      return;
    }


    setIsAnalyzing(true);

    setErrorMessage("");

    setAnalysisResult(null);


    try {

      const formData =
        new FormData();

      formData.append(
        "file",
        selectedFile
      );


      const response =
        await axios.post(
          `${API_URL}/analyze`,
          formData,
          {
            headers: {
              "Content-Type":
                "multipart/form-data",
            },
          }
        );


      setAnalysisResult(
        response.data
      );

    } catch (error) {

      console.error(
        "CancerLense analysis error:",
        error
      );


      if (
        error.response?.data?.detail
      ) {

        setErrorMessage(
          String(
            error.response.data.detail
          )
        );

      } else if (
        error.code === "ERR_NETWORK"
      ) {

        setErrorMessage(
          "CancerLense backend is not reachable. Make sure FastAPI is running on http://127.0.0.1:8000."
        );

      } else {

        setErrorMessage(
          "Analysis could not be completed. Please check the backend and try again."
        );

      }

    } finally {

      setIsAnalyzing(false);
    }
  };


  /* =======================================================
     RESET SCREEN
  ======================================================= */

  const resetScreen = () => {

    setSelectedFile(null);

    setAnalysisResult(null);

    setErrorMessage("");

    setLesionLocation("");

    setShowContext(false);
  };


  /* =======================================================
     GRAD-CAM URL
  ======================================================= */

  const getGradcamUrl = () => {

    if (!analysisResult?.gradcam) {
      return "";
    }

    if (
      analysisResult.gradcam.startsWith(
        "http"
      )
    ) {
      return analysisResult.gradcam;
    }

    return `${API_URL}${analysisResult.gradcam}`;
  };


  /* =======================================================
     HELPERS
  ======================================================= */

  const formatNumber = (
    value,
    decimals = 2
  ) => {

    if (
      value === null ||
      value === undefined ||
      Number.isNaN(Number(value))
    ) {
      return "—";
    }

    return Number(value).toFixed(
      decimals
    );
  };


  const getSignalClass = () => {

    if (
      analysisResult?.prediction_class ===
      "cancer"
    ) {
      return "signal-cancer";
    }

    return "signal-neutral";
  };


  const getQualityClass = () => {

    const status =
      analysisResult?.quality?.quality_status;

    if (status === "ACCEPTABLE") {
      return "quality-good";
    }

    return "quality-warning";
  };


  /* =======================================================
     DASHBOARD
  ======================================================= */

  const renderDashboard = () => {

    return (
      <section className="dashboard-page">

        <div className="dashboard-hero">

          <div className="hero-copy">

            <div className="hero-label">
              AI-ASSISTED ORAL IMAGE SCREENING
            </div>

            <h2>
              See beyond
              <br />
              <span>the visible.</span>
            </h2>

            <p>
              CancerLense is an AI-assisted
              research prototype designed to
              analyze oral images, evaluate image
              quality, surface model signals, and
              provide explainable visual evidence.
            </p>

            <button
              className="primary-button"
              onClick={() =>
                setActivePage("Screen")
              }
            >
              <span>
                Start Screening
              </span>

              <ChevronRight
                size={17}
              />
            </button>


            <div className="hero-meta">

              <div className="hero-meta-item">
                <span>MODEL</span>
                <strong>
                  MobileNetV3
                </strong>
              </div>

              <div className="hero-meta-item">
                <span>EXPLAINABILITY</span>
                <strong>
                  Grad-CAM
                </strong>
              </div>

              <div className="hero-meta-item">
                <span>MODE</span>
                <strong>
                  Research
                </strong>
              </div>

            </div>

          </div>


          <div className="dashboard-visual">

            <div className="visual-header">
              <span>
                CANCERLENSE / 01
              </span>

              <span>
                AI VISION
              </span>
            </div>


            <div className="scan-visual">

              <div className="scan-grid"></div>

              <div className="scan-glow"></div>

              <div className="scan-ring ring-one"></div>

              <div className="scan-ring ring-two"></div>

              <div className="scan-ring ring-three"></div>

              <div className="scan-center">
                <ScanLine
                  size={34}
                />
              </div>

              <div className="visual-tag tag-image">
                IMAGE
              </div>

              <div className="visual-tag tag-analysis">
                ANALYSIS
              </div>

              <div className="visual-tag tag-model">
                MODEL
              </div>

              <div className="crosshair horizontal"></div>

              <div className="crosshair vertical"></div>

            </div>


            <div className="visual-footer">

              <span>
                MOBILENET V3
              </span>

              <span>
                GRAD-CAM
              </span>

              <span>
                QUALITY CHECK
              </span>

            </div>

          </div>

        </div>


        <div className="feature-grid">

          <div className="feature-card">

            <div className="feature-icon">
              <ScanLine size={20} />
            </div>

            <div>
              <strong>
                Fast Screening
              </strong>

              <span>
                Image-based AI analysis
              </span>
            </div>

          </div>


          <div className="feature-card">

            <div className="feature-icon">
              <Activity size={20} />
            </div>

            <div>
              <strong>
                Explainable
              </strong>

              <span>
                Grad-CAM visual evidence
              </span>
            </div>

          </div>


          <div className="feature-card">

            <div className="feature-icon">
              <ShieldCheck size={20} />
            </div>

            <div>
              <strong>
                Research First
              </strong>

              <span>
                Not a medical diagnosis
              </span>
            </div>

          </div>

        </div>


        <div className="research-notice">

          <div className="research-notice-icon">
            <ShieldCheck size={18} />
          </div>

          <div>
            <strong>
              Research prototype
            </strong>

            <p>
              CancerLense provides AI-assisted
              screening signals and visual
              explanations for research use. It
              does not provide a medical diagnosis.
            </p>
          </div>

        </div>

      </section>
    );
  };


  /* =======================================================
     SCREEN PAGE
  ======================================================= */

  const renderScreen = () => {

    const contextFlags =
      getContextFlags();


    return (
      <section className="screen-page">


        {/* =================================================
            UPLOAD AREA
        ================================================= */}

        {!selectedFile && !analysisResult && (

          <div className="screen-intro">

            <div className="screen-intro-copy">

              <div className="screen-eyebrow">
                CANCERLENSE / CAPTURE
              </div>

              <h2>
                Bring the image.
                <br />
                <span>Let the model look.</span>
              </h2>

              <p>
                Upload an oral image or capture one
                directly with your camera. CancerLense
                will evaluate image quality and run
                the research screening model.
              </p>

            </div>


            <div className="capture-grid">


              {/* UPLOAD */}

              <div
                className={`drop-zone ${
                  dragActive
                    ? "drag-active"
                    : ""
                }`}
                onDragOver={
                  handleDragOver
                }
                onDragLeave={
                  handleDragLeave
                }
                onDrop={
                  handleDrop
                }
                onClick={() =>
                  fileInputRef.current?.click()
                }
              >

                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  hidden
                  onChange={
                    handleFileInput
                  }
                />

                <div className="capture-icon">
                  <Upload size={25} />
                </div>

                <h3>
                  Upload image
                </h3>

                <p>
                  Drag & drop an oral image here
                </p>

                <span>
                  JPG, JPEG, PNG, WEBP
                </span>

              </div>


              {/* CAMERA */}

              <button
                className="camera-card"
                onClick={openCamera}
              >

                <div className="capture-icon">
                  <Camera size={25} />
                </div>

                <h3>
                  Use camera
                </h3>

                <p>
                  Capture an image directly
                </p>

                <span>
                  Camera access required
                </span>

              </button>

            </div>


            <div className="capture-note">

              <Info size={15} />

              <span>
                For research screening only. Use
                clear, well-lit images whenever
                possible.
              </span>

            </div>

          </div>

        )}


        {/* =================================================
            IMAGE WORKSPACE
        ================================================= */}

        {selectedFile && (

          <div className="screen-workspace">


            {/* IMAGE PANEL */}

            <div className="image-workspace-card">

              <div className="workspace-header">

                <div>

                  <div className="workspace-eyebrow">
                    IMAGE INPUT
                  </div>

                  <h3>
                    Captured oral image
                  </h3>

                </div>

                <button
                  className="icon-button"
                  onClick={resetScreen}
                  title="Remove image"
                >
                  <X size={17} />
                </button>

              </div>


              <div className="image-preview-container">

                {previewUrl && (
                  <img
                    src={previewUrl}
                    alt="Selected oral image"
                    className="image-preview"
                  />
                )}

                <div className="preview-overlay">

                  <div>
                    <FileImage
                      size={15}
                    />

                    <span>
                      IMAGE READY
                    </span>
                  </div>

                </div>

              </div>


              <div className="image-file-info">

                <div>
                  <FileImage size={14} />

                  <span>
                    {selectedFile.name}
                  </span>
                </div>

                <span>
                  {(
                    selectedFile.size /
                    1024 /
                    1024
                  ).toFixed(2)}{" "}
                  MB
                </span>

              </div>

            </div>


            {/* CONTEXT PANEL */}

            <div className="context-workspace-card">

              <div className="workspace-header">

                <div>

                  <div className="workspace-eyebrow">
                    RESEARCH CONTEXT
                  </div>

                  <h3>
                    Case context
                  </h3>

                </div>

                <button
                  className={`context-toggle ${
                    showContext
                      ? "active"
                      : ""
                  }`}
                  onClick={() =>
                    setShowContext(
                      !showContext
                    )
                  }
                >
                  {showContext
                    ? "Close"
                    : "Add context"}
                </button>

              </div>


              <div className="location-section">

                <div className="field-label">
                  <MapPin size={13} />
                  Lesion location
                </div>

                <select
                  value={lesionLocation}
                  onChange={(event) =>
                    setLesionLocation(
                      event.target.value
                    )
                  }
                >

                  <option value="">
                    Select location
                  </option>

                  {lesionLocations.map(
                    (location) => (
                      <option
                        key={location}
                        value={location}
                      >
                        {location}
                      </option>
                    )
                  )}

                </select>

              </div>


              {showContext && (

                <div className="context-form">


                  <div className="form-grid">


                    <label>

                      <span>
                        Age group
                      </span>

                      <select
                        value={
                          patientContext.ageGroup
                        }
                        onChange={(event) =>
                          setPatientContext({
                            ...patientContext,
                            ageGroup:
                              event.target.value,
                          })
                        }
                      >

                        <option value="">
                          Not provided
                        </option>

                        <option>
                          Under 18
                        </option>

                        <option>
                          18–30
                        </option>

                        <option>
                          31–45
                        </option>

                        <option>
                          46–60
                        </option>

                        <option>
                          61+
                        </option>

                      </select>

                    </label>


                    <label>

                      <span>
                        Tobacco exposure
                      </span>

                      <select
                        value={
                          patientContext.tobacco
                        }
                        onChange={(event) =>
                          setPatientContext({
                            ...patientContext,
                            tobacco:
                              event.target.value,
                          })
                        }
                      >

                        <option value="">
                          Not provided
                        </option>

                        <option>
                          Never
                        </option>

                        <option>
                          Former
                        </option>

                        <option>
                          Current
                        </option>

                      </select>

                    </label>


                    <label>

                      <span>
                        Alcohol exposure
                      </span>

                      <select
                        value={
                          patientContext.alcohol
                        }
                        onChange={(event) =>
                          setPatientContext({
                            ...patientContext,
                            alcohol:
                              event.target.value,
                          })
                        }
                      >

                        <option value="">
                          Not provided
                        </option>

                        <option>
                          None
                        </option>

                        <option>
                          Occasional
                        </option>

                        <option>
                          Regular
                        </option>

                      </select>

                    </label>


                    <label>

                      <span>
                        Previous oral lesion
                      </span>

                      <select
                        value={
                          patientContext.previousOralLesion
                        }
                        onChange={(event) =>
                          setPatientContext({
                            ...patientContext,
                            previousOralLesion:
                              event.target.value,
                          })
                        }
                      >

                        <option value="">
                          Not provided
                        </option>

                        <option>
                          Yes
                        </option>

                        <option>
                          No
                        </option>

                      </select>

                    </label>


                    <label>

                      <span>
                        Previous oral cancer
                      </span>

                      <select
                        value={
                          patientContext.previousOralCancer
                        }
                        onChange={(event) =>
                          setPatientContext({
                            ...patientContext,
                            previousOralCancer:
                              event.target.value,
                          })
                        }
                      >

                        <option value="">
                          Not provided
                        </option>

                        <option>
                          Yes
                        </option>

                        <option>
                          No
                        </option>

                      </select>

                    </label>


                    <label>

                      <span>
                        Symptom duration
                      </span>

                      <select
                        value={
                          patientContext.symptomDuration
                        }
                        onChange={(event) =>
                          setPatientContext({
                            ...patientContext,
                            symptomDuration:
                              event.target.value,
                          })
                        }
                      >

                        <option value="">
                          Not provided
                        </option>

                        <option>
                          Less than 1 week
                        </option>

                        <option>
                          1–2 weeks
                        </option>

                        <option>
                          2–4 weeks
                        </option>

                        <option>
                          More than 1 month
                        </option>

                        <option>
                          Not sure
                        </option>

                      </select>

                    </label>

                  </div>


                  <div className="symptom-block">

                    <div className="field-label">
                      Symptoms
                    </div>

                    <div className="symptom-grid">

                      {symptomOptions.map(
                        (symptom) => {

                          const active =
                            patientContext.symptoms.includes(
                              symptom
                            );

                          return (
                            <button
                              key={symptom}
                              type="button"
                              className={`symptom-chip ${
                                active
                                  ? "active"
                                  : ""
                              }`}
                              onClick={() =>
                                toggleSymptom(
                                  symptom
                                )
                              }
                            >
                              {active && (
                                <CheckCircle2
                                  size={13}
                                />
                              )}

                              {symptom}
                            </button>
                          );

                        }
                      )}

                    </div>

                  </div>


                  <label className="notes-field">

                    <span>
                      Additional notes
                    </span>

                    <textarea
                      value={
                        patientContext.notes
                      }
                      onChange={(event) =>
                        setPatientContext({
                          ...patientContext,
                          notes:
                            event.target.value,
                        })
                      }
                      placeholder="Optional research notes..."
                      rows={3}
                    />

                  </label>


                  <div className="context-warning">

                    <Info size={14} />

                    <span>
                      Patient context is user-reported
                      research information. It does not
                      change the MobileNet prediction.
                    </span>

                  </div>

                </div>

              )}


              <button
                className="analyze-button"
                onClick={analyzeImage}
                disabled={isAnalyzing}
              >

                {isAnalyzing ? (
                  <>
                    <span className="button-spinner"></span>

                    Analyzing image...
                  </>
                ) : (
                  <>
                    <BrainCircuit size={18} />

                    Analyze with CancerLense

                    <ChevronRight
                      size={16}
                    />
                  </>
                )}

              </button>


              <button
                className="secondary-action"
                onClick={resetScreen}
                disabled={isAnalyzing}
              >
                <RotateCcw size={14} />
                Choose another image
              </button>

            </div>

          </div>

        )}


        {/* =================================================
            ERROR
        ================================================= */}

        {errorMessage && (

          <div className="error-box">

            <AlertTriangle size={18} />

            <div>

              <strong>
                Analysis issue
              </strong>

              <span>
                {errorMessage}
              </span>

            </div>

            <button
              onClick={() =>
                setErrorMessage("")
              }
            >
              <X size={15} />
            </button>

          </div>

        )}


        {/* =================================================
            RESULTS
        ================================================= */}

        {analysisResult && (

          <div className="results-section">


            {/* RESULT HEADER */}

            <div className="results-header">

              <div>

                <div className="screen-eyebrow">
                  CANCERLENSE / ANALYSIS COMPLETE
                </div>

                <h2>
                  Research screening result
                </h2>

                <p>
                  The following values are outputs
                  from the current research model
                  and image-processing pipeline.
                </p>

              </div>


              <div className="result-actions">

                <button
                  className="secondary-action"
                  onClick={resetScreen}
                >
                  <RotateCcw size={14} />
                  New analysis
                </button>

              </div>

            </div>


            {/* PRIMARY RESULT */}

            <div className="result-main-grid">


              <div
                className={`primary-result-card ${
                  getSignalClass()
                }`}
              >

                <div className="result-card-top">

                  <span>
                    SCREENING SIGNAL
                  </span>

                  <Sparkles size={17} />

                </div>


                <div className="result-signal">

                  {analysisResult.prediction_class ===
                  "cancer"
                    ? "CANCER-CLASS SIGNAL"
                    : "NON-CANCER-CLASS SIGNAL"}

                </div>


                <div className="confidence-row">

                  <div>

                    <span>
                      MODEL CONFIDENCE
                    </span>

                    <strong>
                      {formatNumber(
                        analysisResult.model_confidence
                      )}
                      %
                    </strong>

                  </div>


                  <div className="confidence-ring">

                    <div
                      className="confidence-ring-inner"
                      style={{
                        "--confidence":
                          `${Math.min(
                            100,
                            Number(
                              analysisResult.model_confidence ||
                                0
                            )
                          ) * 3.6}deg`,
                      }}
                    >
                      <span>
                        {Math.round(
                          Number(
                            analysisResult.model_confidence ||
                              0
                          )
                        )}
                      </span>

                    </div>

                  </div>

                </div>


                <div className="result-disclaimer">

                  <Info size={14} />

                  <span>
                    Model confidence is not clinical
                    certainty or a diagnosis.
                  </span>

                </div>

              </div>


              {/* CLASS SCORES */}

              <div className="scores-card">

                <div className="result-card-top">

                  <span>
                    CLASS SCORES
                  </span>

                  <BarChart3 size={17} />

                </div>


                <div className="score-list">


                  <div className="score-item">

                    <div className="score-label">

                      <span>
                        Cancer
                      </span>

                      <strong>
                        {formatNumber(
                          analysisResult
                            .class_scores
                            ?.cancer
                        )}
                        %
                      </strong>

                    </div>

                    <div className="score-track">

                      <div
                        className="score-fill cancer-fill"
                        style={{
                          width: `${
                            Math.min(
                              100,
                              Number(
                                analysisResult
                                  .class_scores
                                  ?.cancer || 0
                              )
                            )
                          }%`,
                        }}
                      />

                    </div>

                  </div>


                  <div className="score-item">

                    <div className="score-label">

                      <span>
                        Non-cancer
                      </span>

                      <strong>
                        {formatNumber(
                          analysisResult
                            .class_scores
                            ?.non_cancer
                        )}
                        %
                      </strong>

                    </div>

                    <div className="score-track">

                      <div
                        className="score-fill neutral-fill"
                        style={{
                          width: `${
                            Math.min(
                              100,
                              Number(
                                analysisResult
                                  .class_scores
                                  ?.non_cancer || 0
                              )
                            )
                          }%`,
                        }}
                      />

                    </div>

                  </div>

                </div>


                <div className="score-note">
                  Scores represent the model's
                  class outputs for this image.
                </div>

              </div>

            </div>


            {/* =================================================
                QUALITY + IMAGE
            ================================================= */}

            <div className="analysis-grid">


              <div className="result-panel">

                <div className="panel-heading">

                  <div>
                    <div className="panel-eyebrow">
                      IMAGE QUALITY
                    </div>

                    <h3>
                      Capture assessment
                    </h3>
                  </div>

                  <div
                    className={`status-pill ${
                      getQualityClass()
                    }`}
                  >
                    {analysisResult.quality
                      ?.quality_status ||
                      "UNKNOWN"}
                  </div>

                </div>


                <div className="metric-grid">

                  <div className="metric-box">
                    <span>
                      WIDTH
                    </span>

                    <strong>
                      {
                        analysisResult
                          .quality?.width ||
                        "—"
                      }
                      <small> px</small>
                    </strong>
                  </div>


                  <div className="metric-box">
                    <span>
                      HEIGHT
                    </span>

                    <strong>
                      {
                        analysisResult
                          .quality?.height ||
                        "—"
                      }
                      <small> px</small>
                    </strong>
                  </div>


                  <div className="metric-box">
                    <span>
                      BRIGHTNESS
                    </span>

                    <strong>
                      {formatNumber(
                        analysisResult
                          .quality?.brightness
                      )}
                    </strong>
                  </div>


                  <div className="metric-box">
                    <span>
                      SHARPNESS
                    </span>

                    <strong>
                      {formatNumber(
                        analysisResult
                          .quality?.sharpness
                      )}
                    </strong>
                  </div>

                </div>

              </div>


              {/* GRAD CAM */}

              <div className="result-panel gradcam-panel">

                <div className="panel-heading">

                  <div>
                    <div className="panel-eyebrow">
                      EXPLAINABILITY
                    </div>

                    <h3>
                      Grad-CAM evidence
                    </h3>
                  </div>

                  <Eye size={17} />

                </div>


                {getGradcamUrl() ? (

                  <div className="gradcam-image-wrapper">

                    <img
                      src={getGradcamUrl()}
                      alt="Grad-CAM visualization"
                      className="gradcam-image"
                    />

                    <div className="gradcam-label">
                      MODEL ATTENTION VISUALIZATION
                    </div>

                  </div>

                ) : (

                  <div className="empty-visual">

                    <Eye size={25} />

                    <span>
                      Grad-CAM image unavailable
                    </span>

                  </div>

                )}


                <p className="panel-note">
                  Grad-CAM highlights image regions
                  that contributed to the model's
                  prediction. It is not a clinical
                  lesion boundary or diagnosis.
                </p>

              </div>

            </div>


            {/* =================================================
                LESION MEASUREMENT
            ================================================= */}

            <div className="result-panel measurement-panel">

              <div className="panel-heading">

                <div>

                  <div className="panel-eyebrow">
                    IMAGE ANALYSIS
                  </div>

                  <h3>
                    Lesion measurement
                  </h3>

                </div>

                <Ruler size={18} />

              </div>


              {analysisResult.lesion_measurement ? (

                <div className="measurement-content">

                  <div className="measurement-status">

                    <CheckCircle2 size={17} />

                    <span>
                      {
                        analysisResult
                          .lesion_measurement
                          .status ||
                        "ESTIMATED"
                      }
                    </span>

                  </div>


                  <div className="measurement-grid">

                    <div className="measurement-box">

                      <span>
                        WIDTH
                      </span>

                      <strong>
                        {
                          analysisResult
                            .lesion_measurement
                            .width_pixels ??
                          "—"
                        }

                        <small>
                          px
                        </small>
                      </strong>

                    </div>


                    <div className="measurement-box">

                      <span>
                        HEIGHT
                      </span>

                      <strong>
                        {
                          analysisResult
                            .lesion_measurement
                            .height_pixels ??
                          "—"
                        }

                        <small>
                          px
                        </small>
                      </strong>

                    </div>


                    <div className="measurement-box">

                      <span>
                        AREA
                      </span>

                      <strong>
                        {
                          formatNumber(
                            analysisResult
                              .lesion_measurement
                              .area_pixels
                          )
                        }

                        <small>
                          px²
                        </small>
                      </strong>

                    </div>


                    <div className="measurement-box">

                      <span>
                        CALIBRATION
                      </span>

                      <strong>
                        {analysisResult
                          .lesion_measurement
                          .calibration_available
                          ? "AVAILABLE"
                          : "NOT AVAILABLE"}
                      </strong>

                    </div>

                  </div>


                  <div className="measurement-note">

                    <Info size={14} />

                    <span>
                      {
                        analysisResult
                          .lesion_measurement
                          .note ||
                        "Physical dimensions require a valid image calibration reference."
                      }
                    </span>

                  </div>

                </div>

              ) : (

                <div className="measurement-unavailable">

                  <Ruler size={22} />

                  <div>

                    <strong>
                      Image-based measurement
                    </strong>

                    <span>
                      No lesion measurement was returned
                      by the current API response.
                    </span>

                  </div>

                </div>

              )}

            </div>


            {/* =================================================
                CONTEXT FLAGS
            ================================================= */}

            <div className="analysis-grid">


              <div className="result-panel">

                <div className="panel-heading">

                  <div>

                    <div className="panel-eyebrow">
                      RESEARCH CONTEXT
                    </div>

                    <h3>
                      Case profile
                    </h3>

                  </div>

                  <UserRound size={17} />

                </div>


                <div className="case-profile-list">

                  <div>
                    <span>
                      LESION LOCATION
                    </span>

                    <strong>
                      {lesionLocation ||
                        "Not specified"}
                    </strong>
                  </div>


                  <div>
                    <span>
                      SYMPTOMS
                    </span>

                    <strong>
                      {
                        patientContext.symptoms
                          .length
                      }{" "}
                      reported
                    </strong>
                  </div>


                  <div>
                    <span>
                      TOBACCO
                    </span>

                    <strong>
                      {patientContext.tobacco ||
                        "Not provided"}
                    </strong>
                  </div>


                  <div>
                    <span>
                      ALCOHOL
                    </span>

                    <strong>
                      {patientContext.alcohol ||
                        "Not provided"}
                    </strong>
                  </div>

                </div>

              </div>


              <div className="result-panel">

                <div className="panel-heading">

                  <div>

                    <div className="panel-eyebrow">
                      REVIEW PROMPTS
                    </div>

                    <h3>
                      Context flags
                    </h3>

                  </div>

                  <AlertTriangle size={17} />

                </div>


                {contextFlags.length > 0 ? (

                  <div className="flag-list">

                    {contextFlags.map(
                      (flag, index) => (

                        <div
                          className="flag-item"
                          key={`${flag}-${index}`}
                        >

                          <AlertTriangle
                            size={14}
                          />

                          <span>
                            {flag}
                          </span>

                        </div>

                      )
                    )}

                  </div>

                ) : (

                  <div className="no-flags">

                    <CheckCircle2 size={17} />

                    <span>
                      No additional context flags
                      were entered.
                    </span>

                  </div>

                )}


                <p className="panel-note">
                  These are user-reported research
                  context prompts. They do not alter
                  the model prediction.
                </p>

              </div>

            </div>


            {/* =================================================
                RECOMMENDATION
            ================================================= */}

            <div className="recommendation-card">

              <div className="recommendation-icon">

                <Stethoscope size={21} />

              </div>


              <div>

                <div className="panel-eyebrow">
                  NEXT STEP
                </div>

                <h3>
                  Model recommendation
                </h3>

                <p>
                  {analysisResult.recommendation ||
                    "No recommendation returned by the API."}
                </p>

              </div>

            </div>


            {/* =================================================
                DISCLAIMER
            ================================================= */}

            <div className="medical-disclaimer">

              <ShieldCheck size={18} />

              <div>

                <strong>
                  Research-only output
                </strong>

                <p>
                  CancerLense is an AI-assisted
                  research screening prototype.
                  Its image prediction, confidence
                  score, class scores and Grad-CAM
                  visualization are model outputs,
                  not a medical diagnosis. Professional
                  clinical evaluation remains separate
                  from this system.
                </p>

              </div>

            </div>

          </div>

        )}

      </section>
    );
  };


  /* =======================================================
     PLACEHOLDER
  ======================================================= */

  const renderPlaceholder = () => {

    const current =
      navigation.find(
        (item) =>
          item.label === activePage
      );

    const Icon =
      current?.icon || ScanLine;


    return (
      <section className="placeholder-page">

        <div className="placeholder-icon">

          <Icon
            size={30}
            strokeWidth={1.5}
          />

        </div>


        <div className="placeholder-label">
          CANCERLENSE /{" "}
          {activePage.toUpperCase()}
        </div>


        <h2>
          {pageTitles[activePage]}
        </h2>


        <p>
          This module will be connected
          to the CancerLense research
          workflow next.
        </p>


        <button
          className="placeholder-button"
          onClick={() =>
            setActivePage("Dashboard")
          }
        >
          Back to Dashboard
        </button>

      </section>
    );
  };


  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div className="app-shell">


      {/* =================================================
          TOPBAR
      ================================================= */}

      <header className="topbar">

        <div className="brand">

          <div className="brand-mark">

            <ScanLine
              size={20}
              strokeWidth={1.8}
            />

          </div>


          <div className="brand-text">

            <div className="brand-name">
              Cancer<span>Lense</span>
            </div>

            <div className="brand-subtitle">
              AI RESEARCH PROTOTYPE
            </div>

          </div>

        </div>


        <div className="topbar-right">

          <div className="system-status">

            <span className="status-dot"></span>

            <span>
              Online
            </span>

          </div>


          <button
            className="profile-button"
            aria-label="Profile"
          >

            <CircleUserRound
              size={19}
              strokeWidth={1.7}
            />

          </button>

        </div>

      </header>


      {/* =================================================
          APPLICATION LAYOUT
      ================================================= */}

      <div className="application-layout">


        {/* =================================================
            SIDEBAR
        ================================================= */}

        <aside className="sidebar">

          <div className="sidebar-navigation">

            {navigation.map(
              (item) => {

                const Icon =
                  item.icon;

                return (

                  <button
                    key={item.label}
                    className={`sidebar-item ${
                      activePage ===
                      item.label
                        ? "active"
                        : ""
                    }`}
                    onClick={() =>
                      setActivePage(
                        item.label
                      )
                    }
                  >

                    <Icon
                      size={18}
                      strokeWidth={1.8}
                    />

                    <span>
                      {item.label}
                    </span>


                    {activePage ===
                      item.label && (

                      <ChevronRight
                        size={14}
                        className="sidebar-arrow"
                      />

                    )}

                  </button>

                );

              }
            )}

          </div>


          <div className="sidebar-footer">

            <div className="privacy-box">

              <ShieldCheck
                size={18}
                strokeWidth={1.7}
              />

              <div>

                <strong>
                  Research Mode
                </strong>

                <span>
                  AI-assisted screening only
                </span>

              </div>

            </div>


            <div className="version">
              CancerLense v0.1
            </div>

          </div>

        </aside>


        {/* =================================================
            MAIN
        ================================================= */}

        <main className="main-content">


          <section className="page-header">

            <div>

              <div className="eyebrow">
                CANCERLENSE /{" "}
                {activePage.toUpperCase()}
              </div>

              <h1>
                {pageTitles[activePage]}
              </h1>

              <p>
                AI-assisted oral image screening
                research environment.
              </p>

            </div>


            <div className="page-status">

              <Activity
                size={17}
              />

              <span>
                SYSTEM READY
              </span>

            </div>

          </section>


          {activePage ===
            "Dashboard" &&
            renderDashboard()}


          {activePage ===
            "Screen" &&
            renderScreen()}


          {activePage !== "Dashboard" &&
            activePage !== "Screen" &&
            renderPlaceholder()}

        </main>

      </div>


      {/* =================================================
          CAMERA MODAL
      ================================================= */}

      {cameraOpen && (

        <div className="camera-modal">

          <div className="camera-modal-card">


            <div className="camera-modal-header">

              <div>

                <div className="panel-eyebrow">
                  CANCERLENSE / CAMERA
                </div>

                <h3>
                  Capture oral image
                </h3>

              </div>


              <button
                className="icon-button"
                onClick={closeCamera}
              >
                <X size={18} />
              </button>

            </div>


            <div className="camera-view">

              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
              ></video>


              <div className="camera-frame">

                <div className="corner top-left"></div>
                <div className="corner top-right"></div>
                <div className="corner bottom-left"></div>
                <div className="corner bottom-right"></div>

              </div>


              <div className="camera-guide">
                Position the oral area inside the frame
              </div>

            </div>


            <div className="camera-actions">

              <button
                className="secondary-action"
                onClick={closeCamera}
              >
                Cancel
              </button>


              <button
                className="analyze-button capture-button"
                onClick={capturePhoto}
              >
                <Camera size={18} />
                Capture image
              </button>

            </div>


          </div>

        </div>

      )}


      <canvas
        ref={canvasRef}
        style={{ display: "none" }}
      />

    </div>

  );
}

export default App;