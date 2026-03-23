import google.generativeai as genai
import base64, os
from dotenv import load_dotenv

load_dotenv('c:/imf/habitacion/.env')
key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
print('Key starts with:', key[:12] if key else 'None')
print('Is AQ key (invalid for AI Studio):', key.startswith('AQ.') if key else 'N/A')
genai.configure(api_key=key)

JPEG_1x1 = bytes([255,216,255,224,0,16,74,70,73,70,0,1,1,0,0,1,0,1,0,0,255,219,0,67,0,8,6,6,7,6,5,8,7,7,7,9,9,8,10,12,20,13,12,11,11,12,25,18,19,15,20,29,26,31,30,29,26,28,28,32,36,46,39,32,34,44,35,28,28,40,55,41,44,48,49,52,52,52,31,39,57,61,56,50,60,46,51,52,50,255,192,0,11,8,0,1,0,1,1,1,17,0,255,196,0,31,0,0,1,5,1,1,1,1,1,1,0,0,0,0,0,0,0,0,1,2,3,4,5,6,7,8,9,10,11,255,218,0,8,1,1,0,0,63,0,128,255,217])
img_b64 = base64.b64encode(JPEG_1x1).decode('utf-8')

model = genai.GenerativeModel('gemini-2.0-flash')

# Test format 1: inline_data (TEXT then IMAGE)
print('--- Test 1: text then inline_data ---')
try:
    parts1 = [{'text': 'Describe this image briefly.'}, {'inline_data': {'mime_type': 'image/jpeg', 'data': img_b64}}]
    r = model.generate_content(parts1)
    print('SUCCESS:', r.text[:100])
except Exception as e:
    print('ERROR T1:', str(e)[:200])

# Test format 2: IMAGE then TEXT (opposite order)
print('--- Test 2: inline_data then text ---')
try:
    parts2 = [{'inline_data': {'mime_type': 'image/jpeg', 'data': img_b64}}, {'text': 'Describe this image briefly.'}]
    r = model.generate_content(parts2)
    print('SUCCESS:', r.text[:100])
except Exception as e:
    print('ERROR T2:', str(e)[:200])

# Test format 3: raw string only (no image)
print('--- Test 3: raw string only ---')
try:
    r = model.generate_content('Say hello')
    print('SUCCESS:', r.text[:100])
except Exception as e:
    print('ERROR T3:', str(e)[:200])
