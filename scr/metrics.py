from datetime import datetime
import time
import threading
from pathlib import Path

class MetricsCollector:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.metrics_list = []
                # Create a unique folder in 'simpynoc/simulations_result' directory
                script_dir = Path(__file__).resolve().parent
                project_root = script_dir.parent.parent
                metrics_base = project_root / "simpynoc" / "simulation_results"
                cls._instance.simulation_id = datetime.now().strftime('%Y%m%d_%H%M%S')
                cls._instance.metrics_folder = str(metrics_base / cls._instance.simulation_id)
            return cls._instance
    

    def push_metric(self, metric):
        if not isinstance(metric, dict):
            raise ValueError("Metric must be a dictionary.")
        m = {
            'source': metric.get('source', ''),
            'id': metric.get('id', ''),
            'type': metric.get('type', ''),
            'timestamp': datetime.now(),
            'packet_id': metric.get('packet_id', ''),
            'src': metric.get('src', ''),
            'dst': metric.get('dst', ''),
            'hops': metric.get('hops', 0),
            'cycles': metric.get('cycles', 0),
            'from_dir': metric.get('from_dir', ''),
            'to_dir': metric.get('to_dir', ''),
            'creation_time': metric.get('creation_time', ''),
            'deliver_time': metric.get('deliver_time', ''),
            "execution_id": metric.get("execution_id", ''),
            "weight": metric.get("weight", '')
        }        
        self.metrics_list.append(m)
    

    def get_metrics_folder(self):
        return self.metrics_folder

    def get_all_metrics(self):
        return list(self.metrics_list)
    
    def reset_metrics(self):
        self.metrics_list = []

    def save_logs_to_csv(self, suffix=""):
        import os
        import csv

        os.makedirs(self.metrics_folder, exist_ok=True)
        if suffix:
            file_name = f"{self.metrics_folder}/logs_{suffix}.csv"
        else:
            file_name = f"{self.metrics_folder}/logs.csv"

        # If there are no metrics, create an empty file with headers based on known keys
        if not self.metrics_list:
            # write empty file
            with open(file_name, 'w', newline='', encoding='utf-8') as f:
                pass
            return file_name

        # Write metrics incrementally to avoid building a large DataFrame in memory
        fieldnames = list(self.metrics_list[0].keys())
        try:
            with open(file_name, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for m in self.metrics_list:
                    row = m.copy()
                    ts = row.get('timestamp')
                    if hasattr(ts, 'isoformat'):
                        row['timestamp'] = ts.isoformat()
                    writer.writerow(row)
        except MemoryError:
            # As a fallback, write in chunks using pandas if available
            try:
                import pandas as pd
                chunk_size = 100000
                for i in range(0, len(self.metrics_list), chunk_size):
                    chunk = self.metrics_list[i:i+chunk_size]
                    df = pd.DataFrame(chunk)
                    mode = 'w' if i == 0 else 'a'
                    header = True if i == 0 else False
                    df.to_csv(file_name, mode=mode, header=header, index=False)
            except Exception:
                raise

        # Clear metrics to free memory
        del self.metrics_list
        self.metrics_list = []
        return file_name