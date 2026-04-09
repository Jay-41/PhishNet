"""Load CEAS CSV and build the modeling dataframe."""

from __future__ import annotations

import os

import pandas as pd
from sklearn.model_selection import train_test_split

from phishing_ml import config
from phishing_ml.preprocessing import clean_text


def load_ceas_dataset(
    csv_path: str | None = None,
    max_samples: int | None = None,
    nrows: int | None = None,
) -> tuple[pd.Series, pd.Series]:
    """
    Load CEAS_08-style CSV. Builds a single `text` column from subject + body.

    Expected columns: subject, body, label (0 = legitimate, 1 = phishing).
    """
    path = csv_path or config.DEFAULT_CSV_PATH
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Dataset not found: {path}")

    usecols = ["subject", "body", "label"]
    read_kw: dict = dict(
        usecols=usecols,
        encoding="utf-8",
        on_bad_lines="skip",
        low_memory=False,
    )
    nrows_eff = nrows if nrows is not None else (config.CEAS_NROWS or 0)
    if nrows_eff and nrows_eff > 0:
        read_kw["nrows"] = int(nrows_eff)
    df = pd.read_csv(path, **read_kw)

    if df.empty:
        raise ValueError("Dataset is empty after loading.")

    df["subject"] = df["subject"].fillna("").astype(str)
    df["body"] = df["body"].fillna("").astype(str)
    df["text"] = (df["subject"] + " " + df["body"]).map(clean_text)

    df = df.dropna(subset=["label"])
    df["label"] = pd.to_numeric(df["label"], errors="coerce")
    df = df.dropna(subset=["label"])
    df["label"] = df["label"].astype(int)

    # Drop empty documents
    df = df[df["text"].str.len() > 0]

    cap = max_samples if max_samples is not None else config.MAX_SAMPLES
    if cap > 0 and len(df) > cap:
        try:
            df, _ = train_test_split(
                df,
                train_size=cap,
                stratify=df["label"],
                random_state=config.RANDOM_STATE,
            )
        except ValueError:
            df = df.sample(n=cap, random_state=config.RANDOM_STATE)

    X = df["text"]
    y = df["label"]
    return X, y
