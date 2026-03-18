import os
import base64
import uuid
import datetime
import json
from datetime import timezone
from typing import List, Dict, Any, Optional, Union
from flask import Flask, request, jsonify, send_from_directory  # type: ignore
from dotenv import load_dotenv  # type: ignore

def safe_truncate(text: Any, limit: int = 500) -> str:
    """Safely truncate text to avoid massive log payloads."""
    if text is None:
        return ""
    text_val = f"{text}"
    if len(text_val) <= limit:
        return text_val
    return text_val[0:limit] + "... [TRUNCATED]"  # type: ignore

# Load environment variables from .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"Loaded .env from {env_path}")
else:
    print(f"Warning: .env file not found at {env_path}")

import vertexai  # type: ignore
from vertexai.preview import vision_models  # type: ignore
from vertexai.preview.vision_models import (  # type: ignore
    ImageGenerationModel,
    Image as VisionImage,
)
from vertexai.generative_models import GenerativeModel, Part, Image as VertexImage  # type: ignore
import firebase_admin  # type: ignore
from firebase_admin import credentials, auth, firestore, storage  # type: ignore
import stripe  # type: ignore
from fpdf import FPDF # type: ignore

app = Flask(__name__, static_folder="public", static_url_path="")

# Stripe Initialization with explicit check
STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY")
if not STRIPE_KEY or "placeholder" in STRIPE_KEY.lower():
    print("WARNING: STRIPE_SECRET_KEY is missing or invalid in .env")
    stripe.api_key = "invalid_key_placeholder"
else:
    stripe.api_key = STRIPE_KEY
    print(f"Stripe initialized with key: {STRIPE_KEY[:10]}...")

webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_placeholder")

# Initialize Vertex AI
project_id = os.environ.get("GCP_PROJECT_ID", "gen-lang-client-0426824151")
location = os.environ.get("GCP_LOCATION", "us-central1")
storage_bucket = os.environ.get(
    "FIREBASE_STORAGE_BUCKET", f"{project_id}.firebasestorage.app"
)

# ... (GCP config above)

try:
    # Explicitly use us-central1 for better model availability
    vertexai.init(project=project_id, location=location)
    print(f"Vertex AI initialized: {project_id} in {location}")
except Exception as e:
    print(
        f"Warning: Could not initialize Vertex AI for project {project_id} in {location}: {safe_truncate(e, 200)}"
    )

# Initialize Firebase Admin
try:
    if not firebase_admin._apps:
        # Pass project_id explicitly for local development
        firebase_admin.initialize_app(options={
            "projectId": project_id,
            "storageBucket": storage_bucket
        })
        print(f"Firebase Admin initialized: {project_id}")
    db = firestore.client()
    bucket = storage.bucket()
    print(f"Firestore and Storage clients initialized successfully.")
except Exception as e:
    print(f"CRITICAL ERROR initializing Firebase Admin: {safe_truncate(e, 500)}")
    db = None
    bucket = None

@app.route("/api/health")
def health_check():
    """Health check endpoint for diagnostics"""
    status = {
        "status": "online",
        "firebase": db is not None,
        "storage": bucket is not None,
        "stripe": stripe.api_key and "placeholder" not in stripe.api_key.lower(),
        "project_id": project_id,
        "env_loaded": os.path.exists(env_path)
    }
    return jsonify(status)


def get_render_price(quality: str = "normal"):
    """Get the current render price from Firebase based on quality, fallback to default"""
    if not db:
        return 2.50 if quality == "normal" else 5.00
    try:
        doc_id = "render_normal" if quality == "normal" else "render_high"
        doc = db.collection("pricing").document(doc_id).get()
        if doc.exists:
            return doc.to_dict().get("price", 2.50 if quality == "normal" else 5.00)
        
        # Fallback to old 'render' doc if new docs don't exist yet
        old_doc = db.collection("pricing").document("render").get()
        if old_doc.exists:
            return old_doc.to_dict().get("price", 2.50)
            
    except Exception as e:
        print(f"Error fetching {quality} price:", e)
    return 2.50 if quality == "normal" else 5.00


def get_credits_price():
    """Get the current credits price from Firebase, fallback to default"""
    if not db:
        return 10.00
    try:
        doc = db.collection("pricing").document("credits").get()
        if doc.exists:
            return doc.to_dict().get("price", 10.00)
    except Exception as e:
        print("Error fetching credits price:", e)
    return 10.00


STYLE_DESCRIPTIONS = {
    "moderno": "Modern style: sleek contemporary furniture, neutral palette (white, gray, beige, black accent), clean lines, minimal clutter, hidden storage solutions, Statement lighting pieces, open space, large artwork, geometric patterns, glass and metal accents, sophisticated and timeless atmosphere.",
    "nordico": "Scandinavian style: light oak furniture, white/cream/warm gray palette, cozy textiles (wool, linen, sheepskin), hygge lighting (warm pendant lamps, candles, fairy lights), minimal clutter, natural plants in simple pots, functional storage solutions, clean lines, relaxed yet sophisticated hygge atmosphere.",
    "industrial": "Industrial style: exposed brick walls, raw concrete surfaces, metal accents (black iron, copper, brass), Edison bulb lighting, dark palette (charcoal, rust, burgundy, steel gray), open-plan warehouse aesthetic, vintage leather furniture, reclaimed wood tables, Statement lighting fixtures, edgy yet warm atmosphere.",
    "minimalista": "Monochromatic palette (white, black, gray, beige), essential furniture only, zero clutter, clean surfaces, emphasis on negative space, quality over quantity, subtle texture variations, hidden storage, simple geometric forms, serene and peaceful atmosphere with maximum functionality.",
    "rustico": "Rustic farmhouse style: warm earthy tones (terracotta, olive, cream, brown), natural stone or reclaimed wood textures, handcrafted furniture with imperfect finishes, wrought iron details, cozy textiles (tartan, burlap, linen), vintage accessories, warm ambient lighting, cottage or farmhouse charm with authentic character.",
    "bohemio": "Bohemian eclectic style: layered textiles (macramé, rugs, pillows, curtains), jewel tones mixed with warm neutrals (emerald, burgundy, navy, gold), vintage and repurposed furniture, macramé wall hangings, abundant plants, global decorative accessories, layered rugs, free-spirited and artistic atmosphere with rich textures.",
}

def analyze_room_image(images_base64: list) -> dict:
    """RoomChic Engine: 3D Triangulation and Perspective Analysis using Gemini via Vertex AI."""
    # Use verified stable models
    models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
    
    contents = []
    # ... (contents setup remains same)

    contents.append("You are the RoomChic Architectural AI, specialized in 3D space reconstruction from multiple 2D angles.")

    for i, img_b64 in enumerate(images_base64):
        role = "PRIMARY MASTER IMAGE (Perspective Source)" if i == 0 else f"DEPTH REFERENCE {i} (Blind Spots & Context)"
        contents.append(f"ROLE: {role}")
        try:
            image_part = Part.from_data(data=base64.b64decode(img_b64), mime_type="image/jpeg")
            contents.append(image_part)
        except Exception as e:
            print(f"Error decoding image {i}: {safe_truncate(e, 100)}")

    analysis_prompt = """You are the RoomChic Architectural AI. Your PRIMARY task before any analysis is to validate the image quality for AI-assisted interior design rendering.

## STEP 1 — IMAGE VALIDATION (CRITICAL)
Evaluate the MASTER IMAGE (first image) against these criteria for angle-preserving render generation:
- **is_interior_room**: Is this clearly an interior room (not exterior, not abstract)?
- **has_clear_perspective**: Is there a single, stable camera perspective (not a panorama, collage, or multi-angle crop)?
- **is_not_blurry**: Is the image reasonably sharp and in focus (not heavily blurred or pixelated)?
- **sufficient_coverage**: Does the image show enough of the room (floor, walls, at least one architectural anchor visible)?
- **no_heavy_distortion**: Is the image free of extreme fisheye/wide-angle distortions that would cause AI deformation?
- **is_single_room**: Does the image show a single contiguous room (not a collage of different rooms)?

Combine these into:
- **viability_score**: Integer 0-100. 0=completely invalid, 100=perfect for render.
  - 90-100: Perfect — proceed with analysis
  - 70-89: Good — minor issues, warn user but proceed
  - 40-69: Poor — significant issues, warn clearly
  - 0-39: Invalid — BLOCK render, must upload new photo
- **viability_issues_es**: List of issue strings in Spanish (empty if no issues). Be specific and actionable.
- **viability_ok**: boolean — true if score >= 40 and is_interior_room is true.

## STEP 2 — ROOM ANALYSIS (only if viability_ok is true)
Use all provided images to perform PERSPECTIVE TRIANGULATION:
1. Use DEPTH REFERENCES to understand what is behind furniture or in blind spots of the MASTER IMAGE.
2. Identify the 'Untouchable Structure': walls, windows, doors, floor, and ceiling.
3. Estimate real-world dimensions by cross-referencing standard objects across all angles.
4. Detect the current style and potential improvements.

Return ONLY a valid JSON object (all fields required):
{
  "image_validation": {
    "viability_score": 95,
    "viability_ok": true,
    "viability_issues_es": [],
    "is_interior_room": true,
    "has_clear_perspective": true,
    "is_not_blurry": true,
    "sufficient_coverage": true,
    "no_heavy_distortion": true,
    "is_single_room": true
  },
  "room_type": "Confirmed room type. Leave empty string if viability_ok is false.",
  "architecture_en": "List of untouchable architectural anchors (walls, windows, layout). Empty if viability_ok false.",
  "dimensions_est": "Estimated metric size (e.g. 3.5x4.5m). Empty if viability_ok false.",
  "inventory_en": "List 5-8 main objects detected across all photos. Empty if viability_ok false.",
  "blind_spot_data": "Details from context images not visible in master. Empty if viability_ok false.",
  "detailed_description_es": "Descripción profesional. If not viability_ok, explain specifically why the image cannot be used for rendering.",
  "imagen_prompt_seed_en": "STRUCTURAL_LOCK: Specific geometric description to ensure 100% fidelity to MASTER IMAGE perspective. Empty if viability_ok false.",
  "recommendations": {
    "add_es": ["Elemento decorativo 1", "Elemento decorativo 2", "Elemento decorativo 3"],
    "remove_es": ["Objeto a quitar 1", "Objeto a quitar 2"]
  }
}
CRITICAL: Always return valid JSON. Always include image_validation block. If viability_ok is false, fill other fields with empty values or the issue explanation.
Note: Recommendations are tailored to the detected room type and style, focusing on high-impact changes.
"""
    contents.append(analysis_prompt)

    for model_name in models_to_try:
        try:
            model = GenerativeModel(model_name)
            response = model.generate_content(contents)
            resp_text = response.text.strip()
            
            # Clean JSON markdown if present
            if resp_text.startswith("```json"): resp_text = resp_text[7:]
            elif resp_text.startswith("```"): resp_text = resp_text[3:]
            if resp_text.endswith("```"): resp_text = resp_text[:-3]
            
            return {"success": True, "data": json.loads(resp_text.strip())}
        except Exception as e:
            error_msg = safe_truncate(e, 500)
            print(f"Error with model {model_name}: {error_msg}")
            continue
    return {"success": False, "error": "Fallo en motor RoomChic (Gemini Vertex AI)"}

def generate_room_render(
    prompt: str,
    room_data: Optional[Dict[str, Any]] = None,
    style: str = "moderno",
    base_image_b64: Optional[str] = None,
    quality: str = "normal",
) -> Dict[str, Any]:
    """
    RoomChic Render — Photo-faithful room restyling.

    Strategy:
    1. PRIMARY: Gemini 2.0 Flash with native image output — sees the original photo
       and edits ONLY the movable/decorative layer (furniture, lighting, textiles, decor).
    2. FALLBACK: Imagen 3 Edit API (imagegeneration@006) with the original photo as
       reference image, using inpainting-free mode.
    3. LAST RESORT: informative error.

    The structural shell (walls, windows, doors, floor area, ceiling, camera angle)
    is NEVER modified. The client must recognise the same room after the transformation.
    """
    import time
    import io

    style_desc = STYLE_DESCRIPTIONS.get(style.lower(), STYLE_DESCRIPTIONS["moderno"])

    if room_data:
        arch        = room_data.get("architecture_en", "")
        room_type   = room_data.get("room_type", "interior room")
        dims        = room_data.get("dimensions_est", "")
        inventory   = room_data.get("inventory_en", "")
    else:
        arch = room_type = dims = inventory = ""

    is_high_quality = quality == "high"

    # ── Shared edit instruction ───────────────────────────────────────────────
    base_instruction = (
        f"You are an expert interior designer. I am giving you a photograph of a {room_type}. "
        "Your task is to DIGITALLY RESTYLE this exact room. "
        "\n\nSTRICT RULES — NEVER CHANGE THESE:"
        "\n- Walls: keep the EXACT same surfaces, positions and proportions."
        "\n- Windows: keep EXACT size, position, frame and natural light."
        "\n- Doors and door frames: keep EXACT position and size."
        "\n- Ceiling: shape, height and any beams stay identical."
        "\n- Camera angle: the perspective, framing and focal length must be 100% identical to the original photo."
        "\n- Room dimensions and floor plan: do NOT reshape or resize anything structural."
        f"\n- Architectural details to preserve: {arch}"
        "\n\nYOU ARE ALLOWED TO CHANGE ONLY THESE DECORATIVE / MOVABLE ELEMENTS:"
        "\n- Furniture: replace or restyle sofas, chairs, tables, beds, shelves, desks."
        "\n- Lighting fixtures: replace ceiling lights, floor lamps, pendant lights."
        "\n- Textiles: replace rugs, curtains, cushions, bedcovers, throws."
        "\n- Wall art and decorations hanging on the walls."
        "\n- Decorative accessories: plants, vases, books, mirrors, candles."
        "\n- Floor finish tone (same floor area, only visual material/color)."
        f"\n\nSTYLE TO APPLY: {style_desc}"
        f"\n\nCLIENT SPECIFIC REQUESTS: {prompt}"
    )

    if is_high_quality:
        quality_suffix = (
            "\n\nOUTPUT QUALITY: Ultra-high-fidelity 4K interior design photography. "
            "Render every surface material with extreme precision: wood grain, fabric weave, glass reflections, metal sheen. "
            "Perfect global illumination with accurate caustics and soft shadows. "
            "The result must look like a professional architectural photography studio shot. "
            "Maximum detail on all decorative elements — every texture must be crisp and photorealistic."
        )
        gen_temperature = 0.2
    else:
        quality_suffix = (
            "\n\nOUTPUT: Photorealistic interior design photo of the SAME room after restyling. "
            "The client must immediately recognise it as the same physical space."
        )
        gen_temperature = 0.5

    edit_instruction = base_instruction + quality_suffix

    # ── PRIMARY: Gemini 2.0 Flash with image output ───────────────────────────
    if base_image_b64:
        try:
            from google import genai as google_genai  # type: ignore
            from google.genai import types as genai_types  # type: ignore

            genai_client = google_genai.Client(
                vertexai=True,
                project=project_id,
                location=location,
            )

            # Decode base64 → bytes
            img_bytes = base64.b64decode(base_image_b64)

            response = genai_client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[
                    genai_types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                    genai_types.Part.from_text(text=edit_instruction),
                ],
                config=genai_types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                    temperature=gen_temperature,
                ),
            )
            # Extract image from response — pick candidate with most detail
            best_b64 = None
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                        best_b64 = base64.b64encode(part.inline_data.data).decode("utf-8")
                        break  # take first valid candidate (Gemini ranks them)
                if best_b64:
                    break
            if best_b64:
                return {
                    "success": True,
                    "image_base64": best_b64,
                    "engine": f"gemini-2.0-flash-exp-{'hq' if is_high_quality else 'normal'}",
                    "style_description": style_desc,
                    "full_prompt": edit_instruction,
                    "quality": quality,
                }
            print("Gemini image output: no image part returned, falling back.")
        except Exception as gemini_err:
            print(f"Gemini image edit error: {safe_truncate(gemini_err, 400)}")

    # ── FALLBACK: Imagen Edit API with source image ───────────────────────────
    if base_image_b64:
        try:
            from vertexai.preview.vision_models import ImageGenerationModel  # type: ignore
            from vertexai.vision_models import Image as VisionImage  # type: ignore

            edit_model = ImageGenerationModel.from_pretrained("imagegeneration@006")
            src_image  = VisionImage(image_bytes=base64.b64decode(base_image_b64))

            imagen_prompt = (
                f"Interior design restyling. Apply {style_desc} style. "
                "ONLY change furniture, lighting, textiles and decorative accessories. "
                "Keep all walls, windows, doors, ceiling and camera angle IDENTICAL to the source image. "
                f"Client request: {prompt}"
            )

            for attempt in range(3):
                try:
                    result = edit_model.edit_image(
                        prompt=imagen_prompt,
                        base_image=src_image,
                        edit_mode="inpainting-insert",
                        number_of_images=1,
                    )
                    if result and result.images:
                        result_b64 = base64.b64encode(result.images[0]._image_bytes).decode("utf-8")
                        return {
                            "success": True,
                            "image_base64": result_b64,
                            "engine": "imagen-edit-inpainting",
                            "style_description": style_desc,
                            "full_prompt": imagen_prompt,
                        }
                except Exception as edit_err:
                    print(f"Imagen Edit attempt {attempt+1}: {safe_truncate(edit_err, 300)}")
                    if attempt < 2:
                        time.sleep(2 ** attempt)
        except ImportError:
            print("ImageEditingModel not available in this SDK version.")
        except Exception as fallback_err:
            print(f"Imagen Edit fallback error: {safe_truncate(fallback_err, 400)}")

    # ── LAST RESORT: text-only Imagen (signals error clearly) ─────────────────
    return {
        "success": False,
        "error": (
            "No se pudo aplicar el restyling manteniendo la habitación original. "
            "Asegúrate de que la imagen original fue enviada correctamente."
        ),
    }



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
    """Verify Firebase ID Token."""
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

    if not db:
        return jsonify({"error": "Firestore not initialized"}), 500

    # ── Credit Check ──
    user_ref = db.collection("users").document(user["uid"])
    user_doc = user_ref.get()
    
    if not user_doc.exists:
        # Create user if not exists with 0 credits
        user_ref.set({
            "email": user.get("email"),
            "credits": 0,
            "totalGenerations": 0,
            "createdAt": datetime.datetime.now(timezone.utc)
        })
        return jsonify({"error": "No tienes créditos suficientes.", "needsCredits": True}), 402
    
    user_data = user_doc.to_dict()
    current_credits = user_data.get("credits", 0)
    
    if current_credits < 1:
        return jsonify({"error": "No tienes créditos suficientes.", "needsCredits": True}), 402

    data = request.json
    prompt = data.get("prompt", "")
    room_data = data.get("room_data", {})
    style = data.get("style", "moderno")
    quality = data.get("quality", "normal")
    image_base64 = data.get("image_base64")

    # High quality costs 2 credits, normal costs 1
    credits_needed = 2 if quality == "high" else 1

    if current_credits < credits_needed:
        return jsonify({
            "error": f"Necesitas {credits_needed} crédito{'s' if credits_needed > 1 else ''} para calidad {'alta' if quality == 'high' else 'normal'}. Tienes {current_credits}.",
            "needsCredits": True,
            "creditsNeeded": credits_needed,
            "creditsAvailable": current_credits,
        }), 402

    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    result = generate_room_render(prompt, room_data, style, image_base64, quality)
    if result.get("success"):
        # ── Deduct Credits (amount depends on quality) ──
        user_ref.update({
            "credits": firestore.Increment(-credits_needed),
            "totalGenerations": firestore.Increment(1)
        })

        image_b64 = result["image_base64"]

        # Generate a local image_id regardless of storage availability
        image_id = str(uuid.uuid4())

        # Check Firebase Storage
        if not bucket:
            return jsonify(
                {
                    "image_id": image_id,
                    "image_base64": image_b64,
                    "warning": "Firebase Storage not initialized. Image not saved.",
                    "full_prompt": result["full_prompt"],
                    "style_description": result["style_description"],
                }
            )

        try:
            # Save Input Image to Firebase Storage if provided
            input_image_filename = None
            if image_base64:
                input_image_id = f"{str(uuid.uuid4())}_input"
                input_image_filename = f"uploads/{user['uid']}/{input_image_id}.png"
                input_blob = bucket.blob(input_image_filename)
                input_data = base64.b64decode(image_base64)
                input_blob.upload_from_string(input_data, content_type="image/png")

            # Save Generated Render to Firebase Storage (image_id already set above)
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
                    "quality": quality,
                    "room_type": room_type,
                    "approx_size": room_size,
                    "imageUrl": filename,
                    "inputImageUrl": input_image_filename,
                    "createdAt": datetime.datetime.now(timezone.utc),
                    "roomData": room_data,
                    "fullPrompt": result["full_prompt"],
                    "price": get_render_price(quality),
                    "currency": "EUR",
                    "status": "completed",
                }

                # If we have the base image, we could theoretically save it too
                # For now, we'll just mark that we processed this render successfully
                doc_ref = db.collection("renders").document(image_id)
                doc_ref.set(render_doc)

                # Record as a formal purchase for direct reporting
                purchase_doc = {
                    "userId": user["uid"],
                    "email": user.get("email", "unknown"),
                    "productId": f"render_{style}_{quality}",
                    "amount": get_render_price(quality),
                    "currency": "EUR",
                    "timestamp": datetime.datetime.now(timezone.utc),
                    "renderId": image_id,
                    "method": "simulated_bizum",
                }
                db.collection("purchases").add(purchase_doc)

            return jsonify(
                {
                    "image_id": image_id,
                    "image_base64": image_b64,
                    "full_prompt": result["full_prompt"],
                    "style_description": result["style_description"],
                }
            )
        except Exception as e:
            print("Error saving to Firebase:", e)
            return jsonify(
                {
                    "image_id": image_id,
                    "image_base64": image_b64,
                    "warning": f"Error saving to Firebase: {str(e)}",
                    "full_prompt": result["full_prompt"],
                    "style_description": result["style_description"],
                }
            )
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
        renders = (
            db.collection("renders")
            .where("userId", "==", user["uid"])
            .order_by("createdAt", direction=firestore.Query.DESCENDING)
            .stream()
        )
        result = []
        for doc in renders:
            r = doc.to_dict()
            r["id"] = doc.id
            # Convert datetime to string for JSON
            if "createdAt" in r and r["createdAt"]:
                r["createdAt"] = r["createdAt"].isoformat()
            
            # Proxy URLs
            if r.get("imageUrl"):
                r["imageUrl"] = f"/api/storage/{r['imageUrl']}"
            if r.get("inputImageUrl"):
                r["inputImageUrl"] = f"/api/storage/{r['inputImageUrl']}"
                
            result.append(r)
        return jsonify(result)
    except Exception as e:
        print("Error fetching from Firestore:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/storage/<path:path>")
def serve_firebase_storage(path):
    """Proxy route to serve files from Firebase Storage."""
    if not bucket:
        return jsonify({"error": "Storage not initialized"}), 500
    
    try:
        blob = bucket.blob(path)
        if not blob.exists():
            return jsonify({"error": "File not found"}), 404
        
        # Download as bytes
        data = blob.download_as_bytes()
        
        # Content type mapping
        content_type = "image/png"
        if path.endswith(".jpg") or path.endswith(".jpeg"):
            content_type = "image/jpeg"
        elif path.endswith(".pdf"):
            content_type = "application/pdf"
            
        from flask import Response
        return Response(data, mimetype=content_type)
    except Exception as e:
        print(f"Error serving storage path {path}:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/simulate-payment", methods=["POST"])
def api_simulate_payment():
    print("Pre-production payment simulation...")
    return jsonify({"success": True, "message": "Payment successful!"})


@app.route("/api/checkout", methods=["POST"])
def api_checkout():
    user = verify_token()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    if not db:
        return jsonify({"error": "Firestore not initialized"}), 500

    data = request.json
    package_id = data.get("packageId")
    if not package_id:
        return jsonify({"error": "Missing packageId"}), 400

    try:
        # Hardcoded fallback packages (in case Firestore packages collection is empty)
        FALLBACK_PACKAGES = {
            'package_5':  {'name': 'Inicial',      'price': 500,  'currency': 'eur', 'creditsAmount': 5,  'isActive': True},
            'package_10': {'name': 'Estándar',     'price': 1000, 'currency': 'eur', 'creditsAmount': 12, 'isActive': True},
            'package_15': {'name': 'Profesional',  'price': 1500, 'currency': 'eur', 'creditsAmount': 20, 'isActive': True},
            'package_25': {'name': 'Premium',      'price': 2500, 'currency': 'eur', 'creditsAmount': 40, 'isActive': True},
        }

        # Check package price in Firestore, fall back to hardcoded if not found
        pkg_data = None
        if db:
            pkg_doc = db.collection("packages").document(package_id).get()
            if pkg_doc.exists:
                pkg_data = pkg_doc.to_dict()

        if not pkg_data:
            # Try hardcoded fallback
            pkg_data = FALLBACK_PACKAGES.get(package_id)
            if not pkg_data:
                return jsonify({"error": "Package not found"}), 404
            print(f"Using hardcoded fallback for package: {package_id}")

        if not pkg_data.get("isActive", True):
            return jsonify({"error": "Package is not active"}), 400

        price = pkg_data.get("price", 0)  # in cents
        currency = pkg_data.get("currency", "eur")
        name = pkg_data.get("name", "Credits Package")
        credits_amount = pkg_data.get("creditsAmount", 0)

        line_item = {}
        stripe_price_id = pkg_data.get("stripePriceId")
        
        if stripe_price_id:
            line_item = {
                'price': stripe_price_id,
                'quantity': 1,
            }
        else:
            line_item = {
                'price_data': {
                    'currency': currency,
                    'product_data': {
                        'name': name,
                    },
                    'unit_amount': price,
                },
                'quantity': 1,
            }

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[line_item],
            mode='payment',
            success_url=request.host_url + '05-gracias.html?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'modal-compra.html?error=cancelled',
            client_reference_id=user['uid'],
            metadata={
                'userId': user['uid'],
                'packageId': package_id,
                'creditsAmount': str(credits_amount)
            }
        )

        return jsonify({'url': session.url})
    except Exception as e:
        print("Error creating checkout session:", e)
        return jsonify({"error": str(e)}), 500


def add_credits_to_user(user_id, credits_amount, amount_paid):
    """Atomically add credits to a user using a Firestore transaction."""
    user_ref = db.collection("users").document(user_id)

    @firestore.transactional
    def _txn(transaction):
        snapshot = user_ref.get(transaction=transaction)
        if snapshot.exists:
            current = snapshot.to_dict()
            new_credits = current.get("credits", 0) + credits_amount
            new_purchases = current.to_dict().get("totalPurchases", 0) + amount_paid if hasattr(snapshot, 'to_dict') else amount_paid
            transaction.update(user_ref, {
                "credits": new_credits,
                "totalPurchases": firestore.Increment(amount_paid)
            })
        else:
            transaction.set(user_ref, {
                "credits": credits_amount,
                "totalPurchases": amount_paid,
                "totalGenerations": 0
            })

    try:
        _txn(db.transaction())
    except Exception:
        # Fallback: non-transactional update
        snap = user_ref.get()
        if snap.exists:
            user_ref.update({
                "credits": firestore.Increment(credits_amount),
                "totalPurchases": firestore.Increment(amount_paid)
            })
        else:
            user_ref.set({
                "credits": credits_amount,
                "totalPurchases": amount_paid,
                "totalGenerations": 0
            })


@app.route("/api/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400

    if event['type'] == 'checkout.session.completed':
        session_obj = event['data']['object']
        
        user_id = session_obj.get('metadata', {}).get('userId') or session_obj.get('client_reference_id')
        package_id = session_obj.get('metadata', {}).get('packageId')
        credits_amount = int(session_obj.get('metadata', {}).get('creditsAmount', 0))
        amount_paid = session_obj.get('amount_total', 0)
        session_id = session_obj.get('id', '')
        
        print(f"Webhook: payment completed user={user_id} credits={credits_amount} amount={amount_paid}")
        
        if db and user_id and credits_amount > 0:
            # Idempotency: only process once
            txn_ref = db.collection("transactions").document(session_id)
            if txn_ref.get().exists:
                print(f"Webhook: session {session_id} already processed, skipping.")
                return jsonify({'status': 'already_processed'})

            txn_ref.set({
                "userId": user_id,
                "packageId": package_id,
                "amountPaid": amount_paid,
                "creditsAmount": credits_amount,
                "status": "completed",
                "createdAt": datetime.datetime.now(timezone.utc),
            })
            add_credits_to_user(user_id, credits_amount, amount_paid)
            print(f"Webhook: {credits_amount} credits added to user {user_id}")

    return jsonify({'status': 'success'})

# ============ ADMIN API ENDPOINTS ============


def verify_admin():
    """Verify if the user is an admin."""
    user = verify_token()
    if not user:
        return None
    # Check custom claims for admin role
    try:
        user_record = auth.get_user(user["uid"])
        claims = user_record.custom_claims
        if claims and claims.get("admin") == True:
            return user
    except Exception as e:
        print("Error checking admin claims:", e)
    return None


@app.route("/api/admin/users", methods=["GET"])
def admin_get_users():
    """Get all users (admin only)."""
    admin = verify_admin()
    if not admin:
        return jsonify({"error": "Unauthorized - Admin access required"}), 403

    if not db:
        return jsonify({"error": "Firestore not initialized"}), 500

    try:
        users = []
        # Get all user documents from users collection
        docs = db.collection("users").stream()
        for doc in docs:
            u = doc.to_dict()
            u["id"] = doc.id
            users.append(u)
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/users/<uid>", methods=["PATCH"])
def admin_update_user(uid):
    """Update user data (admin only)."""
    admin = verify_admin()
    if not admin:
        return jsonify({"error": "Unauthorized - Admin access required"}), 403

    if not db:
        return jsonify({"error": "Firestore not initialized"}), 500

    try:
        data = request.json
        # Only allow updating specific fields for safety
        allowed_fields = ["credits", "isAdmin", "displayName"]
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400

        db.collection("users").document(uid).update(update_data)
        
        return jsonify({"success": True, "message": f"User {uid} updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/renders", methods=["GET"])
def admin_get_renders():
    """Get all renders (admin only)."""
    admin = verify_admin()
    if not admin:
        return jsonify({"error": "Unauthorized - Admin access required"}), 403

    if not db:
        return jsonify({"error": "Firestore not initialized"}), 500

    try:
        limit = request.args.get("limit", 100, type=int)
        renders = []
        docs = (
            db.collection("renders")
            .order_by("createdAt", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        for doc in docs:
            r = doc.to_dict()
            r["id"] = doc.id
            if "createdAt" in r and r["createdAt"]:
                r["createdAt"] = r["createdAt"].isoformat()
            
            # Proxy URLs
            if r.get("imageUrl"):
                r["imageUrl"] = f"/api/storage/{r['imageUrl']}"
            if r.get("inputImageUrl"):
                r["inputImageUrl"] = f"/api/storage/{r['inputImageUrl']}"
                
            renders.append(r)
        return jsonify(renders)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/stats", methods=["GET"])
def admin_get_stats():
    """Get platform statistics (admin only)."""
    admin = verify_admin()
    if not admin:
        return jsonify({"error": "Unauthorized - Admin access required"}), 403

    if not db:
        return jsonify({"error": "Firestore not initialized"}), 500

    try:
        # Get counts
        users_count = sum(1 for _ in db.collection("users").stream())
        renders_count = sum(1 for _ in db.collection("renders").stream())

        # Calculate total revenue and conversion metrics
        total_revenue = 0
        purchasing_users = set()
        
        for doc in db.collection("purchases").stream():
            p = doc.to_dict()
            amount = p.get("amount", 0)
            user_id = p.get("userId")
            if user_id:
                purchasing_users.add(user_id)
            
            # Normalization: Stripe (cents) vs manual (EUR)
            if amount > 50:
                total_revenue += amount / 100
            else:
                total_revenue += amount

        conversion_rate = 0
        if users_count > 0:
            conversion_rate = (len(purchasing_users) / users_count) * 100

        return jsonify(
            {
                "totalUsers": users_count,
                "totalRenders": renders_count,
                "totalRevenue": float("{:.2f}".format(total_revenue)),
                "conversionRate": float("{:.1f}".format(conversion_rate)),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/pricing", methods=["GET"])
def admin_get_pricing():
    """Get current pricing (public endpoint)."""
    if not db:
        return jsonify({"error": "Firestore not initialized"}), 500

    try:
        pricing = {}
        # Fetch render prices
        render_docs = db.collection("pricing").stream()
        for doc in render_docs:
            pricing[doc.id] = doc.to_dict()

        # Fetch credit packages
        packages = []
        pkg_docs = db.collection("packages").stream()
        for doc in pkg_docs:
            p = doc.to_dict()
            p["id"] = doc.id
            packages.append(p)
        
        pricing["packages"] = packages

        # Return defaults if not set
        if "render_normal" not in pricing:
            pricing["render_normal"] = {"price": 2.50}
        if "render_high" not in pricing:
            pricing["render_high"] = {"price": 5.00}

        return jsonify(pricing)
    except Exception as e:
        print("Error in admin_get_pricing:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/pricing", methods=["POST"])
def admin_update_pricing():
    """Update pricing (admin only)."""
    admin = verify_admin()
    if not admin:
        return jsonify({"error": "Unauthorized - Admin access required"}), 403

    if not db:
        return jsonify({"error": "Firestore not initialized"}), 500

    try:
        data = request.json
        doc_id = data.get("id")
        new_price = data.get("price")

        if not doc_id or new_price is None:
            return jsonify({"error": "Missing id or price"}), 400

        # Get old price for history
        old_price = None
        old_doc = db.collection("pricing").document(doc_id).get()
        if old_doc.exists:
            old_price = old_doc.to_dict().get("price")

        # Update price
        db.collection("pricing").document(doc_id).set(
            {
                "price": float(new_price),
                "updatedAt": datetime.datetime.now(timezone.utc),
                "updatedBy": admin["uid"],
            }
        )

        # Record price history
        db.collection("priceHistory").add(
            {
                "pricingId": doc_id,
                "oldPrice": old_price,
                "newPrice": float(new_price),
                "changedAt": datetime.datetime.now(timezone.utc),
                "changedBy": admin["uid"],
                "type": "render"
            }
        )

        return jsonify({"success": True, "message": f"Price updated to {new_price}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/package", methods=["POST"])
def admin_update_package():
    """Update a credit package (admin only)."""
    admin = verify_admin()
    if not admin:
        return jsonify({"error": "Unauthorized - Admin access required"}), 403

    if not db:
        return jsonify({"error": "Firestore not initialized"}), 500

    try:
        data = request.json
        pkg_id = data.get("id")
        name = data.get("name")
        price = data.get("price")
        credits_amount = data.get("creditsAmount")
        stripe_price_id = data.get("stripePriceId")
        is_active = data.get("isActive", True)

        if not pkg_id:
            return jsonify({"error": "Missing package id"}), 400

        pkg_ref = db.collection("packages").document(pkg_id)
        old_pkg = pkg_ref.get()
        old_data = old_pkg.to_dict() if old_pkg.exists else {}

        update_data = {
            "updatedAt": datetime.datetime.now(timezone.utc),
            "updatedBy": admin["uid"]
        }
        if name: update_data["name"] = name
        if price is not None: update_data["price"] = int(price)
        if credits_amount is not None: update_data["creditsAmount"] = int(credits_amount)
        if stripe_price_id: update_data["stripePriceId"] = stripe_price_id
        update_data["isActive"] = is_active

        pkg_ref.update(update_data)

        # Record history
        db.collection("priceHistory").add({
            "packageId": pkg_id,
            "oldData": old_data,
            "newData": update_data,
            "changedAt": datetime.datetime.now(timezone.utc),
            "changedBy": admin["uid"],
            "type": "package"
        })

        return jsonify({"success": True, "message": f"Package {pkg_id} updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/pricing/history", methods=["GET"])
def admin_get_price_history():
    """Get price change history (admin only)."""
    admin = verify_admin()
    if not admin:
        return jsonify({"error": "Unauthorized - Admin access required"}), 403

    if not db:
        return jsonify({"error": "Firestore not initialized"}), 500

    try:
        history = []
        docs = (
            db.collection("priceHistory")
            .order_by("changedAt", direction=firestore.Query.DESCENDING)
            .limit(50)
            .stream()
        )
        for doc in docs:
            h = doc.to_dict()
            h["id"] = doc.id
            if "changedAt" in h and h["changedAt"]:
                h["changedAt"] = h["changedAt"].isoformat()
            history.append(h)
        return jsonify(history)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/generate-pdf", methods=["POST"])
def api_generate_pdf():
    """Generate a PDF report for a render."""
    user = verify_token()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    render_id = data.get("renderId")

    # Try to load render data from Firestore if we have a render_id and db
    render_data = None
    doc_ref = None
    if render_id and db is not None:
        try:
            doc_ref = db.collection("renders").document(render_id)
            doc = doc_ref.get()
            if doc.exists:
                render_data = doc.to_dict()
                if render_data.get("userId") != user["uid"] and not verify_admin():
                    return jsonify({"error": "Access denied"}), 403
        except Exception as e:
            print("Error fetching render from Firestore:", e)

    # Fallback: use inline data passed from the frontend
    if render_data is None:
        inline = data.get("renderData", {})
        if not inline:
            return jsonify({"error": "Missing renderId and no inline renderData provided"}), 400
        render_data = inline
        render_id = render_id or str(uuid.uuid4())

    try:

        # from fpdf import FPDF # Moved to top
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", "B", 24)
        pdf.set_text_color(240, 164, 0) # Primary color
        pdf.cell(0, 20, "Propuesta de Diseño RenderRoom", ln=True, align="C")
        
        pdf.ln(10)
        pdf.set_font("helvetica", "B", 14)
        pdf.set_text_color(0, 0, 0)
        pdf_title = f"{render_data.get('room_type', 'Habitación')} - Estilo {render_data.get('style', 'Moderno').capitalize()}"
        pdf.cell(0, 10, f"Proyecto: {pdf_title}", ln=True)
        
        created_at = render_data.get('createdAt')
        date_str = created_at.strftime('%d/%m/%Y') if hasattr(created_at, 'strftime') else 'Reciente'
        pdf.cell(0, 10, f"Fecha: {date_str}", ln=True)
        
        pdf.ln(10)
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, "Análisis del Espacio:", ln=True)
        pdf.set_font("helvetica", "", 10)
        analysis_text = render_data.get("roomData", {}).get("detailed_description_es", "No disponible")
        pdf.multi_cell(0, 5, analysis_text)
        
        pdf.ln(5)
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, "Recomendaciones de Estilo:", ln=True)
        
        recs = render_data.get("roomData", {}).get("recommendations", {})
        if recs:
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(0, 7, "Elementos sugeridos para añadir:", ln=True)
            pdf.set_font("helvetica", "", 10)
            for item in recs.get("add_es", []):
                pdf.cell(0, 7, f"- {item}", ln=True)
            
            pdf.ln(2)
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(0, 7, "Elementos a retirar o mejorar:", ln=True)
            pdf.set_font("helvetica", "", 10)
            for item in recs.get("remove_es", []):
                pdf.cell(0, 7, f"- {item}", ln=True)
        
        pdf.ln(15)
        pdf.set_font("helvetica", "I", 8)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 10, "Este informe ha sido generado automáticamente por la tecnología RoomChic AI.", align="C")

        # Output to bytes
        pdf_content = pdf.output(dest='S')

        # Try to upload to Firebase Storage, fall back to base64 delivery
        if bucket is not None:
            try:
                pdf_blob_path = f"reports/{user['uid']}/{render_id}.pdf"
                blob = bucket.blob(pdf_blob_path)
                blob.upload_from_string(pdf_content, content_type="application/pdf")
                blob.make_public()
                pdf_url = blob.public_url
                if doc_ref:
                    try:
                        doc_ref.update({"pdfUrl": pdf_url})
                    except Exception:
                        pass
                return jsonify({"success": True, "pdfUrl": pdf_url})
            except Exception as upload_err:
                print("PDF upload failed, delivering as base64:", upload_err)

        # Deliver PDF as base64 when storage is unavailable
        pdf_b64 = base64.b64encode(pdf_content).decode("utf-8")
        return jsonify({"success": True, "pdfBase64": pdf_b64})
        
    except Exception as e:
        print("Error generating PDF:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
