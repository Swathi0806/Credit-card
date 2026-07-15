#!/usr/bin/env bash
# Starts the Flask prediction API in the background, then launches the
# Streamlit UI in the foreground. Ctrl+C stops the UI; kill the API
# separately if needed (pkill -f api.py).
set -e

echo "Training/checking model..."
python3 model.py

echo "Starting API server on port 5001..."
python3 api.py &
API_PID=$!
sleep 2

echo "API started (PID $API_PID). Launching Streamlit UI..."
streamlit run app.py

# Clean up the API process when Streamlit exits
kill $API_PID 2>/dev/null || true
