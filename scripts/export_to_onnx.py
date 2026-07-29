import os
import torch
from sentence_transformers import SentenceTransformer

# Silence the HuggingFace unauthenticated warning limit prompt
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# 1. Dynamically calculate the project root folder (one level up from /scripts/)
script_dir = os.path.dirname(os.path.abspath(__file__))  # Finds D:\project\logs_anomaly_detection\scripts
project_root = os.path.dirname(script_dir)               # Moves up to D:\project\logs_anomaly_detection

# 2. Map absolute paths dynamically (Docker safe)
model_name = "all-MiniLM-L6-v2"
model_path = os.path.join(project_root, "models", "transformer_model")
onnx_path = os.path.join(project_root, "models", "model.onnx")

# Create the folder if it does not exist
os.makedirs(model_path, exist_ok=True)

# 3. Download and save the model locally
print(f"[*] Downloading '{model_name}' from Hugging Face...")
model = SentenceTransformer(model_name)
model.save(model_path)
print(f"[+] Model downloaded and saved locally to: {model_path}")

# Resolve correct internal transformer module layer
if hasattr(model, "transformers_model"):
    core_model = model.transformers_model
else:
    core_model = model.auto_model

# 4. Prepare dummy input for the graph export
dummy_model_input = model.tokenizer("dummy text", return_tensors="pt")

# 5. Export to ONNX
print(f"[*] Exporting local model to ONNX...")
torch.onnx.export(
    core_model,
    (dummy_model_input["input_ids"], dummy_model_input["attention_mask"]),
    onnx_path,
    input_names=["input_ids", "attention_mask"],
    output_names=["output"],
    dynamic_axes={
        "input_ids": {0: "batch_size", 1: "sequence_length"},
        "attention_mask": {0: "batch_size", 1: "sequence_length"}
    },
    opset_version=18
)

print(f"[+] Export successful: {onnx_path}")
