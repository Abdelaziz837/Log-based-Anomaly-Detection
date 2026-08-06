import asyncio
from ingestors.file_tailer import AsyncTailer

async def run_test():
    
    log_file = "access.log"
    tailer = AsyncTailer(log_file)

    print(f"--- TAILER TEST STARTED ---")
    try:
        async for line in tailer.tail():
            print(f"[TAILER RECEIVED]: {line.strip()}")
    except KeyboardInterrupt:
        print("\n[*] Test stopped.")

if __name__ == "__main__":
    asyncio.run(run_test())