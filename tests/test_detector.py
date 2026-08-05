# tests/test_detector.py
import os
import csv
from processors.parser import LogParser
from processors.embedder import LogEmbedder
from detectors.isolation_forests import AnomalyDetector

def run_nginx_test():
    name = "Nginx"
    log_type = "nginx"
    data_path = "data/raw/nginx.log"
    labels_path = "data/raw/labels_nginx.csv"

    print("\n" + "█" * 60 + f"\n STREAMING TEST: {name}\n" + "█" * 60)

    # 1. Setup Parser, Embedder, and Detector
    parser = LogParser(log_type=log_type)
    embedder = LogEmbedder()
    detector = AnomalyDetector()

    # 2. Load Dataset & Labels
    if not os.path.exists(data_path):
        print(f"[!] Error: Data path {data_path} not found.")
        return

    with open(data_path, "r", encoding='utf-8', errors='ignore') as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    
    labels = {}
    if os.path.exists(labels_path):
        with open(labels_path, newline="") as f:
            for row in csv.DictReader(f):
                labels[int(row["line_number"])] = int(row["is_anomaly"])

    metrics = {"TP": 0, "FP": 0, "TN": 0, "FN": 0}
    warmup_count = 0
    
    print(f"[*] Processing {len(lines)} lines...")

    for i, line in enumerate(lines, start=1):
        is_anomaly_truth = labels.get(i, 0)
        p = parser.parse(line)
        v = embedder.embed(p["template_str"])
        
        # --- WARMUP ---
        if not detector.is_trained:
            if is_anomaly_truth == 0:
                detector.process(v, p["raw_params"], p["template_id"])
                warmup_count += 1
                if warmup_count % 50 == 0:
                    print(f"  └─ Warmup: {warmup_count}/{detector.min_warmup_size}")
            continue

        # --- TEST ---
        result = detector.process(v, p["raw_params"],p["template_id"])
        is_flagged = (result == -1)

        if is_anomaly_truth == 1 and is_flagged: 
            metrics["TP"] += 1
        elif is_anomaly_truth == 0 and is_flagged: 
            metrics["FP"] += 1
        elif is_anomaly_truth == 0 and not is_flagged: 
            metrics["TN"] += 1
        elif is_anomaly_truth == 1 and not is_flagged:
            metrics["FN"] += 1
            print(f" [MISS] Line {i}: {line[:70]}...")

    # 3. Report Metrics
    tp, fp, tn, fn = metrics["TP"], metrics["FP"], metrics["TN"], metrics["FN"]
    recall = (tp / (tp + fn) * 100) if (tp + fn) > 0 else 0
    precision = (tp / (tp + fp) * 100) if (tp + fp) > 0 else 0
    
    print(f"\n RESULTS: {name}\n  ├─ Recall: {recall:.2f}% | Precision: {precision:.2f}%\n" + "═"*60)

if __name__ == "__main__":
    run_nginx_test()