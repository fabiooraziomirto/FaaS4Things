import json
import time

def handler(context, event):
    """
    Handler semplificato per Nuctl.
    Esegue Bubble Sort su un array statico decrescente e misura solo il tempo di esecuzione.
    """
    context.logger.info('Eseguendo Bubble Sort O(n²) su array statico decrescente...')

    # Array statico di 1000 elementi in ordine decrescente
    data = list(range(999, -1, -1))
    context.logger.info(f'Array di {len(data)} elementi generato in ordine decrescente')

    try:
        # Timestamp di inizio
        start_timestamp = time.time()

        # Esecuzione del bubble sort con misurazione del tempo
        start_time = time.time()
        bubble_sort(data)
        end_time = time.time()

        execution_time = end_time - start_time

        context.logger.info(f'Array ordinato in {execution_time:.6f} secondi')

        # Determina lo stato in base al tempo
        status = "success" if execution_time <= 5.0 else "slow"

        response_body = {
            "status": status,
            "execution_time": execution_time,
            "array_info": {
                "original_size": len(data),
                "sorted_first_10": data[:10],
                "sorted_last_10": data[-10:],
                "complexity": "O(n²)",
                "algorithm": "bubble_sort"
            },
            "performance": {
                "execution_time_seconds": execution_time,
                "start_timestamp": start_timestamp,
                "end_timestamp": time.time()
            },
            "test_metadata": {
                "request_id": f"req_{int(start_timestamp * 1000)}",
                "function_name": "bubble_sort_o2",
                "array_type": "static_descending"
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
        context.logger.error(f"Errore: {str(e)}")
        return context.Response(
            body=json.dumps({
                "status": "error",
                "execution_time": 0,
                "error": str(e),
                "timestamp": time.time(),
                "error_type": type(e).__name__
            }, indent=2),
            headers={
                "Content-Type": "application/json",
                "X-Status": "error"
            },
            content_type='application/json',
            status_code=500
        )

def bubble_sort(arr):
    """Bubble Sort con complessità O(n²)"""
    n = len(arr)
    for i in range(n - 1):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]

# Test locale standalone
if __name__ == "__main__":
    class MockContext:
        class Logger:
            def info(self, msg): print(f"INFO: {msg}")
            def error(self, msg): print(f"ERROR: {msg}")
        class Response:
            def __init__(self, body, headers, content_type, status_code):
                self.body = body
                print(body)
                print(f"Status Code: {status_code}")
        def __init__(self):
            self.logger = self.Logger()
            self.Response = self.Response

    mock_context = MockContext()
    test_event = type("Event", (), {"body": None})()
    handler(mock_context, test_event)
