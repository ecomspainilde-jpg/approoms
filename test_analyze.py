import os
import vertexai
from dotenv import load_dotenv

load_dotenv()
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0426824151")
REGION = "us-central1"
vertexai.init(project=PROJECT_ID, location=REGION)

from vertexai.generative_models import GenerativeModel

try:
    model = GenerativeModel("gemini-1.5-pro-002")
    response = model.generate_content("Hello! Are you working via Vertex AI in us-central1?")
    print("Success:", response.text)
except Exception as e:
    print("Error:", e)
