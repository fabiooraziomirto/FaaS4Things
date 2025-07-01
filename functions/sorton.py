# linear_operations.py - Handler compatibile con Nuctl
import json
import random
import time

def handler(context, event):
    """
    Handler principale per Nuctl.
    Event può contenere:
    - size: dimensione dell'array (default: 10)
    - max_val: valore massimo per gli elementi (default: 100)
    - array: array personalizzato da sommare (opzionale)
    """
    
    context.logger.info('Eseguendo operazioni lineari O(n)...')
    
    # Imposta seed per rendere l'array casuale sempre diverso
    random.seed(time.time_ns())
    
    try:
        # Parse degli argomenti dall'event
        # In Nuctl, i dati possono essere in event.body se è una POST request
        # o negli headers/query parameters per GET
        event_data = {}
        
        # Prova a parsare il body se presente
        if hasattr(event, 'body') and event.body:
            try:
                event_data = json.loads(event.body)
            except:
                event_data = {}
        
        # Usa valori di default se non sono presenti nell'event
        size = event_data.get('size', 10) if isinstance(event_data, dict) else 10
        max_val = event_data.get('max_val', 100) if isinstance(event_data, dict) else 100
        custom_array = event_data.get('array', None) if isinstance(event_data, dict) else None
        
        context.logger.info(f'Parametri ricevuti - size: {size}, max_val: {max_val}')
        
        # Usa array personalizzato se fornito, altrimenti genera uno casuale
        if custom_array:
            data = custom_array
            context.logger.info(f'Usando array personalizzato di {len(data)} elementi')
        else:
            data = genera_array_random(size, max_val)
            context.logger.info(f'Generato array casuale di {len(data)} elementi')
        
        # Calcola la somma con complessità O(n)
        start_time = time.time()
        result = sum_array(data)
        end_time = time.time()
        execution_time = end_time - start_time
        
        context.logger.info(f'Somma calcolata: {result} in {execution_time:.6f} secondi')
        
        # Prepara la risposta
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

# Funzione O(n): somma tutti gli elementi dell'array
def sum_array(arr):
    """Calcola la somma di tutti gli elementi dell'array con complessità O(n)"""
    total = 0
    for val in arr:
        total += val
    return total

# Funzione per generare un array casuale
def genera_array_random(size, max_val):
    """Genera un array di numeri casuali"""
    return [random.randint(0, max_val) for _ in range(size)]

# Test locale (non verrà eseguito su Nuctl)
if __name__ == "__main__":
    # Simulazione del context per test locale
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
    
    # Test con parametri di default
    mock_context = MockContext()
    test_event = {"size": 10, "max_val": 100}
    handler(mock_context, test_event)
    
    print("\n" + "="*50 + "\n")
    
    # Test con array personalizzato
    test_event_custom = {"array": [1, 2, 3, 4, 5, 10, 20, 30]}
    handler(mock_context, test_event_custom)
