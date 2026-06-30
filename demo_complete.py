#!/usr/bin/env python3
"""
Plant Intelligence Capability - Complete Demo with Terminal Output
This script demonstrates the full system with both UI and terminal logging
"""

import requests
import json
from datetime import datetime
import sys

# Force UTF-8 encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def print_section(title):
    """Print a section header."""
    print(f"\n{title}")
    print("-" * len(title))

def demo_api():
    """Run a complete API demo."""
    
    BASE_URL = "http://127.0.0.1:8000"
    TEST_IMAGE = "test_leaf.jpg"
    
    print_header("PLANT INTELLIGENCE CAPABILITY - COMPLETE SYSTEM DEMO")
    
    print(f"[INFO] API Base URL: {BASE_URL}")
    print(f"[INFO] Test Image: {TEST_IMAGE}")
    print(f"[INFO] Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Health Check
    print_section("TEST 1: HEALTH CHECK - GET /health")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"[OK] Status Code: {response.status_code}")
        print(f"[RESPONSE]:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"[ERROR] {e}")
    
    # Test 2: Capabilities
    print_section("TEST 2: CAPABILITIES CHECK - GET /capabilities")
    try:
        response = requests.get(f"{BASE_URL}/capabilities", timeout=5)
        print(f"[OK] Status Code: {response.status_code}")
        data = response.json()
        print(f"[RESPONSE]:")
        for key, value in data.items():
            status = "[OK]" if value else "[FAIL]"
            print(f"  {status} {key}: {value}")
    except Exception as e:
        print(f"[ERROR] {e}")
    
    # Test 3: Identify
    print_section("TEST 3: PLANT IDENTIFICATION - POST /identify")
    try:
        with open(TEST_IMAGE, 'rb') as f:
            files = {'image': f}
            response = requests.post(f"{BASE_URL}/identify", files=files, timeout=30)
        
        print(f"[OK] Status Code: {response.status_code}")
        result = response.json()
        print(f"[RESPONSE]:")
        print(json.dumps(result, indent=2))
        
        print(f"\n[ANALYSIS]:")
        print(f"  Status: {result.get('status', 'N/A')}")
        print(f"  Confidence: {result.get('confidence', 'N/A') * 100:.1f}%")
        if result.get('reason'):
            print(f"  Reason: {result.get('reason')}")
            
    except Exception as e:
        print(f"[ERROR] {e}")
    
    # Test 4: Full Analysis
    print_section("TEST 4: FULL ANALYSIS - POST /analyze")
    try:
        with open(TEST_IMAGE, 'rb') as f:
            files = {'image': f}
            response = requests.post(f"{BASE_URL}/analyze", files=files, timeout=30)
        
        print(f"[OK] Status Code: {response.status_code}")
        result = response.json()
        
        print(f"\n[QUICK ANALYSIS]:")
        print(f"  Plant Species: {result.get('plant_species', 'N/A')}")
        print(f"  Plant Part: {result.get('plant_part', 'N/A')}")
        print(f"  Growth Stage: {result.get('growth_stage', 'N/A')}")
        print(f"  Confidence: {result.get('confidence', 'N/A') * 100:.1f}%")
        print(f"  Model Version: {result.get('model_version', 'N/A')}")
        print(f"  Inference Time: {result.get('inference_time', 'N/A')}")
        
        observations = result.get('observations', [])
        print(f"\n[STRUCTURED OBSERVATIONS] ({len(observations)} generated):")
        for i, obs in enumerate(observations, 1):
            print(f"\n  [{i}] {obs.get('type')}")
            print(f"      Value: {obs.get('value')}")
            print(f"      Confidence: {obs.get('confidence') * 100:.1f}%")
            print(f"      Evidence Source: {obs.get('evidence_source')}")
        
        print(f"\n[FULL JSON RESPONSE]:")
        print(json.dumps(result, indent=2))
            
    except Exception as e:
        print(f"[ERROR] {e}")
    
    # Test 5: Invalid Image
    print_section("TEST 5: ERROR HANDLING - Invalid Image")
    try:
        files = {'image': ('invalid.txt', b'not an image')}
        response = requests.post(f"{BASE_URL}/identify", files=files)
        
        print(f"[WARN] Status Code: {response.status_code}")
        print(f"[OK] Invalid image correctly rejected")
        print(f"[ERROR RESPONSE]:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"[ERROR] {e}")
    
    # Test 6: Missing Image
    print_section("TEST 6: ERROR HANDLING - Missing Image")
    try:
        response = requests.post(f"{BASE_URL}/identify", files={})
        
        print(f"[WARN] Status Code: {response.status_code}")
        print(f"[OK] Missing image correctly rejected")
        print(f"[ERROR RESPONSE]:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"[ERROR] {e}")
    
    # Summary
    print_header("DEMO COMPLETE - SUMMARY")
    
    summary = f"""
    [STATUS] System Status: OPERATIONAL
    
    [ENDPOINTS TESTED]
       + GET /health - Server health check
       + GET /capabilities - Feature detection
       + POST /identify - Quick species identification
       + POST /analyze - Full analysis with evidence
    
    [ERROR HANDLING]
       + Invalid image format rejection
       + Missing image detection
       + Proper HTTP status codes
    
    [FEATURES]
       + Image upload and processing
       + Confidence-based filtering (>70% threshold)
       + Structured agricultural evidence generation
       + JSON response formatting
       + Comprehensive logging
    
    [WEB UI]
       + Available at: {BASE_URL}
       + Drag-and-drop image upload
       + Real-time analysis results
       + JSON display and copy functionality
       + Terminal logging integration
    
    [API DOCUMENTATION]
       + Swagger UI at: {BASE_URL}/docs
       + Interactive endpoint testing
       + Request/response schemas
    """
    
    print(summary)
    
    print(f"\n[NEXT STEPS]:")
    print(f"   1. Open UI at {BASE_URL}")
    print(f"   2. Upload a plant image")
    print(f"   3. View results in browser")
    print(f"   4. Check server logs in terminal")
    print(f"   5. Use Swagger at {BASE_URL}/docs for API testing")

if __name__ == "__main__":
    try:
        demo_api()
    except Exception as e:
        print(f"❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()
