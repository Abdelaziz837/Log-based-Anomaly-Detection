#!/usr/bin/env python3
"""
scripts/evaluate.py

Offline evaluation script for Log-based-Anomaly-Detection (LogShield).

This script supports two input modes:
  1) Labeled CSV/JSONL file where each row/object has 'log' and 'label' fields.
  2) A pair of files produced by the test generator: data/access.log and data/labels.csv
     where data/labels.csv contains rows: line_number,is_anomaly,category
     (line_number is 1-based and refers to the corresponding line in data/access.log).

The script warms up the detector with the first N samples (MIN_WARMUP_SIZE by default),
then runs inference on the remaining samples and reports precision, recall, F1-score,
and a confusion matrix.

Examples
  # CSV input (existing behavior)
  python scripts/evaluate.py --test-file data/test_labels.csv --format csv --min-warmup 200

  # Use generator output: data/access.log + data/labels.csv
  python scripts/evaluate.py --use-access-log --access-log data/access.log --labels-csv data/labels.csv --min-warmup 200

Outputs: metrics to stdout and an optional CSV with predictions (--out-preds).
"""

import argparse
import csv
import json
import os
import sys
from typing import List, Tuple, Dict

import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

# Local imports from the repo
from processors.parser import LogParser
from processors.embedder import LogEmbedder
from detectors.isolation_forests import AnomalyDetector


def read_csv(path: str, log_field: str = "log", label_field: str = "label") -> List[Tuple[str, int]]:
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            log_line = r.get(log_field)
            lbl = r.get(label_field)
            if log_line is None or lbl is None:
                continue
            try:
                lbl_i = int(lbl)
            except Exception:
                lbl_i = 1 if str(lbl).lower() in ("true", "1", "yes") else 0
            rows.append((log_line, lbl_i))
    return rows


def read_jsonl(path: str, log_field: str = "log", label_field: str = "label") -> List[Tuple[str, int]]:
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                j = json.loads(line)
            except json.JSONDecodeError:
                continue
            log_line = j.get(log_field)
            lbl = j.get(label_field)
            if log_line is None or lbl is None:
                continue
            rows.append((log_line, int(lbl)))
    return rows


def read_generator_outputs(access_log_path: str, labels_csv_path: str) -> List[Tuple[str, int]]:
    """Read data/access.log and data/labels.csv (line_number,is_anomaly,category).
    Returns a list of (log_line, label) ordered by line_number ascending.
    """
    if not os.path.exists(access_log_path):
        raise FileNotFoundError(f"Access log not found: {access_log_path}")
    if not os.path.exists(labels_csv_path):
        raise FileNotFoundError(f"Labels CSV not found: {labels_csv_path}")

    # Read access log into a list (1-based indexing expected by labels)
    with open(access_log_path, 'r', encoding='utf-8') as f:
        lines = [l.rstrip('\n') for l in f]

    labels: Dict[int, int] = {}
    with open(labels_csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Accept header variants: line_number,is_anomaly,... or index,is_anomaly
        for r in reader:
            # Attempt to find line number field
            if 'line_number' in r:
                ln = r['line_number']
            elif 'index' in r:
                ln = r['index']
            else:
                # Fallback: try first column
                ln = next(iter(r.values()))
            # Attempt to find anomaly flag
            if 'is_anomaly' in r:
                an = r['is_anomaly']
            elif 'label' in r:
                an = r['label']
            else:
                # Fallback: second column
                vals = list(r.values())
                an = vals[1] if len(vals) > 1 else '0'

            try:
                line_no = int(ln)
                is_an = int(an)
            except Exception:
                continue
            labels[line_no] = 1 if is_an else 0

    data: List[Tuple[str, int]] = []
    # Iterate labels in sorted order to produce deterministic evaluation
    for line_no in sorted(labels.keys()):
        if 1 <= line_no <= len(lines):
            data.append((lines[line_no - 1], labels[line_no]))
    return data


def evaluate(
    data: List[Tuple[str, int]],
    parser: LogParser,
    embedder: LogEmbedder,
    detector: AnomalyDetector,
    min_warmup: int = 200,
    out_preds: str = None,
):
    """Run an offline evaluation. Warm up on the first `min_warmup` samples, then predict on the rest."""
    total = len(data)
    if total == 0:
        print("[!] No samples provided.")
        return

    print(f"[*] Total samples: {total}")
    warmup_end = min(min_warmup, total)

    # Warmup phase
    print(f"[*] Warming up with first {warmup_end} samples (buffering for training)...")
    for i in range(warmup_end):
        line, _ = data[i]
        try:
            p = parser.parse(line)
            v = embedder.embed(p['template_str'])
            # detector.process will buffer until warmup reached
            detector.process(v, p['raw_params'], p['template_id'])
        except Exception as e:
            # Ignore parse/embed errors during warmup
            print(f"[!] Warmup parsing error on line {i}: {e}")

    # After warmup we assume detector.is_trained is True (if enough data)
    print(f"[*] Warmup finished. Detector trained: {detector.is_trained}")

    y_true = []
    y_pred = []
    preds_out = []

    for i in range(warmup_end, total):
        line, label = data[i]
        try:
            p = parser.parse(line)
            v = embedder.embed(p['template_str'])
            status = detector.process(v, p['raw_params'], p['template_id'])
            predicted_anom = 1 if status == -1 else 0
        except Exception as e:
            print(f"[!] Error processing sample {i}: {e}")
            # If processing fails, count as normal (conservative)
            predicted_anom = 0

        y_true.append(label)
        y_pred.append(predicted_anom)
        preds_out.append({"log": line, "label": label, "pred": predicted_anom})

    if len(y_true) == 0:
        print("[!] No samples were evaluated after warmup — increase dataset or reduce warmup size.")
        return

    prec = precision_score(y_true, y_pred)
    rec = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    cm = confusion_matrix(y_true, y_pred)

    print("\n=== Evaluation Results ===")
    print(f"Samples evaluated: {len(y_true)} (after warmup)")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1-score:  {f1:.4f}")
    print("Confusion matrix (rows=true, cols=pred):")
    print(cm)

    if out_preds:
        out_dir = os.path.dirname(out_preds)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        with open(out_preds, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["log", "label", "pred"])
            writer.writeheader()
            for r in preds_out:
                writer.writerow(r)
        print(f"[*] Predictions written to {out_preds}")


def main(argv=None):
    parser_arg = argparse.ArgumentParser(description="Offline evaluation for LogShield (Log-based-Anomaly-Detection)")
    parser_arg.add_argument("--test-file", required=False, help="Path to labeled test file (CSV or JSONL)")
    parser_arg.add_argument("--format", choices=["csv", "jsonl"], default="csv", help="Format of the test file")
    parser_arg.add_argument("--log-field", default="log", help="Field name for the log line in CSV/JSONL")
    parser_arg.add_argument("--label-field", default="label", help="Field name for the ground-truth label in CSV/JSONL (1=anomaly,0=normal)")
    parser_arg.add_argument("--model-dir", default="models/transformer_model", help="Tokenizer model directory for AutoTokenizer")
    parser_arg.add_argument("--onnx-path", default="models/model.onnx", help="ONNX model path for embedder")
    parser_arg.add_argument("--parser-config", default=None, help="Custom drain3 config path (INI)")
    parser_arg.add_argument("--min-warmup", type=int, default=200, help="Number of samples to use for warmup/training before evaluation")
    parser_arg.add_argument("--out-preds", default=None, help="Optional CSV to write predictions")

    # New options for generator outputs
    parser_arg.add_argument("--use-access-log", action='store_true', help="Use data/access.log + data/labels.csv format produced by generator")
    parser_arg.add_argument("--access-log", default="data/access.log", help="Path to generated access.log (used with --use-access-log)")
    parser_arg.add_argument("--labels-csv", default="data/labels.csv", help="Path to labels CSV with columns line_number,is_anomaly,category (used with --use-access-log)")

    ns = parser_arg.parse_args(argv)

    # Load data
    if ns.use_access_log:
        print(f"[*] Loading generator outputs: access_log={ns.access_log}, labels={ns.labels_csv}")
        try:
            data = read_generator_outputs(ns.access_log, ns.labels_csv)
        except Exception as e:
            print(f"[!] Failed to load generator outputs: {e}")
            sys.exit(1)
    else:
        if not ns.test_file:
            print("[!] --test-file is required when not using --use-access-log")
            sys.exit(1)
        if ns.format == "csv":
            data = read_csv(ns.test_file, log_field=ns.log_field, label_field=ns.label_field)
        else:
            data = read_jsonl(ns.test_file, log_field=ns.log_field, label_field=ns.label_field)

    if len(data) == 0:
        print("[!] No valid rows found in the test file.")
        sys.exit(1)

    # Initialize components
    print("[*] Initializing Parser, Embedder, Detector...")
    parser_obj = LogParser(log_type="nginx", custom_config_path=ns.parser_config)
    embedder_obj = LogEmbedder(model_dir=ns.model_dir, onnx_path=ns.onnx_path)
    detector_obj = AnomalyDetector(min_warmup_size=ns.min_warmup)

    evaluate(data, parser_obj, embedder_obj, detector_obj, min_warmup=ns.min_warmup, out_preds=ns.out_preds)


if __name__ == "__main__":
    main()
