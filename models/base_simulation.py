from abc import ABC, abstractmethod
import aiohttp, asyncio, random
from time import time

class BaseSimulation(ABC):
    def __init__(self):
        self.run_exploit = False

    @property
    def syscall_dir(self) -> str:
        file_name = self.get_data_dir()
        return f'{file_name}{'_exploit' if self.run_exploit else ''}'

    def simulate(self, duration: int, stop_sim, run_exploit: bool):
        self.setup()
        asyncio.run(self.trigger_api(duration, stop_sim, run_exploit))

    async def trigger_api(self, duration: int, stop_sim, run_exploit: bool):
        stop_time = None
        if duration > 0:
            stop_time = time() + duration

        connector = aiohttp.TCPConnector(limit=0, force_close=True)
        concurrency = random.randint(1, 50) if not run_exploit else random.randint(20, 150)

        # TODO: this code is a bit repetitive (maybe it could be improved??)
        async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=10), auto_decompress=True) as session:
            start_time = time()
            if stop_time:
                while time() < stop_time:
                    # wait for the event to be set (to end the simulation)
                    if stop_sim.is_set():
                        print('Ending Sim')
                        self.cleanup()
                        return

                    # create the async tasks
                    tasks = []
                    for _ in range(concurrency):
                        task = asyncio.create_task(self.worker(session))
                        tasks.append(task)

                    # print status and wait for the current tasks to finish
                    elapsed = int(time() - start_time)
                    remaining = int(stop_time - time())
                    print(f'\rActive: {len(tasks)} | Elapsed: {elapsed}s | Remaining: {remaining}s')
                    concurrency = random.randint(1,50) if not run_exploit else random.randint(20,150)
                    await asyncio.gather(*tasks, return_exceptions=True)
            else:
                while True:
                    # wait for the event to be set (to end the simulation)
                    if stop_sim.is_set():
                        print('Ending Sim')
                        self.cleanup()
                        return

                    # create the async tasks
                    tasks = []
                    for _ in range(concurrency):
                        task = asyncio.create_task(self.worker(session))
                        tasks.append(task)

                    # print status and wait for the current tasks to finish
                    elapsed = int(time() - start_time)
                    print(f'\rActive: {len(tasks)} | Elapsed: {elapsed}s')
                    concurrency = random.randint(1,50) if not run_exploit else random.randint(20,150)
                    await asyncio.gather(*tasks, return_exceptions=True)

    def set_run_exploit(self, run_exploit: bool):
        self.run_exploit = run_exploit

    @abstractmethod
    def setup(self):
        pass

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def get_data_dir(self) -> str:
        pass

    @abstractmethod 
    async def worker(self, session):
        pass

    @abstractmethod 
    def call_exploit(self):
        pass

    @abstractmethod
    def cleanup(self):
        pass
