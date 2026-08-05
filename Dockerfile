# --- Stage 1: The Builder ---
FROM python:3.10-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY scripts/ ./scripts/
COPY sentinellog/ ./sentinellog/
# Pre-download and Export model to ONNX
RUN python scripts/export_to_onnx.py

# --- Stage 2: The Production Image ---
FROM python:3.10-slim
WORKDIR /app

# Install ONLY runtime dependencies (No Torch!)
RUN pip install --no-cache-dir \
    onnxruntime \
    numpy \
    scikit-learn \
    drain3 \
    requests \
    transformers

# Copy only the necessary files
COPY --from=builder /app/models /app/models
COPY sentinellog/ /app/sentinellog/
COPY configs/ /app/configs/
COPY main.py .

# Environment variable for the log file location
ENV LOG_FILE="/var/log/nginx/access.log"

CMD ["python", "main.py"]