"""
Garbage Classification — Flask backend
======================================
Loads the trained Keras model and serves predictions to the React frontend.

Endpoints
---------
GET  /api/health    -> {"status": "ok", "model_loaded": bool, "classes": [...]}
POST /api/predict   -> multipart form with field "image"
                       returns predicted class, confidence, full distribution,
                       and disposal guidance.

Run:  python app.py   (serves on http://localhost:5000)
"""

import io
import json
import os

import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS
from PIL import Image
import tensorflow as tf

# --------------------------------------------------------------------------
# Paths & config
# --------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "garbage_model.keras")
CLASSES_PATH = os.path.join(BASE_DIR, "models", "class_names.json")
IMG_SIZE = (224, 224)
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

# Disposal guidance shown alongside each prediction. This is the bit that
# turns a raw classifier into something actually useful to a person holding
# a piece of trash. Tune the bin names to your local council if needed.
GUIDANCE = {
    "paper":       {"bin": "Recycling (paper)",   "recyclable": True,
                    "tip": "Keep it dry and clean. Shredded paper often needs a separate bag."},
    "cardboard":   {"bin": "Recycling (paper)",   "recyclable": True,
                    "tip": "Flatten boxes. Remove heavy tape and plastic windows."},
    "biological":  {"bin": "Compost / organic",   "recyclable": True,
                    "tip": "Food scraps and garden waste go to compost, not recycling."},
    "metal":       {"bin": "Recycling (metal)",   "recyclable": True,
                    "tip": "Rinse cans. Empty aerosols can usually be recycled too."},
    "plastic":     {"bin": "Recycling (plastic)", "recyclable": True,
                    "tip": "Check the resin code. Soft films usually aren't kerbside recyclable."},
    "green-glass": {"bin": "Recycling (glass)",   "recyclable": True,
                    "tip": "Rinse and remove lids. Colour sorting helps glass reprocessing."},
    "brown-glass": {"bin": "Recycling (glass)",   "recyclable": True,
                    "tip": "Rinse and remove lids. Colour sorting helps glass reprocessing."},
    "white-glass": {"bin": "Recycling (glass)",   "recyclable": True,
                    "tip": "Clear glass is the most valuable to recycle. Rinse it first."},
    "clothes":     {"bin": "Textile donation/recycling", "recyclable": True,
                    "tip": "Wearable items can be donated; worn-out textiles go to fabric recycling."},
    "shoes":       {"bin": "Textile donation/recycling", "recyclable": True,
                    "tip": "Tie pairs together. Many stores run shoe take-back schemes."},
    "batteries":   {"bin": "Hazardous / e-waste",  "recyclable": True,
                    "tip": "Never bin batteries. Use a dedicated collection point — fire risk."},
    "trash":       {"bin": "General waste",        "recyclable": False,
                    "tip": "No recycling stream for this — general waste is the right place."},
}

# --------------------------------------------------------------------------
# App + model loading
# --------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)  # allow the React dev server (different port) to call this API

model = None
class_names = []


def load_artifacts():
    """Load model + class list once at startup. Missing files are not fatal
    so the server still boots and /api/health can report what's wrong."""
    global model, class_names
    if os.path.exists(MODEL_PATH) and os.path.exists(CLASSES_PATH):
        model = tf.keras.models.load_model(MODEL_PATH)
        with open(CLASSES_PATH) as f:
            class_names = json.load(f)
        print(f"Loaded model with {len(class_names)} classes: {class_names}")
    else:
        print("WARNING: model files not found in ./models/")
        print("Train on Kaggle, then place garbage_model.keras and "
              "class_names.json in the backend/models/ folder.")


def preprocess(file_storage):
    """Bytes -> (1, 224, 224, 3) float array. We resize to the model's input
    size; the model graph itself applies MobileNetV2 preprocessing, so we do
    NOT scale pixel values here."""
    img = Image.open(io.BytesIO(file_storage.read())).convert("RGB")
    img = img.resize(IMG_SIZE)
    arr = np.array(img, dtype=np.float32)
    return np.expand_dims(arr, axis=0)


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "model_loaded": model is not None,
        "classes": class_names,
    })


@app.route("/api/predict", methods=["POST"])
def predict():
    if model is None:
        return jsonify({"error": "Model not loaded. Add the trained model "
                                 "to backend/models/ and restart."}), 503

    if "image" not in request.files:
        return jsonify({"error": "No image uploaded. Send a file in the "
                                 "'image' form field."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXT:
        return jsonify({"error": f"Unsupported file type '{ext}'. "
                                 f"Use one of: {', '.join(sorted(ALLOWED_EXT))}"}), 400

    try:
        batch = preprocess(file)
        probs = model.predict(batch, verbose=0)[0]
    except Exception as exc:
        return jsonify({"error": f"Could not read that image: {exc}"}), 400

    top_idx = int(np.argmax(probs))
    label = class_names[top_idx]
    guidance = GUIDANCE.get(label, {})

    # Full sorted distribution so the frontend can show runner-up guesses.
    distribution = sorted(
        ({"label": class_names[i], "confidence": float(p)}
         for i, p in enumerate(probs)),
        key=lambda d: d["confidence"], reverse=True,
    )

    return jsonify({
        "prediction": label,
        "confidence": float(probs[top_idx]),
        "guidance": guidance,
        "distribution": distribution,
    })


if __name__ == "__main__":
    load_artifacts()
    app.run(host="0.0.0.0", port=5000, debug=True)
