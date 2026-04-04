# Phishing Email Content Analyzer

Full-stack web app: **React (Vite)** frontend and **Flask** backend. Paste email text, call `/analyze`, and view a risk score plus flags from simple heuristics (links, urgency wording, sensitive requests, etc.).

## Project layout

- `frontend/` — Vite + React UI
- `backend/` — Flask API

## Prerequisites

- [Node.js](https://nodejs.org/) (LTS recommended)
- [Python](https://www.python.org/) 3.10+ with `pip`

## Backend setup

```bash
cd backend
python -m venv .venv
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

**macOS / Linux:**

```bash
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

The API listens on **http://127.0.0.1:5000**. The `POST /analyze` endpoint expects JSON:

```json
{ "email": "paste email text here" }
```

Example response (values depend on content):

```json
{
  "risk_score": 58,
  "flags": ["Contains HTTP/HTTPS links", "Urgent or high-pressure language"]
}
```

## Frontend setup

In a **second** terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the URL shown in the terminal (usually **http://localhost:5173**). The Vite dev server proxies `/analyze` to the Flask app, so keep the backend running while you use the UI.

### Optional: direct API URL

To call the backend without the proxy (e.g. custom ports), create `frontend/.env`:

```env
VITE_API_URL=http://127.0.0.1:5000
```

The app will then use `fetch` to `${VITE_API_URL}/analyze`.

## Run both locally

1. Start Flask: `python app.py` from `backend/` (port 5000).
2. Start Vite: `npm run dev` from `frontend/` (port 5173).
3. Use the browser UI to paste email content and click **Analyze**.
