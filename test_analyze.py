import os
import vertexai
from dotenv import load_dotenv

load_dotenv()
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0426824151")
REGION = "us-central1"
vertexai.init(project=PROJECT_ID, location=REGION)

from vertexai.generative_models import GenerativeModel

models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]

for model_name in models:
    try:
        print(f"Testing {model_name}...")
        model = GenerativeModel(model_name)
        response = model.generate_content("Hello! Are you working via Vertex AI in us-central1?")
        print(f"Success with {model_name}:", response.text)
        break
    except Exception as e:
        print(f"Error with {model_name}:", str(e)[:200])
