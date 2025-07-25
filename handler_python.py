import requests
import json
 
def handler(context, event):
    try:
        # Dati ricevuti dalla richiesta (es. POST body)
        payload = event.body.decode('utf-8')
        context.logger.info(f"Received event: {payload}")
 
        # Forward al server Node.js
        response = requests.get(
            "http://10.42.0.237:3000/health"#,
            #data=payload,
            #headers={"Content-Type": "application/json"}
        )
 
        # Log e risposta
        context.logger.info(f"Forwarded to Node.js. Status: {response.status_code}")
        return context.Response(body=f"Forwarded with status {response.status_code}", status_code=200)
 
    except Exception as e:
        context.logger.error(f"Error: {str(e)}")
        return context.Response(body="Error forwarding request", status_code=500)
