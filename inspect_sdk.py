import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
import inspect

try:
    model = ImageGenerationModel.from_pretrained("imagen-3.0-capability-001")
    print("Methods of ImageGenerationModel:")
    
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
