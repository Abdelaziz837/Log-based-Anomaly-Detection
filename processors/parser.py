import os
import hashlib
import pickle
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig
import re

class LogParser:
    def __init__(self, log_type= "generic" ,custom_config_path=None ,state_path="models/parser_brain.pkl"):
        self.state_path = state_path

        # if dict does not work , create it
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        
        
        # Determine config path
        if custom_config_path and os.path.exists(custom_config_path):
            config_file = custom_config_path
        else:
           
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
            
            config_file = os.path.join(base_dir, "config", f"{log_type}.ini")
            
            
            if not os.path.exists(config_file):
                parent_dir = os.path.dirname(base_dir)
                config_file = os.path.join(parent_dir, "config", f"{log_type}.ini")
                
            else:
                raise Warning("[!] Warning , can't find config file")
            
        cfg = TemplateMinerConfig()
        if os.path.exists(config_file):
            cfg.load(config_file)
            print(f"[*] Parser initialized with: {log_type} config")
        else:
            print(f"[!] Warning: {config_file} not found. Using Drain3 defaults.")

        # Load state or Create new
        if os.path.exists(self.state_path):
            with open(self.state_path, "rb") as f:
                self.template_miner = pickle.load(f)
        else:
            self.template_miner = TemplateMiner(config=cfg)

    def _hash_value(self, value):
        return hashlib.sha256(value.encode()).hexdigest()[:8]

    def parse(self, log_line: str):
        # 1. Basic Cleaning
        line = log_line.strip()
        
        #JSON Protection: Don't let Drain3 shred JSON
        if line.startswith("{") and line.endswith("}"):
            return {
                "template_id": 9999,
                "template_str": "{ JSON_DATA }",
                "params": [line]
            }

        result = self.template_miner.add_log_message(line)
        t_id = result.get("cluster_id")
        t_str = result.get("template_mined")

        all_candidates = []
        for instr in self.template_miner.masker.masking_instructions:
            for m in instr.regex.finditer(line):
                all_candidates.append((m.start(), m.end(), m.group()))

        #  Sort by length
        # If lengths are equal, sort by start position ASCENDING
        all_candidates.sort(key=lambda x: (x[0] - x[1], x[0]))

        #  Use a bytearray 
        mask = bytearray(len(line))
        accepted = []

        for start, end, val in all_candidates:
            
            if not any(mask[start:end]):
                accepted.append((start, val))
                
                mask[start:end] = b'\x01' * (end - start)

        
        accepted.sort()
        raw_params = [p[1] for p in accepted]


        processed_params = []
        for p in raw_params:
            if isinstance(p, str) and re.match(r"^\d{1,3}(\.\d{1,3}){3}$", p):
                processed_params.append(self._hash_value(p))
            else:
                processed_params.append(p)

        return {
            "template_id": t_id,
            "template_str": t_str,
            "params": processed_params
        }

    def save_state(self):
        with open(self.state_path, "wb") as f:
            pickle.dump(self.template_miner, f)