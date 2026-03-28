import os
import base64
import uuid
import datetime
import json
from datetime import timezone
from typing import List, Dict, Any, Optional, Union
from flask import Flask, request, jsonify, send_from_directory  # type: ignore
from dotenv import load_dotenv  # type: ignore
import io
from PIL import Image

def safe_truncate(text: Any, limit: int = 500) -> str:
    """Safely truncate text to avoid massive log payloads."""
    if text is None:
        return ""
    text_val = f"{text}"
    if len(text_val) <= limit:
        return text_val
    return text_val[0:limit] + "... [TRUNCATED]"  # type: ignore

def optimize_image_data(image_base64, max_dim=1600, quality=75):
    """
    Decodes base64 image, resizes if necessary, and compresses as JPEG.
    Returns the optimized binary data and the new content type.
    """
    if not image_base64:
        return b"", "image/jpeg"
    
    # Pre-strip common data URI prefixes if present
    if "," in image_base64:
        image_base64 = image_base64.split(",")[1]
    
    try:
        # Decode base64 to bytes
        img_data = base64.b64decode(image_base64)
        img = Image.open(io.BytesIO(img_data))
        
        # Convert to RGB (removes alpha channel, required for JPEG)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        # Resize if too large
        width, height = img.size
        if width > max_dim or height > max_dim:
            if width > height:
                new_width = max_dim
                new_height = int(max_dim * height / width)
            else:
                new_height = max_dim
                new_width = int(max_dim * width / height)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save to buffer
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        return buffer.getvalue(), "image/jpeg"
    except Exception as e:
        print(f"Error optimizing image: {e}")
        # Fallback to original data if optimization fails
        # Attempt to determine original content type if possible, otherwise default to png
        try:
            # This is a heuristic, not foolproof
            if image_base64.startswith("/9j/"): # JPEG magic number
                return base64.b64decode(image_base64), "image/jpeg"
            elif image_base64.startswith("iVBORw0KGgo"): # PNG magic number
                return base64.b64decode(image_base64), "image/png"
            else:
                return base64.b64decode(image_base64), "application/octet-stream" # Generic fallback
        except Exception:
            return base64.b64decode(image_base64), "application/octet-stream"


# Load environment variables from .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"Loaded .env from {env_path}")
else:
    print(f"Warning: .env file not found at {env_path}")

import google.generativeai as genai
from google.generativeai import types as genai_types
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part, Image as VertexImage
    VERTEXAI_AVAILABLE = True
except ImportError:
    VERTEXAI_AVAILABLE = False
    print("vertexai package not available, Vertex AI fallback disabled.")
import firebase_admin  # type: ignore
from firebase_admin import credentials, auth, firestore, storage  # type: ignore
import stripe  # type: ignore
from fpdf import FPDF # type: ignore

app = Flask(__name__, static_folder="public", static_url_path="")

# Stripe Initialization with explicit check
STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY")
def is_valid_stripe_key(key):
    """Check if a Stripe key is valid (not a placeholder or secret ref)."""
    if not key:
        return False
    invalid_prefixes = ["projects/", "invalid_", "placeholder"]
    return not any(key.lower().startswith(p) or p in key.lower() for p in invalid_prefixes)

if not is_valid_stripe_key(STRIPE_KEY):
    print(f"WARNING: STRIPE_SECRET_KEY is missing or invalid (got: {STRIPE_KEY[:20] if STRIPE_KEY else 'None'}...)")
    stripe.api_key = None
else:
    stripe.api_key = STRIPE_KEY
    stripe.api_version = "2026-02-25.clover"
    print(f"Stripe initialized with key: {STRIPE_KEY[:10]}... and version 2026-02-25.clover")

webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_placeholder")

# Initialize Google Generative AI (AI Studio) - local dev fallback only
GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
if GEMINI_API_KEY:
    # Most keys start with AIza. Only ignore known generic placeholders.
    generic_placeholders = ["API_KEY_HOLDER", "TU_API_KEY", "PLACE_HOLDER", "YOUR_API_KEY"]
    if any(p in GEMINI_API_KEY.upper() for p in generic_placeholders):
        print(f"Skipping placeholder API key: {GEMINI_API_KEY[:4]}...")
        GEMINI_API_KEY = None
    else:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            print(f"GenAI configure success with key: {GEMINI_API_KEY[:8]}...")
        except Exception as e:
            print(f"GenAI configure error: {e}")
            GEMINI_API_KEY = None

# --- 1. Basic configuration ---
project_id = os.environ.get("GCP_PROJECT_ID")
location = os.environ.get("GCP_LOCATION", "us-central1")
storage_bucket = os.environ.get("FIREBASE_STORAGE_BUCKET")
if not storage_bucket and project_id:
    storage_bucket = f"{project_id}.firebasestorage.app"

# --- 2. Initialize Vertex AI PRIMARY hub ---
if VERTEXAI_AVAILABLE:
    try:
        # Use location from env or default to us-central1 (Vertex Gemini hub)
        vertex_project = project_id or None
        vertex_location = location
        vertexai.init(project=vertex_project, location=vertex_location)
        print(f"Vertex AI: Hub initialized in {vertex_location} (project: {vertex_project or 'AUTO-DETECTED'})")
    except Exception as e:
        print(f"Vertex AI: Init skipped ({safe_truncate(e, 100)})")

def get_model_providers(model_name):
    """
    Returns a list of (model_object, provider_name) for a given model.
    Tries AI Studio (studio) first if key is available, then Vertex AI (vertex).
    """
    providers = []
    
    # ── AI Studio (genai) ──
    if GEMINI_API_KEY:
        try:
            # For AI Studio, it's often better to prefix with 'models/' if it doesn't have it
            studio_model_name = model_name if model_name.startswith("models/") else f"models/{model_name}"
            m_studio = genai.GenerativeModel(studio_model_name)
            if m_studio: providers.append((m_studio, "studio"))
        except Exception as e:
            print(f"AI Studio model load error ({model_name}): {e}")

    # ── Vertex AI (vertexai) ──
    if VERTEXAI_AVAILABLE:
        try:
            # For Vertex AI, we use the simple name, typically WITHOUT 'models/' prefix
            vertex_model_name = model_name.replace("models/", "")
            m_vertex = GenerativeModel(vertex_model_name)
            if m_vertex: providers.append((m_vertex, "vertex"))
        except Exception as e:
            print(f"Vertex AI model load error ({model_name}): {e}")

    return providers

# (Removed redundant initialization blocks, moved to top)

# Stripe Webhook Secret check
webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
if not webhook_secret or "holder" in webhook_secret:
    print("WARNING: STRIPE_WEBHOOK_SECRET is missing or contains a placeholder.")
    webhook_secret = None

# Initialize Firebase Admin with dynamic options (filters None values)
try:
    if not firebase_admin._apps:
        fb_options = {}
        if project_id: fb_options["projectId"] = project_id
        if storage_bucket: fb_options["storageBucket"] = storage_bucket
        
        firebase_admin.initialize_app(options=fb_options)
        print(f"Firebase Admin: Connected to {project_id or 'DEFAULT'}")
    
    db = firestore.client()
    # Explicitly check if client is working
    db.collection("health").document("ping").get(timeout=5)
    
    bucket = storage.bucket() if storage_bucket else None
    print(f"Firebase Client: Success (db: {db.project if hasattr(db, 'project') else 'ok'}, bucket: {bucket.name if bucket else 'none'})")
except Exception as e:
    print(f"Firebase initialization CRITICAL: {safe_truncate(e, 500)}")
    db = None
    bucket = None

@app.route("/api/health")
def health_check():
    """Health check endpoint for diagnostics"""
    status = {
        "status": "online",
        "firebase": db is not None,
        "storage": bucket is not None,
        "stripe": stripe.api_key and "placeholder" not in stripe.api_key.lower() if stripe.api_key else False,
        "project_id": project_id,
    }
    return jsonify(status)

@app.errorhandler(Exception)
def handle_unexpected_error(e):
    # Log the full traceback to stdout for Cloud Run logging
    import traceback
    print("UNHANDLED EXCEPTION IN FLASK:")
    traceback.print_exc()
    return jsonify({
        "error": "Internal Server Error",
        "message": safe_truncate(str(e), 300),
        "success": False
    }), 500


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
    """RoomChic Engine: Structured Room Analysis using Gemini via Vertex AI / AI Studio."""
    # Preferred models for analysis. Flash is prioritized for SPEED (Cloud Run timeouts)
    models_to_try = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-lite"]
    
    # Validation and Analysis Prompt
    analysis_prompt = """You are the RoomChic Architectural AI. 
    Evaluate the MASTER IMAGE (first image) for viability.
    Return ONLY valid JSON:    {
      "image_validation": {
        "viability_score": 0-100,
        "viability_ok": true/false,
        "viability_issues_es": ["lista de problemas en español"],
        "is_interior_room": true,
        "has_clear_perspective": true,
        "lighting_quality": "excelente/pobre"
      },
      "room_type": "Dormitorio/Salón/Cocina/Baño/Oficina/Terraza",
      "approx_size": "Pequeño/Mediano/Grande",
      "detailed_description_es": "Descripción detallada del espacio en ESPAÑOL resaltando arquitectura, muebles actuales y luz.",
      "recommendations": {
        "add_es": ["muebles o accesorios a añadir en español"],
        "remove_es": ["qué quitar para mejorar el estilo en español"]
      }
    }"""


    last_error = "Unknown"
    for model_name in models_to_try:
        # Get all providers for this model
        providers = get_model_providers(model_name)
        if not providers:
            print(f"No providers available for model {model_name}")
            continue

        for model, provider in providers:
            try:
                print(f"Attempting analysis with {model_name} via {provider}...")

                # SDK-specific content preparation
                parts = []
                if provider == "studio":
                    # AI Studio format (standard string or dict part)
                    parts.append(analysis_prompt)
                    for img_b64 in images_base64:
                        if "," in img_b64: img_b64 = img_b64.split(",")[1]
                        opt_bytes, _ = optimize_image_data(img_b64, max_dim=1024, quality=70)
                        parts.append({'mime_type': 'image/jpeg', 'data': opt_bytes})
                else:
                    # Vertex AI format
                    parts.append(Part.from_text(analysis_prompt))
                    for img_b64 in images_base64:
                        if "," in img_b64: img_b64 = img_b64.split(",")[1]
                        opt_bytes, _ = optimize_image_data(img_b64, max_dim=1024, quality=70)
                        parts.append(Part.from_data(data=opt_bytes, mime_type="image/jpeg"))

                try:
                    # Try call with per-provider timeout
                    request_opts = {"timeout": 30}
                    if provider == "studio":
                        response = model.generate_content(
                            parts, 
                            generation_config={"response_mime_type": "application/json"},
                            request_options=request_opts
                        )
                    else:
                        response = model.generate_content(
                            parts, 
                            generation_config={"response_mime_type": "application/json"}
                        )
                except Exception as e:
                    print(f"JSON failure with {model_name} ({provider}): {e}")
                    # Fallback to text mode
                    if provider == "studio":
                        response = model.generate_content(parts, request_options=request_opts)
                    else:
                        response = model.generate_content(parts)

                if response and response.text:
                    text = response.text.strip()
                    # Strip markdown markers
                    if "```" in text:
                        text = text.split("```")[1]
                        if text.lower().startswith("json"): text = text[4:]
                    return {"success": True, "data": json.loads(text.strip())}

            except Exception as e:
                last_error = str(e)
                print(f"Error with model {model_name} ({provider}): {safe_truncate(e, 200)}")
                continue
            
    return {"success": False, "error": f"Motores RoomChic fallaron: {safe_truncate(last_error, 200)}"}

def generate_room_render(
    prompt: str,
    room_data: Optional[Dict[str, Any]] = None,
    style: str = "moderno",
    base_image_b64: Optional[str] = None,
    quality: str = "normal",
) -> Dict[str, Any]:
    """RoomChic Render - Photo-faithful room restyling using Gemini 2.0."""
    style_desc = STYLE_DESCRIPTIONS.get(style.lower(), STYLE_DESCRIPTIONS["moderno"])
    
    # Combined instruction
    edit_instruction = f"""
    You are an expert interior designer. Restyle the provided room photo.
    STRICT: Keep walls, windows, doors, and camera angle identical.
    STYLE: {style_desc}
    CLIENT REQUEST: {prompt}
    QUALITY: {quality}
    """

    # Comprehensive fallback list including specific versions
    models_to_try = [
        "gemini-1.5-flash-002", "gemini-1.5-flash", 
        "gemini-2.0-flash-001", "gemini-2.0-flash",
        "gemini-1.5-pro-002", "gemini-1.5-pro", 
        "gemini-2.0-flash-lite-preview-02-05", "gemini-2.0-flash-lite"
    ]
    last_error = "Unknown"
    for model_name in models_to_try:
        # Try both providers for each model name
        providers = get_model_providers(model_name)
        if not providers: continue

        for model, provider in providers:
            try:
                print(f"Generating render with {model_name} via {provider} ({quality})...")

                # SDK-specific content preparation
                prompt_parts = []
                if provider == "studio":
                    # AI Studio format (prompt string, direct image dict)
                    prompt_parts.append(edit_instruction)
                    if base_image_b64:
                        if "," in base_image_b64: base_image_b64 = base_image_b64.split(",")[1]
                        # Optimize for render (higher res than analysis)
                        opt_bytes, _ = optimize_image_data(base_image_b64, max_dim=2560, quality=85)
                        prompt_parts.append({'mime_type': 'image/jpeg', 'data': opt_bytes})
                else:
                    # Vertex AI format
                    prompt_parts.append(Part.from_text(edit_instruction))
                    if base_image_b64:
                        if "," in base_image_b64: base_image_b64 = base_image_b64.split(",")[1]
                        opt_bytes, _ = optimize_image_data(base_image_b64, max_dim=2560, quality=85)
                        prompt_parts.append(Part.from_data(data=opt_bytes, mime_type="image/jpeg"))

                try:
                    # 45s timeout for render
                    request_opts = {"timeout": 45} 
                    generation_config = {"temperature": 0.4}
                    if "2.0" in model_name:
                        generation_config["response_modalities"] = ["IMAGE", "TEXT"]
                    
                    if provider == "studio":
                        response = model.generate_content(prompt_parts, generation_config=generation_config, request_options=request_opts)
                    else:
                        response = model.generate_content(prompt_parts, generation_config=generation_config)
                except Exception as e:
                    print(f"Render generation fail ({model_name} {provider}): {e}")
                    if provider == "studio":
                        response = model.generate_content(prompt_parts, generation_config={"temperature": 0.4}, request_options=request_opts)
                    else:
                        response = model.generate_content(prompt_parts, generation_config={"temperature": 0.4})
                
                # Extract image from response
                image_b64 = None
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'inline_data') and part.inline_data:
                                image_b64 = base64.b64encode(part.inline_data.data).decode('utf-8')
                                break
                
                if image_b64:
                    return {
                        "success": True,
                        "image_base64": image_b64,
                        "full_prompt": edit_instruction,
                        "style_description": style_desc
                    }
                else:
                    print(f"Model {model_name} ({provider}) produced no image data.")
            except Exception as e:
                last_error = str(e)
                print(f"Model error {model_name} ({provider}): {safe_truncate(e, 400)}")
                continue

    return {
        "success": False,
        "error": f"Motores RoomChic fallaron: {safe_truncate(last_error, 200)}"
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
            # Save Input Image to Firebase Storage if provided (Optimized)
            input_image_filename = None
            if image_base64:
                input_image_id = f"{str(uuid.uuid4())}_input"
                input_image_filename = f"uploads/{user['uid']}/{input_image_id}.jpg"
                input_blob = bucket.blob(input_image_filename)
                
                # Optimize input image
                optimized_input_data, content_type_input = optimize_image_data(image_base64)
                input_blob.upload_from_string(optimized_input_data, content_type=content_type_input)

            # Save Generated Render to Firebase Storage (Optimized)
            filename = f"renders/{user['uid']}/{image_id}.jpg"
            blob = bucket.blob(filename)
            
            # Optimize generated image
            optimized_gen_data, content_type_gen = optimize_image_data(image_b64)
            blob.upload_from_string(optimized_gen_data, content_type=content_type_gen)

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
    """Verify if the user is an admin by checking Firestore."""
    user = verify_token()
    if not user:
        return None
    
    if not db:
        return None

    try:
        # Source of truth: Firestore users collection
        user_doc = db.collection("users").document(user["uid"]).get()
        if user_doc.exists and user_doc.to_dict().get("isAdmin") == True:
            # Optionally sync claim if missing for faster subsequent checks if needed
            # but for now, we just return the user
            return user
            
        # Fallback: check custom claims (old method)
        user_record = auth.get_user(user["uid"])
        claims = user_record.custom_claims
        if claims and claims.get("admin") == True:
            return user
    except Exception as e:
        print("Error checking admin status:", e)
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
    """Update user data and sync admin claims (admin only)."""
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

        # Update Firestore
        db.collection("users").document(uid).update(update_data)
        
        # Sync Firebase Auth Custom Claims if isAdmin is changed
        if "isAdmin" in update_data:
            is_admin_val = update_data["isAdmin"]
            try:
                auth.set_custom_user_claims(uid, {"admin": is_admin_val})
                print(f"Synced custom claims for user {uid}: admin={is_admin_val}")
            except Exception as e:
                print(f"Warning: failed to sync custom claims for {uid}: {e}")

        return jsonify({"success": True, "message": f"User {uid} updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/users/<uid>", methods=["DELETE"])
def admin_delete_user(uid):
    """Delete all user data across Auth, Firestore, and Storage (admin only)."""
    admin = verify_admin()
    if not admin:
        return jsonify({"error": "Unauthorized - Admin access required"}), 403

    if not db:
        return jsonify({"error": "Firestore not initialized"}), 500

    try:
        print(f"ADMIN DELETE REQUEST: User {uid} by Admin {admin['uid']}")

        # 1. Delete from Firebase Auth
        try:
            auth.delete_user(uid)
            print(f"Auth: User {uid} deleted.")
        except auth.UserNotFoundError:
            print(f"Auth: User {uid} not found, continuing cleanup.")
        except Exception as e:
            print(f"Auth Error: {e}")

        # 2. Delete Renders and Storage Files
        renders_deleted = 0
        try:
            render_docs = db.collection("renders").where("userId", "==", uid).stream()
            for doc in render_docs:
                data = doc.to_dict()
                
                # Delete files from Storage
                if bucket:
                    for field in ["imageUrl", "inputImageUrl"]:
                        path = data.get(field)
                        if path:
                            try:
                                # Standardize path (remove /api/storage/ prefix if present)
                                clean_path = path.replace("/api/storage/", "")
                                blob = bucket.blob(clean_path)
                                if blob.exists():
                                    blob.delete()
                                    print(f"Storage: Deleted {clean_path}")
                            except Exception as se:
                                print(f"Storage Error deleting {path}: {se}")

                # Delete render document
                doc.reference.delete()
                renders_deleted += 1
            print(f"Firestore: {renders_deleted} renders deleted.")
        except Exception as e:
            print(f"Firestore Renders Error: {e}")

        # 3. Delete Purchases and Transactions
        try:
            for coll in ["purchases", "transactions"]:
                docs = db.collection(coll).where("userId", "==", uid).stream()
                count = 0
                for doc in docs:
                    doc.reference.delete()
                    count += 1
                print(f"Firestore: {count} {coll} deleted.")
        except Exception as e:
            print(f"Firestore Payment Data Error: {e}")

        # 4. Delete Price History (optional, but keep it for record?) 
        # Usually we keep price history as it's an admin log. 
        # But if it's "all data related to user", maybe we should if user was an admin?
        # Let's skip it to preserve system logs.

        # 5. Finally, delete the User document
        db.collection("users").document(uid).delete()
        print(f"Firestore: User document {uid} deleted.")

        return jsonify({
            "success": True, 
            "message": f"Usuario {uid} y todos sus datos han sido eliminados correctamente.",
            "cleanup": {
                "renders": renders_deleted,
                "auth": True
            }
        })
    except Exception as e:
        print(f"Critical error in admin_delete_user: {e}")
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
