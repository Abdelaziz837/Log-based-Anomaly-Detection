from processors.parser import LogParser
from processors.embedder import LogEmbedder

# 1. Initialize both components
# You can change log_type to 'nginx', 'hdfs', etc.
parser = LogParser(log_type="postgres") 
embedder = LogEmbedder()

# 2. Test with a sample log
raw_log = '2026-07-28 10:00:01.123 UTC [1001] postgres@app_db LOG:  statement: SELECT * FROM users WHERE id = 101;'

# 3. Parse to get the Template
parsed_result = parser.parse(raw_log)
template = parsed_result['template_str']
print(f"[*] Parser Output: {template}")

# 4. Embed to get the Vector
vector = embedder.embed(template)

print("-" * 30)
print(f"[*] AI Vector Length: {len(vector)}") # Should be 384
print(f"[*] First 5 Vector Values: {vector[:5]}")
print("-" * 30)