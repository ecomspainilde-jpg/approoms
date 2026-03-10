import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
import inspect

# Initialize Vertex AI
project_id = "gen-lang-client-0426824151"
location = "us-central1"
vertexai.init(project=project_id, location=location)

try:
    print(f"Inspecting model: imagen-4.0-fast-generate-001")
    model = ImageGenerationModel.from_pretrained("imagen-4.0-fast-generate-001")
    
    # Check generate_images
    sig_gen = inspect.signature(model.generate_images)
    print(f"\ngenerate_images signature: {sig_gen}")
    
    # Check edit_image
    try:
        sig_edit = inspect.signature(model.edit_image)
        print(f"\nedit_image signature: {sig_edit}")
    except AttributeError:
        print("\nedit_image method not found")
        
except Exception as e:
    print(f"Error: {e}")
