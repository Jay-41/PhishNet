"""Train multiple classifiers, evaluate, persist the best by macro F1."""

from __future__ import annotations

import os
import pickle
from typing import Any

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from phishing_ml import config


def _tfidf_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(
        max_features=config.TFIDF_MAX_FEATURES,
        ngram_range=config.TFIDF_NGRAM_RANGE,
        stop_words="english",
        lowercase=True,
        sublinear_tf=True,
    )


def build_candidate_pipelines() -> dict[str, Pipeline]:
    """
    TF-IDF features shared in spirit; RandomForest uses TruncatedSVD on TF-IDF
    because tree ensembles expect dense numeric input.
    """
    tfidf = _tfidf_vectorizer()

    lr = Pipeline(
        [
            ("tfidf", tfidf),
            (
                "clf",
                LogisticRegression(
                    max_iter=1000,
                    solver="saga",
                    class_weight="balanced",
                    random_state=config.RANDOM_STATE,
                ),
            ),
        ]
    )

    # Fresh vectorizer per pipeline (clone semantics) — rebuild for each
    nb = Pipeline(
        [
            ("tfidf", _tfidf_vectorizer()),
            ("clf", MultinomialNB(alpha=0.1)),
        ]
    )

    rf = Pipeline(
        [
            ("tfidf", _tfidf_vectorizer()),
            (
                "svd",
                TruncatedSVD(
                    n_components=400,
                    random_state=config.RANDOM_STATE,
                ),
            ),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=150,
                    max_depth=24,
                    min_samples_leaf=2,
                    random_state=config.RANDOM_STATE,
                    n_jobs=-1,
                    class_weight="balanced_subsample",
                ),
            ),
        ]
    )

    return {
        "logistic_regression": lr,
        "multinomial_nb": nb,
        "random_forest": rf,
    }


def _evaluate_binary(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }


def train_compare_and_save(
    X,
    y,
    model_path: str | None = None,
) -> dict[str, Any]:
    """
    80/20 split, fit all models, print metrics, save best pipeline by F1-score.
    """
    out_path = model_path or config.MODEL_PICKLE_PATH
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=config.RANDOM_STATE,
            stratify=y,
        )
    except ValueError:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=config.RANDOM_STATE
        )

    pipelines = build_candidate_pipelines()
    results: dict[str, dict[str, float]] = {}
    fitted: dict[str, Pipeline] = {}

    print("\n" + "=" * 60)
    print("MODEL EVALUATION (test set)")
    print("=" * 60)

    for name, pipe in pipelines.items():
        print(f"\n--- Training: {name} ---")
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        metrics = _evaluate_binary(y_test.values, y_pred)
        results[name] = metrics
        fitted[name] = pipe
        print(
            f"  Accuracy:  {metrics['accuracy']:.4f}\n"
            f"  Precision: {metrics['precision']:.4f}\n"
            f"  Recall:    {metrics['recall']:.4f}\n"
            f"  F1-score:  {metrics['f1']:.4f}"
        )

    best_name = max(results.keys(), key=lambda k: results[k]["f1"])
    best_pipe = fitted[best_name]
    best_f1 = results[best_name]["f1"]

    print("\n" + "=" * 60)
    print(f"BEST MODEL (by F1): {best_name}  |  F1 = {best_f1:.4f}")
    print("=" * 60 + "\n")

    bundle = {
        "pipeline": best_pipe,
        "model_name": best_name,
        "metrics": results,
        "best_f1": best_f1,
    }
    with open(out_path, "wb") as f:
        pickle.dump(bundle, f)
    print(f"Saved model bundle to: {out_path}\n")

    return bundle


def load_model_bundle(path: str | None = None) -> dict[str, Any]:
    """Load pickle produced by train_compare_and_save."""
    p = path or config.MODEL_PICKLE_PATH
    if not os.path.isfile(p):
        raise FileNotFoundError(f"No trained model at {p}")
    with open(p, "rb") as f:
        return pickle.load(f)
