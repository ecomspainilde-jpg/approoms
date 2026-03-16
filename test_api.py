import os
import io
import base64
from app import project_id, location
from google import genai as google_genai
from google.genai import types as genai_types
from PIL import Image

# Create a dummy image
img = Image.new('RGB', (256, 256), color = 'red')
buf = io.BytesIO()
img.save(buf, format='JPEG')
img_bytes = buf.getvalue()

try:
    print("Testing Gemini Flash Normal Quality...")
    genai_client = google_genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    response = genai_client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=[
            genai_types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
            genai_types.Part.from_text(text="Redecorate this room"),
        ],
        config=genai_types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
            temperature=0.5,
            candidate_count=1,
        ),
    )
    print("Gemini Normal OK")
except Exception as e:
    print("Gemini Normal ERROR:")
    import traceback
    traceback.print_exc()

try:
    print("\nTesting Imagen Edit with ImageGenerationModel...")
    from vertexai.preview.vision_models import ImageGenerationModel
    from vertexai.vision_models import Image as VisionImage
    edit_model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
    src_image = VisionImage(image_bytes=img_bytes)
    result = edit_model.edit_image(
        prompt="Redecorate this room",
        base_image=src_image,
        edit_mode="inpainting-insert",
        number_of_images=1,
    )
    print("Imagen Edit OK")
except Exception as e:
    print("Imagen Edit ERROR:")
    import traceback
    traceback.print_exc()
