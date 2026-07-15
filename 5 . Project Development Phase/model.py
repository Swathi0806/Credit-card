"""
model.py
--------
Builds a synthetic-but-realistic credit card approval dataset and trains a
RandomForestClassifier. Saves the fitted model + scaler to models/ so the
Flask API can load them without retraining on every request.

Run directly to (re)train:
    python model.py
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import joblib
import os

FEATURES = ["age", "annual_income", "credit_score", "existing_debt", "employment_years"]
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "approval_model.joblib")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "models", "scaler.joblib")


def generate_synthetic_data(n=6000, seed=42):
    rng = np.random.default_rng(seed)

    age = rng.integers(18, 80, size=n)
    annual_income = rng.gamma(shape=4.0, scale=15000, size=n).round(2)
    credit_score = rng.normal(650, 90, size=n).clip(300, 850).round().astype(int)
    existing_debt = (rng.gamma(shape=2.0, scale=6000, size=n)).round(2)
    employment_years = rng.gamma(shape=2.0, scale=3.0, size=n).clip(0, 45).round(1)

    debt_to_income = existing_debt / np.maximum(annual_income, 1)

    # Underlying "true" approval logic (a bank-like scoring rule) + noise
    score = (
        0.045 * credit_score
        - 6.5 * debt_to_income
        + 0.00006 * annual_income
        + 0.6 * employment_years
        - 0.02 * np.abs(age - 40)
        - 28
    )
    prob_approve = 1 / (1 + np.exp(-score / 3))
    noise = rng.normal(0, 0.05, size=n)
    approved = (prob_approve + noise > 0.5).astype(int)

    df = pd.DataFrame({
        "age": age,
        "annual_income": annual_income,
        "credit_score": credit_score,
        "existing_debt": existing_debt,
        "employment_years": employment_years,
        "approved": approved,
    })
    return df


def train_and_save():
    df = generate_synthetic_data()
    X = df[FEATURES]
    y = df["approved"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    clf = RandomForestClassifier(
        n_estimators=200, max_depth=8, random_state=42, n_jobs=-1
    )
    clf.fit(X_train_scaled, y_train)

    acc = accuracy_score(y_test, clf.predict(X_test_scaled))
    print(f"Validation accuracy: {acc:.3f}")

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(clf, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"Saved model to {MODEL_PATH}")
    print(f"Saved scaler to {SCALER_PATH}")
    return clf, scaler, acc


def load_model():
    if not (os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH)):
        train_and_save()
    clf = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    return clf, scaler


def predict_one(clf, scaler, applicant: dict):
    """applicant must contain all FEATURES keys."""
    row = pd.DataFrame([{k: applicant[k] for k in FEATURES}])
    scaled = scaler.transform(row)
    pred = int(clf.predict(scaled)[0])
    proba = float(clf.predict_proba(scaled)[0][1])
    return pred, proba


if __name__ == "__main__":
    train_and_save()
