import os
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer
import re 

class LogEmbedder:
    def __init__(self, model_dir="models/transformer_model", onnx_path="models/model.onnx" ):
        if not os.path.exists(onnx_path):
            raise FileNotFoundError("ONNX model not found. run export_to_onnx first")

        # load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)

        
        self.session = ort.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])
        print(f"[*] Embeddder running on ONNX")


    def _mean_pooling(self, model_output, attention_mask):
        """condense trasnformer output to a single vector"""
        token_embedding = model_output 
        input_mask_expanded = np.expand_dims(attention_mask, -1).astype(float)
        return np.sum(token_embedding * input_mask_expanded, 1) /  np.maximum(input_mask_expanded.sum(1), 1e-9) 

    def embed(self, template_str: str) -> np.ndarray:
       
        clean_template = re.sub(r'<ID_\w+>', '', template_str)
        clean_template = " ".join(clean_template.split())
        
        
        if not clean_template.strip():
            clean_template = "empty_log"

        
        encoded_input = self.tokenizer(
            clean_template, 
            padding='max_length', 
            max_length=64, 
            truncation=True, 
            return_tensors='np'
        )

       
        inputs = {
            'input_ids': encoded_input['input_ids'],
            'attention_mask': encoded_input['attention_mask'] 
        }

        model_output = self.session.run(None, inputs)[0]

        
        sentence_embedding = self._mean_pooling(model_output, encoded_input['attention_mask']) 

        
        return sentence_embedding.flatten()