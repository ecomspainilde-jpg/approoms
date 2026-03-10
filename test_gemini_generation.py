import os
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Image as VertexImage
import base64

project_id = "gen-lang-client-0426824151"
location = "us-central1"

vertexai.init(project=project_id, location=location)

def test_generation_with_image():
    # Model gemini-2.0-flash-001
    model = GenerativeModel("gemini-2.0-flash-001")
    
    # Use one of the gallery images as a base
    image_path = r"c:\imf\habitacion\approoms\public\img\gallery_modern.png"
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    vertex_image = VertexImage.from_bytes(image_bytes)
    
    prompt = """Based on the provided image of a modern living room, generate a NEW photorealistic interior design render of this EXACT room but in NORDICO style.
Keep the same architecture (windows, walls, doors). Change the furniture and decor to follow the Nordic style: light oak furniture, white/cream palette, cozy textiles, and warm lighting.
The output MUST be a generated image."""
    
    try:
        print(f"Attempting generation with {model._model_name} and image input...")
        response = model.generate_content([
            Part.from_image(vertex_image),
            Part.from_text(prompt)
        ])
        
        print("Response received.")
        for i, part in enumerate(response.candidates[0].content.parts):
            if part.inline_data:
                mime_type = part.inline_data.mime_type
                if "image" in mime_type:
                    print(f"Success! Found image part with mime_type: {mime_type}")
                    # Save for verification
                    filename = f"generated_test_{i}.png"
                    with open(filename, "wb") as out:
                        out.write(part.inline_data.data)
                    print(f"Saved to {filename}")
                    return True
            if part.file_data:
                print(f"Found file_data part: {part.file_data.file_uri}")
        
        print("No image part found in the response.")
        print("Response text:", response.text)
        return False
    except Exception as e:
        print(f"Error during generation: {e}")
        return False

if __name__ == "__main__":
    test_generation_with_image()
