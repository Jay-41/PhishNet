# Phishing Email Content Analyzer

Full-stack app: **React (Vite)** frontend and **Flask** backend. The backend classifies pasted email text with **scikit-learn** (TF-IDF features + trained classifier) using the **CEAS_08** dataset (`frontend/public/CEAS_08.csv`).

## Project layout

- `frontend/` — Vite + React UI
- `backend/` — Flask API, training script, and ML package
  - `phishing_ml/` — data loading, preprocessing, training
  - `train_model.py` — train models, evaluate, save `models/phishing_model.pkl`
  - `app.py` — loads the saved model and serves `POST /predict`

## Prerequisites

- [Node.js](https://nodejs.org/) (LTS recommended)
- [Python](https://www.python.org/) 3.10+ with `pip`
- Enough RAM/disk to read the CEAS CSV (large file; training uses a stratified subsample by default)

## Train the model (required before first API run)

From the `backend/` directory, install dependencies and run training:

```bash
cd backend
python -m venv .venv
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python train_model.py
```

**macOS / Linux:**

```bash
source .venv/bin/activate
pip install -r requirements.txt
python train_model.py
```

Training loads `CEAS_08.csv`, builds `text` from **subject + body** (cleaned), compares **Logistic Regression**, **Multinomial Naive Bayes**, and **Random Forest** (TF-IDF → truncated SVD → forest), prints accuracy / precision / recall / F1, and saves the **best F1** pipeline to `backend/models/phishing_model.pkl`.

### Tuning large datasets

| Environment variable | Meaning |
|---------------------|--------|
| `CEAS_MAX_SAMPLES` | Max rows after load (stratified subsample); default `150000` |
| `CEAS_NROWS` | Read only first N rows from the CSV (optional speed/debug) |
| `TFIDF_MAX_FEATURES` | TF-IDF vocabulary cap; default `25000` |

CLI shortcuts:

```bash
python train_model.py --nrows 50000 --max-samples 20000
```

## Run the API

With the virtualenv activated:

```bash
python app.py
```

The API listens on **http://127.0.0.1:5000**. It **does not** retrain on startup; it loads `models/phishing_model.pkl`. If the file is missing, `POST /predict` returns **503** with a hint to run `train_model.py`.

### Endpoints

- `POST /predict` — JSON `{"email": "<text>"}` → `prediction` (0 or 1), `confidence`, `label` (`legitimate` / `phishing`), `model`
- `GET /health` — `model_loaded` status

## Frontend setup

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the URL shown (e.g. **http://localhost:5173**). The dev server proxies `/predict` to Flask.

### Optional: direct API URL

Create `frontend/.env`:

```env
VITE_API_URL=http://127.0.0.1:5000
```

The UI calls `${VITE_API_URL}/predict`.

## Run both locally

1. Train once: `python train_model.py` from `backend/`.
2. Start Flask: `python app.py` (port 5000).
3. Start Vite: `npm run dev` from `frontend/`.
4. Paste email text and click **Analyze**.
