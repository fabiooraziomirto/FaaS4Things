#!/usr/bin/env python3
"""
Script per monitorare CPU e RAM durante l'esecuzione delle funzioni
VM Server - Monitora le risorse mentre il client esegue i test
"""

import psutil
import time
import csv
import os
import sys
from datetime import datetime
import threading
import signal

# Configurazione
SYNC_PORT = 9999  # Porta per ricevere segnali di sincronizzazione
MONITORING_FILE = f"resource_monitoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
SUMMARY_FILE = f"resource_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
SAMPLING_INTERVAL = 0.1  # 100ms - ottimale per articoli scientifici
PROCESS_NAME = "python"  # Nome del processo della funzione (modificare se necessario)

# Variabili globali
monitoring_active = False
resource_data = []
stop_monitoring = False

def wait_for_sync():
    """Attende il segnale di sincronizzazione via TCP"""
    import socket

    print(f"In attesa del segnale di inizio sulla porta {SYNC_PORT}...")

    try:
        # Crea socket server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', SYNC_PORT))
        server_socket.listen(1)

        while True:
            client_socket, address = server_socket.accept()
            try:
                data = client_socket.recv(1024)
                message = data.decode('utf-8')

                if message == "START_TEST":
                    print(f"Segnale di START ricevuto da {address[0]}! Avvio monitoraggio...")
                    client_socket.close()
                    server_socket.close()
                    return True
                elif message == "STOP_TEST":
                    print(f"Segnale di STOP ricevuto da {address[0]}! Arresto monitoraggio...")
                    client_socket.close()
                    server_socket.close()
                    return False

            except Exception as e:
                print(f"Errore nella ricezione del messaggio: {e}")
            finally:
                client_socket.close()

    except Exception as e:
        print(f"Errore nella configurazione del server di sincronizzazione: {e}")
        return False

def setup_stop_listener():
    """Configura listener per segnale di stop in background"""
    import socket
    import threading

    def stop_listener():
        global stop_monitoring
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('0.0.0.0', SYNC_PORT))
            server_socket.listen(1)
            server_socket.settimeout(1)  # Timeout per permettere controllo periodico

            while not stop_monitoring:
                try:
                    client_socket, address = server_socket.accept()
                    data = client_socket.recv(1024)
                    message = data.decode('utf-8')

                    if message == "STOP_TEST":
                        print(f"Segnale di STOP ricevuto da {address[0]}!")
                        stop_monitoring = True
                        client_socket.close()
                        break

                    client_socket.close()
                except socket.timeout:
                    continue
                except Exception as e:
                    if not stop_monitoring:
                        print(f"Errore nel listener di stop: {e}")
                    break

            server_socket.close()

        except Exception as e:
            print(f"Errore nella configurazione del listener di stop: {e}")

    # Avvia listener in background
    listener_thread = threading.Thread(target=stop_listener)
    listener_thread.daemon = True
    listener_thread.start()
    return listener_thread

def get_system_resources():
    """Ottiene le metriche di sistema correnti"""
    try:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        # RAM
        memory = psutil.virtual_memory()
        ram_total_gb = memory.total / (1024**3)
        ram_used_gb = memory.used / (1024**3)
        ram_percent = memory.percent

        # Swap
        swap = psutil.swap_memory()
        swap_used_gb = swap.used / (1024**3)
        swap_percent = swap.percent

        # Disco I/O
        disk_io = psutil.disk_io_counters()

        # Network I/O
        net_io = psutil.net_io_counters()

        # Load average (solo Linux)
        load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)

        return {
            'timestamp': time.time(),
            'cpu_percent': cpu_percent,
            'cpu_count': cpu_count,
            'cpu_freq_mhz': cpu_freq.current if cpu_freq else 0,
            'ram_total_gb': ram_total_gb,
            'ram_used_gb': ram_used_gb,
            'ram_percent': ram_percent,
            'ram_available_gb': memory.available / (1024**3),
            'swap_used_gb': swap_used_gb,
            'swap_percent': swap_percent,
            'load_avg_1min': load_avg[0],
            'load_avg_5min': load_avg[1],
            'load_avg_15min': load_avg[2],
            'disk_read_mb': disk_io.read_bytes / (1024**2) if disk_io else 0,
            'disk_write_mb': disk_io.write_bytes / (1024**2) if disk_io else 0,
            'net_sent_mb': net_io.bytes_sent / (1024**2) if net_io else 0,
            'net_recv_mb': net_io.bytes_recv / (1024**2) if net_io else 0
        }
    except Exception as e:
        print(f"Errore nella raccolta metriche: {e}")
        return None

def get_process_resources():
    """Ottiene le metriche specifiche del processo della funzione"""
    try:
        function_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'cmdline']):
            try:
                # Cerca processi che potrebbero essere la funzione
                if proc.info['name'] and (
                    PROCESS_NAME.lower() in proc.info['name'].lower() or
                    (proc.info['cmdline'] and any('onmarco' in cmd for cmd in proc.info['cmdline']))
                ):
                    function_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_mb': proc.info['memory_info'].rss / (1024**2) if proc.info['memory_info'] else 0,
                        'cmdline': ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return function_processes
    except Exception as e:
        print(f"Errore nella raccolta metriche processi: {e}")
        return []

def monitor_resources():
    """Thread principale di monitoraggio"""
    global resource_data, stop_monitoring

    print(f"Monitoraggio attivo (intervallo: {SAMPLING_INTERVAL}s)")
    sample_count = 0

    while not stop_monitoring:
        try:
            # Metriche di sistema
            system_metrics = get_system_resources()
            if system_metrics:
                system_metrics['sample_id'] = sample_count
                system_metrics['datetime'] = datetime.fromtimestamp(system_metrics['timestamp']).isoformat()

                # Metriche processi
                process_metrics = get_process_resources()
                system_metrics['active_processes'] = len(process_metrics)

                if process_metrics:
                    total_proc_cpu = sum(p['cpu_percent'] for p in process_metrics)
                    total_proc_memory = sum(p['memory_mb'] for p in process_metrics)
                    system_metrics['process_cpu_total'] = total_proc_cpu
                    system_metrics['process_memory_total_mb'] = total_proc_memory
                else:
                    system_metrics['process_cpu_total'] = 0
                    system_metrics['process_memory_total_mb'] = 0

                resource_data.append(system_metrics)
                sample_count += 1

                # Progress ogni 50 campioni
                if sample_count % 50 == 0:
                    print(f"Campioni raccolti: {sample_count}")

            time.sleep(SAMPLING_INTERVAL)

        except Exception as e:
            print(f"Errore durante il monitoraggio: {e}")
            time.sleep(SAMPLING_INTERVAL)

def save_monitoring_data():
    """Salva i dati di monitoraggio in CSV"""
    if not resource_data:
        print("Nessun dato da salvare")
        return

    # Salva dati grezzi
    with open(MONITORING_FILE, 'w', newline='') as csvfile:
        fieldnames = [
            'sample_id', 'datetime', 'timestamp', 'cpu_percent', 'cpu_count', 'cpu_freq_mhz',
            'ram_total_gb', 'ram_used_gb', 'ram_percent', 'ram_available_gb',
            'swap_used_gb', 'swap_percent', 'load_avg_1min', 'load_avg_5min', 'load_avg_15min',
            'disk_read_mb', 'disk_write_mb', 'net_sent_mb', 'net_recv_mb',
            'active_processes', 'process_cpu_total', 'process_memory_total_mb'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(resource_data)

    # Calcola statistiche
    calculate_and_save_summary()

def calculate_and_save_summary():
    """Calcola e salva statistiche riassuntive"""
    if not resource_data:
        return

    # Calcola statistiche
    cpu_values = [d['cpu_percent'] for d in resource_data]
    ram_values = [d['ram_percent'] for d in resource_data]
    ram_used_values = [d['ram_used_gb'] for d in resource_data]
    load_values = [d['load_avg_1min'] for d in resource_data]

    def calc_stats(values):
        if not values:
            return {}
        return {
            'mean': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'median': sorted(values)[len(values)//2],
            'std_dev': (sum((x - sum(values)/len(values))**2 for x in values) / len(values))**0.5
        }

    cpu_stats = calc_stats(cpu_values)
    ram_stats = calc_stats(ram_values)
    ram_used_stats = calc_stats(ram_used_values)
    load_stats = calc_stats(load_values)

    summary = {
        'total_samples': len(resource_data),
        'duration_seconds': resource_data[-1]['timestamp'] - resource_data[0]['timestamp'],
        'sampling_interval': SAMPLING_INTERVAL,
        'cpu_mean_percent': cpu_stats.get('mean', 0),
        'cpu_max_percent': cpu_stats.get('max', 0),
        'cpu_min_percent': cpu_stats.get('min', 0),
        'cpu_std_dev': cpu_stats.get('std_dev', 0),
        'ram_mean_percent': ram_stats.get('mean', 0),
        'ram_max_percent': ram_stats.get('max', 0),
        'ram_min_percent': ram_stats.get('min', 0),
        'ram_std_dev': ram_stats.get('std_dev', 0),
        'ram_used_mean_gb': ram_used_stats.get('mean', 0),
        'ram_used_max_gb': ram_used_stats.get('max', 0),
        'ram_used_min_gb': ram_used_stats.get('min', 0),
        'load_avg_mean': load_stats.get('mean', 0),
        'load_avg_max': load_stats.get('max', 0),
        'load_avg_min': load_stats.get('min', 0)
    }

    # Salva summary
    with open(SUMMARY_FILE, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=summary.keys())
        writer.writeheader()
        writer.writerow(summary)

    # Stampa statistiche
    print("\n=== STATISTICHE RISORSE ===")
    print(f"Campioni totali: {summary['total_samples']}")
    print(f"Durata monitoraggio: {summary['duration_seconds']:.2f} secondi")
    print(f"CPU - Media: {summary['cpu_mean_percent']:.2f}% | Max: {summary['cpu_max_percent']:.2f}%")
    print(f"RAM - Media: {summary['ram_mean_percent']:.2f}% | Max: {summary['ram_max_percent']:.2f}%")
    print(f"RAM - Utilizzata: {summary['ram_used_mean_gb']:.2f} GB (media) | {summary['ram_used_max_gb']:.2f} GB (max)")
    print(f"Load Average - Media: {summary['load_avg_mean']:.2f} | Max: {summary['load_avg_max']:.2f}")

def signal_handler(signum, frame):
    """Gestisce i segnali di interruzione"""
    global stop_monitoring
    print("\nInterruzione rilevata, terminando monitoraggio...")
    stop_monitoring = True

def cleanup():
    """Pulisce le risorse"""
    pass  # Non ci sono più file temporanei da pulire

def main():
    """Funzione principale"""
    global stop_monitoring

    # Gestione segnali
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        print("=== MONITOR RISORSE SERVER ===")
        print(f"Porta di sincronizzazione: {SYNC_PORT}")
        print(f"Intervallo di campionamento: {SAMPLING_INTERVAL}s")
        print(f"File dati: {MONITORING_FILE}")
        print(f"File statistiche: {SUMMARY_FILE}")

        # Attende sincronizzazione
        if not wait_for_sync():
            print("Test terminato prima dell'avvio del monitoraggio")
            return

        # Configura listener per segnale di stop
        stop_listener_thread = setup_stop_listener()

        # Avvia monitoraggio
        monitor_thread = threading.Thread(target=monitor_resources)
        monitor_thread.daemon = True
        monitor_thread.start()

        # Attende che il monitoraggio termini
        while not stop_monitoring:
            time.sleep(1)

        print("Arresto monitoraggio...")
        monitor_thread.join(timeout=5)

        # Salva dati
        save_monitoring_data()

        print(f"\nMonitoraggio completato!")
        print(f"Dati salvati in:")
        print(f"  - Dettagli: {MONITORING_FILE}")
        print(f"  - Statistiche: {SUMMARY_FILE}")

    except Exception as e:
        print(f"Errore durante l'esecuzione: {e}")
    finally:
        cleanup()

if __name__ == "__main__":
    main()
