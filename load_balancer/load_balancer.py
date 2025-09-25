#!/usr/bin/env python3
"""
Load Balancer IoT Minimale - Deploy funzioni Nuclio
Con firma HMAC-SHA256 simmetrica
"""

from flask import Flask, request, jsonify
import requests
import logging
import time
import hmac
import hashlib
import os
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Secret condivisa (crittografia simmetrica, 256 bit esadecimale)
SECRET_KEY = bytes.fromhex(os.environ.get("SHARED_SECRET", "00"*32))

# Lista dei nodi IoT
NODES = [
    "http://10.42.0.164:50012",  # Proxy 1
]

current_node = 0


def sign_payload(payload: dict) -> str:
    """Genera la firma HMAC-SHA256 del payload JSON con chiave simmetrica"""
    payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
    signature = hmac.new(SECRET_KEY, payload_bytes, hashlib.sha256).hexdigest()
    return signature


def get_next_node():
    """Seleziona il nodo meno carico"""
    nodes_load = []

    for node in NODES:
        try:
            start_time = time.time()
            response = requests.get(f"{node}/functions", timeout=5)
            response_time = time.time() - start_time

            if response.status_code == 200:
                functions = response.json()
                num_functions = len(functions) if isinstance(functions, list) else 0
                nodes_load.append((node, num_functions, response_time))
            else:
                logger.warning(f"Nodo {node} non ha risposto correttamente a /functions")
        except Exception as e:
            logger.warning(f"Errore contattando il nodo {node}: {e}")
            continue

    if not nodes_load:
        return None

    min_count = min(load for _, load, _ in nodes_load)
    least_loaded_nodes = [(node, response_time) for node, count, response_time in nodes_load if count == min_count]

    selected_node = min(least_loaded_nodes, key=lambda x: x[1])[0]
    return selected_node


@app.route('/deploy', methods=['POST'])
def deploy_function():
    """Deploy da codice inline"""
    try:
        node_url = get_next_node()
        if not node_url:
            return jsonify({'error': 'Nessun nodo disponibile'}), 503

        function_data = request.get_json()
        if not function_data:
            return jsonify({'error': 'Dati funzione mancanti'}), 400

        signature = sign_payload(function_data)

        response = requests.post(
            f"{node_url}/deploy",
            json=function_data,
            headers={"X-Signature": signature},
            timeout=30
        )

        return jsonify({
            'status': 'success' if response.status_code == 200 else 'error',
            'node': node_url,
            'response': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        }), response.status_code

    except Exception as e:
        logger.error(f"Errore deploy: {e}")
        return jsonify({'error': 'Errore interno'}), 500


@app.route('/deploy-github', methods=['POST'])
def deploy_function_from_github():
    """Deploy da repository GitHub"""
    try:
        node_url = get_next_node()
        if not node_url:
            return jsonify({'error': 'Nessun nodo disponibile'}), 503

        github_data = request.get_json()
        if not github_data:
            return jsonify({'error': 'Dati GitHub mancanti'}), 400

        signature = sign_payload(github_data)

        response = requests.post(
            f"{node_url}/deploy-github",
            json=github_data,
            headers={"X-Signature": signature},
            timeout=120
        )

        return jsonify({
            'status': 'success' if response.status_code == 200 else 'error',
            'node': node_url,
            'response': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        }), response.status_code

    except Exception as e:
        logger.error(f"Errore deploy GitHub: {e}")
        return jsonify({'error': 'Errore interno'}), 500


@app.route('/deploy-remote', methods=['POST'])
def deploy_remote():
    """
    Deploy di una funzione su un nodo remoto scelto manualmente o round-robin
    JSON richiesto:
    {
        "nodeUrl": "http://10.42.0.164:50012",  # opzionale
        "type": "github" | "inline",
        "data": {...}
    }
    """
    try:
        req_data = request.get_json()
        if not req_data:
            return jsonify({'error': 'Dati mancanti'}), 400

        node_url = req_data.get('nodeUrl') or get_next_node()
        if not node_url:
            return jsonify({'error': 'Nessun nodo disponibile'}), 503

        deploy_type = req_data.get('type')
        deploy_data = req_data.get('data')
        if not deploy_type or not deploy_data:
            return jsonify({'error': 'Campi "type" o "data" mancanti'}), 400

        signature = sign_payload(deploy_data)

        if deploy_type == 'github':
            endpoint = '/deploy-github'
            timeout = 120
        elif deploy_type == 'inline':
            endpoint = '/deploy'
            timeout = 30
        else:
            return jsonify({'error': 'Tipo di deploy non valido'}), 400

        response = requests.post(
            f"{node_url}{endpoint}",
            json=deploy_data,
            headers={"X-Signature": signature},
            timeout=timeout
        )

        return jsonify({
            'status': 'success' if response.status_code == 200 else 'error',
            'node': node_url,
            'response': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        }), response.status_code

    except Exception as e:
        logger.error(f"Errore deploy remoto: {e}")
        return jsonify({'error': 'Errore interno'}), 500


@app.route('/deploy-github-to', methods=['POST'])
def deploy_github_to_specific_node():
    """Deploy da GitHub su un nodo specifico"""
    try:
        data = request.get_json()
        if not data or 'nodeUrl' not in data:
            return jsonify({'error': 'Campo "nodeUrl" mancante'}), 400

        node_url = data.pop('nodeUrl')
        signature = sign_payload(data)

        response = requests.post(
            f"{node_url}/deploy-github",
            json=data,
            headers={"X-Signature": signature},
            timeout=120
        )

        return jsonify({
            'status': 'success' if response.status_code == 200 else 'error',
            'node': node_url,
            'response': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        }), response.status_code

    except Exception as e:
        logger.error(f"Errore deploy GitHub mirato: {e}")
        return jsonify({'error': 'Errore interno'}), 500


@app.route('/deploy-to', methods=['POST'])
def deploy_to_specific_node():
    """Deploy inline su un nodo specifico"""
    try:
        data = request.get_json()
        if not data or 'nodeUrl' not in data:
            return jsonify({'error': 'Campo "nodeUrl" mancante'}), 400

        node_url = data.pop('nodeUrl')
        signature = sign_payload(data)

        response = requests.post(
            f"{node_url}/deploy",
            json=data,
            headers={"X-Signature": signature},
            timeout=30
        )

        return jsonify({
            'status': 'success' if response.status_code == 200 else 'error',
            'node': node_url,
            'response': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        }), response.status_code

    except Exception as e:
        logger.error(f"Errore deploy mirato: {e}")
        return jsonify({'error': 'Errore interno'}), 500


@app.route('/nodes/health', methods=['GET'])
def check_nodes_health():
    """Verifica lo stato di salute di tutti i nodi"""
    nodes_status = []
    for node in NODES:
        try:
            response = requests.get(f"{node}/health", timeout=5)
            nodes_status.append({
                'node': node,
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response.elapsed.total_seconds(),
                'details': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            })
        except Exception as e:
            nodes_status.append({
                'node': node,
                'status': 'unreachable',
                'error': str(e)
            })

    return jsonify({
        'total_nodes': len(NODES),
        'healthy_nodes': len([n for n in nodes_status if n['status'] == 'healthy']),
        'nodes': nodes_status
    })


@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        'status': 'running',
        'nodes': NODES
    })


if __name__ == '__main__':
    logger.info("Avvio Load Balancer con firma HMAC...")
    app.run(
        host='0.0.0.0',
        port=5002,
        debug=False
    )
