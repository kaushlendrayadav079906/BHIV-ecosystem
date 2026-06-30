# Plant Intelligence Capability - System Architecture

## 🏗️ Complete System Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                             │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────┐      ┌──────────────────┐                  │
│  │   WEB BROWSER    │      │  TERMINAL        │                  │
│  │                  │      │                  │                  │
│  │ • Upload UI      │◄────►│ • Logging        │                  │
│  │ • Image Preview  │      │ • Debugging      │                  │
│  │ • Results Disp   │      │ • Monitoring     │                  │
│  │ • JSON Viewer    │      │                  │                  │
│  │ • Copy Button    │      │                  │                  │
│  └──────────────────┘      └──────────────────┘                  │
│                                                                    │
└─────────────────────────┬──────────────────────────────────────────┘
                          │
                HTTP Requests (JSON)
                          │
         ┌────────────────▼──────────────────┐
         │    FASTAPI WEB SERVER             │
         │    (Port 8000)                    │
         ├───────────────────────────────────┤
         │                                   │
         │  ┌─────────────────────────────┐  │
         │  │  ROUTE HANDLERS             │  │
         │  │                             │  │
         │  │ • GET /                     │  │  Serve UI
         │  │ • GET /health               │  │  Health Check
         │  │ • GET /capabilities         │  │  Feature List
         │  │ • POST /identify            │  │  Quick ID
         │  │ • POST /analyze             │  │  Full Analysis
         │  │ • GET /static/*             │  │  CSS/JS Files
         │  │ • GET /docs (Swagger)       │  │  API Docs
         │  └─────────────────────────────┘  │
         │                                   │
         └───────────────┬───────────────────┘
                         │
         ┌───────────────▼───────────────────┐
         │   INFERENCE ENGINE                │
         │   (Orchestration Layer)           │
         ├───────────────────────────────────┤
         │                                   │
         │  ┌──────────────────────────────┐ │
         │  │ Image Preprocessing          │ │
         │  │ • File validation            │ │
         │  │ • Format conversion          │ │
         │  │ • Resizing to model input    │ │
         │  └──────────────────────────────┘ │
         │                 │                 │
         │  ┌──────────────▼──────────────┐ │
         │  │ Model Inference             │ │
         │  │ • Load species classifier   │ │
         │  │ • Load growth stage model   │ │
         │  │ • Load YOLO detector        │ │
         │  │ • Run predictions           │ │
         │  └──────────────────────────────┘ │
         │                 │                 │
         │  ┌──────────────▼──────────────┐ │
         │  │ Evidence Generation         │ │
         │  │ • Generate 11 observations  │ │
         │  │ • OpenCV analysis           │ │
         │  │ • Feature extraction        │ │
         │  │ • Confidence scoring        │ │
         │  └──────────────────────────────┘ │
         │                                   │
         └───────────────┬───────────────────┘
                         │
         ┌───────────────▼───────────────────┐
         │   ML MODELS                       │
         ├───────────────────────────────────┤
         │                                   │
         │  ┌──────────────────────────────┐ │
         │  │ SPECIES CLASSIFIER           │ │  species_model.pth
         │  │ • PyTorch state dict         │ │  40+ plant species
         │  │ • Confidence: 0-1.0          │ │  224x224 input
         │  └──────────────────────────────┘ │
         │                                   │
         │  ┌──────────────────────────────┐ │
         │  │ GROWTH STAGE DETECTOR        │ │  growth_stage.pt
         │  │ • PyTorch model              │ │  4 stages
         │  │ • Seedling/Veg/Flow/Fruit    │ │  Time series capable
         │  └──────────────────────────────┘ │
         │                                   │
         │  ┌──────────────────────────────┐ │
         │  │ PLANT PART DETECTOR (YOLO)   │ │  Plant part.pt
         │  │ • Ultralytics YOLO v8        │ │  Leaf/Flower/Fruit/Stem
         │  │ • Bounding boxes             │ │  Real-time detection
         │  │ • Multi-class detection      │ │
         │  └──────────────────────────────┘ │
         │                                   │
         └───────────────────────────────────┘
```

---

## 📊 Data Flow Diagram

```
┌─────────────┐
│   UPLOAD    │
│  IMAGE      │
│  (jpeg/png) │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│  VALIDATION                 │
│  • File type check          │
│  • Format verification      │
│  • Size validation          │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│  IMAGE PREPROCESSING        │
│  • Load with PIL            │
│  • Convert to RGB           │
│  • Resize to 224x224        │
│  • Normalize to tensor      │
└──────┬──────────────────────┘
       │
       ├──────────────────────────┬──────────────────────────┐
       │                          │                          │
       ▼                          ▼                          ▼
  ┌─────────┐           ┌──────────────┐          ┌─────────────┐
  │ SPECIES │           │GROWTH STAGE  │          │PLANT PARTS  │
  │ PREDICT │           │  PREDICT     │          │ DETECT      │
  │         │           │              │          │             │
  │ Result: │           │ Result:      │          │ Result:     │
  │ Tomato  │           │ Flowering    │          │ Leaves (95%)│
  │ 92%     │           │ 87%          │          │ Flower(78%) │
  └────┬────┘           └──────┬───────┘          └──────┬──────┘
       │                       │                         │
       └───────────────────────┼─────────────────────────┘
                               │
                               ▼
                    ┌──────────────────────────┐
                    │ Confidence > 70%?        │
                    └──────┬──────────────────┘
                           │
                    ┌──────┴──────┐
                    │             │
                   YES           NO
                    │             │
                    ▼             ▼
        ┌───────────────────┐  ┌──────────────────┐
        │ GENERATE 11 OBS   │  │ Return Unknown   │
        │                   │  │ Plant Status     │
        │ • Leaf Colour     │  │                  │
        │ • Leaf Shape      │  │ Confidence: 0.5  │
        │ • Leaf Texture    │  │ Reason: Below    │
        │ • Stem Health     │  │ threshold        │
        │ • Flower Presence │  └──────────────────┘
        │ • Fruit Condition │
        │ • Pest Indicators │
        │ • Nutrient Status │
        │ • Water Stress    │
        │ • Mechanical Dmg  │
        │ • Abnormalities   │
        └────────┬──────────┘
                 │
                 ▼
        ┌──────────────────────────┐
        │ FORMAT JSON RESPONSE     │
        │                          │
        │ {                        │
        │  "species": "Tomato",    │
        │  "confidence": 0.92,     │
        │  "observations": [       │
        │    { OBS001 },           │
        │    { OBS002 },           │
        │    ...                   │
        │  ]                       │
        │ }                        │
        └────────┬─────────────────┘
                 │
                 ▼
        ┌──────────────────────┐
        │ RETURN TO UI         │
        │ Display Results      │
        │ Show JSON            │
        │ Enable Copy Button   │
        └──────────────────────┘
```

---

## 🌐 HTTP Request/Response Flow

### Identify Request
```
┌─ REQUEST ──────────────────────────────────────────────┐
│ POST /identify HTTP/1.1                                 │
│ Host: 127.0.0.1:8000                                    │
│ Content-Type: multipart/form-data                       │
│                                                         │
│ [Binary image data in form field "image"]               │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼ (Processing)
                        │
                        ▼
┌─ RESPONSE ─────────────────────────────────────────────┐
│ HTTP/1.1 200 OK                                         │
│ Content-Type: application/json                          │
│                                                         │
│ {                                                       │
│   "status": "Unknown Plant",                            │
│   "confidence": 0.5,                                    │
│   "reason": "Confidence below threshold"                │
│ }                                                       │
└─────────────────────────────────────────────────────────┘
```

### Analyze Request
```
┌─ REQUEST ──────────────────────────────────────────────┐
│ POST /analyze HTTP/1.1                                  │
│ Host: 127.0.0.1:8000                                    │
│ Content-Type: multipart/form-data                       │
│                                                         │
│ [Binary image data in form field "image"]               │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼ (Processing - 400-800ms)
                        │
                        ▼
┌─ RESPONSE ─────────────────────────────────────────────┐
│ HTTP/1.1 200 OK                                         │
│ Content-Type: application/json                          │
│                                                         │
│ {                                                       │
│   "plant_species": "Tomato",                            │
│   "plant_part": "Leaf",                                 │
│   "growth_stage": "Flowering",                          │
│   "confidence": 0.92,                                   │
│   "observations": [                                     │
│     {                                                   │
│       "observation_id": "OBS001",                       │
│       "type": "Leaf Colour",                            │
│       "value": "Dark Green",                            │
│       "confidence": 0.95,                               │
│       "supporting_features": ["HSV Analysis"],          │
│       "timestamp": "2026-06-25T12:00:00Z",              │
│       "model_version": "PlantAI-v1.0",                  │
│       "evidence_source": "Image Analysis"               │
│     },                                                  │
│     ... (10 more observations)                          │
│   ],                                                    │
│   "model_version": "Analysis-v1",                       │
│   "inference_time": "450 ms"                            │
│ }                                                       │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         FASTAPI SERVER                      │
│                                                              │
│  ┌────────────────┐     ┌──────────────┐                   │
│  │  MAIN.PY       │────→│  ROUTES.PY   │                   │
│  │ • App config   │     │ • Endpoints  │                   │
│  │ • Static files │     │ • Handlers   │                   │
│  │ • Middleware   │     │              │                   │
│  └────────────────┘     └──────┬───────┘                   │
│                                 │                          │
│                    ┌────────────▼──────────────┐            │
│                    │    UTILS.PY               │            │
│                    │ • Image validation        │            │
│                    │ • File type checking      │            │
│                    └────────────┬──────────────┘            │
│                                 │                          │
│                    ┌────────────▼──────────────┐            │
│                    │  INFERENCE.PY             │            │
│                    │ • Model orchestration     │            │
│                    │ • Pipeline execution      │            │
│                    └────┬──────────┬──────┬────┘            │
│                         │          │      │                │
│         ┌───────────────┼──────────┼──────┼──────────────┐  │
│         │               │          │      │              │  │
│         ▼               ▼          ▼      ▼              │  │
│  ┌─────────────┐ ┌────────┐ ┌────────┐ ┌────────────┐   │  │
│  │SPECIES      │ │GROWTH  │ │PART    │ │EVIDENCE.PY │   │  │
│  │_MODEL.PY    │ │_MODEL  │ │_MODEL  │ │ • 11 Obs   │   │  │
│  │ • Predict   │ │ • Pred │ │ • YOLO │ │ • Features │   │  │
│  │   species   │ │  stage │ │Detect  │ │ • Scoring  │   │  │
│  └──────┬──────┘ └───┬────┘ └───┬────┘ └────────────┘   │  │
│         │            │          │                       │  │
│         └────────────┼──────────┘                       │  │
│                      │                                  │  │
│              ┌───────▼──────────┐                       │  │
│              │ SCHEMAS.PY       │                       │  │
│              │ • Response models│                       │  │
│              │ • Validation     │                       │  │
│              └──────────────────┘                       │  │
│                                                         │  │
└─────────────────────────────────────────────────────────┘  │
                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📱 Frontend Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    BROWSER (HTML/CSS/JS)                 │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │           INDEX.HTML (Structure)                   │ │
│  │                                                    │ │
│  │ • Header + Title                                  │ │
│  │ • Upload area (drag & drop)                       │ │
│  │ • File input (hidden)                             │ │
│  │ • Image preview section                           │ │
│  │ • Buttons (Analyze, Identify, Clear)              │ │
│  │ • Results section (hidden initially)              │ │
│  │ • Quick info cards area                           │ │
│  │ • Observations list area                          │ │
│  │ • JSON viewer                                     │ │
│  │ • Error section                                   │ │
│  │ • Footer + Links                                  │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │         STYLE.CSS (Styling & Animations)          │ │
│  │                                                    │ │
│  │ • Variables (colors, shadows)                     │ │
│  │ • Gradient backgrounds                            │ │
│  │ • Card layouts                                    │ │
│  │ • Button states                                   │ │
│  │ • Upload area hover effects                       │ │
│  │ • Responsive grid layouts                         │ │
│  │ • Animations (fade, slide, bounce)                │ │
│  │ • Mobile breakpoints                              │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │        SCRIPT.JS (Interactivity & Logic)          │ │
│  │                                                    │ │
│  │ ┌── File Upload Handlers ────────────────────────┐ │
│  │ │ • Drag over event handling                     │ │
│  │ │ • Drop event handling                          │ │
│  │ │ • File input change                            │ │
│  │ │ • Preview image generation                     │ │
│  │ └────────────────────────────────────────────────┘ │
│  │                                                    │ │
│  │ ┌── API Call Handlers ───────────────────────────┐ │
│  │ │ • Fetch to /identify endpoint                  │ │
│  │ │ • Fetch to /analyze endpoint                   │ │
│  │ │ • Request/response handling                    │ │
│  │ │ • Loading state management                     │ │
│  │ └────────────────────────────────────────────────┘ │
│  │                                                    │ │
│  │ ┌── Result Display ──────────────────────────────┐ │
│  │ │ • Populate quick info cards                    │ │
│  │ │ • Generate observation items                   │ │
│  │ │ • Format and display JSON                      │ │
│  │ │ • Show/hide sections                           │ │
│  │ └────────────────────────────────────────────────┘ │
│  │                                                    │ │
│  │ ┌── Utility Functions ───────────────────────────┐ │
│  │ │ • Copy to clipboard                            │ │
│  │ │ • Error display                                │ │
│  │ │ • Clear UI                                     │ │
│  │ │ • Terminal console logging                     │ │
│  │ └────────────────────────────────────────────────┘ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 🔐 Error Handling Flow

```
REQUEST
   │
   ▼
┌─────────────────┐
│ FILE VALIDATION │
└────────┬────────┘
         │
    ┌────┴────┐
    │          │
   NO         YES (File exists, readable)
    │          │
    ▼          ▼
ERROR400    ┌────────────┐
Return      │MIME CHECK  │
Error       └────┬───────┘
                 │
            ┌────┴────┐
            │          │
           NO         YES (image/*)
            │          │
            ▼          ▼
         ERROR400    ┌────────────┐
         Return      │ IMAGE OPEN │
         Error       └────┬───────┘
                          │
                    ┌─────┴─────┐
                    │           │
                   ERROR       SUCCESS
                    │           │
                    ▼           ▼
                 ERROR400    ┌──────────────┐
                 Return      │ PROCESS      │
                 Error       │ IMAGE        │
                             └──────────────┘
```

---

## 📊 Model Pipeline

```
INPUT: Preprocessed Image (224x224)
        │
        ├──────────────────────┬──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
    ┌────────┐          ┌──────────┐         ┌──────────┐
    │ SPECIES│          │ GROWTH   │         │ PLANT    │
    │ MODEL  │          │ STAGE    │         │ PART     │
    │ OUTPUT │          │ MODEL    │         │ DETECTOR │
    │        │          │ OUTPUT   │         │ OUTPUT   │
    │Plant:  │          │Stage:    │         │Detections│
    │Tomato  │          │Flowering │         │Leaves:95%│
    │Conf:92%│          │Conf: 87% │         │Flower:78%│
    │        │          │          │         │          │
    └───┬────┘          └──────┬───┘         └──────┬───┘
        │                      │                    │
        └──────────────────────┼────────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │ CHECK CONFIDENCE │
                        │ > 70% threshold  │
                        └────┬─────────────┘
                             │
                        ┌────┴────┐
                        │          │
                       NO         YES
                        │          │
                        ▼          ▼
                    UNKNOWN    ┌─────────────────┐
                    PLANT      │ EVIDENCE        │
                    RETURN     │ GENERATION      │
                               │                 │
                               │ Analyze:        │
                               │ • HSV colours   │
                               │ • Contours      │
                               │ • Texture       │
                               │ • Features      │
                               │                 │
                               └────┬────────────┘
                                    │
                                    ▼
                            ┌─────────────────┐
                            │ OUTPUT: 11      │
                            │ OBSERVATIONS    │
                            │ + CONFIDENCE    │
                            │ + FEATURES      │
                            │ + TIMESTAMP     │
                            └─────────────────┘
```

---

## 🎯 System Status Summary

```
┌─────────────────────────────────────┐
│   PLANT INTELLIGENCE CAPABILITY     │
│          Version 1.0.0              │
└─────────────────────────────────────┘

✅ OPERATIONAL COMPONENTS:
  ├─ Web UI (HTML/CSS/JS)
  ├─ FastAPI Server
  ├─ Image Preprocessing
  ├─ Species Classifier
  ├─ Growth Stage Detector
  ├─ Plant Part Detector (YOLO)
  ├─ Evidence Generator (11 observations)
  ├─ Error Handling
  ├─ Terminal Logging
  └─ API Documentation (Swagger)

📊 ENDPOINTS AVAILABLE:
  ├─ GET  /           (Web UI)
  ├─ GET  /health     (Health Check)
  ├─ GET  /capabilities (Feature List)
  ├─ POST /identify   (Quick ID)
  ├─ POST /analyze    (Full Analysis)
  ├─ GET  /docs       (Swagger UI)
  └─ GET  /static/*   (Assets)

🎨 UI FEATURES:
  ├─ Drag & Drop Upload
  ├─ Image Preview
  ├─ Real-time Analysis
  ├─ Results Display
  ├─ JSON Viewer
  ├─ Copy to Clipboard
  ├─ Error Handling
  └─ Terminal Logging

🔧 CONFIGURATION:
  ├─ Confidence Threshold: 70%
  ├─ API Port: 8000
  ├─ API Host: 127.0.0.1
  ├─ Model Directory: ../weights
  ├─ Static Files: /app/static
  └─ Log Level: INFO

✨ READY FOR:
  ├─ Plant Image Analysis
  ├─ Agricultural Evidence Generation
  ├─ Structured JSON Output
  ├─ Integration with BHIV
  ├─ Real-time Monitoring
  └─ Production Deployment
```

---

This architecture ensures **robust**, **scalable**, and **maintainable** plant analysis capabilities!
