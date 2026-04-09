#!/usr/bin/env python3
"""
Train phishing classifiers on CEAS_08.csv and save the best model (by F1).

Usage (from the `backend/` directory):
    python train_model.py

Environment:
    CEAS_MAX_SAMPLES   Max rows to use (stratified); default 150000
    TFIDF_MAX_FEATURES TF-IDF vocabulary cap; default 25000
"""

from __future__ import annotations

import argparse
import os
import sys

# Ensure `backend/` is on the path when run as a script
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from phishing_ml import config  # noqa: E402
from phishing_ml.data import load_ceas_dataset  # noqa: E402
from phishing_ml.training import train_compare_and_save  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Train phishing ML models on CEAS CSV.")
    parser.add_argument(
        "--csv",
        default=None,
        help=f"Path to CEAS CSV (default: {config.DEFAULT_CSV_PATH})",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Stratified row cap (overrides CEAS_MAX_SAMPLES if set).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help=f"Output pickle path (default: {config.MODEL_PICKLE_PATH})",
    )
    parser.add_argument(
        "--nrows",
        type=int,
        default=None,
        help="Read only first N rows from CSV (overrides CEAS_NROWS env if set).",
    )
    args = parser.parse_args()

    max_samples = args.max_samples
    if max_samples is None:
        max_samples = config.MAX_SAMPLES

    nrows = args.nrows
    print(f"Loading dataset (max_samples={max_samples}, nrows={nrows})...")
    X, y = load_ceas_dataset(csv_path=args.csv, max_samples=max_samples, nrows=nrows)
    print(f"  Samples: {len(X)}  |  Phishing rate: {y.mean():.3f}")

    train_compare_and_save(X, y, model_path=args.output)


if __name__ == "__main__":
    main()
