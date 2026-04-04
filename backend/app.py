import re
from urllib.parse import urlparse

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Normalize obfuscated schemes for URL extraction
_HXXP_RE = re.compile(r"hxxps?://", re.IGNORECASE)

_URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_IP_IN_URL = re.compile(r"\d{1,3}(?:\.\d{1,3}){3}")
_SHORTENERS = (
    "bit.ly/",
    "tinyurl.com/",
    "goo.gl/",
    "t.co/",
    "ow.ly/",
    "buff.ly/",
    "is.gd/",
    "rebrand.ly/",
)

# Keyword groups → official site host suffixes (lowercase)
_BRAND_RULES: list[tuple[tuple[str, ...], tuple[str, ...]]] = [
    (("paypal", "pay pal"), ("paypal.com",)),
    (
        ("microsoft", "office 365", "outlook", "onedrive", "sharepoint", "teams"),
        (
            "microsoft.com",
            "live.com",
            "outlook.com",
            "office.com",
            "microsoftonline.com",
            "windows.com",
        ),
    ),
    (
        ("amazon", "prime video"),
        ("amazon.com", "amazon.co.uk", "amazon.de", "amazon.fr", "amzn.com", "amazonaws.com"),
    ),
    (("apple", "icloud", "apple id", "app store"), ("apple.com", "icloud.com")),
    (("google", "gmail", "youtube"), ("google.com", "gmail.com", "youtube.com", "googleusercontent.com")),
    (("chase", "jpmorgan"), ("chase.com",)),
    (("wells fargo",), ("wellsfargo.com",)),
    (("bank of america", "bofa"), ("bankofamerica.com",)),
    (("citi", "citibank"), ("citi.com", "citibank.com")),
    (("netflix",), ("netflix.com",)),
    (("spotify",), ("spotify.com",)),
    (("coinbase", "crypto wallet", "cryptocurrency"), ("coinbase.com",)),
    (("irs", "internal revenue", "tax refund"), ("irs.gov",)),
    (("fedex",), ("fedex.com",)),
    (("ups", "ups tracking", "ups delivery"), ("ups.com",)),
    (("dhl",), ("dhl.com",)),
    (("linkedin",), ("linkedin.com",)),
    (("facebook", "meta"), ("facebook.com", "meta.com", "fb.com")),
    (("instagram",), ("instagram.com",)),
    (("dropbox",), ("dropbox.com",)),
    (("adobe",), ("adobe.com",)),
    (("zoom",), ("zoom.us",)),
]

_URGENT = (
    "urgent",
    "immediately",
    "right away",
    "as soon as possible",
    "act now",
    "within 24 hours",
    "within 48 hours",
    "today only",
    "account suspended",
    "account has been suspended",
    "verify your account",
    "confirm your identity",
    "verify your identity",
    "click here now",
    "click the link",
    "click on the link",
    "click below",
    "limited time",
    "will expire",
    "expires soon",
    "account locked",
    "locked your account",
    "was locked",
    "been locked",
    "been suspended",
    "unusual activity",
    "unusual sign-in",
    "suspicious activity",
    "security alert",
    "action required",
    "immediate action",
    "failure to comply",
    "legal action",
    "avoid closure",
    "prevent suspension",
)

_ACTION_PHISH = (
    "reset your password",
    "reset password",
    "password reset",
    "re-activate",
    "reactivate your",
    "unlock your account",
    "restore your account",
    "validate your account",
    "confirm your account",
    "update your payment",
    "update billing",
    "verify billing",
    "update your details",
    "sign in to review",
    "login to verify",
    "log in to confirm",
    "sign in to avoid",
    "confirm you did not",
    "if you did not make",
    "did not authorize",
    "payment declined",
    "payment failed",
    "invoice attached",
    "open the attachment",
    "download the file",
    "view the document",
    "shared a document",
    "document with you",
    "wire transfer",
    "western union",
    "gift card",
    "itunes gift",
    "google play card",
    "send bitcoin",
    "send crypto",
    "seed phrase",
    "private key",
    "kindly confirm",
    "kindly send",
    "dear beneficiary",
    "verification required",
    "verify this transaction",
    "confirm this activity",
    "validate your email",
    "secure your account",
    "please review",
    "kindly review",
    "review this link",
)

_SENSITIVE = (
    "password",
    "pin code",
    "ssn",
    "social security",
    "routing number",
    "account number",
    "credit card",
    "cvv",
    "mother's maiden",
    "full card details",
)

_GENERIC_GREETING = (
    "dear customer",
    "dear user",
    "dear valued",
    "dear client",
    "dear member",
    "dear account holder",
    "hello dear",
)

_SCAM_HOOKS = (
    "you have won",
    "you've won",
    "congratulations you",
    "selected as a winner",
    "lottery winner",
    "inheritance",
    "next of kin",
    "nigerian prince",
    "million dollars",
    "claim your prize",
    "business proposal",
    "confidential offer",
)


def _normalize_for_urls(text: str) -> str:
    return _HXXP_RE.sub(lambda m: m.group(0).replace("x", "t"), text)


def _extract_urls(text: str) -> list[str]:
    return _URL_RE.findall(_normalize_for_urls(text))


def _url_hostname(url: str) -> str | None:
    try:
        host = urlparse(url).hostname
        return host.lower() if host else None
    except (ValueError, AttributeError):
        return None


def _host_matches_allowed(hostname: str, allowed: tuple[str, ...]) -> bool:
    h = hostname.lower()
    for suffix in allowed:
        if h == suffix or h.endswith("." + suffix):
            return True
    return False


def _url_has_credential_trick(url: str) -> bool:
    """Detect userinfo abuse, e.g. https://paypal.com@evil.com/"""
    try:
        parsed = urlparse(url)
        if parsed.username or parsed.password:
            return True
        # Double @ or @ before host in path-style tricks (heuristic)
        if url.count("@") > 1:
            return True
    except (ValueError, AttributeError):
        pass
    return False


def _suspicious_url_path(url: str) -> bool:
    ul = url.lower()
    needles = (
        "/login",
        "/signin",
        "/sign-in",
        "/verify",
        "/secure",
        "/update",
        "/confirm",
        "/account/",
        "/webscr",
        "/wp-login",
        "/auth/",
        "/session",
        "/banking",
    )
    try:
        path = urlparse(url).path.lower()
    except (ValueError, AttributeError):
        path = ul
    return any(n in path or n in ul for n in needles)


def _prose_without_urls(lower: str, urls: list[str]) -> str:
    """Strip URL text so brand names inside deceptive links are not read as 'mentioned'."""
    s = lower
    for u in urls:
        s = s.replace(u.lower(), " ")
    return s


def _text_has_keyword(lower: str, kw: str) -> bool:
    """Match phrases as substrings; single tokens use word boundaries."""
    k = kw.lower()
    if " " in k:
        return k in lower
    return re.search(rf"(?<![a-z0-9]){re.escape(k)}(?![a-z0-9])", lower) is not None


def _any_url_matches_brand_hosts(urls: list[str], allowed: tuple[str, ...]) -> bool:
    for u in urls:
        h = _url_hostname(u)
        if h and _host_matches_allowed(h, allowed):
            return True
    return False


def analyze_email(text: str) -> tuple[int, list[str]]:
    """Heuristic score 0–100 and human-readable flags."""
    lower = text.lower()
    flags: list[str] = []
    score = 0
    serious_signals = 0

    urls = _extract_urls(text)
    lowered_urls = [u.lower() for u in urls]
    has_raw_ip = False

    if urls:
        flags.append("Contains HTTP/HTTPS links")
        score += min(10 + 5 * (len(urls) - 1), 25)

        has_raw_ip = any(_IP_IN_URL.search(u) for u in lowered_urls)
        if has_raw_ip:
            flags.append("Link targets a raw IP address")
            score += 30
            serious_signals += 1

        if any(short in u for u in lowered_urls for short in _SHORTENERS):
            flags.append("URL shortener present")
            score += 20
            serious_signals += 1

        for u in urls:
            if _url_has_credential_trick(u):
                flags.append("URL uses misleading login or @-style trick")
                score += 18
                break
        if any(_suspicious_url_path(u) for u in urls):
            flags.append("Link path looks like a login or verify page")
            score += 14

    urgent_hits = [p for p in _URGENT if p in lower]
    if urgent_hits:
        flags.append("Urgent or high-pressure language")
        n_u = len(urgent_hits)
        score += min(10 + 5 * (n_u - 1), 35)
        if n_u >= 2:
            serious_signals += 1

    sensitive_hits = [p for p in _SENSITIVE if p in lower]
    if sensitive_hits:
        flags.append("Asks for sensitive or financial information")
        n_s = len(sensitive_hits)
        score += min(20 + 5 * (n_s - 1), 35)
        serious_signals += 1

    if has_raw_ip and sensitive_hits:
        flags.append("Raw IP link combined with requests for sensitive information")
        score += 10

    if any(g in lower for g in _GENERIC_GREETING):
        flags.append("Generic greeting")
        score += 22

    prize_scam = False
    if "prize" in lower and ("won" in lower or "winner" in lower):
        flags.append("Prize or lottery-style pitch")
        score += 22
        prize_scam = True
    elif any(h in lower for h in _SCAM_HOOKS):
        flags.append("Common scam or prize/inheritance pitch")
        score += 22
        prize_scam = True
    if prize_scam:
        serious_signals += 1

    if "attachment" in lower and any(
        ext in lower for ext in (".exe", ".zip", ".scr", ".bat", ".js", ".vbs")
    ):
        flags.append("References risky attachment types")
        score += 25
        serious_signals += 1

    if serious_signals >= 2:
        score = int(score * (1.0 + 0.15 * (serious_signals - 1)))

    seen: set[str] = set()
    unique = [f for f in flags if not (f in seen or seen.add(f))]
    if not unique:
        unique = ["No strong phishing heuristics matched"]
        score = min(score, 15)

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
