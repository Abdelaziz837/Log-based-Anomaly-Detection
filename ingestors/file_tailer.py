import asyncio
import os

class AsyncTailer:
    def __init__(self, file_path):
        self.file_path = file_path

    async def tail(self):
        while not os.path.exists(self.file_path):
            await asyncio.sleep(1)

        # Using standard 'r' mode
        with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
            # Jump to end initially
            f.seek(0, os.SEEK_END)
            last_pos = f.tell()

            while True:
                line = f.readline()
                if not line:
                    await asyncio.sleep(0.1)
                    # Check if file was truncated/wiped
                    if os.path.exists(self.file_path):
                        curr_size = os.path.getsize(self.file_path)
                        if curr_size < last_pos:
                            print("[!] Log reset detected. Rewinding...")
                            f.seek(0)
                        last_pos = f.tell()
                    continue
                
                yield line.strip()
                last_pos = f.tell()