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
SLACK_URL = os.getenv("SLACK_WEBHOOK_URL")
LOG_PATH = os.getenv("TARGET_LOG_PATH", "access.log") # Fallback to access.log if not set
WARMUP = int(os.getenv("MIN_WARMUP_SIZE", 200))


def ml_engine_worker(log_queue):
    print("[*] ML Brain Process starting...")
    parser = LogParser(log_type="nginx")
    embedder = LogEmbedder()
    detector = AnomalyDetector(min_warmup_size=WARMUP)

    if not SLACK_URL:
        print("[!] Warning : Slack_webhook_URL is not found , ALerts will appear in the terminal ")
    else:
        alerter = SlackAlerter(SLACK_URL) # Initialize Alerter
    
    print("[*] ML Brain is ready. Waiting for logs...")

    while True:
        try:
            raw_line = log_queue.get()
            if raw_line == "SHUTDOWN": break

            p = parser.parse(raw_line)
            v = embedder.embed(p['template_str'])
            status = detector.process(v, p['params'], p['template_id'])
            
            if status == -1:
                print(f"\n[!!!] ANOMALY DETECTED [!!!]")
                # TRIGGER THE SLACK ALERT
                alerter.send_anomaly(raw_line, p['template_str'])
            
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
    tailer = AsyncTailer("access.log")
    
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