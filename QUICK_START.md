# 🚀 Quick Reference Guide - Plant Intelligence Capability

## ⚡ 30-Second Quick Start

### 1. Start the server:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 2. Open in browser:
```
http://127.0.0.1:8000
```

### 3. Upload image → Click Analyze → See Results!

---

## 🌐 What You Can Access

| Feature | URL | Description |
|---------|-----|-------------|
| **Web UI** | http://127.0.0.1:8000 | Upload images & get results |
| **API Docs** | http://127.0.0.1:8000/docs | Swagger interactive docs |
| **Health Check** | http://127.0.0.1:8000/health | Server status |
| **Capabilities** | http://127.0.0.1:8000/capabilities | Available features |

---

## 📤 Upload Methods

### Method 1: Web UI (Recommended)
1. Drag image to upload area
2. OR click to browse files
3. Click "Analyze Plant"
4. View results instantly

### Method 2: Using curl
```bash
curl -X POST -F "image=@plant.jpg" \
  http://127.0.0.1:8000/identify
```

### Method 3: Using Python
```python
import requests

with open('plant.jpg', 'rb') as f:
    response = requests.post(
        'http://127.0.0.1:8000/analyze',
        files={'image': f}
    )
print(response.json())
```

---

## 📊 Expected Results

### If Confidence > 70%:
```json
{
  "plant_species": "Tomato",
  "confidence": 0.92,
  "observations": [
    {
      "type": "Leaf Colour",
      "value": "Dark Green",
      "confidence": 0.95
    },
    ...
  ]
}
```

### If Confidence < 70%:
```json
{
  "status": "Unknown Plant",
  "confidence": 0.5,
  "reason": "Confidence below threshold"
}
```

---

## 🧪 Test It

### Option 1: Use Test Image
```bash
python test_api.py
```

### Option 2: Run Full Demo
```bash
python demo_complete.py
```

### Option 3: Manual with Swagger
1. Go to http://127.0.0.1:8000/docs
2. Expand endpoint
3. Click "Try it out"
4. Upload image
5. Click "Execute"

---

## 🎯 11 Observations Generated

When confidence is high:

| # | Type | Detects |
|---|------|---------|
| 1 | Leaf Colour | Green/Yellow/Brown hue |
| 2 | Leaf Shape | Round/Oval/Linear/Heart |
| 3 | Leaf Texture | Smooth/Medium/Rough |
| 4 | Stem Health | Healthy/Dry appearance |
| 5 | Flower Presence | Present/Not Present |
| 6 | Fruit Condition | Ripening/Mature status |
| 7 | Pest Indicators | Present/Not Present |
| 8 | Nutrient Deficiency | Chlorosis signs |
| 9 | Water Stress | Curling/Drooping |
| 10 | Mechanical Damage | Broken/Torn leaves |
| 11 | Abnormalities | Unknown issues |

---

## 📋 JSON Response Structure

```json
{
  "plant_species": "string",
  "plant_part": "string",
  "growth_stage": "string",
  "confidence": 0.0-1.0,
  "observations": [
    {
      "observation_id": "OBS001",
      "type": "string",
      "value": "string",
      "confidence": 0.0-1.0,
      "supporting_features": ["string"],
      "timestamp": "ISO 8601",
      "model_version": "string",
      "evidence_source": "Image Analysis"
    }
  ],
  "model_version": "string",
  "inference_time": "string"
}
```

---

## 🎨 UI Screenshot Description

```
┌─────────────────────────────────────┐
│  🌿 Plant Intelligence Capability   │
│  Advanced Agricultural Evidence...  │
├─────────────────────────────────────┤
│                                     │
│  📤 Upload Plant Image              │
│  ┌─────────────────────────────┐   │
│  │ Drag and drop your plant    │   │
│  │ image here or click to select│  │
│  └─────────────────────────────┘   │
│                                     │
│  [🔍 Analyze] [Quick] [Clear]      │
│                                     │
│  ─ Results ─────────────────────   │
│  [📋 Copy JSON]                    │
│                                     │
│  STATUS: Unknown Plant              │
│  CONFIDENCE: 50.0%                 │
│                                     │
│  📄 Full JSON Response              │
│  {                                  │
│    "status": "Unknown Plant"        │
│    "confidence": 0.5                │
│  }                                  │
│                                     │
└─────────────────────────────────────┘
```

---

## 🖥️ Terminal Output You'll See

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:plant_ai:Starting Plant Intelligence Capability...
INFO:plant_ai.part:Loaded part detection model
INFO:     Application startup complete.

INFO:     127.0.0.1:56588 - "POST /analyze HTTP/1.1" 200 OK
WARNING:plant_ai.species:Species prediction...
```

---

## ⚙️ Configuration

### Change Confidence Threshold:
Edit `app/config.py`:
```python
UNKNOWN_CONFIDENCE_THRESHOLD = 0.7  # Change from 70% to whatever
```

### Change API Port:
```bash
python -m uvicorn app.main:app --port 9000
```

### Change API Host:
```bash
python -m uvicorn app.main:app --host 0.0.0.0
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 8000 in use | Kill process or use different port |
| Models not loading | Check weights/ directory |
| UI not loading | Clear browser cache |
| Slow inference | Ensure GPU available |
| 400 error on upload | File must be image format |

---

## 📁 Important Files

```
app/
├── main.py              ← FastAPI server
├── routes.py            ← Endpoints
├── inference.py         ← Model orchestration
├── evidence.py          ← 11 observations
└── static/
    ├── index.html       ← Web UI
    ├── style.css        ← Styling
    └── script.js        ← JavaScript

weights/
├── species_model.pth    ← Species classifier
├── growth_stage.pt      ← Growth detector
└── Plant part.pt        ← YOLO detector
```

---

## 📊 API Endpoints Summary

### GET /health
```bash
curl http://127.0.0.1:8000/health
```
Returns: `{"status": "running", "version": "..."}`

### GET /capabilities
```bash
curl http://127.0.0.1:8000/capabilities
```
Returns: All 5 features as true/false

### POST /identify
```bash
curl -X POST -F "image=@plant.jpg" \
  http://127.0.0.1:8000/identify
```
Returns: Species + confidence (fast)

### POST /analyze
```bash
curl -X POST -F "image=@plant.jpg" \
  http://127.0.0.1:8000/analyze
```
Returns: Full analysis + 11 observations

---

## 💾 Saving Results

### Copy from UI:
1. Click "Copy JSON" button
2. Paste into file

### Via Terminal:
```bash
python -c "
import requests
with open('plant.jpg', 'rb') as f:
    r = requests.post('http://127.0.0.1:8000/analyze', 
                     files={'image': f})
with open('result.json', 'w') as f:
    import json
    json.dump(r.json(), f, indent=2)
"
```

---

## 🎓 Example Workflow

```
1. START SERVER
   ↓
2. OPEN BROWSER (http://127.0.0.1:8000)
   ↓
3. UPLOAD IMAGE
   • Drag image
   • See preview
   ↓
4. CLICK ANALYZE
   • Loading spinner appears
   • Server processes in terminal
   ↓
5. VIEW RESULTS
   • UI shows status & confidence
   • Results cards display
   • JSON viewer shows full data
   ↓
6. EXPORT/COPY
   • Click Copy JSON
   • Paste to your app
```

---

## ✅ Verification

Run test script to verify everything works:
```bash
python test_api.py
```

Expected output:
```
[OK] Status Code: 200
[OK] All endpoints respond
[OK] Results format correct
[OK] Error handling works
```

---

## 📚 Documentation Files

In workspace:
- `SYSTEM_SUMMARY.md` - This complete guide
- `COMPLETE_SYSTEM_GUIDE.md` - Detailed guide
- `ARCHITECTURE.md` - System architecture
- `TEST_REPORT.md` - Test results

---

## 🎯 What's Next?

1. ✅ Test with real plant images
2. ✅ Adjust confidence threshold
3. ✅ Integrate with your app
4. ✅ Deploy to production

---

## 📞 Quick Help

**Server won't start?**
```bash
# Check if port is in use
netstat -ano | findstr :8000
```

**Want to debug?**
- Check terminal for logs
- Open http://127.0.0.1:8000/docs for API debugging
- Use browser console (F12) for UI debugging

**Need to stop server?**
```
Press Ctrl+C in terminal
```

---

**Ready to analyze plants? Go to http://127.0.0.1:8000 now! 🌿**
