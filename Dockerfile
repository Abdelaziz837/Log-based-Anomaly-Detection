# --- STAGE 1: Builder ---
FROM python:3.10-slim AS builder
WORKDIR /app

RUN pip install --upgrade pip

# Use massive timeouts for every pip command
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

RUN pip install --no-cache-dir --default-timeout=1000 --retries 10 \
    torch --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir --default-timeout=1000 --retries 10 \
    sentence-transformers onnxscript onnx

COPY scripts/ ./scripts/
COPY processors/ ./processors/
COPY config/ ./config/

# Ensure the models directory exists
RUN mkdir -p models
RUN python scripts/export_to_onnx.py

# --- STAGE 2: Runner ---
FROM python:3.10-slim
WORKDIR /app

# THE FIX: Added --default-timeout=1000 here as well!
RUN pip install --no-cache-dir --default-timeout=1000 \
    onnxruntime numpy scikit-learn drain3 requests python-dotenv watchdog transformers

# Copy the AI models we built in the first stage
COPY --from=builder /app/models ./models

# Copy the application logic
COPY config/ ./config/
COPY detectors/ ./detectors/
COPY ingestors/ ./ingestors/
COPY processors/ ./processors/
COPY main.py .

# Standardize the log environment
RUN mkdir -p /var/log/sentinel
ENV TARGET_LOG_PATH=/var/log/sentinel/access.log
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]