# quadratic_operations.py
import json
import random
import time

def handler(context, event):
    """
    Handler principale per Nuctl.
    Event può contenere:
    - size: dimensione dell'array (default: 10)
    - max_val: valore massimo per gli elementi (default: 100)
    - array: array personalizzato da ordinare (opzionale)
    """

    context.logger.info('Eseguendo Bubble Sort O(n²)...')

    # Imposta seed per rendere l'array casuale sempre diverso
    random.seed(time.time_ns())

    try:
        # Parsare il body JSON dall'evento
        event_body = json.loads(event.body.decode('utf-8')) if event.body else {}

        size = event_body.get('size', 10)
        max_val = event_body.get('max_val', 100)
        custom_array = event_body.get('array', None)

        context.logger.info(f'Parametri ricevuti - size: {size}, max_val: {max_val}')

        if custom_array:
            data = custom_array
            context.logger.info(f'Usando array personalizzato di {len(data)} elementi')
        else:
            data = genera_array_random(size, max_val)
            context.logger.info(f'Generato array casuale di {len(data)} elementi')

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

# Funzione per generare un array casuale
def genera_array_random(size, max_val):
    return [random.randint(0, max_val) for _ in range(size)]


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

    # Test con parametri default
    test_event = type("Event", (), {"body": json.dumps({"size": 10, "max_val": 100}).encode('utf-8')})()
    handler(mock_context, test_event)

    print("\n" + "="*50 + "\n")

    # Test con array personalizzato
    test_event_custom = type("Event", (), {"body": json.dumps({"array": [5, 3, 8, 1, 2]}).encode('utf-8')})()
    handler(mock_context, test_event_custom)
