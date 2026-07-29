import os
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

class LogEmbedder:
    def __init__(self, model_dir="models/transformer_model", onnx_path="models/model.onnx" ):
        if not os.path.exists(onnx_path):
            raise FileNotFoundError("ONNX model not found. run export_to_onnx first")

        # load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)

        # load the ONNX session
        self.session = ort.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])
        print(f"[*] Embeddder running on ONNX")


    def _mean_pooling(self, model_output, attention_mask):
        """condense trasnformer output to a single vector"""
        token_embedding = model_output 
        input_mask_expanded = np.expand_dims(attention_mask, -1).astype(float)
        return np.sum(token_embedding * input_mask_expanded, 1) /  np.maximum(input_mask_expanded.sum(1), 1e-9) 

    def embed(self, template_str: str) -> np.ndarray:
        # tokenize 
        encoded_input = self.tokenizer(template_str, padding=True, truncation=True, return_tensors='np')

        # run ONNX Inference
        inputs = {
            'input_ids': encoded_input['input_ids'],
            'attention_mask': encoded_input['input_ids']
        }

        model_output =self.session.run(None, inputs)[0]

        # pool the output to our 384-dim vector
        sentence_embedding = self._mean_pooling(model_output, encoded_input['attention_mask']) 

        return sentence_embedding.flatten()


        