import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
import inspect

project_id = "gen-lang-client-0426824151"
location = "us-central1"
vertexai.init(project=project_id, location=location)

try:
    model = ImageGenerationModel.from_pretrained("imagen-3.0-capability-001")
    print("Methods of ImageGenerationModel:")
    
    # Check generate_images
    sig_gen = inspect.signature(model.generate_images)
    print(f"\ngenerate_images signature: {sig_gen}")
    
    # Check what it returns
    import typing
    return_type = typing.get_type_hints(model.generate_images).get('return')
    print(f"Return type of generate_images: {return_type}")
    
    if return_type:
        # Try to see attributes of return type if possible
        print(f"Attributes of {return_type}: {dir(return_type)}")

except Exception as e:
    print(f"Error: {e}")
