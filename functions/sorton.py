import json
import random
import time

def handler(context, event):
    context.logger.info('Eseguendo operazioni lineari O(n)...')
    
    random.seed(time.time_ns())
    
    try:
        # Parsare il body JSON dall'evento
        event_body = json.loads(event.body.decode('utf-8')) if event.body else {}
        
        size = event_body.get('size', 100)
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

def genera_array_random(size, max_val):
    return [random.randint(0, max_val) for _ in range(size)]
