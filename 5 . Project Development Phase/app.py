"""
app.py
------
Streamlit front-end for the Credit Card Approval Predictor.

Run (after starting api.py in another terminal):
    streamlit run app.py
"""

import time
import requests
import streamlit as st

from validators import validate_application

API_BASE_URL = "http://127.0.0.1:5001"
API_KEY = "dev-key-12345"  # must match CREDIT_API_KEY used by api.py

st.set_page_config(page_title="Credit Card Approval Predictor", page_icon="💳", layout="centered")

st.title("💳 Credit Card Approval Predictor")
st.caption("Fill out the application below. All fields are validated before a prediction is made.")

# ---------------------------------------------------------------------------
# Sidebar: API connectivity diagnostics
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("API Connectivity")
    st.write(f"Endpoint: `{API_BASE_URL}`")

    if st.button("Test API Connection"):
        try:
            t0 = time.perf_counter()
            health = requests.get(f"{API_BASE_URL}/health", timeout=5)
            key_check = requests.get(
                f"{API_BASE_URL}/verify-key", headers={"X-API-Key": API_KEY}, timeout=5
            )
            elapsed = round((time.perf_counter() - t0) * 1000, 1)

            if health.status_code == 200:
                st.success(f"Health check OK ({elapsed} ms)")
                st.json(health.json())
            else:
                st.error(f"Health check failed: HTTP {health.status_code}")

            if key_check.status_code == 200 and key_check.json().get("valid"):
                st.success("API key verified.")
            else:
                st.error("API key rejected.")
        except requests.exceptions.RequestException as exc:
            st.error(f"Could not reach the API: {exc}")

# ---------------------------------------------------------------------------
# Application form
# ---------------------------------------------------------------------------
with st.form("application_form"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full name", placeholder="e.g. Priya Sharma")
        job_title = st.text_input("Job title", placeholder="e.g. Software Engineer")
        age = st.number_input("Age", min_value=0, max_value=120, value=30, step=1)
    with col2:
        annual_income = st.number_input("Annual income ($)", min_value=0.0, value=50000.0, step=1000.0)
        credit_score = st.number_input("Credit score", min_value=0, max_value=900, value=680, step=1)
        existing_debt = st.number_input("Existing debt ($)", min_value=0.0, value=5000.0, step=500.0)
    employment_years = st.number_input("Years employed", min_value=0.0, max_value=80.0, value=3.0, step=0.5)

    submitted = st.form_submit_button("Predict")

if submitted:
    application = {
        "name": name,
        "job_title": job_title,
        "age": age,
        "annual_income": annual_income,
        "credit_score": credit_score,
        "existing_debt": existing_debt,
        "employment_years": employment_years,
    }

    is_valid, errors = validate_application(application)

    if not is_valid:
        st.error("Please fix the following before submitting:")
        for field, message in errors.items():
            st.markdown(f"- **{field.replace('_', ' ').title()}**: {message}")
    else:
        try:
            t0 = time.perf_counter()
            resp = requests.post(
                f"{API_BASE_URL}/predict",
                json=application,
                headers={"X-API-Key": API_KEY},
                timeout=10,
            )
            elapsed = round(time.perf_counter() - t0, 2)

            if resp.status_code == 200:
                result = resp.json()
                if result["approved"]:
                    st.success(f"✅ Approved (probability: {result['approval_probability']:.1%})")
                else:
                    st.error(f"❌ Not approved (probability: {result['approval_probability']:.1%})")
                st.caption(f"Round-trip time: {elapsed}s | Server processing: {result['response_time_ms']} ms")
            elif resp.status_code == 401:
                st.error("API key was rejected by the server. Check API configuration.")
            else:
                st.error(f"API returned an error: {resp.json()}")
        except requests.exceptions.RequestException as exc:
            st.error(
                "Could not reach the prediction API. "
                "Make sure `python api.py` is running on port 5001."
            )
            st.exception(exc)
