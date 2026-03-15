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
load_dotenv()

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

app = Flask(__name__, static_folder="public", static_url_path="")
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "sk_test_placeholder")
webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_placeholder")

# Initialize Vertex AI
project_id = os.environ.get("GCP_PROJECT_ID", "gen-lang-client-0426824151")
location = os.environ.get("GCP_LOCATION", "us-central1")
storage_bucket = os.environ.get(
    "FIREBASE_STORAGE_BUCKET", f"{project_id}.firebasestorage.app"
)

try:
    vertexai.init(project=project_id, location=location)
except Exception as e:
    print(
        f"Warning: Could not initialize Vertex AI for project {project_id} in {location}:",
        e,
    )

# Initialize Firebase Admin
try:
    if not firebase_admin._apps:
        # Pass project_id explicitly for local development
        firebase_admin.initialize_app(options={
            "projectId": project_id,
            "storageBucket": storage_bucket
        })
    db = firestore.client()
    bucket = storage.bucket()
    print(f"Firebase initialized successfully for project: {project_id}")
except Exception as e:
    print(f"Error initializing Firebase Admin for project {project_id}:", e)
    db = None
    bucket = None


def get_render_price():
    """Get the current render price from Firebase, fallback to default"""
    if not db:
        return 2.50
    try:
        doc = db.collection("pricing").document("render").get()
        if doc.exists:
            return doc.to_dict().get("price", 2.50)
    except Exception as e:
        print("Error fetching price:", e)
    return 2.50


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
    # Use stable models from GEMINI.md
    models_to_try = ["gemini-2.0-flash-exp", "gemini-1.5-pro-002"]
    
    contents = []
    contents.append("You are the RoomChic Architectural AI, specialized in 3D space reconstruction from multiple 2D angles.")

    for i, img_b64 in enumerate(images_base64):
        role = "PRIMARY MASTER IMAGE (Perspective Source)" if i == 0 else f"DEPTH REFERENCE {i} (Blind Spots & Context)"
        contents.append(f"ROLE: {role}")
        try:
            image_part = Part.from_data(data=base64.b64decode(img_b64), mime_type="image/jpeg")
            contents.append(image_part)
        except Exception as e:
            print(f"Error decoding image {i}: {safe_truncate(e, 100)}")

    analysis_prompt = """Use all provided images to perform PERSPECTIVE TRIANGULATION:
1. Use DEPTH REFERENCES to understand what is behind furniture or in blind spots of the MASTER IMAGE.
2. Identify the 'Untouchable Structure': walls, windows, doors, floor, and ceiling.
3. Estimate real-world dimensions by cross-referencing standard objects across all angles.
4. Detect the current style and potential improvements.

Return ONLY a valid JSON object:
{
  "room_type": "Confirmed room type.",
  "architecture_en": "List of untouchable architectural anchors (walls, windows, layout).",
  "dimensions_est": "Estimated metric size (e.g. 3.5x4.5m).",
  "inventory_en": "List 5-8 main objects detected across all photos.",
  "blind_spot_data": "Details from context images not visible in master.",
  "detailed_description_es": "Descripción profesional confirmando que hemos triangulado el espacio correctamente.",
  "imagen_prompt_seed_en": "STRUCTURAL_LOCK: Specific geometric description to ensure 100% fidelity to MASTER IMAGE perspective."
}"""
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
) -> Dict[str, Any]:
    """RoomChic Render: Surgical transformation using Imagen 3.0 via Vertex AI."""
    import time
    max_retries = 3
    
    try:
        style_desc = STYLE_DESCRIPTIONS.get(style.lower(), STYLE_DESCRIPTIONS["moderno"])
        
        if room_data:
            arch = room_data.get("architecture_en", "")
            seed = room_data.get("imagen_prompt_seed_en", "")
        else:
            arch = ""
            seed = ""
        
        # Step 1: Theoretical BEFORE description (Conceptual Structural Anchor)
        structural_prompt = (
            "Professional architectural photography, wide-angle lens. "
            "SCENE CONTEXT: Extreme clutter, ancient worn-out furniture, dim poor lighting, scratched floors. "
            f"STRUCTURAL ANCHOR: {arch}. Perspective lock: {seed}. "
        )

        # Step 2: AFTER transformation (The actual generation)
        transformation_prompt = (
            f"HIGH-END TRANSFORMATION: {style_desc}. "
            "REPLACE ALL MATERIALS with luxury finishes, implement professional ambient lighting, contemporary upscale design. "
            f"USER REQUEST: {prompt}. "
            "CRITICAL CONSTRAINTS: ABSOLUTE PERSPECTIVE LOCK. Maintain 100% of the original camera angle, "
            "window/door positions, and structural layout. 8K photorealistic, interior design magazine quality."
        )

        # Use Vertex AI Imagen 3.0
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        
        # Build the final prompt combining everything
        # We explicitly tell Imagen 3.0 to act as a Gemini-powered engine for high-fidelity interior design.
        final_prompt = (
            f"Gemini-powered Architectural Transformation. "
            f"Original Scene: {structural_prompt} "
            f"Required Evolution: {transformation_prompt}"
        )

        for attempt in range(max_retries):
            try:
                # Imagen 3.0 generation
                images = model.generate_images(
                    prompt=final_prompt,
                    number_of_images=1,
                    aspect_ratio="16:9"
                )
                
                if images:
                    generated_img_b64 = base64.b64encode(images[0]._image_bytes).decode("utf-8")
                    return {
                        "success": True, 
                        "image_base64": generated_img_b64,
                        "full_prompt": final_prompt,
                        "style_description": style_desc
                    }
                else:
                    raise Exception("No images returned from Imagen model.")
                    
            except Exception as retry_e:
                print(f"Generation Attempt {attempt + 1} failed: {safe_truncate(retry_e, 500)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise retry_e

        return {"success": False, "error": "Maximum retries exceeded."}

    except Exception as e:
        print(f"Imagen 3.0 Render Error: {safe_truncate(e, 500)}")
        return {"success": False, "error": f"Render error: {safe_truncate(e, 200)}"}


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
    image_base64 = data.get("image_base64")

    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    result = generate_room_render(prompt, room_data, style, image_base64)
    if result.get("success"):
        # ── Deduct Credit ──
        user_ref.update({
            "credits": firestore.Increment(-1),
            "totalGenerations": firestore.Increment(1)
        })

        image_b64 = result["image_base64"]

        # Check Firebase Storage
        if not bucket:
            return jsonify(
                {
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

            # Save Generated Render to Firebase Storage
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
                    "inputImageUrl": input_image_filename,
                    "createdAt": datetime.datetime.now(timezone.utc),
                    "roomData": room_data,
                    "fullPrompt": result["full_prompt"],
                    "price": get_render_price(),
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
                    "productId": f"render_{style}",
                    "amount": get_render_price(),
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
        # Check package price in Firestore
        pkg_doc = db.collection("packages").document(package_id).get()
        if not pkg_doc.exists:
            return jsonify({"error": "Package not found"}), 404
        
        pkg_data = pkg_doc.to_dict()
        if not pkg_data.get("isActive", True):
            return jsonify({"error": "Package is not active"}), 400

        price = pkg_data.get("price", 0)  # in cents
        currency = pkg_data.get("currency", "eur")
        name = pkg_data.get("name", "Credits Package")
        credits_amount = pkg_data.get("creditsAmount", 0)

        session = stripe.checkout.Session.create(
            payment_method_types=['card', 'paypal', 'ideal'],
            line_items=[{
                'price_data': {
                    'currency': currency,
                    'product_data': {
                        'name': name,
                    },
                    'unit_amount': price,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.host_url + '05-gracias.html?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + '04-pago-bizum.html',
            metadata={
                'userId': user['uid'],
                'packageId': package_id,
                'creditsAmount': credits_amount
            }
        )

        return jsonify({'url': session.url})
    except Exception as e:
        print("Error creating checkout session:", e)
        return jsonify({"error": str(e)}), 500


@firestore.transactional
def add_credits_txn(transaction, user_ref, credits_amount, amount_paid):
    user_doc = user_ref.get(transaction=transaction)
    if user_doc.exists:
        data = user_doc.to_dict()
        new_credits = data.get("credits", 0) + credits_amount
        new_purchases = data.get("totalPurchases", 0) + amount_paid
        transaction.update(user_ref, {
            "credits": new_credits,
            "totalPurchases": new_purchases
        })
    else:
        transaction.set(user_ref, {
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
    except ValueError as e:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        return jsonify({'error': 'Invalid signature'}), 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        user_id = session.get('metadata', {}).get('userId')
        package_id = session.get('metadata', {}).get('packageId')
        credits_amount = int(session.get('metadata', {}).get('creditsAmount', 0))
        amount_paid = session.get('amount_total', 0)
        
        if db and user_id:
            db.collection("transactions").document(session['id']).set({
                "userId": user_id,
                "packageId": package_id,
                "amountPaid": amount_paid,
                "status": "completed",
                "createdAt": datetime.datetime.now(timezone.utc),
            })
            
            user_ref = db.collection("users").document(user_id)
            add_credits_txn(db.transaction(), user_ref, credits_amount, amount_paid)

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

        # Calculate total revenue from purchases
        total_revenue = 0
        for doc in db.collection("purchases").stream():
            p = doc.to_dict()
            total_revenue += p.get("amount", 0)

        return jsonify(
            {
                "totalUsers": users_count,
                "totalRenders": renders_count,
                "totalRevenue": total_revenue,
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
        docs = db.collection("pricing").stream()
        for doc in docs:
            pricing[doc.id] = doc.to_dict()

        # Return defaults if not set
        if "render" not in pricing:
            pricing["render"] = {"price": 2.50, "description": "Single render"}
        if "credits" not in pricing:
            pricing["credits"] = {"price": 10.00, "description": "Credits pack"}

        return jsonify(pricing)
    except Exception as e:
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
                "changedBy": admin["uid"],
                "changedAt": datetime.datetime.now(timezone.utc),
            }
        )

        return jsonify({"success": True, "message": f"Price updated to {new_price}"})
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
