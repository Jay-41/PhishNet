"""Paths and training hyperparameters."""

import os

# backend/ directory (parent of this package)
_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_PROJECT_ROOT = os.path.abspath(os.path.join(_BACKEND_ROOT, ".."))

# Dataset: CEAS challenge CSV shipped under frontend/public
DEFAULT_CSV_PATH = os.path.join(_PROJECT_ROOT, "frontend", "public", "CEAS_08.csv")

# Serialized best model + metadata
MODEL_DIR = os.path.join(_BACKEND_ROOT, "models")
MODEL_PICKLE_PATH = os.path.join(MODEL_DIR, "phishing_model.pkl")

# Optional cap for very large CSVs (full dataset ~1.3M rows; stratified subsample for feasible training)
MAX_SAMPLES = int(os.environ.get("CEAS_MAX_SAMPLES", "150000"))

# Optional: only read the first N rows from disk (faster tests; set 0 to read entire file)
CEAS_NROWS = int(os.environ.get("CEAS_NROWS", "0"))

# TF-IDF: limit vocabulary size for memory and speed on large corpora
TFIDF_MAX_FEATURES = int(os.environ.get("TFIDF_MAX_FEATURES", "25000"))
TFIDF_NGRAM_RANGE = (1, 2)

# Reproducibility
RANDOM_STATE = 42
