# detectors/isolation_forests.py
import numpy as np
from collections import deque, defaultdict
from sklearn.ensemble import IsolationForest

class AnomalyDetector:
    def __init__(self, window_size=50, retrain_interval=1000 , min_warmup_size = 200):
        self.window_size = window_size
        self.retrain_interval = retrain_interval
        
        
        self.expert_semantic = IsolationForest(n_estimators=100, contamination=0.01, random_state=42)
        self.expert_metric = IsolationForest(n_estimators=100, contamination=0.01, random_state=42)
        self.expert_history = IsolationForest(n_estimators=100, contamination=0.01, random_state=42)

        self.is_trained = False
        self.min_warmup_size = min_warmup_size 
        
        # Sliding training windows (maxlen=1000) representing current baseline context
        self.training_sem = deque(maxlen=1000)
        self.training_met = deque(maxlen=1000)
        self.training_hist = deque(maxlen=1000)
        
        self.processed_since_train = 0
        
        # Track sliding window of size N strictly per IP address
        self.ip_histories = defaultdict(lambda: deque(maxlen=window_size))
        
        self.thresholds = {"sem": -1.0, "met": -1.0, "hist": -1.0}

    def process(self, semantic_vector, raw_params, template_id):
        # 1. Extract IP Address (index 0)
        ip_address = raw_params[0] if len(raw_params) > 0 else "unknown"

        # 2. Metric Extraction: Isolate Status and Bytes
        nums = []
        for p in raw_params:
            try:
                cleaned = str(p).split()[0].replace(',', '').replace(';', '').replace(':', '')
                nums.append(float(cleaned))
            except (ValueError, IndexError):
                pass
        
        status = 200.0
        bytes_sent = 0.0
        if len(nums) >= 2:
            status = nums[-2]
            bytes_sent = nums[-1]
        elif len(nums) == 1:
            status = nums[0]

        met_vec = np.array([status, bytes_sent], dtype=float)

        # 3. Update IP history window and extract personal statistical features
        self.ip_histories[ip_address].append((status, template_id, bytes_sent))
        history_list = list(self.ip_histories[ip_address])
        h_len = len(history_list)

        error_count = sum(1 for s, _, _ in history_list if s >= 400.0)
        ip_error_rate = error_count / h_len if h_len > 0 else 0.0
        
        unique_templates = len(set(tid for _, tid, _ in history_list))
        ip_uniqueness = unique_templates / h_len if h_len > 0 else 1.0
        
        ip_avg_bytes = sum(b for _, _, b in history_list) / h_len if h_len > 0 else 0.0

        hist_vec = np.array([ip_error_rate, ip_uniqueness, ip_avg_bytes], dtype=float)

        
        if not self.is_trained:
            self.training_sem.append(semantic_vector)
            self.training_met.append(met_vec)
            self.training_hist.append(hist_vec)
            
            if len(self.training_sem) >= self.min_warmup_size:
                self._train()
            return 1 # Normal during warmup

        
        # Evaluate Experts
        s_hist = self.expert_history.score_samples(hist_vec.reshape(1, -1))[0]
        is_hist_anom = s_hist < self.thresholds["hist"]

        s_met = self.expert_metric.score_samples(met_vec.reshape(1, -1))[0]
        is_met_anom = s_met < self.thresholds["met"]

        s_sem = self.expert_semantic.score_samples(semantic_vector.reshape(1, -1))[0]
        is_sem_anom = s_sem < self.thresholds["sem"]

        # Final anomaly status
        is_anomalous = is_hist_anom or is_met_anom or is_sem_anom

        # Only append to moving training windows if log is classified as normal
        if not is_anomalous:
            self.training_sem.append(semantic_vector)
            self.training_met.append(met_vec)
            self.training_hist.append(hist_vec)

        # 3. Dynamic Retraining Check
        self.processed_since_train += 1
        if self.processed_since_train >= self.retrain_interval:
            self._train()
            self.processed_since_train = 0

        return -1 if is_anomalous else 1

    def _train(self):
        print(f"[*] Training/Retraining Experts for Nginx (Buffer size: {len(self.training_sem)})...")
        
        # Train Semantic Expert
        x_sem = np.array(self.training_sem)
        self.expert_semantic.fit(x_sem)
        sem_scores = self.expert_semantic.score_samples(x_sem)
        self.thresholds["sem"] = np.percentile(sem_scores, 1.0)

        # Train Metric Expert
        x_met = np.array(self.training_met)
        self.expert_metric.fit(x_met)
        met_scores = self.expert_metric.score_samples(x_met)
        self.thresholds["met"] = np.percentile(met_scores, 1.0)

        # Train Personal History Expert
        x_hist = np.array(self.training_hist)
        self.expert_history.fit(x_hist)
        hist_scores = self.expert_history.score_samples(x_hist)
        self.thresholds["hist"] = np.percentile(hist_scores, 1.0)

        self.is_trained = True
        print(f"  └─ Retraining Complete. New thresholds established.")