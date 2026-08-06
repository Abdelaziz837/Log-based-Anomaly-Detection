import os
import pickle
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig

class LogParser:
    def __init__(self, log_type="nginx", custom_config_path=None, state_path="models/parser_brain.pkl"):
        self.state_path = state_path

        # Create directory for state file if it doesn't exist
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        
        # Determine config path
        if custom_config_path and os.path.exists(custom_config_path):
            config_file = custom_config_path
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            config_file = os.path.join(base_dir, "config", f"{log_type}.ini")
            
            # Fallback for different directory structures
            if not os.path.exists(config_file):
                parent_dir = os.path.dirname(base_dir)
                config_file = os.path.join(parent_dir, "config", f"{log_type}.ini")

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

    def parse(self, log_line: str):
        line = log_line.strip()
        
        
        # 1. Drain3 Clustering
        result = self.template_miner.add_log_message(line)
        t_id = result.get("cluster_id")
        t_str = result.get("template_mined")

        # 2. Extract Parameters and Tags using Masking Instructions
        all_candidates = []
        for instr in self.template_miner.masker.masking_instructions:
            tag = instr.mask_with 
            for m in instr.regex.finditer(line):
                all_candidates.append((m.start(), m.end(), m.group(), tag))

        # Sort to handle overlapping masks (prefer longer matches)
        all_candidates.sort(key=lambda x: (x[0] - x[1], x[0]))

        mask = bytearray(len(line))
        accepted = [] 

        for start, end, val, tag in all_candidates:
            if not any(mask[start:end]):
                accepted.append((start, val, tag))
                mask[start:end] = b'\x01' * (end - start)

       
        accepted.sort() 
        
       
        raw_params = [p[1] for p in accepted]
        ordered_tags = [p[2] for p in accepted]

        
        return {
            "template_id": t_id,
            "template_str": t_str,     # Contains placeholders like <ID_IP> for the Embedder
            "raw_params": raw_params,  # All extracted values
            "tags": ordered_tags       # All corresponding tags 
        }
        
    def save_state(self):
        with open(self.state_path, "wb") as f:
            pickle.dump(self.template_miner, f)