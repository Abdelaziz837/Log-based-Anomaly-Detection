from processors.parser import LogParser
import pandas as pd
import os , sys

# High-fidelity sample logs to validate each distinct configuration file
TEST_DATASETS = {
    "nginx": [
    '192.168.1.10 - - [28/Jul/2026:10:00:01 +0000] "GET /api/v1/user/101 HTTP/1.1" 200 512',
    '192.168.1.11 - - [28/Jul/2026:10:00:02 +0000] "GET /api/v1/products HTTP/1.1" 200 2048',
    '10.0.0.5 - - [28/Jul/2026:10:00:03 +0000] "GET /api/v1/metrics HTTP/1.1" 200 4500',
    '192.168.1.12 - - [28/Jul/2026:10:00:05 +0000] "GET /api/v1/user/102 HTTP/1.1" 200 515',
    '172.16.0.44 - - [28/Jul/2026:10:00:06 +0000] "GET /favicon.ico HTTP/1.1" 404 150',
    '192.168.1.10 - - [28/Jul/2026:10:00:08 +0000] "PUT /api/v1/user/101/settings HTTP/1.1" 200 64',
    '10.0.0.6 - - [28/Jul/2026:10:00:15 +0000] "GET /health HTTP/1.1" 200 12',
    '192.168.1.13 - - [28/Jul/2026:10:00:20 +0000] "GET /api/v1/user/104 HTTP/1.1" 200 518',
    '172.16.0.10 - - [28/Jul/2026:10:00:30 +0000] "GET /static/css/main.css HTTP/1.1" 200 8900',
    '172.16.0.11 - - [28/Jul/2026:10:00:32 +0000] "GET /static/js/bundle.js HTTP/1.1" 200 45000',
    '192.168.1.14 - - [28/Jul/2026:10:00:42 +0000] "GET /api/v1/user/106 HTTP/1.1" 200 509',
    '192.168.1.10 - - [28/Jul/2026:10:00:45 +0000] "DELETE /api/v1/user/101/session HTTP/1.1" 204 0',
    '192.168.1.15 - - [28/Jul/2026:10:01:01 +0000] "GET /api/v1/user/107 HTTP/1.1" 200 514',
    '192.168.1.16 - - [28/Jul/2026:10:01:12 +0000] "GET /api/v1/user/108 HTTP/1.1" 200 520',
    '172.16.0.12 - - [28/Jul/2026:10:01:15 +0000] "GET /images/logo.png HTTP/1.1" 200 12400',
    '192.168.1.17 - - [28/Jul/2026:10:01:25 +0000] "GET /api/v1/user/109 HTTP/1.1" 200 512',
    '10.0.0.6 - - [28/Jul/2026:10:01:30 +0000] "GET /health HTTP/1.1" 200 12',
    '192.168.1.18 - - [28/Jul/2026:10:01:32 +0000] "GET /api/v1/user/110 HTTP/1.1" 200 515',
    '192.168.1.19 - - [28/Jul/2026:10:01:35 +0000] "GET /api/v1/user/111 HTTP/1.1" 200 518',
    '192.168.1.20 - - [28/Jul/2026:10:01:40 +0000] "GET /api/v1/user/112 HTTP/1.1" 200 511',
    '10.0.0.5 - - [28/Jul/2026:10:01:50 +0000] "GET /api/v1/metrics HTTP/1.1" 200 4505',
    '192.168.1.21 - - [28/Jul/2026:10:01:55 +0000] "GET /api/v1/user/114 HTTP/1.1" 200 513',
    '192.168.1.22 - - [28/Jul/2026:10:02:05 +0000] "GET /api/v1/user/115 HTTP/1.1" 200 516',
    '10.0.0.6 - - [28/Jul/2026:10:02:10 +0000] "GET /health HTTP/1.1" 200 12',
    '192.168.1.10 - - [28/Jul/2026:10:02:15 +0000] "POST /api/v1/upload HTTP/1.1" 200 1048576',
    '192.168.1.23 - - [28/Jul/2026:10:02:20 +0000] "GET /api/v1/user/116 HTTP/1.1" 200 512',
    '192.168.1.24 - - [28/Jul/2026:10:02:25 +0000] "GET /api/v1/user/117 HTTP/1.1" 200 514',
    '192.168.1.25 - - [28/Jul/2026:10:02:30 +0000] "GET /api/v1/user/118 HTTP/1.1" 200 519',
    '192.168.1.26 - - [28/Jul/2026:10:02:40 +0000] "GET /api/v1/user/120 HTTP/1.1" 200 512',
    '10.0.0.5 - - [28/Jul/2026:10:02:45 +0000] "GET /api/v1/metrics HTTP/1.1" 200 4520',
    '192.168.1.27 - - [28/Jul/2026:10:03:01 +0000] "GET /api/v1/user/121 HTTP/1.1" 200 512',
    '192.168.1.28 - - [28/Jul/2026:10:03:05 +0000] "GET /api/v1/user/122 HTTP/1.1" 200 514',
    '10.0.0.6 - - [28/Jul/2026:10:03:20 +0000] "GET /health HTTP/1.1" 200 12',
    '192.168.1.29 - - [28/Jul/2026:10:03:25 +0000] "GET /api/v1/user/123 HTTP/1.1" 200 512',
    '192.168.1.30 - - [28/Jul/2026:10:03:30 +0000] "GET /api/v1/user/124 HTTP/1.1" 200 517',
    '10.0.0.5 - - [28/Jul/2026:10:03:45 +0000] "GET /api/v1/metrics HTTP/1.1" 200 4508',
    '192.168.1.31 - - [28/Jul/2026:10:04:10 +0000] "GET /api/v1/user/127 HTTP/1.1" 200 512',
    '192.168.1.32 - - [28/Jul/2026:10:04:15 +0000] "GET /api/v1/user/128 HTTP/1.1" 200 514',
    '10.0.0.6 - - [28/Jul/2026:10:04:20 +0000] "GET /health HTTP/1.1" 200 12',
    '192.168.1.33 - - [28/Jul/2026:10:04:25 +0000] "GET /api/v1/user/129 HTTP/1.1" 200 518',
    '10.0.0.5 - - [28/Jul/2026:10:04:40 +0000] "GET /api/v1/metrics HTTP/1.1" 200 4512',
    '192.168.1.34 - - [28/Jul/2026:10:05:01 +0000] "GET /api/v1/user/132 HTTP/1.1" 200 512',
    '192.168.1.35 - - [28/Jul/2026:10:05:10 +0000] "GET /api/v1/user/134 HTTP/1.1" 200 519',
    '10.0.0.6 - - [28/Jul/2026:10:05:20 +0000] "GET /health HTTP/1.1" 200 12',
    '192.168.1.36 - - [28/Jul/2026:10:05:25 +0000] "GET /api/v1/user/136 HTTP/1.1" 200 512',
    '192.168.1.37 - - [28/Jul/2026:10:05:35 +0000] "GET /api/v1/user/138 HTTP/1.1" 200 511',
    '10.0.0.5 - - [28/Jul/2026:10:05:45 +0000] "GET /api/v1/metrics HTTP/1.1" 200 4505',
    '192.168.1.38 - - [28/Jul/2026:10:06:01 +0000] "GET /api/v1/user/140 HTTP/1.1" 200 512',
    '192.168.1.39 - - [28/Jul/2026:10:06:10 +0000] "GET /api/v1/user/142 HTTP/1.1" 200 519',
    '10.0.0.6 - - [28/Jul/2026:10:06:20 +0000] "GET /health HTTP/1.1" 200 12',
    '192.168.1.40 - - [28/Jul/2026:10:06:30 +0000] "GET /api/v1/user/145 HTTP/1.1" 200 517',
    '10.0.0.5 - - [28/Jul/2026:10:06:45 +0000] "GET /api/v1/metrics HTTP/1.1" 200 4506',
    '192.168.1.41 - - [28/Jul/2026:10:07:05 +0000] "GET /api/v1/user/149 HTTP/1.1" 200 514',
    '192.168.1.42 - - [28/Jul/2026:10:07:10 +0000] "GET /api/v1/user/150 HTTP/1.1" 200 519',
    '192.168.1.43 - - [28/Jul/2026:10:07:15 +0000] "GET /api/v1/user/151 HTTP/1.1" 200 510',
    '192.168.1.44 - - [28/Jul/2026:10:07:20 +0000] "GET /api/v1/user/152 HTTP/1.1" 200 515',
    '192.168.1.45 - - [28/Jul/2026:10:07:25 +0000] "GET /api/v1/user/153 HTTP/1.1" 200 511',
    '10.0.0.6 - - [28/Jul/2026:10:07:30 +0000] "GET /health HTTP/1.1" 200 12',
    '192.168.1.46 - - [28/Jul/2026:10:07:35 +0000] "GET /api/v1/user/154 HTTP/1.1" 200 512',
    '192.168.1.47 - - [28/Jul/2026:10:07:45 +0000] "GET /api/v1/user/155 HTTP/1.1" 200 513',
    '10.0.0.5 - - [28/Jul/2026:10:07:50 +0000] "GET /api/v1/metrics HTTP/1.1" 200 4502',
    '192.168.1.48 - - [28/Jul/2026:10:08:01 +0000] "GET /api/v1/user/156 HTTP/1.1" 200 512',
    '192.168.1.49 - - [28/Jul/2026:10:08:10 +0000] "GET /api/v1/user/157 HTTP/1.1" 200 514',
    '10.0.0.6 - - [28/Jul/2026:10:08:20 +0000] "GET /health HTTP/1.1" 200 12',
    '192.168.1.50 - - [28/Jul/2026:10:08:30 +0000] "GET /api/v1/user/158 HTTP/1.1" 200 519',
    '192.168.1.51 - - [28/Jul/2026:10:08:35 +0000] "GET /api/v1/user/159 HTTP/1.1" 200 511',
    '192.168.1.52 - - [28/Jul/2026:10:08:40 +0000] "GET /api/v1/user/160 HTTP/1.1" 200 512',
    '10.0.0.5 - - [28/Jul/2026:10:08:45 +0000] "GET /api/v1/metrics HTTP/1.1" 200 4511',
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
    '185.122.1.5 - - [28/Jul/2026:10:11:52 +0000] "GET /.env HTTP/1.1" 404 150',
    '185.122.1.5 - - [28/Jul/2026:10:11:53 +0000] "GET /phpmyadmin HTTP/1.1" 404 150',
    '185.122.1.5 - - [28/Jul/2026:10:11:54 +0000] "GET /config.json HTTP/1.1" 404 150',

    # --- ANOMALY: BACKEND ERRORS (Server crashing) ---
    '192.168.1.10 - - [28/Jul/2026:10:12:10 +0000] "GET /api/v1/user/101 HTTP/1.1" 500 256',
    '192.168.1.10 - - [28/Jul/2026:10:12:20 +0000] "GET /api/v1/user/101 HTTP/1.1" 500 256',
    '192.168.1.10 - - [28/Jul/2026:10:12:30 +0000] "GET /api/v1/user/101 HTTP/1.1" 500 256',
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
    '10.0.0.6 - - [28/Jul/2026:10:15:20 +0000] "GET /health HTTP/1.1" 200 12',
    '192.168.1.62 - - [28/Jul/2026:10:15:25 +0000] "GET /api/v1/user/167 HTTP/1.1" 200 512',
    '192.168.1.63 - - [28/Jul/2026:10:15:35 +0000] "GET /api/v1/user/168 HTTP/1.1" 200 511',
    '10.0.0.5 - - [28/Jul/2026:10:15:45 +0000] "GET /api/v1/metrics HTTP/1.1" 200 4505',
    '192.168.1.64 - - [28/Jul/2026:10:16:01 +0000] "GET /api/v1/user/170 HTTP/1.1" 200 512',
    '192.168.1.65 - - [28/Jul/2026:10:16:10 +0000] "GET /api/v1/user/172 HTTP/1.1" 200 519',
    '10.0.0.6 - - [28/Jul/2026:10:16:20 +0000] "GET /health HTTP/1.1" 200 12',
    '192.168.1.66 - - [28/Jul/2026:10:16:30 +0000] "GET /api/v1/user/175 HTTP/1.1" 200 517'

          # Tests your JSON trap
    ],
    "syslog": [
        'Jul 28 09:01:10 web-node-01 systemd[1]: Started Periodic Command Scheduler.',
        'Jul 28 09:02:15 web-node-01 sshd[22941]: Invalid user admin from 192.168.1.100 port 44321',
        'Jul 28 09:02:18 web-node-01 sshd[22941]: Connection closed by authenticating user root 10.0.0.5 port 55123'
    ],
    "bgl": [
     # --- NORMAL KERNEL OPERATIONS ---
    '- 1117838570 2005.06.14 R02-M1-N0-C:J12-U11 RAS KERNEL INFO instruction cache parity error corrected',
    '- 1117838570 2005.06.14 R02-M1-N0-C:J12-U11 RAS KERNEL INFO 163464848 double-hummer alignment exceptions',
    '- 1117838571 2005.06.14 R02-M1-N0-C:J12-U11 RAS KERNEL INFO generating core.1025',
    '- 1117838572 2005.06.14 R02-M0-N1-C:J02-U01 RAS KERNEL INFO instruction cache parity error corrected',
] + [
    # --- REPEATED NORMAL TRAFFIC (50 lines across different nodes) ---
    f'- {1117838600+i} 2005.06.14 R03-M{i%2}-N{i%4}-C:J12-U11 RAS KERNEL INFO instruction cache parity error corrected' for i in range(50)
] + [
    # --- ANOMALY: MACHINE CHECK / HARDWARE FAILURE ---
    'FATAL 1117838670 2005.06.14 R02-M1-N0-C:J12-U11 RAS KERNEL FATAL machine check interrupt',
    'FATAL 1117838671 2005.06.14 R02-M1-N0-C:J12-U11 RAS KERNEL FATAL data storage interrupt',
    'ERROR 1117838675 2005.06.14 R04-M0-N4-C:J05-U01 RAS APP ERROR uncaught error: memory protection fault at 0x00004500',
    'ERROR 1117838680 2005.06.14 R04-M0-N4-C:J05-U01 RAS APP ERROR uncaught error: segmentation fault at 0x000089ff',

    # --- ANOMALY: KERNEL PANIC & REBOOTS ---
    'FATAL 1118000001 2005.06.15 R12-M1-N2-C:J10-U01 RAS KERNEL FATAL panic: buffer overflow in network stack',
    'FATAL 1118000002 2005.06.15 R12-M1-N2-C:J10-U01 RAS KERNEL FATAL unexpected termination of compute process',
    'INFO 1118000010 2005.06.15 R12-M1-N2-C:J10-U01 RAS KERNEL INFO rebooting node due to critical failure',

    # --- ANOMALY: NETWORK / LINK FAILURE ---
    'ERROR 1118100000 2005.06.16 R00-M0-N0-I:J18-U11 RAS BRIDGE ERROR tree link failure on link 0',
    'ERROR 1118100001 2005.06.16 R00-M0-N0-I:J18-U11 RAS BRIDGE ERROR tree link failure on link 1',
    'ERROR 1118100005 2005.06.16 R00-M0-N0-I:J18-U11 RAS BRIDGE ERROR packet discarded: checksum error',

    # --- SYSTEM MAINTENANCE ---
    '- 1118200000 2005.06.17 R01-M0-N0-C:J01-U01 RAS MONITOR INFO threshold exceeded: temperature is 45C',
    '- 1118200010 2005.06.17 R01-M0-N0-C:J01-U01 RAS MONITOR INFO fan speed adjusted to 3500 RPM',

    # --- MORE NORMAL TRAFFIC ---
    '- 1118300001 2005.06.18 R05-M1-N8-C:J12-U11 RAS KERNEL INFO instruction cache parity error corrected',
    '- 1118300005 2005.06.18 R05-M1-N8-C:J12-U11 RAS KERNEL INFO double-hummer alignment exceptions',
    '- 1118300010 2005.06.18 R06-M0-N2-C:J12-U11 RAS KERNEL INFO instruction cache parity error corrected',
    '- 1118300015 2005.06.18 R06-M0-N2-C:J12-U11 RAS KERNEL INFO generating core.5012'
],
    "postgres": [
        # --- NORMAL TRAFFIC (Connections and CRUD) ---
    '2026-07-28 10:00:01.123 UTC [1001] postgres@app_db LOG:  statement: SELECT * FROM users WHERE id = 101;',
    '2026-07-28 10:00:02.456 UTC [1002] app_user@app_db LOG:  statement: SELECT name, email FROM users WHERE status = "active";',
    '2026-07-28 10:00:03.789 UTC [1003] postgres@app_db LOG:  statement: INSERT INTO audit_logs (user_id, action) VALUES (101, "login");',
    '2026-07-28 10:00:04.111 UTC [1001] postgres@app_db LOG:  statement: UPDATE users SET last_login = NOW() WHERE id = 101;',
    '2026-07-28 10:00:05.222 UTC [1004] reporter@app_db LOG:  statement: SELECT count(*) FROM orders WHERE created_at > "2026-01-01";',
    '2026-07-28 10:00:10.001 UTC [1005] [unknown]@[unknown] LOG:  connection received: host=192.168.1.50 port=54321',
    '2026-07-28 10:00:10.005 UTC [1005] app_user@app_db LOG:  connection authorized: user=app_user database=app_db',
    '2026-07-28 10:00:15.555 UTC [1001] postgres@app_db LOG:  statement: SELECT * FROM products LIMIT 20 OFFSET 0;',
    '2026-07-28 10:00:20.123 UTC [1002] app_user@app_db LOG:  statement: SELECT * FROM categories;',
    '2026-07-28 10:00:25.888 UTC [1003] postgres@app_db LOG:  statement: COMMIT;',
    
    # --- REPEATED NORMAL PATTERN (50 lines) ---
] + [f'2026-07-28 10:10:{i:02d}.000 UTC [{1100+i}] app_user@app_db LOG:  statement: SELECT * FROM orders WHERE id = {5000+i};' for i in range(50)] + [

    # --- ANOMALY: DATABASE ERRORS (Syntax & Constraints) ---
    '2026-07-28 10:20:01.001 UTC [1001] app_user@app_db ERROR:  syntax error at or near "SELECC" at character 1',
    '2026-07-28 10:20:01.001 UTC [1001] app_user@app_db STATEMENT:  SELECC * FROM users;',
    '2026-07-28 10:20:05.123 UTC [1002] app_user@app_db ERROR:  duplicate key value violates unique constraint "users_email_key"',
    '2026-07-28 10:20:05.123 UTC [1002] app_user@app_db DETAIL:  Key (email)=(test@example.com) already exists.',
    '2026-07-28 10:20:10.555 UTC [1003] app_user@app_db ERROR:  column "non_existent_col" does not exist at character 8',
    '2026-07-28 10:20:15.999 UTC [1004] app_user@app_db FATAL:  terminating connection due to administrator command',

    # --- ANOMALY: SECURITY ATTACK (SQL Injection) ---
    '2026-07-28 10:30:01.001 UTC [2001] hacker@app_db LOG:  statement: SELECT * FROM users WHERE id = 1 OR 1=1;',
    '2026-07-28 10:30:02.002 UTC [2001] hacker@app_db LOG:  statement: SELECT * FROM users WHERE id = 1; DROP TABLE users;--',
    '2026-07-28 10:30:03.003 UTC [2001] hacker@app_db LOG:  statement: SELECT pg_sleep(10);',
    '2026-07-28 10:30:04.004 UTC [2001] hacker@app_db LOG:  statement: SELECT * FROM users WHERE username = "admin" AND password = "password" UNION SELECT null, pg_read_file("/etc/passwd"), null;',
    
    # --- ANOMALY: UNAUTHORIZED ACCESS ---
    '2026-07-28 10:40:01.001 UTC [3001] [unknown]@app_db FATAL:  password authentication failed for user "postgres"',
    '2026-07-28 10:40:02.002 UTC [3001] [unknown]@app_db FATAL:  password authentication failed for user "postgres"',
    '2026-07-28 10:40:03.003 UTC [3001] [unknown]@app_db FATAL:  password authentication failed for user "postgres"',
    '2026-07-28 10:40:04.004 UTC [3001] [unknown]@app_db FATAL:  password authentication failed for user "postgres"',

    # --- SYSTEM MAINTENANCE (Background noise) ---
    '2026-07-28 10:50:01.001 UTC [501]  LOG:  checkpoint starting: time',
    '2026-07-28 10:52:05.123 UTC [501]  LOG:  checkpoint complete: wrote 45 buffers (0.1%); 0 transaction log file(s) added',
    '2026-07-28 10:55:01.001 UTC [502]  LOG:  autovacuum launcher started',
    
    # --- MORE NORMAL TRAFFIC ---
    '2026-07-28 11:00:01.111 UTC [4001] app_user@app_db LOG:  statement: SELECT * FROM settings WHERE key = "theme";',
    '2026-07-28 11:00:05.222 UTC [4002] app_user@app_db LOG:  statement: SELECT * FROM notifications WHERE user_id = 101 AND read = false;',
    '2026-07-28 11:00:10.333 UTC [4003] app_user@app_db LOG:  statement: BEGIN;',
    '2026-07-28 11:00:15.444 UTC [4003] app_user@app_db LOG:  statement: UPDATE profile SET bio = "Hello world" WHERE user_id = 101;',
    '2026-07-28 11:00:20.555 UTC [4003] app_user@app_db LOG:  statement: COMMIT;'
    ],
    "hdfs":[ # --- NORMAL BLOCK REPLICATION (The Life Cycle) ---
    '2026-07-28 10:00:01,001 INFO org.apache.hadoop.hdfs.server.datanode.DataNode: Receiving block BP-10.0.0.1-12345:blk_1073741825 src: /10.0.0.5:50010 dest: /10.0.0.6:50010',
    '2026-07-28 10:00:01,050 INFO org.apache.hadoop.hdfs.server.datanode.DataNode: PacketResponder: block BP-10.0.0.1-12345:blk_1073741825, terminating',
    '2026-07-28 10:00:01,100 INFO org.apache.hadoop.hdfs.server.datanode.DataNode: Received block BP-10.0.0.1-12345:blk_1073741825 of size 67108864 from /10.0.0.5',
    '2026-07-28 10:00:05,001 INFO org.apache.hadoop.hdfs.server.namenode.FSNamesystem: BLOCK* NameSystem.addStoredBlock: blockMap updated: 10.0.0.6:50010 is added to blk_1073741825 size 67108864',
] + [
    # --- REPEATED NORMAL TRAFFIC (50 lines of different blocks) ---
    f'2026-07-28 10:10:{i:02d},000 INFO org.apache.hadoop.hdfs.server.datanode.DataNode: Receiving block BP-10.0.0.1-12345:blk_{2000+i} src: /10.0.0.5:50010 dest: /10.0.0.6:50010' for i in range(50)
] + [
    # --- NORMAL: Heartbeats and Verification ---
    '2026-07-28 10:20:01,001 INFO org.apache.hadoop.hdfs.server.datanode.DataNode: BlockVerificationServer: Verification succeeded for blk_1073741825',
    '2026-07-28 10:20:10,000 INFO org.apache.hadoop.hdfs.server.datanode.DataNode: DataNode.run: Sending heartbeat to NameNode',
    
    # --- ANOMALY: DATA LOSS / DISK FAILURE ---
    '2026-07-28 10:30:01,001 ERROR org.apache.hadoop.hdfs.server.datanode.DataNode: DataNode.run: java.io.IOException: No space left on device',
    '2026-07-28 10:30:05,123 WARN org.apache.hadoop.hdfs.server.datanode.DataNode: Failed to place shadow copy of block blk_1073742000 on DataNode 10.0.0.7:50010',
    '2026-07-28 10:30:10,555 ERROR org.apache.hadoop.hdfs.server.datanode.DataNode: org.apache.hadoop.util.DiskChecker$DiskErrorException: Invalid directory in voldir',

    # --- ANOMALY: NETWORK / TIMEOUTS ---
    '2026-07-28 10:40:01,001 WARN org.apache.hadoop.hdfs.server.datanode.DataNode: Slow notifyNamenode received; execution time 450ms',
    '2026-07-28 10:40:05,002 ERROR org.apache.hadoop.hdfs.server.datanode.DataNode: PacketResponder blk_1073741825: Interrupted exception',
    '2026-07-28 10:40:10,999 INFO org.apache.hadoop.ipc.Server: IPC Server handler 0 on 50010, call getBlockLocations from 10.0.0.5:45210: error java.net.SocketTimeoutException',
    
    # --- ANOMALY: UNAUTHORIZED ACCESS ATTEMPTS ---
    '2026-07-28 10:50:01,001 WARN org.apache.hadoop.security.UserGroupInformation: PrivilegedActionException as:bad_user (auth:SIMPLE) cause:org.apache.hadoop.security.AccessControlException: Permission denied',
    '2026-07-28 10:50:02,002 WARN org.apache.hadoop.security.UserGroupInformation: PrivilegedActionException as:bad_user (auth:SIMPLE) cause:org.apache.hadoop.security.AccessControlException: Permission denied',

    # --- SYSTEM MAINTENANCE ---
    '2026-07-28 11:00:01,001 INFO org.apache.hadoop.hdfs.server.datanode.DataNode: Deleting block BP-10.0.0.1-12345:blk_1073741825',
    '2026-07-28 11:00:05,222 INFO org.apache.hadoop.hdfs.server.namenode.FSNamesystem: Roll edit log succeeded',
    
    # --- MORE NORMAL TRAFFIC ---
    '2026-07-28 11:10:01,111 INFO org.apache.hadoop.hdfs.server.datanode.DataNode: Receiving block BP-10.0.0.1-12345:blk_1073743000 src: /10.0.0.5:50010 dest: /10.0.0.6:50010',
    '2026-07-28 11:10:05,555 INFO org.apache.hadoop.hdfs.server.datanode.DataNode: Received block BP-10.0.0.1-12345:blk_1073743000 of size 128 from /10.0.0.5'
]
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
                
                print(f"   Line {idx} Input  : {line[:90]}..." if len(line) > 93 else f"   Line {idx} Input  : {line}")
                print(f"   Mined Template : {parsed['template_str']}")
                print(f"   Extracted Parameters : {parsed['params']}")
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
