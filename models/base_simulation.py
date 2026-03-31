from abc import ABC, abstractmethod
import aiohttp, asyncio
from time import time
import random

class BaseSimulation(ABC):
    def __init__(self):
        self.run_exploit = False

    @property
    def name(self) -> str:
        return self.name

    @property
    def syscallDir(self) -> str:
        fileName = self.get_data_dir()
        return f"{fileName}{"_exploit" if self.run_exploit else ""}"

    def simulate(self, duration: int, stop_sim, run_exploit: bool) -> None:
        asyncio.run(self.trigger_api(duration, stop_sim, run_exploit))

    async def trigger_api(self, sim_time, stop_sim, run_exploit: bool):
        if sim_time:
            stop_time = time() + sim_time
        else:
            stop_time = None
        connector = aiohttp.TCPConnector(limit=0, force_close=True)
        concurrency = random.randint(1,50) if not run_exploit else random.randint(20,150)

        async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=10), auto_decompress=True) as session:
            start_time = time()
            if stop_time:
                while time() < stop_time:
                    if stop_sim.is_set():
                        print("Ending Sim")
                        self.cleanup()
                        return
                    tasks = []
                    for _ in range(concurrency):
                        task = asyncio.create_task(self.worker(session))
                        tasks.append(task)
                    elapsed = int(time() - start_time)
                    remaining = int(stop_time - time())
                    print(f"\rActive: {len(tasks)} | Elapsed: {elapsed}s | Remaining: {remaining}s")
                    concurrency = random.randint(1,50) if not run_exploit else random.randint(20,150)
                    await asyncio.gather(*tasks, return_exceptions=True)
            else:
                while True:
                    if stop_sim.is_set():
                        print("Ending Sim")
                        self.cleanup()
                        return
                    tasks = []
                    for _ in range(concurrency):
                        task = asyncio.create_task(self.worker(session))
                        tasks.append(task)
                    elapsed = int(time() - start_time)
                    print(f"\rActive: {len(tasks)} | Elapsed: {elapsed}s ")
                    concurrency = random.randint(1,50) if not run_exploit else random.randint(20,150)
                    await asyncio.gather(*tasks, return_exceptions=True)

    def set_run_exploit(self, run_exploit: bool):
        self.run_exploit = run_exploit

    @abstractmethod 
    async def worker(self, session):
        pass

    @abstractmethod 
    def call_exploit(self):
        pass

    @abstractmethod
    def get_data_dir(self) -> str:
        pass

    @abstractmethod
    def cleanup(self):
        pass
