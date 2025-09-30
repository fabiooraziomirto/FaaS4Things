import os
import json
import hmac
import time
import hashlib
import requests

# Chiave segreta usata per firmare le richieste verso il forward server
FORWARD_SECRET = os.environ.get("FORWARD_SECRET", "forward_secret_123")

# Tipo di istruzione associata a questa funzione (es. "istruzione1", "istruzione2", ecc.)
INSTRUCTION_TYPE = os.environ.get("INSTRUCTION_TYPE", "istruzione_default")

# URL del forward server (porta 3000)
FORWARD_URL = os.environ.get("FORWARD_URL", "http://10.42.1.70:3000/forward")


def handler(context, event):
    try:
        # Parsing del body in ingresso
        if isinstance(event.body, (bytes, str)):
            body_str = event.body.decode("utf-8") if isinstance(event.body, bytes) else event.body
            payload_in = json.loads(body_str)
        elif isinstance(event.body, dict):
            payload_in = event.body
        else:
            raise ValueError("Formato del body non riconosciuto")

        context.logger.info(f"Payload ricevuto: {payload_in}")

        # Aggiunge il tipo di istruzione a quello ricevuto
        payload_out = {
            "variable": payload_in.get("variable", "server1"),  # es. monk di destinazione
            "instruction": INSTRUCTION_TYPE,
            "payload": payload_in.get("payload", {})
        }

        # Serializzazione compatta per la firma
        body_str = json.dumps(payload_out, separators=(',', ':'))

        # Firma HMAC
        ts = str(int(time.time()))
        msg = f"{body_str}:{ts}".encode("utf-8")
        sig = hmac.new(FORWARD_SECRET.encode("utf-8"), msg, hashlib.sha256).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-Signature": f"sha256={sig}",
            "X-Signature-Timestamp": ts
        }

        context.logger.info(f"Inoltro istruzione '{INSTRUCTION_TYPE}' a {FORWARD_URL}")

        # Inoltra la richiesta al forward server
        response = requests.post(
            FORWARD_URL,
            headers=headers,
            data=body_str,
            timeout=10
        )

        context.logger.info(f"Forward completato con status {response.status_code}")

        return context.Response(
            body=response.text,
            status_code=response.status_code,
            headers={"Content-Type": "application/json"}
        )

    except Exception as e:
        context.logger.error(f"Errore durante il forward: {str(e)}")
        return context.Response(
            body=json.dumps({"error": "Errore interno", "message": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"}
        )
