from processors.parser import LogParser
import os , sys

# High-fidelity sample logs to validate each distinct configuration file
TEST_DATASETS = {
    "nginx": [
    '192.168.1.10 - - [28/Jul/2026:10:00:01 +0000] "GET /api/v1/user/101 HTTP/1.1" 200 512',
    '192.168.1.11 - - [28/Jul/2026:10:00:02 +0000] "GET /api/v1/products HTTP/1.1" 200 2048',
    '192.168.1.47 - - [28/Jul/2026:10:07:45 +0000] "GET /api/v1/user/155 HTTP/1.1" 200 513',
    '192.168.1.53 - - [28/Jul/2026:10:09:01 +0000] "GET /api/v1/user/161 HTTP/1.1" 200 512',
    '192.168.1.54 - - [28/Jul/2026:10:09:10 +0000] "GET /api/v1/user/162 HTTP/1.1" 200 514',

    # --- ANOMALY: BRUTE FORCE (Login attempts followed by success) ---
    '10.0.0.99 - - [28/Jul/2026:10:10:22 +0000] "POST /api/v1/auth/login HTTP/1.1" 401 128',
    '10.0.0.99 - - [28/Jul/2026:10:10:23 +0000] "POST /api/v1/auth/login HTTP/1.1" 401 128',
    '10.0.0.99 - - [28/Jul/2026:10:10:24 +0000] "POST /api/v1/auth/login HTTP/1.1" 401 128',
    '10.0.0.99 - - [28/Jul/2026:10:10:25 +0000] "POST /api/v1/auth/login HTTP/1.1" 200 128',

    # --- ANOMALY: VULNERABILITY SCANNER (Bot searching for backdoors) ---
    '185.122.1.5 - - [28/Jul/2026:10:11:50 +0000] "GET /wp-admin HTTP/1.1" 404 150',
    '185.122.1.5 - - [28/Jul/2026:10:11:51 +0000] "GET /wp-login.php HTTP/1.1" 404 150',

    # --- ANOMALY: BACKEND ERRORS (Server crashing) ---
    '192.168.1.10 - - [28/Jul/2026:10:12:10 +0000] "GET /api/v1/user/101 HTTP/1.1" 500 256',
    '192.168.1.10 - - [28/Jul/2026:10:13:10 +0000] "GET /api/v1/user/101/reports HTTP/1.1" 504 0',
    '192.168.1.10 - - [28/Jul/2026:10:13:15 +0000] "GET /api/v1/user/101/reports HTTP/1.1" 504 0',

    # --- ANOMALY: SECURITY INJECTIONS (SQL and Path Traversal) ---
    '45.33.22.11 - - [28/Jul/2026:10:14:01 +0000] "GET /api/v1/user/1\'OR\'1\'=\'1 HTTP/1.1" 400 150',
    '45.33.22.11 - - [28/Jul/2026:10:14:02 +0000] "GET /api/v1/user/../../etc/passwd HTTP/1.1" 400 150',
    '45.33.22.11 - - [28/Jul/2026:10:14:03 +0000] "GET /api/v1/user/<script>alert(1)</script> HTTP/1.1" 400 150',
    '45.33.22.11 - - [28/Jul/2026:10:14:04 +0000] "GET /api/v1/user/%2e%2e/%2e%2e/etc/passwd HTTP/1.1" 400 150',
    '45.33.22.11 - - [28/Jul/2026:10:14:05 +0000] "GET /api/v1/user/union+select+null,null HTTP/1.1" 400 150',

    # --- MORE NORMAL TRAFFIC (To finish the 100) ---
    '192.168.1.60 - - [28/Jul/2026:10:15:01 +0000] "GET /api/v1/user/165 HTTP/1.1" 200 512',
    '192.168.1.61 - - [28/Jul/2026:10:15:05 +0000] "GET /api/v1/user/166 HTTP/1.1" 200 514',
    '10.0.0.6 - - [28/Jul/2026:10:15:20 +0000] "GET /health HTTP/1.1" 200 12']
    }

    

def run_multi_config_evaluation():
    print("=" * 65)
    print("          DRAIN3 CONFIGURATION-SPECIFIC EVALUATION SUITE        ")
    print("=" * 65)

    configs_dir = os.path.join(os.getcwd(), "config")
    
    # 1. Pre-flight directory checks
    if not os.path.exists(configs_dir):
        print(f"[!] Error: 'configs/' directory missing at {configs_dir}")
        sys.exit(1)

    # 2. Iterate dynamically over each configured log engine
    for log_type, sample_lines in TEST_DATASETS.items():
        expected_ini = os.path.join(configs_dir, f"{log_type}.ini")
        print(f"\n[TARGET ENGINE: {log_type.upper()}]")
        print(f" Checking for file: {expected_ini}")
        
        if not os.path.exists(expected_ini):
            print(f" [!] Missing config file. Skipping evaluation for {log_type}.")
            print("-" * 65)
            continue
            
        # Target an isolated state file for each run so they do not contaminate each other
        state_file = f"models/parser_brain_{log_type}.pkl"
        
        # Clean out stale state logs if executing a fresh regression run
        if os.path.exists(state_file):
            os.remove(state_file)
            
        try:
            # Initializes using your exact dynamic file construction route
            parser = LogParser(log_type=log_type, state_path=state_file)
            
            print(" Processed Stream Verification Output:")
            for idx, line in enumerate(sample_lines, 1):
                parsed = parser.parse(line)
                
                print(f"   Line {idx} Input  : {line}..." if len(line) > 93 else f"   Line {idx} Input  : {line}")
                print(f"   Mined Template : {parsed['template_str']}")
                print(f"   full params : {parsed['raw_params']}")
                print(f"   Assigned Cluster ID  : {parsed['template_id']}")
                print("   " + "." * 55)
                
            # Validate save cycle execution
            parser.save_state()
            print(f" [✓] Verification complete. State serialized cleanly to: {state_file}")
            
        except Exception as e:
            print(f" [X] Crash detected while processing engine {log_type}: {str(e)}")
            
        print("-" * 65)

if __name__ == "__main__":
    run_multi_config_evaluation()
