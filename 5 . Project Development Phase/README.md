# Credit Card Approval Predictor

A fully Python web application for predicting credit card approval decisions.

- **Front-end:** [Streamlit](https://streamlit.io) (`app.py`)
- **Back-end:** [Flask](https://flask.palletsprojects.com) REST API (`api.py`)
- **Model:** scikit-learn `RandomForestClassifier` trained on a synthetic-but-realistic dataset (`model.py`)
- **Validation:** shared rules used by both UI and API (`validators.py`)
- **Tests:** `pytest` suites covering every requirement below (`tests/`)

## 1. Setup

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Run the app

**Option A — one command:**
```bash
./start.sh
```

**Option B — manual (two terminals):**
```bash
# Terminal 1: train the model (first run only) and start the API
python model.py
python api.py            # serves on http://127.0.0.1:5001

# Terminal 2: start the UI
streamlit run app.py     # opens in your browser
```

The Streamlit sidebar has a "Test API Connection" button to confirm the UI
can reach the API and that the API key is accepted.

## 3. Run the test suite

```bash
pytest tests/ -v
```

This runs 67 tests covering:

| Requirement | Test file |
|---|---|
| Text input validation (name, job title) | `tests/test_validators.py` |
| Number input validation (age, income, credit score, debt, employment years) | `tests/test_validators.py` |
| Prediction correctness on submission | `tests/test_prediction.py` |
| API connectivity, API key verification, model response | `tests/test_api_connectivity.py` |
| Performance: avg response time < 3s, stability under concurrent load | `tests/test_performance.py` |

## 4. Real-network load test

With `api.py` running, hit it over real HTTP with configurable concurrency:

```bash
python scripts/load_test.py --requests 100 --concurrency 25
```

Reports success rate, average/min/max response time, and p95 latency.

## 5. Application fields & valid ranges

| Field | Type | Rule |
|---|---|---|
| Name | text | 2–50 chars, letters/spaces/`'`/`-`/`.` only |
| Job title | text | 2–60 chars, letters/numbers + common punctuation |
| Age | number | 18–100 |
| Annual income | number | 0–10,000,000 |
| Credit score | number | 300–850 |
| Existing debt | number | 0–10,000,000 |
| Employment years | number | 0–70 |

## 6. API reference

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/health` | GET | none | Liveness + confirms model is loaded |
| `/verify-key` | GET | `X-API-Key` header | Confirms the API key is valid |
| `/predict` | POST | `X-API-Key` header | Validates payload, returns `approved`, `approval_probability`, `response_time_ms` |

Example:
```bash
curl -X POST http://127.0.0.1:5001/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-12345" \
  -d '{"name":"Priya Sharma","job_title":"Engineer","age":35,
       "annual_income":95000,"credit_score":780,
       "existing_debt":2000,"employment_years":8}'
```

## 7. Notes

- The default API key (`dev-key-12345`) is for local development only. In
  production, set it via the `CREDIT_API_KEY` environment variable and keep
  `app.py`'s `API_KEY` in sync (or load both from a shared secret store).
- The model is trained on synthetic data with a realistic scoring rule
  (credit score, debt-to-income ratio, income, employment tenure, age) —
  swap `generate_synthetic_data()` in `model.py` for real historical data
  when available.
