import os
import base64
from dotenv import load_dotenv
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel, Image as VisionImage

# Load environment variables
load_dotenv()

# Initialize Vertex AI
project_id = os.environ.get("GCP_PROJECT_ID", "gen-lang-client-0426824151")
location = os.environ.get("GCP_LOCATION", "us-central1")

try:
    vertexai.init(project=project_id, location=location)
    print(f"Vertex AI initialized: {project_id} ({location})")
except Exception as e:
    print(f"Error initializing Vertex AI: {e}")
    exit(1)

def test_generation():
    print("Testing Imagen 3.0 generation...")
    try:
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        
        # Test Prompt
        prompt = "Professional interior design photography, modern style: sleek contemporary furniture, neutral palette, clean lines, photorealistic 8K, architectural digest style."
        
        # Generate image (Text-to-Image fallback test)
        images = model.generate_images(
            prompt=prompt,
            number_of_images=1,
        )
        
        if images:
            # Save locally, do NOT print base64
            with open("test_render_result.png", "wb") as f:
                f.write(images[0]._image_bytes)
            print("SUCCESS: Image generated and saved to 'test_render_result.png'.")
            return True
        else:
            print("ERROR: No images returned from model.")
            return False
            
    except Exception as e:
        # SENSITIVE: Truncate error to avoid massive history if it contains raw bytes
        print(f"Error in generation: {str(e)[:500]}")
        return False

if __name__ == "__main__":
    test_generation()
