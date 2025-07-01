import json
import time

def handler(context, event):
    """
    Handler principale per Nuctl.
    Usa sempre un array statico di 100 elementi ordinati in modo decrescente (caso peggiore).
    """

    context.logger.info('Eseguendo Bubble Sort O(n²) su array statico decrescente di 100 elementi...')

    # Array statico di 100 elementi in ordine decrescente (da 99 a 0)
    data = list(range(999, -1, -1))
    context.logger.info(f'Usando array statico di {len(data)} elementi ordinati in modo decrescente')

    try:
        start_time = time.time()
        bubble_sort(data)
        end_time = time.time()
        execution_time = end_time - start_time

        context.logger.info(f'Array ordinato in {execution_time:.6f} secondi')

        response_body = {
            "original_array_size": len(data),
            "sorted_array": data,
            "execution_time_seconds": execution_time,
            "complexity": "O(n²)",
            "timestamp": time.time()
        }

        return context.Response(
            body=json.dumps(response_body, indent=2),
            headers={"Content-Type": "application/json"},
            content_type='application/json',
            status_code=200
        )

    except Exception as e:
        error_msg = f"Errore durante l'elaborazione delle operazioni quadratiche: {str(e)}"
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


# Funzione O(n²): Bubble Sort
def bubble_sort(arr):
    n = len(arr)
    for i in range(n - 1):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]


# Test locale (non eseguito su Nuctl)
if __name__ == "__main__":
    class MockContext:
        class Logger:
            def info(self, msg): print(f"INFO: {msg}")
            def error(self, msg): print(f"ERROR: {msg}")

        class Response:
            def __init__(self, body, headers, content_type, status_code):
                self.body = body
                self.headers = headers
                self.content_type = content_type
                self.status_code = status_code
                print(f"Response [{status_code}]: {body}")

        def __init__(self):
            self.logger = self.Logger()
            self.Response = self.Response

    mock_context = MockContext()

    # Test con array statico decrescente
    test_event = type("Event", (), {"body": None})()
    handler(mock_context, test_event)
