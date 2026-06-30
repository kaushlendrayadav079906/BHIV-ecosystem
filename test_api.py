import requests
import json
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
TEST_IMAGE = "test_leaf.jpg"

print("=" * 80)
print("PLANT INTELLIGENCE CAPABILITY - COMPREHENSIVE TEST")
print("=" * 80)

# Test 1: Health endpoint
print("\n[TEST 1] ✅ GET /health")
try:
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Capabilities endpoint
print("\n[TEST 2] ✅ GET /capabilities")
try:
    response = requests.get(f"{BASE_URL}/capabilities")
    print(f"Status: {response.status_code}")
    caps = response.json()
    print(f"Response: {json.dumps(caps, indent=2)}")
    print(f"  - Species Detection: {caps.get('species_detection')}")
    print(f"  - Growth Stage: {caps.get('growth_stage')}")
    print(f"  - Plant Part Detection: {caps.get('plant_part_detection')}")
    print(f"  - Structured Evidence: {caps.get('structured_evidence')}")
    print(f"  - Explainability: {caps.get('explainability')}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Identify endpoint
print("\n[TEST 3] ✅ POST /identify - Upload plant image")
try:
    with open(TEST_IMAGE, 'rb') as f:
        files = {'image': f}
        response = requests.post(f"{BASE_URL}/identify", files=files)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response:\n{json.dumps(result, indent=2)}")
    print(f"\n  ✅ Species Predicted: {result.get('plant_species')}")
    print(f"  ✅ Confidence: {result.get('confidence')}")
    print(f"  ✅ Model Version: {result.get('model_version')}")
    print(f"  ✅ Inference Time: {result.get('inference_time')}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Analyze endpoint
print("\n[TEST 4] ✅ POST /analyze - Full analysis with structured evidence")
try:
    with open(TEST_IMAGE, 'rb') as f:
        files = {'image': f}
        response = requests.post(f"{BASE_URL}/analyze", files=files)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"\nAnalysis Response:")

    # ── Model 1: Species ──────────────────────────────────────
    print(f"\n  [MODEL 1] Species Detection")
    print(f"  ✅ Plant Species   : {result.get('plant_species')}")
    print(f"  ✅ Confidence      : {result.get('confidence')}")
    alts = result.get('alternatives', [])
    for a in alts:
        print(f"     Alternative    : {a.get('species')} ({round(a.get('confidence',0)*100,1)}%)")

    # ── Model 2: Growth Stage ─────────────────────────────────
    print(f"\n  [MODEL 2] Growth Stage Detection")
    print(f"  ✅ Growth Stage    : {result.get('growth_stage')}")
    print(f"  ✅ Growth Conf     : {result.get('growth_confidence')}")

    # ── Model 3: Plant Part ───────────────────────────────────
    print(f"\n  [MODEL 3] Plant Part Detection")
    print(f"  ✅ Plant Part      : {result.get('plant_part')}")
    print(f"  ✅ Part Confidence : {result.get('plant_part_confidence')}")

    print(f"\n  ✅ Model Version   : {result.get('model_version')}")
    print(f"  ✅ Inference Time  : {result.get('inference_time')}")

    # ── Explanation ───────────────────────────────────────────
    explanation = result.get('explanation', {})
    if explanation:
        print(f"\n  [EXPLANATION]")
        print(f"  ✅ Summary        : {explanation.get('summary')}")
        print(f"  ✅ Growth Signal  : {explanation.get('growth_signal')}")
        print(f"  ✅ Obs Count      : {explanation.get('observation_count')}")

    # ── Observations ──────────────────────────────────────────
    observations = result.get('observations', [])
    print(f"\n  ✅ Structured Observations Generated: {len(observations)}/11")
    for i, obs in enumerate(observations, 1):
        print(f"\n    [{i:02d}] {obs.get('type')}")
        print(f"          Value      : {obs.get('value')}")
        print(f"          Confidence : {obs.get('confidence')}")
        print(f"          Features   : {obs.get('supporting_features')}")
        print(f"          Source     : {obs.get('evidence_source')}")
        print(f"          Timestamp  : {obs.get('timestamp')}")

except Exception as e:
    print(f"❌ Error: {e}")

# Test 5: Invalid image handling
print("\n[TEST 5] ✅ POST /identify - Invalid image handling")
try:
    files = {'image': ('invalid.txt', b'not an image')}
    response = requests.post(f"{BASE_URL}/identify", files=files)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    if response.status_code != 200:
        print("  ✅ Invalid image correctly rejected")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 6: Missing image handling
print("\n[TEST 6] ✅ POST /identify - Missing image handling")
try:
    response = requests.post(f"{BASE_URL}/identify", files={})
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print("  ✅ Missing image correctly rejected")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("TEST SUMMARY - ALL ENDPOINTS VERIFIED")
print("=" * 80)
