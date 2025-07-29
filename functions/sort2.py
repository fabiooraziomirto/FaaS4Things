import json
import time

def handler(context, event):
    context.logger.info('Eseguendo operazioni lineari O(n) su array statico...')

    data = list(range(1000))
    context.logger.info(f'Usando array statico di {len(data)} elementi')

    try:
        start_time = time.time()
        result = sum(data)
        execution_time = time.time() - start_time

        context.logger.info(f'Somma calcolata: {result} in {execution_time:.6f} secondi')

        response_body = {
            "array": data,
            "sum": result,
            "array_size": len(data),
            "execution_time_seconds": execution_time,
            "complexity": "O(n)",
            "timestamp": time.time()
        }

        return context.Response(
            body=json.dumps(response_body, indent=2),
            headers={"Content-Type": "application/json"},
            content_type='application/json',
            status_code=200
        )

    except Exception as e:
        context.logger.error(f"Errore durante l'elaborazione: {e}")

        error_response = {
            "error": str(e),
            "message": "Errore durante l'elaborazione",
            "timestamp": time.time()
        }

        return context.Response(
            body=json.dumps(error_response, indent=2),
            headers={"Content-Type": "application/json"},
            content_type='application/json',
            status_code=500
        )
