import json
import time
import psutil
import os
import threading
from typing import Dict, List, Tuple

def handler(context, event):
    context.logger.info('Eseguendo operazioni lineari O(n) su array statico con monitoraggio CPU e RAM...')
    
    # Array statico di 1000 elementi
    data = list(range(1000))
    context.logger.info(f'Usando array statico di {len(data)} elementi')
    
    try:
        # Timestamp di inizio per tracking
        start_timestamp = time.time()
        
        # Inizializza il monitoraggio delle risorse
        resource_monitor = ResourceMonitor()
        
        # Avvia il monitoraggio
        resource_monitor.start_monitoring()
        
        # Misura le risorse prima dell'esecuzione
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        initial_cpu = psutil.cpu_percent(interval=0.1)
        
        start_time = time.time()
        result = sum_array(data)
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
        
        context.logger.info(f'Somma calcolata: {result} in {execution_time:.6f} secondi')
        context.logger.info(f'CPU media: {cpu_stats["average"]:.2f}%, RAM media: {memory_stats["average"]:.2f} MB')
        
        # Determina lo status dell'esecuzione
        status = "success"
        if execution_time > 1.0:  # Se impiega più di 1 secondo
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
                "size": len(data),
                "sum": result,
                "complexity": "O(n)"
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
                "function_name": "on2",
                "array_type": "static",
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
        error_msg = f"Errore durante l'elaborazione delle operazioni lineari: {str(e)}"
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

def sum_array(arr):
    """Calcola la somma di un array con complessità O(n)"""
    total = 0
    for val in arr:
        total += val
        # Aggiunge un micro-delay per rendere il calcolo più visibile nei test
        time.sleep(0.00001)  # 10 microsecondi per elemento
    return total

class ResourceMonitor:
    """Classe per monitorare CPU e RAM durante l'esecuzione"""
    
    def __init__(self, interval: float = 0.05):  # Intervallo ridotto per più campioni
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
        while self.monitoring:
            try:
                # CPU usage (percentuale del sistema)
                cpu_percent = psutil.cpu_percent(interval=None)
                if cpu_percent > 0:  # Solo se abbiamo una lettura valida
                    self.cpu_readings.append(cpu_percent)
                
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
