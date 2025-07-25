import json
import requests
 
def handler(context, event):
    try:
        # Verifica il tipo di event.body e decodifica se necessario
        if isinstance(event.body, (bytes, str)):
            body_str = event.body.decode("utf-8") if isinstance(event.body, bytes) else event.body
            payload = json.loads(body_str)
        elif isinstance(event.body, dict):
            payload = event.body
        else:
            raise ValueError("Formato del body non riconosciuto")
 
        context.logger.info(f"Payload ricevuto: {payload}")
 
        # Inoltra la richiesta al pod Node.js
        response = requests.post(
            "http://10.42.0.240:3000/forward",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=10
        )
 
        context.logger.info(f"Forward riuscito con status {response.status_code}")
 
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
