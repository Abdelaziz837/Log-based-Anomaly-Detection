# LogSheild — Autonomous, Multi‑Expert Log Anomaly Detection Sidecar

LogSheild is a lightweight, high‑performance security sidecar that brings enterprise‑grade log anomaly detection to containerized services without the enterprise price tag. It parses NGINX‑style logs in real time, runs a committee of three specialized Isolation Forest experts, and emits alerts when anomalous activity is observed.

> Reported evaluation (your test set): Recall 85%, Precision 94% — reported on the provided labeled dataset.

Status
- Lightweight Docker sidecar (multi‑stage Dockerfile included)
- Focus: NGINX‑style logs (configurable)
- Design goals: low latency, low memory (ONNX for transformer inference)

Highlights
- Committee of three complementary experts (semantic, metric, history). The current code uses a logical OR aggregation: any expert flag → anomaly.
- ONNX‑exported transformer embedder for low‑latency, low‑memory semantic feature extraction.
- Drain3‑based template mining + masking for robust parsing of messy logs.
- Producer/consumer, multiprocessing sidecar design for non‑blocking ingestion.
- Offline evaluation script that supports labeled CSV/JSONL and generator output (data/access.log + data/labels.csv).

Quick links
- Repo: https://github.com/Abdelaziz837/Log-based-Anomaly-Detection
- Required artifacts: `config/nginx.ini`, `models/model.onnx`, `models/transformer_model/` (tokenizer)

Architecture (concise)
- Tailer (Ear): AsyncTailer reads new lines from a log file and enqueues them.
- Brain: Separate process consumes queued lines, parses with drain3, embeds templates via ONNX transformer, builds numeric and history vectors, and scores the three IsolationForest experts.
- Committee: Semantic Expert (transformer embeddings), Metric Expert (status/bytes), History Expert (per‑IP sliding window).
- Alerts: Slack webhook (`SLACK_WEBHOOK_URL`) if set, otherwise printed to terminal.

What’s implemented in code (verified)
- `main.py`: multiprocessing tailer + ML worker orchestration, env fallbacks for `TARGET_LOG_PATH`.
- `processors/parser.py`: drain3 TemplateMiner with config resolution and parser state persistence (`models/parser_brain.pkl`).
- `processors/embedder.py`: ONNX InferenceSession + `AutoTokenizer` usage (expects `models/transformer_model/` and `models/model.onnx`).
- `detectors/isolation_forests.py`: three scikit‑learn `IsolationForest` experts, warmup buffer, training & thresholds from the 1st percentile, `retrain_interval` logic, windowed per‑IP history.
- `scripts/evaluate.py`: offline evaluation; supports labeled CSV/JSONL and generator outputs (`data/access.log` + `data/labels.csv`).

Quick start (local)
1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Ensure artifacts exist:
- `config/nginx.ini` (parser config)
- `models/model.onnx` and `models/transformer_model/` (tokenizer files)

3. Run as sidecar:

```bash
python main.py
# or use Docker
docker build -t logshield:v1 .
docker run -it --rm -v "/path/to/logs:/var/log/sentinel" --env-file .env logshield:v1
```

Evaluation (offline)

The repository now includes `scripts/evaluate.py` which supports two modes:

A) Labeled CSV/JSONL input (fields: `log`, `label`):

```bash
python scripts/evaluate.py --test-file data/test_labels.csv --format csv --min-warmup 200 --out-preds results/preds.csv
```

B) Generator output mode (use your generated files `data/access.log` and `data/labels.csv`):

```bash
python scripts/evaluate.py --use-access-log --access-log data/access.log --labels-csv data/labels.csv --min-warmup 200 --out-preds results/preds.csv
```

How evaluation works
- The evaluator warms up the detector with the first `--min-warmup` samples (default 200) so the in‑process IsolationForest experts have training data.
- It then runs inference on the remaining samples and prints precision, recall, F1, and the confusion matrix.
- `--out-preds` writes a CSV with `log,label,pred`.

Tuning & operational notes
- Warmup (`--min-warmup` / `MIN_WARMUP_SIZE`) controls how many samples are buffered before first training. Increase for more stable thresholds; reduce to train earlier.
- Thresholds: detectors compute thresholds as the 1st percentile of training scores; raising that percentile (e.g., 3–5%) increases recall, lowering it increases precision.
- Retrain cadence: `retrain_interval` (default 1000) controls how often the experts retrain.
- History window: `window_size` (default 50) affects per‑IP behavior sensitivity.
- ONNX: ensure the ONNX model and tokenizer are present; otherwise the embedder will raise `FileNotFoundError`.

Files & layout
- `main.py` — sidecar entrypoint
- `processors/parser.py` — drain3 parsing + masking
- `processors/embedder.py` — ONNX embedder
- `detectors/isolation_forests.py` — three experts + training/threshold logic
- `ingestors/` — tailer & alerter
- `config/` — parser INI files (place `nginx.ini` here)
- `models/` — ONNX model, tokenizer directory, parser state
- `scripts/` — `export_to_onnx.py`, `simulate_traffic.py`, `evaluate.py`
- `requirements.txt`, `Dockerfile`, `LICENSE`

Contact / Maintainers
- Maintained by: abdelaziz837 (GitHub: @Abdelaziz837)
