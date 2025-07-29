#!/usr/bin/env python3
"""
Script per misurare la latenza delle richieste HTTP POST
VM Client - Esegue 10 batch da 100 iterazioni ciascuno
"""

import requests
import time
import csv
import socket
from datetime import datetime
import statistics

# Configurazione
URL = "http://10.42.0.131:50012/function/on2"
SERVER_IP = "192.168.100.42"
SYNC_PORT = 9999
BATCHES = 10
ITERATIONS_PER_BATCH = 100
RESULTS_FILE = f"latency_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
SUMMARY_FILE = f"latency_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

def send_signal(message):
    """Invia un messaggio di sincronizzazione al server"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((SERVER_IP, SYNC_PORT))
            sock.send(message.encode())
        print(f"Segnale '{message}' inviato a {SERVER_IP}:{SYNC_PORT}")
        return True
    except Exception as e:
        print(f"Errore nell'invio del segnale '{message}': {e}")
        return False

import time
import requests
import json
import re

import time
import requests
import json
import re

def make_request():
    """Esegue una singola richiesta POST e misura la latenza"""
    start_time = time.time()
    try:
        response = requests.post(URL, json={"input": "test"}, headers={"Content-Type": "application/json"}, timeout=30)
        end_time = time.time()
        latency = (end_time - start_time) * 1000  # in ms
        success = response.status_code == 200
        status_code = response.status_code

        execution_time = 0
        function_status = "unknown"

        if success:
            # Provo a leggere header X-Execution-Time
            x_exec_time = response.headers.get("X-Execution-Time")
            if x_exec_time is not None:
                try:
                    execution_time = float(x_exec_time) * 1000  # sec -> ms
                except Exception:
                    execution_time = 0

            # Se header non valido o assente, fallback al json
            if execution_time == 0:
                try:
                    data = response.json()

                    # Estraggo JSON interno da response.result
                    result_str = data.get("response", {}).get("result", "")

                    match = re.search(r'({\s*"status"\s*:\s*"success".*})', result_str, re.DOTALL)
                    if match:
                        inner_json_str = match.group(1)
                        inner_data = json.loads(inner_json_str)
                        performance = inner_data.get("performance", {})
                        execution_time = performance.get("execution_time_seconds", 0) * 1000
                        function_status = inner_data.get("status", "unknown")
                    else:
                        execution_time = 0

                    # Se ancora zero, prova campo execution_time in root JSON
                    if execution_time == 0:
                        execution_time = data.get("execution_time", 0) * 1000
                    function_status = data.get("status", function_status)

                except Exception:
                    pass

        return {
            'timestamp': end_time,
            'latency_ms': latency,
            'function_execution_ms': execution_time,
            'function_status': function_status,
            'success': success,
            'status_code': status_code
        }

    except requests.exceptions.RequestException:
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        return {
            'timestamp': end_time,
            'latency_ms': latency,
            'function_execution_ms': 0,
            'function_status': "error",
            'success': False,
            'status_code': 0
        }

def run_batch(batch_number):
    """Esegue un batch di richieste"""
    print(f"Avvio batch {batch_number + 1}/{BATCHES}")
    batch_results = []

    for i in range(ITERATIONS_PER_BATCH):
        result = make_request()
        result['batch'] = batch_number + 1
        result['iteration'] = i + 1
        batch_results.append(result)

        if (i + 1) % 10 == 0:
            print(f"  {i + 1}/{ITERATIONS_PER_BATCH} iterazioni completate")

    return batch_results

def save_results(results):
    """Salva i risultati dettagliati in CSV"""
    with open(RESULTS_FILE, 'w', newline='') as f:
        fieldnames = ['batch', 'iteration', 'timestamp', 'latency_ms', 'function_execution_ms', 'function_status', 'success', 'status_code']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

def calculate_and_save_summary(results):
    """Calcola statistiche riassuntive e salva in CSV"""
    successful = [r for r in results if r['success']]
    if not successful:
        print("Nessuna richiesta riuscita.")
        return

    latencies = [r['latency_ms'] for r in successful]

    # Filtra solo execution_time > 0 per statistiche tempo funzione
    exec_times = [r['function_execution_ms'] for r in successful if r['function_execution_ms'] > 0]

    # Statistiche per batch
    batch_stats = []
    for batch_num in range(1, BATCHES + 1):
        batch = [r for r in successful if r['batch'] == batch_num]
        if not batch:
            continue
        bl = [r['latency_ms'] for r in batch]
        be = [r['function_execution_ms'] for r in batch if r['function_execution_ms'] > 0]
        batch_stats.append({
            'batch': batch_num,
            'count': len(batch),
            'latency_mean_ms': statistics.mean(bl),
            'latency_median_ms': statistics.median(bl),
            'latency_min_ms': min(bl),
            'latency_max_ms': max(bl),
            'latency_std_dev_ms': statistics.stdev(bl) if len(bl) > 1 else 0,
            'latency_p95_ms': sorted(bl)[int(0.95 * len(bl)) - 1],
            'latency_p99_ms': sorted(bl)[int(0.99 * len(bl)) - 1],
            'function_time_mean_ms': statistics.mean(be) if be else 0,
            'function_time_median_ms': statistics.median(be) if be else 0,
            'function_time_min_ms': min(be) if be else 0,
            'function_time_max_ms': max(be) if be else 0,
            'function_time_std_dev_ms': statistics.stdev(be) if len(be) > 1 else 0,
        })

    # Statistiche globali
    print("\n=== STATISTICHE GLOBALI ===")
    print(f"Richieste totali: {len(results)}")
    print(f"Richieste riuscite: {len(successful)}")
    print(f"Tasso di successo: {len(successful)/len(results)*100:.2f}%")

    print("\n--- LATENZA ---")
    print(f"Media: {statistics.mean(latencies):.2f} ms")
    print(f"Mediana: {statistics.median(latencies):.2f} ms")
    print(f"Min: {min(latencies):.2f} ms")
    print(f"Max: {max(latencies):.2f} ms")
    print(f"Deviazione Std: {statistics.stdev(latencies) if len(latencies) > 1 else 0:.2f} ms")
    print(f"P95: {sorted(latencies)[int(0.95 * len(latencies)) - 1]:.2f} ms")
    print(f"P99: {sorted(latencies)[int(0.99 * len(latencies)) - 1]:.2f} ms")

    print("\n--- TEMPO DI ESECUZIONE FUNZIONE ---")
    if exec_times:
        print(f"Media: {statistics.mean(exec_times):.2f} ms")
        print(f"Mediana: {statistics.median(exec_times):.2f} ms")
        print(f"Min: {min(exec_times):.2f} ms")
        print(f"Max: {max(exec_times):.2f} ms")
        print(f"Deviazione Std: {statistics.stdev(exec_times) if len(exec_times) > 1 else 0:.2f} ms")
    else:
        print("Nessun tempo di esecuzione funzione valido disponibile.")

    # Salva CSV riassunto per batch
    with open(SUMMARY_FILE, 'w', newline='') as f:
        fieldnames = list(batch_stats[0].keys()) if batch_stats else []
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(batch_stats)

def main():
    try:
        print("=== CLIENT TEST LATENZA ===")
        print(f"URL: {URL}")
        print(f"Configurazione: {BATCHES} batch x {ITERATIONS_PER_BATCH} iterazioni")
        print(f"File risultati: {RESULTS_FILE}")
        print(f"File statistiche: {SUMMARY_FILE}")

        if not send_signal("START_TEST"):
            print("⚠️ Impossibile contattare il server monitor. Continuo comunque...")

        time.sleep(3)

        all_results = []
        start = time.time()

        for b in range(BATCHES):
            all_results.extend(run_batch(b))
            if b < BATCHES - 1:
                time.sleep(2)

        end = time.time()
        duration = end - start

        print("\n=== TEST COMPLETATO ===")
        print(f"Durata totale: {duration:.2f} secondi")
        print(f"Throughput medio: {len(all_results)/duration:.2f} richieste/sec")

        save_results(all_results)
        calculate_and_save_summary(all_results)

        print(f"\nRisultati salvati in:\n- {RESULTS_FILE}\n- {SUMMARY_FILE}")

    except KeyboardInterrupt:
        print("\nInterrotto dall'utente.")
    finally:
        send_signal("STOP_TEST")

if __name__ == "__main__":
    main()
