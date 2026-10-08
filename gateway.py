"""
gateway.py — QuantumShield API Gateway (Render.com)

Lightweight proxy that forwards all API requests to the ML service on Railway.
This runs on Render.com free tier (512 MB RAM) — no heavy ML imports needed.

Architecture:
  Browser → Firebase (frontend) → Render (this gateway) → Railway (ML service)
"""

import os
import time
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import requests as http_requests

app = Flask(__name__)
CORS(app)

# Railway ML service URL — set in Render dashboard environment variables
ML_SERVICE_URL = os.environ.get('ML_SERVICE_URL', 'http://localhost:8080')

# In-memory history (lightweight, stays on gateway)
history_records = []


# ═══════════════════════════════════════════════════════════════════════════════
# LOCAL ENDPOINTS (handled by gateway directly — no ML needed)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/health', methods=['GET'])
def health():
    """Gateway health check — used by cron-job.org keep-alive pinger."""
    ml_status = "unknown"
    try:
        r = http_requests.get(f"{ML_SERVICE_URL}/health", timeout=5)
        if r.status_code == 200:
            ml_status = "ok"
        else:
            ml_status = f"error ({r.status_code})"
    except Exception:
        ml_status = "unreachable"

    return jsonify({
        "status": "ok",
        "service": "quantumshield-gateway",
        "ml_service": ml_status,
        "ml_service_url": ML_SERVICE_URL,
        "version": "1.0.0"
    })


@app.route('/history', methods=['GET'])
def get_history():
    return jsonify(history_records)


@app.route('/history/clear', methods=['POST'])
def clear_history():
    global history_records
    history_records = []
    return jsonify({"status": "success", "message": "History cleared"})


# ═══════════════════════════════════════════════════════════════════════════════
# PROXY FUNCTION — forwards requests to Railway ML service
# ═══════════════════════════════════════════════════════════════════════════════

def proxy_json(path, method='POST'):
    """Proxy a JSON request to the ML service."""
    url = f"{ML_SERVICE_URL}{path}"
    try:
        if method == 'GET':
            resp = http_requests.get(url, params=request.args, timeout=300)
        else:
            resp = http_requests.post(
                url,
                json=request.get_json(silent=True),
                timeout=300
            )
        # Store simulation results in local history
        if path == '/simulate' and resp.status_code == 200:
            try:
                result = resp.json()
                data = request.get_json(silent=True) or {}
                record = {
                    "timestamp": data.get('timestamp', ''),
                    "molecule_id": data.get('molecule_id', 'inh-q1'),
                    "binding_energy": result.get("binding_energy"),
                    "final_energy": result.get("final_energy"),
                    "elapsed_time": result.get("elapsed_time"),
                    "qubits": result.get("qubits"),
                    "run_on_qpu": result.get("run_on_qpu")
                }
                history_records.append(record)
            except Exception:
                pass

        return Response(
            resp.content,
            status=resp.status_code,
            content_type=resp.headers.get('Content-Type', 'application/json')
        )
    except http_requests.exceptions.Timeout:
        return jsonify({"error": "ML service timeout — the computation is taking too long. Try again."}), 504
    except http_requests.exceptions.ConnectionError:
        return jsonify({"error": "ML service is starting up. Please wait 30 seconds and try again."}), 503
    except Exception as e:
        return jsonify({"error": f"Gateway proxy error: {str(e)}"}), 502


def proxy_multipart(path):
    """Proxy a multipart/form-data request (for file uploads like disease detection)."""
    url = f"{ML_SERVICE_URL}{path}"
    try:
        files = {}
        for key in request.files:
            f = request.files[key]
            files[key] = (f.filename, f.read(), f.content_type)

        data = {}
        for key in request.form:
            data[key] = request.form[key]

        resp = http_requests.post(url, files=files, data=data, timeout=300)
        return Response(
            resp.content,
            status=resp.status_code,
            content_type=resp.headers.get('Content-Type', 'application/json')
        )
    except http_requests.exceptions.Timeout:
        return jsonify({"error": "Disease detection timeout. Try a smaller image."}), 504
    except http_requests.exceptions.ConnectionError:
        return jsonify({"error": "ML service is starting up. Please wait 30 seconds and try again."}), 503
    except Exception as e:
        return jsonify({"error": f"Gateway proxy error: {str(e)}"}), 502


# ═══════════════════════════════════════════════════════════════════════════════
# PROXIED ENDPOINTS → Railway ML Service
# ═══════════════════════════════════════════════════════════════════════════════

# --- Core Simulation ---
@app.route('/simulate', methods=['POST'])
def simulate():
    return proxy_json('/simulate')

@app.route('/generate', methods=['POST'])
def generate():
    return proxy_json('/generate')

# --- DNA & Hardware ---
@app.route('/dna-interaction', methods=['POST'])
@app.route('/api/dna-interaction', methods=['POST'])
def dna_interaction():
    return proxy_json('/api/dna-interaction')

@app.route('/api/hardware/codesign', methods=['POST'])
def hardware_codesign():
    return proxy_json('/api/hardware/codesign')

# --- Pathogen ---
@app.route('/api/pathogen/lookup', methods=['POST', 'GET'])
def pathogen_lookup():
    if request.method == 'GET':
        return proxy_json('/api/pathogen/lookup', method='GET')
    return proxy_json('/api/pathogen/lookup')

# --- QRL ---
@app.route('/api/qrl/optimize', methods=['POST'])
def qrl_optimize():
    return proxy_json('/api/qrl/optimize')

@app.route('/api/qrl/circuit', methods=['POST'])
def qrl_circuit():
    return proxy_json('/api/qrl/circuit')

# --- Validation ---
@app.route('/api/validation/run', methods=['POST'])
def validation_run():
    return proxy_json('/api/validation/run')

@app.route('/api/validation/compare', methods=['POST'])
def validation_compare():
    return proxy_json('/api/validation/compare')

@app.route('/api/validation/wetlab', methods=['POST'])
def validation_wetlab():
    return proxy_json('/api/validation/wetlab')

# --- MD ---
@app.route('/api/md/trajectory', methods=['POST'])
def md_trajectory():
    return proxy_json('/api/md/trajectory')

# --- Disease Detection ---
@app.route('/api/disease/detect', methods=['POST'])
def disease_detect():
    return proxy_multipart('/api/disease/detect')

@app.route('/api/disease/modalities', methods=['GET'])
def disease_modalities():
    return proxy_json('/api/disease/modalities', method='GET')

@app.route('/api/disease/3d-structure', methods=['POST'])
def disease_3d_structure():
    return proxy_json('/api/disease/3d-structure')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"QuantumShield Gateway starting on port {port}")
    print(f"ML Service URL: {ML_SERVICE_URL}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
