import asyncio
import os

class AsyncTailer:
    def __init__(self, file_path):
        self.file_path = file_path

    async def tail(self):
      
        while not os.path.exists(self.file_path):
            print(f"[*] [DOCKER DEBUG] Waiting for file at {self.file_path}...")
            await asyncio.sleep(2)

        print(f"[*] [DOCKER DEBUG] Found file! Internal path: {os.path.abspath(self.file_path)}")
        
        
        last_pos = 0 
        
        while True:
            try:
                # FORCE a refresh of the file stats
                stats = os.stat(self.file_path)
                curr_size = stats.st_size

                if curr_size > last_pos:
                    with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        f.seek(last_pos)
                        chunk = f.read(curr_size - last_pos)
                        if chunk:
                            for line in chunk.splitlines():
                                if line.strip():
                                    yield line.strip()
                        last_pos = stats.st_size
                elif curr_size < last_pos:
                    print("[!] [DOCKER DEBUG] Log reset detected (file truncated).")
                    last_pos = 0
                
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"[!] [DOCKER DEBUG] Read Error: {e}")
                await asyncio.sleep(1)