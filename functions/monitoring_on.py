import json
import time
from typing import List

def handler(context, event):
    context.logger.info('Eseguendo operazioni lineari O(n) su array statico...')
    
    # Array statico di 1000 elementi
    data = list(range(1000))
    context.logger.info(f'Usando array statico di {len(data)} elementi')
    
    try:
        start_timestamp = time.time()

        # Calcolo
        start_time = time.time()
        result = sum_array(data)
        end_time = time.time()

        execution_time = end_time - start_time
        status = "success" if execution_time <= 1.0 else "slow"

        response_body = {
            "status": status,
            "execution_time": execution_time,
            "array_info": {
                "size": len(data),
                "sum": result,
                "complexity": "O(n)",
                "algorithm": "linear_sum"
            },
            "performance": {
                "execution_time_seconds": execution_time,
                "timestamp": start_timestamp,
                "end_timestamp": time.time()
            },
            "test_metadata": {
                "request_id": f"req_{int(start_timestamp * 1000)}",
                "function_name": "linear_sum_on",
                "array_type": "static_ascending"
            }
        }

        return context.Response(
            body=json.dumps(response_body, indent=2),
            headers={
                "Content-Type": "application/json",
                "X-Execution-Time": str(execution_time),
                "X-Status": status
            },
            content_type='application/json',
            status_code=200
        )

    except Exception as e:
        error_msg = f"Errore durante l'elaborazione delle operazioni lineari: {str(e)}"
        context.logger.error(error_msg)
        error_response = {
            "status": "error",
            "execution_time": 0,
            "error": str(e),
            "message": "Errore durante l'elaborazione",
            "timestamp": time.time(),
            "error_type": type(e).__name__
        }
        return context.Response(
            body=json.dumps(error_response, indent=2),
            headers={
                "Content-Type": "application/json",
                "X-Status": "error"
            },
            content_type='application/json',
            status_code=500
        )

def sum_array(arr: List[int]) -> int:
    total = 0
    for val in arr:
        total += val
        time.sleep(0.00001)  # Per simulare carico
    return total
