import os
import base64
import uuid
import datetime
import json
from datetime import timezone
from flask import Flask, request, jsonify, send_from_directory
import vertexai
from vertexai.preview import vision_models
from vertexai.preview.vision_models import ImageGenerationModel, Image as VisionImage, ReferenceImage
from vertexai.generative_models import GenerativeModel, Part, Image as VertexImage
import firebase_admin
from firebase_admin import credentials, auth, firestore, storage

app = Flask(__name__, static_folder="public", static_url_path="")

# Initialize Vertex AI
project_id = os.environ.get("GCP_PROJECT_ID", "gen-lang-client-0426824151")
location = os.environ.get("GCP_LOCATION", "us-central1")
storage_bucket = os.environ.get("FIREBASE_STORAGE_BUCKET", f"{project_id}.firebasestorage.app")

try:
    vertexai.init(project=project_id, location=location)
except Exception as e:
    print(f"Warning: Could not initialize Vertex AI for project {project_id} in {location}:", e)

# Initialize Firebase Admin
try:
    if not firebase_admin._apps:
        # Default credentials should work in Cloud Run
        firebase_admin.initialize_app(options={
            'storage_bucket': storage_bucket
        })
    db = firestore.client()
    bucket = storage.bucket()
except Exception as e:
    print("Error initializing Firebase Admin:", e)
    db = None
    bucket = None


STYLE_DESCRIPTIONS = {
    "moderno": "Modern style: sleek contemporary furniture, neutral palette (white, gray, beige, black accent), clean lines, minimal clutter, hidden storage solutions, Statement lighting pieces, open space, large artwork, geometric patterns, glass and metal accents, sophisticated and timeless atmosphere.",
    "nordico": "Scandinavian style: light oak furniture, white/cream/warm gray palette, cozy textiles (wool, linen, sheepskin), hygge lighting (warm pendant lamps, candles, fairy lights), minimal clutter, natural plants in simple pots, functional storage solutions, clean lines, relaxed yet sophisticated hygge atmosphere.",
    "industrial": "Industrial style: exposed brick walls, raw concrete surfaces, metal accents (black iron, copper, brass), Edison bulb lighting, dark palette (charcoal, rust, burgundy, steel gray), open-plan warehouse aesthetic, vintage leather furniture, reclaimed wood tables, Statement lighting fixtures, edgy yet warm atmosphere.",
    "minimalista": "Monochromatic palette (white, black, gray, beige), essential furniture only, zero clutter, clean surfaces, emphasis on negative space, quality over quantity, subtle texture variations, hidden storage, simple geometric forms, serene and peaceful atmosphere with maximum functionality.",
    "rustico": "Rustic farmhouse style: warm earthy tones (terracotta, olive, cream, brown), natural stone or reclaimed wood textures, handcrafted furniture with imperfect finishes, wrought iron details, cozy textiles (tartan, burlap, linen), vintage accessories, warm ambient lighting, cottage or farmhouse charm with authentic character.",
    "bohemio": "Bohemian eclectic style: layered textiles (macramé, rugs, pillows, curtains), jewel tones mixed with warm neutrals (emerald, burgundy, navy, gold), vintage and repurposed furniture, macramé wall hangings, abundant plants, global decorative accessories, layered rugs, free-spirited and artistic atmosphere with rich textures.",
}


def analyze_room_image(images_base64: list) -> dict:
    """Use Gemini 2.0 Flash Lite to analyze one or more uploaded room images and return structured JSON."""
    try:
        model = GenerativeModel("gemini-2.0-flash-lite")
        parts = []
        for img_b64 in images_base64:
            image_bytes = base64.b64decode(img_b64)
            vertex_image = VertexImage.from_bytes(image_bytes)
            parts.append(Part.from_image(vertex_image))

        analysis_prompt = """Identify all architectural and structural details in these room images for high-fidelity interior design rendering.
Return ONLY a valid JSON object with the following structure:
{
  "architecture_en": "Precise description of walls, windows (position/size), doors, ceiling type, and built-in elements.",
  "lighting_en": "Light sources, direction, and ambient quality.",
  "materials_en": "Existing textures (wood, concrete, paint, tile).",
  "layout_en": "Spatial arrangement and depth context.",
  "furniture_en": "Summary of existing furniture and their placement.",
  "room_type": "The type of room (e.g., bedroom, living room, office, etc.).",
  "approx_size": "Estimated size/dimensions description (e.g., small, spacious, 15m2).",
  "detailed_description_es": "Descripción profesional y detallada en español para el cliente.",
  "imagen_prompt_seed_en": "A comma-separated list of architectural keywords to preserve the room's geometry."
}
Be extremely accurate with window and door placements. If multiple images are provided, synthesize them into one coherent spatial description."""

        parts.append(Part.from_text(analysis_prompt))
        response = model.generate_content(parts)
        
        # Clean response text in case of markdown formatting
        resp_text = response.text.strip()
        if resp_text.startswith("```json"):
            resp_text = resp_text[7:]
        if resp_text.endswith("```"):
            resp_text = resp_text[:-3]
        resp_text = resp_text.strip()
        
        analysis_data = json.loads(resp_text)
        return {"success": True, "data": analysis_data}
    except Exception as e:
        print("Error analyzing image:", e)
        return {"success": False, "error": str(e)}


def generate_room_render(prompt: str, room_data: dict = None, style: str = "moderno", base_image_b64: str = None) -> dict:
    """Generate a room render with structural preservation. 
    Uses Imagen 4.0 Fast for text-to-image, and Imagen 3.0 for image-to-image (editing).
    """
    try:
        # Model Selection: Imagen 4.0 Fast doesn't support edit_image (inpainting/structural)
        if base_image_b64:
            model_name = "imagen-3.0-capability-001"
        else:
            model_name = "imagen-4.0-fast-generate-001"
            
        model = ImageGenerationModel.from_pretrained(model_name)

        style_desc = STYLE_DESCRIPTIONS.get(style.lower(), STYLE_DESCRIPTIONS["moderno"])

        if room_data:
            # Construct a highly structured English prompt
            arch_seed = room_data.get("imagen_prompt_seed_en", "")
            arch_details = room_data.get("architecture_en", "")
            
            full_prompt = (
                f"Professional interior design render in {style} style. "
                f"**ARCHITECTURAL PRESERVATION [MANDATORY]**: {arch_details}. {arch_seed}. "
                f"Maintain EXACT layout of ALL windows, doors, and walls. "
                f"**INTERIOR DESIGN TRANSFORMATION**: Apply {style} style characteristics: {style_desc}. "
                f"**CLIENT BRIEF**: {prompt}. "
                f"Ultra-high resolution, 8K, photorealistic, cinematic lighting, interior design magazine photography style, crisp textures."
            )
        else:
            full_prompt = (
                f"Professional interior design render, {style} style. "
                f"Style: {style_desc}. "
                f"Design brief: {prompt}. "
                f"High resolution, photorealistic, interior design photography."
            )

        generate_kwargs = {
            "prompt": full_prompt,
            "number_of_images": 1,
            "language": "en",
        }

        if base_image_b64:
            # Use image-to-image (supported by Imagen 3.0)
            base_image = VisionImage(image_bytes=base64.b64decode(base_image_b64))
            
            # Using generate_images with ReferenceImage for structural preservation
            # This is the standard way to do mask-free structural editing in Imagen 3
            images = model.generate_images(
                **generate_kwargs,
                reference_images=[
                    ReferenceImage(image=base_image, reference_id=1, reference_type="structural")
                ]
            )
        else:
            # Standard Text-to-Image (Imagen 4.0 Fast)
            images = model.generate_images(**generate_kwargs)

        if not images:
            raise Exception("No images generated")

        b64_image = base64.b64encode(images[0]._image_bytes).decode("utf-8")
        return {
            "success": True,
            "image_base64": b64_image,
            "full_prompt": full_prompt,
            "style_description": style_desc,
        }
    except Exception as e:
        print("Error generating image:", e)
        return {"success": False, "error": str(e)}


# ── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("public", "index.html")


@app.route("/<path:path>")
def serve_static(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory("public", path)
    return send_from_directory("public", "index.html")




@app.route("/api/analyze-image", methods=["POST"])
def api_analyze_image():
    """Analyze uploaded room image(s) using Gemini Vision and return structured JSON."""
    data = request.json
    # Handle both single image (legacy) and multiple images
    image_b64 = data.get("image_base64")
    images_b64 = data.get("images_base64", [])
    
    if image_b64:
        images_b64 = [image_b64]
        
    if not images_b64:
        return jsonify({"error": "No images provided"}), 400

    result = analyze_room_image(images_b64)
    if result.get("success"):
        return jsonify(result["data"])
    else:
        return jsonify({"error": result.get("error", "Analysis failed")}), 500


def verify_token():
    """Verify Firebase ID Token from Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split("Bearer ")[1]
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        print("Token verification failed:", e)
        return None


@app.route("/api/generate-image", methods=["POST"])
def api_generate_image():
    """Generate a room render. Accepts prompt, optional room_data and style."""
    user = verify_token()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    prompt = data.get("prompt", "")
    room_data = data.get("room_data", {})
    style = data.get("style", "moderno")
    image_base64 = data.get("image_base64")

    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    result = generate_room_render(prompt, room_data, style, image_base64)
    if result.get("success"):
        image_b64 = result["image_base64"]
        
        # Check Firebase Storage
        if not bucket:
            return jsonify({
                "image_base64": image_b64,
                "warning": "Firebase Storage not initialized. Image not saved.",
                "full_prompt": result["full_prompt"],
                "style_description": result["style_description"],
            })

        try:
            # Save to Firebase Storage (private, not public)
            image_id = str(uuid.uuid4())
            filename = f"renders/{user['uid']}/{image_id}.png"
            blob = bucket.blob(filename)
            image_data = base64.b64decode(image_b64)
            blob.upload_from_string(image_data, content_type="image/png")

            # Save metadata to Firestore
            if not db:
                print("Firestore not initialized")
            else:
                # Extract extra metadata if available
                room_type = room_data.get("room_type", "unknown")
                room_size = room_data.get("approx_size", "unknown")

                render_doc = {
                    "userId": user["uid"],
                    "email": user.get("email", "unknown"),
                    "prompt": prompt,
                    "style": style,
                    "room_type": room_type,
                    "approx_size": room_size,
                    "imageUrl": filename,
                    "inputImageUrl": None, # Will be set if we upload the input image
                    "createdAt": datetime.now(timezone.utc),
                    "roomData": room_data,
                    "fullPrompt": result["full_prompt"],
                    "price": 2.50,
                    "currency": "EUR",
                    "status": "completed"
                }
                
                # If we have the base image, we could theoretically save it too
                # For now, we'll just mark that we processed this render successfully
                doc_ref = db.collection("renders").document(image_id)
                doc_ref.set(render_doc)

                # Record as a formal purchase for direct reporting
                purchase_doc = {
                    "userId": user["uid"],
                    "email": user.get("email", "unknown"),
                    "productId": f"render_{style}",
                    "amount": 2.50,
                    "currency": "EUR",
                    "timestamp": datetime.now(timezone.utc),
                    "renderId": image_id,
                    "method": "simulated_bizum"
                }
                db.collection("purchases").add(purchase_doc)

            return jsonify({
                "image_id": image_id,
                "image_base64": image_b64,
                "full_prompt": result["full_prompt"],
                "style_description": result["style_description"],
            })
        except Exception as e:
            print("Error saving to Firebase:", e)
            return jsonify({
                "image_base64": image_b64,
                "warning": f"Error saving to Firebase: {str(e)}",
                "full_prompt": result["full_prompt"],
                "style_description": result["style_description"],
            })
    else:
        return jsonify({"error": result.get("error", "Unknown error")}), 500


@app.route("/api/my-renders", methods=["GET"])
def get_my_renders():
    """Fetch renders for the authenticated user."""
    user = verify_token()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    if not db:
        return jsonify({"error": "Firestore not initialized"}), 500

    try:
        renders = db.collection("renders").where("userId", "==", user["uid"]).order_by("createdAt", direction=firestore.Query.DESCENDING).stream()
        result = []
        for doc in renders:
            r = doc.to_dict()
            r["id"] = doc.id
            # Convert datetime to string for JSON
            if "createdAt" in r:
                r["createdAt"] = r["createdAt"].isoformat()
            result.append(r)
        return jsonify(result)
    except Exception as e:
        print("Error fetching from Firestore:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/simulate-payment", methods=["POST"])
def api_simulate_payment():
    print("Pre-production payment simulation...")
    return jsonify({"success": True, "message": "Payment successful!"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
