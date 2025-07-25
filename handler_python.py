import json
import requests
 
def handler(context, event):
    try:
        payload = event.body  # già un dizionario JSON
        context.logger.info(f"Payload ricevuto: {payload}")
 
        response = requests.post(
            "http://10.42.0.237:3000/forward",
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
