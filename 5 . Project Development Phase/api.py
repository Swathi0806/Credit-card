"""
api.py
------
Flask backend that exposes the credit approval model as a small REST API.

Endpoints
---------
GET  /health           -> liveness + model-loaded check (no API key required)
POST /predict           -> validates payload, requires X-API-Key header, returns prediction
GET  /verify-key         -> confirms whether the supplied API key is valid

Run:
    python api.py
Server listens on http://127.0.0.1:5001
"""

import os
import time
import logging
from flask import Flask, request, jsonify

from model import load_model, predict_one, FEATURES
from validators import validate_application

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("credit-api")

app = Flask(__name__)

# In a real deployment this would come from a secrets manager / env var.
API_KEY = os.environ.get("CREDIT_API_KEY", "dev-key-12345")

_clf, _scaler = load_model()


def _check_api_key():
    supplied = request.headers.get("X-API-Key")
    return supplied is not None and supplied == API_KEY


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "model_loaded": _clf is not None and _scaler is not None,
        "features_expected": FEATURES,
    }), 200


@app.route("/verify-key", methods=["GET"])
def verify_key():
    if _check_api_key():
        return jsonify({"valid": True, "message": "API key accepted."}), 200
    return jsonify({"valid": False, "message": "Invalid or missing API key."}), 401


@app.route("/predict", methods=["POST"])
def predict():
    start = time.perf_counter()

    if not _check_api_key():
        return jsonify({"error": "Invalid or missing API key."}), 401

    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    is_valid, errors = validate_application(payload)
    if not is_valid:
        return jsonify({"error": "Validation failed.", "field_errors": errors}), 400

    applicant = {
        "age": float(payload["age"]),
        "annual_income": float(payload["annual_income"]),
        "credit_score": float(payload["credit_score"]),
        "existing_debt": float(payload["existing_debt"]),
        "employment_years": float(payload["employment_years"]),
    }

    try:
        pred, proba = predict_one(_clf, _scaler, applicant)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Prediction failed")
        return jsonify({"error": f"Prediction failed: {exc}"}), 500

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

    return jsonify({
        "name": payload.get("name"),
        "approved": bool(pred),
        "approval_probability": round(proba, 4),
        "response_time_ms": elapsed_ms,
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
