import random
from time import time
import aiohttp
from abc import ABC, abstractmethod
import asyncio

class BaseSimulation(ABC):
    def __init__(self):
        self.exploit = False

    @property
    def name(self) -> str:
        return self.name

    @property
    def syscallDir(self) -> str:
        fileName = self.get_data_dir()
        return f"{fileName}{"_exploit" if self.exploit else ""}"

    def simulate(self, duration, stop_sim, exploit=False) -> None:
        asyncio.run(self.trigger_api(duration, stop_sim, exploit=exploit))

    async def trigger_api(self, sim_time, stop_sim, exploit=False):
        if sim_time:
            stop_time = time() + sim_time
        else:
            stop_time = None
        connector = aiohttp.TCPConnector(limit=0, force_close=True)
        concurrency = random.randint(1,50) if not exploit else random.randint(20,150)

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=10),
            auto_decompress=True
        ) as session:
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
                    concurrency = random.randint(1,50) if not exploit else random.randint(20,150)
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
                    concurrency = random.randint(1,50) if not exploit else random.randint(20,150)
                    await asyncio.gather(*tasks, return_exceptions=True)
        
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

    def is_exploit(self, exploit=True) -> None:
        self.exploit = exploit