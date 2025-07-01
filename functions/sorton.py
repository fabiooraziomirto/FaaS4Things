import json
import time

def handler(context, event):
    context.logger.info('Eseguendo operazioni lineari O(n) su array statico di 100 elementi...')

    # Array statico di 100 elementi (esempio con numeri da 0 a 99)
    data = list(range(100))
    context.logger.info(f'Usando array statico di {len(data)} elementi')

    try:
        start_time = time.time()
        result = sum_array(data)
        end_time = time.time()
        execution_time = end_time - start_time

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
        error_msg = f"Errore durante l'elaborazione delle operazioni lineari: {str(e)}"
        context.logger.error(error_msg)

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

def sum_array(arr):
    total = 0
    for val in arr:
        total += val
    return total
