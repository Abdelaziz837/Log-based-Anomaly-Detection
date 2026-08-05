import time
import random
import os

LOG_FILE = "access.log"

def write_log(ip, path, status, size):
    timestamp = time.strftime("%d/%b/%Y:%H:%M:%S +0000")
    line = f'{ip} - - [{timestamp}] "GET {path} HTTP/1.1" {status} {size}\n'
    with open(LOG_FILE, "a") as f:
        f.write(line)
        f.flush() # Force Windows to write to disk immediately

def run_simulation():
    # WIPE the file instead of deleting it
    # This keeps the tailer's "pointer" valid
    open(LOG_FILE, 'w').close()
    
    print("[*] Starting Phase 1: Normal Baseline...")
    normal_ips = ["192.168.1.10", "192.168.1.11", "10.0.0.50"]
    normal_paths = ["/", "/index.html", "/style.css", "/api/v1/data", "/logo.png", "/about"]

    for i in range(250):
        ip = random.choice(normal_ips)
        path = random.choice(normal_paths)
        status = 200
        size = random.randint(500, 5000)
        write_log(ip, path, status, size)
        if i % 50 == 0: print(f"  > Generated {i} logs...")
        time.sleep(0.01) # Tiny sleep to let the tailer breathe
    
    print("[+] Warm-up complete. Training...")
    time.sleep(5) # Wait for AI to finish training

    print("\n[*] Starting Phase 2: Injecting Anomalies...")
    # Anomaly 1: Big Bytes
    write_log("192.168.1.10", "/index.html", 200, 99999999) 
    time.sleep(1)

    # Anomaly 2: Hacker Scan
    hacker_ip = "45.33.22.11"
    for path in ["/.env", "/admin/config.php", "/wp-login.php"]:
        write_log(hacker_ip, path, 404, 200)
        time.sleep(0.5)

    print("\n[✓] Simulation Finished.")

if __name__ == "__main__":
    run_simulation()