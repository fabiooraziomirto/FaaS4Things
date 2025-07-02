import json
import time
import psutil
import os
import threading
from typing import Dict, List, Tuple

def handler(context, event):
    """
    Handler principale per Nuctl.
    Usa sempre un array statico di 1000 elementi ordinati in modo decrescente (caso peggiore).
    """
    context.logger.info('Eseguendo Bubble Sort O(n²) su array statico decrescente con monitoraggio CPU e RAM...')
    
    # Array statico di 1000 elementi in ordine decrescente (da 999 a 0)
    data = list(range(999, -1, -1))
    context.logger.info(f'Usando array statico di {len(data)} elementi ordinati in modo decrescente')
    
    try:
        # Timestamp di inizio per tracking
        start_timestamp = time.time()
        
        # Inizializza il monitoraggio delle risorse
        resource_monitor = ResourceMonitor()
        
        # Avvia il monitoraggio
        resource_monitor.start_monitoring()
        
        # Misura le risorse prima dell'esecuzione
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        # Inizializza CPU monitoring con una prima lettura
        psutil.cpu_percent(interval=0.1)  # Prima lettura di inizializzazione
        initial_cpu = psutil.cpu_percent(interval=0.1)
        
        start_time = time.time()
        bubble_sort(data)
        end_time = time.time()
        
        # Ferma il monitoraggio
        resource_monitor.stop_monitoring()
        
        # Misura le risorse dopo l'esecuzione
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        final_cpu = psutil.cpu_percent(interval=0.1)
        
        execution_time = end_time - start_time
        
        # Ottieni le statistiche del monitoraggio
        cpu_stats = resource_monitor.get_cpu_stats()
        memory_stats = resource_monitor.get_memory_stats()
        
        context.logger.info(f'Array ordinato in {execution_time:.6f} secondi')
        context.logger.info(f'CPU media: {cpu_stats["average"]:.2f}%, RAM media: {memory_stats["average"]:.2f} MB')
        
        # Determina lo status dell'esecuzione
        status = "success"
        if execution_time > 5.0:  # Se impiega più di 5 secondi (Bubble Sort è più lento)
            status = "slow"
        elif cpu_stats["max"] > 80:  # Se la CPU supera l'80%
            status = "high_cpu"
        elif memory_stats["max"] > 100:  # Se la memoria supera i 100MB
            status = "high_memory"
        
        response_body = {
            # Campi principali per lo script bash (nomi semplificati)
            "status": status,
            "execution_time": execution_time,
            "memory_used": memory_stats["average"] * 1024 * 1024,  # Converti in bytes per compatibilità
            "cpu_time": cpu_stats["average"],
            
            # Dati dettagliati originali
            "array_info": {
                "original_size": len(data),
                "sorted_first_10": data[:10],  # Primi 10 elementi per verifica
                "sorted_last_10": data[-10:],  # Ultimi 10 elementi per verifica
                "complexity": "O(n²)",
                "algorithm": "bubble_sort"
            },
            "performance": {
                "execution_time_seconds": execution_time,
                "timestamp": start_timestamp,
                "end_timestamp": time.time()
            },
            "cpu_usage": {
                "initial_percent": initial_cpu,
                "final_percent": final_cpu,
                "average_percent": cpu_stats["average"],
                "max_percent": cpu_stats["max"],
                "min_percent": cpu_stats["min"],
                "samples_count": cpu_stats["samples"]
            },
            "memory_usage": {
                "initial_mb": initial_memory,
                "final_mb": final_memory,
                "memory_delta_mb": final_memory - initial_memory,
                "average_mb": memory_stats["average"],
                "max_mb": memory_stats["max"],
                "min_mb": memory_stats["min"],
                "samples_count": memory_stats["samples"]
            },
            "system_info": {
                "cpu_count": psutil.cpu_count(),
                "cpu_count_logical": psutil.cpu_count(logical=True),
                "total_memory_mb": psutil.virtual_memory().total / 1024 / 1024,
                "available_memory_mb": psutil.virtual_memory().available / 1024 / 1024
            },
            # Metadati aggiuntivi per analisi
            "test_metadata": {
                "request_id": f"req_{int(start_timestamp * 1000)}",
                "function_name": "bubble_sort_o2",
                "array_type": "static_descending",
                "monitoring_samples": {
                    "cpu": cpu_stats["samples"],
                    "memory": memory_stats["samples"]
                }
            }
        }
        
        return context.Response(
            body=json.dumps(response_body, indent=2),
            headers={
                "Content-Type": "application/json",
                "X-Execution-Time": str(execution_time),
                "X-Memory-Used": str(memory_stats["average"]),
                "X-CPU-Usage": str(cpu_stats["average"]),
                "X-Status": status
            },
            content_type='application/json',
            status_code=200
        )
        
    except Exception as e:
        error_msg = f"Errore durante l'elaborazione delle operazioni quadratiche: {str(e)}"
        context.logger.error(error_msg)
        error_response = {
            # Campi per compatibilità con script bash
            "status": "error",
            "execution_time": 0,
            "memory_used": 0,
            "cpu_time": 0,
            
            # Dettagli errore
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

# Funzione O(n²): Bubble Sort
def bubble_sort(arr):
    """Bubble Sort con complessità O(n²)"""
    n = len(arr)
    for i in range(n - 1):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
            # Aggiunge un micro-delay per rendere il calcolo più visibile nei test
            time.sleep(0.00001)  # 10 microsecondi per confronto per essere più visibile

class ResourceMonitor:
    """Classe per monitorare CPU e RAM durante l'esecuzione"""
    
    def __init__(self, interval: float = 0.02):  # Intervallo ridotto a 20ms per più campioni
        self.interval = interval
        self.monitoring = False
        self.cpu_readings: List[float] = []
        self.memory_readings: List[float] = []
        self.monitor_thread = None
        self.process = psutil.Process()
    
    def start_monitoring(self):
        """Avvia il monitoraggio delle risorse"""
        self.monitoring = True
        self.cpu_readings = []
        self.memory_readings = []
        self.monitor_thread = threading.Thread(target=self._monitor_resources)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Ferma il monitoraggio delle risorse"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
    
    def _monitor_resources(self):
        """Metodo interno per raccogliere i dati delle risorse"""
        # Prima lettura per inizializzare psutil
        psutil.cpu_percent(interval=None)
        
        while self.monitoring:
            try:
                # CPU usage con intervallo breve per letture più accurate
                cpu_percent = psutil.cpu_percent(interval=0.01)  # 10ms invece di None
                self.cpu_readings.append(cpu_percent)  # Registra sempre, anche se 0
                
                # Memory usage del processo corrente (in MB)
                memory_mb = self.process.memory_info().rss / 1024 / 1024
                self.memory_readings.append(memory_mb)
                
                time.sleep(self.interval)
            except Exception as e:
                # Log l'errore ma continua il monitoraggio
                print(f"Error in monitoring: {e}")
                pass
    
    def get_cpu_stats(self) -> Dict[str, float]:
        """Restituisce le statistiche della CPU"""
        if not self.cpu_readings:
            return {"average": 0, "max": 0, "min": 0, "samples": 0}
        
        return {
            "average": round(sum(self.cpu_readings) / len(self.cpu_readings), 2),
            "max": round(max(self.cpu_readings), 2),
            "min": round(min(self.cpu_readings), 2),
            "samples": len(self.cpu_readings)
        }
    
    def get_memory_stats(self) -> Dict[str, float]:
        """Restituisce le statistiche della memoria"""
        if not self.memory_readings:
            return {"average": 0, "max": 0, "min": 0, "samples": 0}
        
        return {
            "average": round(sum(self.memory_readings) / len(self.memory_readings), 2),
            "max": round(max(self.memory_readings), 2),
            "min": round(min(self.memory_readings), 2),
            "samples": len(self.memory_readings)
        }

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
                print(f"Response [{status_code}]: {json.loads(body)['status'] if 'status' in json.loads(body) else 'unknown'}")
                print(f"Execution time: {json.loads(body).get('execution_time', 'N/A')} seconds")
                print(f"CPU average: {json.loads(body).get('cpu_usage', {}).get('average_percent', 'N/A')}%")
                print(f"Memory average: {json.loads(body).get('memory_usage', {}).get('average_mb', 'N/A')} MB")
        
        def __init__(self):
            self.logger = self.Logger()
            self.Response = self.Response
    
    mock_context = MockContext()
    # Test con array statico decrescente
    test_event = type("Event", (), {"body": None})()
    handler(mock_context, test_event)
