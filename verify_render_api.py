import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

def test_health():
    print("Testing /api/health...")
    try:
        r = requests.get("http://127.0.0.1:5000/api/health")
        print(f"Health Status: {r.status_code}")
        print(r.json())
    except Exception as e:
        print(f"Health check failed (is the server running?): {e}")

def test_analysis():
    print("\nTesting /api/analyze-image-sync...")
    # Create a dummy image
    dummy_img = base64.b64encode(b"dummy image data").decode("utf-8")
    payload = {
        "images": [dummy_img],
        "options": {"isInitial": True}
    }
    try:
        # Note: This will likely fail with a 400 or 500 if the image is actually invalid,
        # but it will tell us if the route and model initialization is working.
        r = requests.post("http://127.0.0.1:5000/api/analyze-image-sync", json=payload)
        print(f"Analysis Status: {r.status_code}")
        print(r.text[:500])
    except Exception as e:
        print(f"Analysis call failed: {e}")

if __name__ == "__main__":
    # Normally we'd start the server in a background process, 
    # but for now I'll just verify the code logic via a quick unit test of the function in app.py if possible,
    # or just assume the refactor is correct based on the test_api.py results (which got to the model part).
    
    # Actually, let's just try to import the core functions from app.py and test them directly.
    import sys
    sys.path.append(".")
    try:
        from app import analyze_room_image, generate_room_render
        print("Successfully imported app functions.")
        
        # Test analysis with dummy
        print("\nDirect test of analyze_room_image...")
        # We need a real-ish image for Gemini to not error immediately on 'invalid image'
        # but let's see if it at least triggers the model call.
        res = analyze_room_image([dummy_img])
        print(f"Result: {res}")
        
    except Exception as e:
        print(f"Direct function test failed: {e}")
