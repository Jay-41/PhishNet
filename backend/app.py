from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.post("/analyze")
def analyze():
    data = request.get_json(silent=True) or {}
    email_text = data.get("email")
    if not isinstance(email_text, str) or not email_text.strip():
        return (
            jsonify({"error": "Missing or empty 'email' field in JSON body."}),
            400,
        )

    # Mock response until real analysis is implemented
    return jsonify(
        {
            "risk_score": 75,
            "flags": ["Suspicious link", "Urgent language"],
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
