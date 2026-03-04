import os
import base64
from flask import Flask, request, jsonify, send_from_directory
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

app = Flask(__name__, static_folder="public", static_url_path="")

# Initialize Vertex AI
project_id = "gen-lang-client-0426824151"
location = "us-central1"

try:
    vertexai.init(project=project_id, location=location)
except Exception as e:
    print("Warning: Could not initialize Vertex AI locally:", e)

def generate_image(prompt):
    try:
        model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        images = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            language="es",
            aspect_ratio="1:1"
        )
        # Extraemos los bytes y convertimos a base64
        import base64
        b64_image = base64.b64encode(images[0]._image_bytes).decode("utf-8")
        return {"success": True, "image_base64": b64_image}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route("/")
def index():
    return send_from_directory("public", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory("public", path)
    return send_from_directory("public", "index.html")

@app.route("/api/simulate-payment", methods=["POST"])
def api_simulate_payment():
    print("Simulating payment of 1 EUR...")
    # Simulate payment processing
    payment_successful = True  # Assume payment is successful for this simulation
    if payment_successful:
        print("Payment successful!")
        return jsonify({"success": True, "message": "Payment successful!"})
    else:
        print("Payment failed.")
        return jsonify({"success": False, "message": "Payment failed."}), 400

@app.route("/api/generate-image", methods=["POST"])
def api_generate_image():
    data = request.json
    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
    
    try:
        result = generate_image(prompt)
        if result.get("success"):
            return jsonify({"image_base64": result["image_base64"]})
        else:
            return jsonify({"error": result.get("error", "Unknown error")}), 500
    except Exception as e:
        print("Error generating content:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
