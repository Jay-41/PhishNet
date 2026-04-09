"""
Flask API for phishing detection using a pre-trained scikit-learn pipeline.
Run `python train_model.py` first to create models/phishing_model.pkl.
"""

from __future__ import annotations

import os
import sys

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from flask import Flask, jsonify, request
from flask_cors import CORS

from phishing_ml import config
from phishing_ml.preprocessing import clean_text
from phishing_ml.training import load_model_bundle

app = Flask(__name__)
CORS(app)

_pipeline = None
_model_name: str | None = None


def get_pipeline():
    """Lazy-load the serialized model once per process."""
    global _pipeline, _model_name
    if _pipeline is None:
        bundle = load_model_bundle(config.MODEL_PICKLE_PATH)
        _pipeline = bundle["pipeline"]
        _model_name = bundle.get("model_name", "unknown")
    return _pipeline, _model_name


@app.post("/predict")
def predict():
    """
    JSON body: {"email": "<raw email text>"}
    Response: {"prediction": 0|1, "confidence": float, "label": "legitimate"|"phishing"}
    """
    data = request.get_json(silent=True) or {}
    raw = data.get("email")

    if raw is None:
        return jsonify({"error": "Missing required field 'email'."}), 400
    if not isinstance(raw, str) or not raw.strip():
        return jsonify({"error": "Field 'email' must be a non-empty string."}), 400

    try:
        pipe, name = get_pipeline()
    except FileNotFoundError as e:
        return (
            jsonify(
                {
                    "error": str(e),
                    "hint": "Train a model first: python train_model.py (from the backend directory).",
                }
            ),
            503,
        )

    text = clean_text(raw)
    if not text:
        return jsonify({"error": "Email text is empty after preprocessing."}), 400

    # Pipeline was fit on string arrays; single-sample batch
    proba = pipe.predict_proba([text])[0]
    pred = int(pipe.predict([text])[0])
    confidence = float(proba[pred])

    label = "phishing" if pred == 1 else "legitimate"
    return jsonify(
        {
            "prediction": pred,
            "confidence": round(confidence, 4),
            "label": label,
            "model": name,
        }
    )


@app.get("/health")
def health():
    """Lightweight readiness check."""
    try:
        load_model_bundle(config.MODEL_PICKLE_PATH)
        ready = True
    except FileNotFoundError:
        ready = False
    return jsonify({"status": "ok", "model_loaded": ready})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
