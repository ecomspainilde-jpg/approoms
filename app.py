import os
import base64
import uuid
import datetime
import json
from datetime import timezone
from flask import Flask, request, jsonify, send_from_directory
import vertexai
from vertexai.preview import vision_models
from vertexai.preview.vision_models import (
    ImageGenerationModel,
    Image as VisionImage,
)
from vertexai.generative_models import GenerativeModel, Part, Image as VertexImage
import firebase_admin
from firebase_admin import credentials, auth, firestore, storage
import stripe

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
        # Default credentials should work in Cloud Run
        firebase_admin.initialize_app(options={"storage_bucket": storage_bucket})
    db = firestore.client()
    bucket = storage.bucket()
except Exception as e:
    print("Error initializing Firebase Admin:", e)
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
    """Use Gemini 2.5 Flash to analyze one or more uploaded room images and return structured JSON."""
    try:
        model = GenerativeModel("gemini-2.5-flash")
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


def generate_room_render(
    prompt: str,
    room_data: dict = None,
    style: str = "moderno",
    base_image_b64: str = None,
) -> dict:
    """Generate a room render with structural preservation.
    Uses Imagen 4.0 for text-to-image.
    When a base image is provided, tries edit_image() first (imagen-3.0-capability-001),
    then falls back to enriched text-to-image generation.
    """
    try:
        style_desc = STYLE_DESCRIPTIONS.get(
            style.lower(), STYLE_DESCRIPTIONS["moderno"]
        )

        if room_data:
            arch_seed = room_data.get("imagen_prompt_seed_en", "")
            arch_details = room_data.get("architecture_en", "")
            full_prompt = (
                f"Professional interior design render in {style} style. "
                f"ARCHITECTURAL PRESERVATION: {arch_details}. {arch_seed}. "
                f"Maintain EXACT layout of ALL windows, doors, and walls. "
                f"Apply {style} style: {style_desc}. "
                f"Client brief: {prompt}. "
                f"Ultra-high resolution, photorealistic, cinematic lighting, interior design magazine photography."
            )
        else:
            full_prompt = (
                f"Professional interior design render, {style} style. "
                f"Style: {style_desc}. "
                f"Design brief: {prompt}. "
                f"High resolution, photorealistic, interior design photography."
            )

        images = None

        if base_image_b64:
            # Try edit_image() on imagen-3.0-capability-001 for image-to-image editing
            try:
                print("Attempting image editing with imagen-3.0-capability-001...")
                edit_model = ImageGenerationModel.from_pretrained("imagen-3.0-capability-001")
                base_image = VisionImage(image_bytes=base64.b64decode(base_image_b64))
                images = edit_model.edit_image(
                    base_image=base_image,
                    prompt=full_prompt,
                    number_of_images=1,
                )
                if images:
                    print("Image-to-image edit successful with imagen-3.0-capability-001")
                else:
                    print("No images returned from edit_image, falling back to text-to-image")
            except Exception as edit_err:
                print(f"edit_image failed ({edit_err}), falling back to text-to-image")
                images = None

        if not images:
            # Standard Text-to-Image with Imagen 4.0
            print("Generating new image with imagen-4.0-generate-001...")
            t2i_model = ImageGenerationModel.from_pretrained("imagen-4.0-generate-001")
            images = t2i_model.generate_images(
                prompt=full_prompt,
                number_of_images=1,
                language="en",
            )
            if images:
                print("Text-to-image generation successful with imagen-4.0-generate-001")

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
                    "inputImageUrl": None,  # Will be set if we upload the input image
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
