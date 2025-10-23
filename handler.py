import os
import json
import hmac
import time
import hashlib
import requests

# Usa SHARED_SECRET per coerenza
SHARED_SECRET = os.environ.get("SHARED_SECRET", "changeme")

# Tipo di istruzione associata a questa funzione
INSTRUCTION_TYPE = os.environ.get("INSTRUCTION_TYPE", "istruzione_default")

# URL del forward server (porta 3000)
FORWARD_URL = os.environ.get("FORWARD_URL", "http://10.42.1.72:3000/forward")


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

        # CORREZIONE: Usa "function" invece di "instruction" per compatibilità con edge-server.js
        payload_out = {
            "variable": payload_in.get("variable", "server1"),
            "function": INSTRUCTION_TYPE  # ← Cambiato da "instruction" a "function"
        }
        
        # Aggiungi altri campi dal payload originale se presenti
        if "payload" in payload_in and isinstance(payload_in["payload"], dict):
            payload_out.update(payload_in["payload"])

        # Serializzazione compatta per la firma
        body_str = json.dumps(payload_out, separators=(',', ':'))
        body_bytes = body_str.encode("utf-8")

        # Firma HMAC
        ts = str(int(time.time()))
        msg = body_bytes + b':' + ts.encode("utf-8")
        sig = hmac.new(SHARED_SECRET.encode("utf-8"), msg, hashlib.sha256).hexdigest()

        # Header in minuscolo
        headers = {
            "Content-Type": "application/json",
            "x-signature": f"sha256={sig}",
            "x-signature-timestamp": ts
        }

        context.logger.info(f"Inoltro istruzione '{INSTRUCTION_TYPE}' a {FORWARD_URL}")
        context.logger.info(f"Body: {body_str}")
        context.logger.info(f"Timestamp: {ts}")
        context.logger.info(f"Signature: sha256={sig}")

        # Inoltra la richiesta al forward server
        response = requests.post(
            FORWARD_URL,
            headers=headers,
            data=body_bytes,
            timeout=10
        )

        context.logger.info(f"Forward completato con status {response.status_code}")
        context.logger.info(f"Response body: {response.text}")

        return context.Response(
            body=response.text,
            status_code=response.status_code,
            headers={"Content-Type": "application/json"}
        )

    except Exception as e:
        context.logger.error(f"Errore durante il forward: {str(e)}")
        import traceback
        context.logger.error(traceback.format_exc())
        return context.Response(
            body=json.dumps({"error": "Errore interno", "message": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"}
        )
