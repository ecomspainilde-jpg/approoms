import os
from flask import Flask, request, jsonify, send_from_directory
import vertexai
from vertexai.generative_models import GenerativeModel

app = Flask(__name__, static_folder="public", static_url_path="")

# Initialize Vertex AI
project_id = "gen-lang-client-0426824151"
location = "us-central1"

try:
    vertexai.init(project=project_id, location=location)
    model = GenerativeModel("gemini-1.5-pro-001")
except Exception as e:
    print("Warning: Could not initialize Vertex AI locally:", e)
    model = None

def generate_image(prompt):
    if not model:
        return "Vertex AI is not initialized."
    responses = model.generate_content(
        [prompt],
        generation_config={
            "max_output_tokens": 2048,
            "temperature": 0.9,
            "top_p": 1
        },
        safety_settings={
            "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE",
        },
        stream=False,
    )
    return responses.text

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
        return jsonify({"description": result})
    except Exception as e:
        print("Error generating content:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
