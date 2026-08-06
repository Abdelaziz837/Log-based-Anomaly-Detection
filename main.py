import asyncio , os
import multiprocessing as mp
import sys
from ingestors.file_tailer import AsyncTailer
from ingestors.alerter import SlackAlerter
from processors.parser import LogParser
from processors.embedder import LogEmbedder
from detectors.isolation_forests import AnomalyDetector
from dotenv import load_dotenv

# Load the variables from .env into the system's environment
load_dotenv()

# Now access them using os.getenv
env_path = os.getenv("TARGET_LOG_PATH")
local_fallback = os.path.join(os.getcwd(), "access.log")
docker_default = "/var/log/sentinel/access.log"

if env_path:
    LOG_PATH = env_path
elif os.path.exists(local_fallback):
    LOG_PATH = local_fallback
else:
    LOG_PATH = docker_default

print(f"[*] SentinelLog is searching for logs at: {LOG_PATH}")


SLACK_URL = os.getenv("SLACK_WEBHOOK_URL")
WARMUP = int(os.getenv("MIN_WARMUP_SIZE", 200))
print(f"[DEBUG] INTERNAL CONTAINER LOG_PATH IS: {os.path.abspath(LOG_PATH)}")


def ml_engine_worker(log_queue):
    print("[*] ML Brain Process starting...")
    parser = LogParser(log_type="nginx")
    embedder = LogEmbedder()
    detector = AnomalyDetector(min_warmup_size=WARMUP)

    slack_url = os.getenv("SLACK_WEBHOOK_URL")
    alerter = None
    if slack_url and slack_url.strip():
        try:
            
            alerter = SlackAlerter(slack_url)
            print("[*] Slack Alerter initialized.")
        except Exception as e:
            print(f"[!] Could not initialize Alerter: {e}")
    else:
        print("[!] Warning: SLACK_WEBHOOK_URL is not found. Alerts will appear in terminal only.")

    print("[*] ML Brain is ready. Waiting for logs...")

    while True:
        try:
            raw_line = log_queue.get()
            if raw_line == "SHUTDOWN": break

            p = parser.parse(raw_line)
            v = embedder.embed(p['template_str'])
            status = detector.process(v, p['raw_params'], p['template_id'])
            
            if status == -1:
                print(f"\n[!!!] ANOMALY DETECTED [!!!]")
                print(f"Log: {raw_line}")
                               
                
                if alerter is not None:
                    try:
                        alerter.send_anomaly(raw_line,p['template_str'])
                    except Exception as e:
                        print(f"[!] Failed to send alert: {e}")
                
                print("-" * 30)
            
        except Exception as e:
            print(f"[!] Brain Error: {e}")

async def main():
    # A Queue to pass logs between processes
    log_queue = mp.Queue()
    
    # Start the Brain Process
    brain_proc = mp.Process(target=ml_engine_worker, args=(log_queue,))
    brain_proc.start()

    # Start the Ear (Tailer)
    # Change 'access.log' to your actual log file path
    tailer = AsyncTailer(LOG_PATH)
    
    print("[*] SentinelLog Sidecar is LIVE.")
    try:
        async for line in tailer.tail():
            log_queue.put(line)
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
        log_queue.put("SHUTDOWN")
        brain_proc.join()

if __name__ == "__main__":
    # This 'spawn' method is safer for AI libraries on Windows/Mac
    if sys.platform == 'win32':
        mp.set_start_method('spawn', force=True)
    
    asyncio.run(main())