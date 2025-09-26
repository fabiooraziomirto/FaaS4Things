#!/usr/bin/env python3
"""
Load Balancer IoT Minimale - Deploy funzioni Nuclio
Con firma HMAC-SHA256 per autenticazione
"""

from flask import Flask, request, jsonify
import requests
import logging
import time
import hmac
import hashlib
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Lista dei nodi IoT (edge workers)
NODES = [
    "http://10.42.0.164:50012",  # Proxy 1
]

# Sicurezza
LB_SECRET = os.environ.get('LB_SECRET', 'changeme')
SIGNATURE_HEADER = 'X-Signature'
TIMESTAMP_HEADER = 'X-Signature-Timestamp'
TIMESTAMP_TOLERANCE = 300  # 5 minuti

def compute_signature(secret: str, body_bytes: bytes, timestamp: int) -> str:
    msg = body_bytes + b':' + str(timestamp).encode()
    mac = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    return f"sha256={mac}"

def forward_request(node_url, endpoint, raw, timeout=30):
    ts = int(time.time())
    signature = compute_signature(LB_SECRET, raw, ts)

    headers = {
        'Content-Type': request.headers.get('Content-Type', 'application/json'),
        SIGNATURE_HEADER: signature,
        TIMESTAMP_HEADER: str(ts)
    }

    response = requests.post(
        f"{node_url}{endpoint}",
        data=raw,
        headers=headers,
        timeout=timeout
    )

    return response

def get_next_node():
    # round-robin minimale: sempre il primo disponibile
    for node in NODES:
        try:
            r = requests.get(f"{node}/health", timeout=3)
            if r.status_code == 200:
                return node
        except Exception:
            continue
    return None

@app.route('/deploy', methods=['POST'])
def deploy_inline():
    node_url = get_next_node()
    if not node_url:
        return jsonify({'error': 'Nessun nodo disponibile'}), 503
    raw = request.get_data()
    if not raw:
        return jsonify({'error': 'Body mancante'}), 400

    response = forward_request(node_url, "/deploy", raw, timeout=30)
    return jsonify({
        'status': 'success' if response.status_code == 200 else 'error',
        'node': node_url,
        'response': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
    }), response.status_code

@app.route('/deploy-github', methods=['POST'])
def deploy_github():
    node_url = get_next_node()
    if not node_url:
        return jsonify({'error': 'Nessun nodo disponibile'}), 503
    raw = request.get_data()
    if not raw:
        return jsonify({'error': 'Body mancante'}), 400

    response = forward_request(node_url, "/deploy-github", raw, timeout=120)
    return jsonify({
        'status': 'success' if response.status_code == 200 else 'error',
        'node': node_url,
        'response': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
    }), response.status_code

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        'status': 'running',
        'nodes': NODES,
        'supported_endpoints': [
            '/deploy',
            '/deploy-github',
            '/status'
        ]
    })

if __name__ == '__main__':
    logger.info("Avvio Load Balancer con firma HMAC...")
    logger.info(f"Nodi configurati: {NODES}")
    app.run(
        host='0.0.0.0',
        port=5002,
        debug=False
    )
