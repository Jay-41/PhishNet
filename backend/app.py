import re

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

_URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_IP_IN_URL = re.compile(r"\d{1,3}(?:\.\d{1,3}){3}")
_SHORTENERS = (
    "bit.ly/",
    "tinyurl.com/",
    "goo.gl/",
    "t.co/",
    "ow.ly/",
    "buff.ly/",
)

_URGENT = (
    "urgent",
    "immediately",
    "act now",
    "within 24 hours",
    "account suspended",
    "verify your account",
    "confirm your identity",
    "click here now",
    "limited time",
    "will expire",
    "account locked",
    "unusual activity",
    "security alert",
    "action required",
)

_SENSITIVE = (
    "password",
    "ssn",
    "social security",
    "routing number",
    "credit card",
    "update payment",
    "verify billing",
    "wire transfer",
    "gift card",
)


def analyze_email(text: str) -> tuple[int, list[str]]:
    """Simple heuristic score 0–100 and human-readable flags."""
    lower = text.lower()
    flags: list[str] = []
    score = 8

    urls = _URL_RE.findall(text)
    if urls:
        flags.append("Contains HTTP/HTTPS links")
        score += min(12 + 4 * (len(urls) - 1), 28)

        for u in urls:
            ul = u.lower()
            if _IP_IN_URL.search(ul):
                flags.append("Link targets a raw IP address")
                score += 22
                break

        lowered = [u.lower() for u in urls]
        if any(short in u for u in lowered for short in _SHORTENERS):
            flags.append("URL shortener present")
            score += 14

    urgent_hits = [p for p in _URGENT if p in lower]
    if urgent_hits:
        flags.append("Urgent or high-pressure language")
        score += min(8 + 4 * len(urgent_hits), 28)

    if any(p in lower for p in _SENSITIVE):
        flags.append("Asks for sensitive or financial information")
        score += 20

    if "dear customer" in lower or "dear user" in lower or "dear valued" in lower:
        flags.append("Generic greeting")
        score += 10

    if "prize" in lower and ("won" in lower or "winner" in lower):
        flags.append("Prize or lottery-style pitch")
        score += 16

    if "attachment" in lower and any(
        ext in lower for ext in (".exe", ".zip", ".scr", ".bat")
    ):
        flags.append("References risky attachment types")
        score += 18

    # De-dupe flags, preserve order
    seen: set[str] = set()
    unique = [f for f in flags if not (f in seen or seen.add(f))]

    if not unique:
        unique = ["No strong phishing heuristics matched"]
        score = min(score, 22)

    score = max(0, min(100, score))
    return score, unique


@app.post("/analyze")
def analyze():
    data = request.get_json(silent=True) or {}
    email_text = data.get("email")
    if not isinstance(email_text, str) or not email_text.strip():
        return (
            jsonify({"error": "Missing or empty 'email' field in JSON body."}),
            400,
        )

    risk_score, flags = analyze_email(email_text)
    return jsonify({"risk_score": risk_score, "flags": flags})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
