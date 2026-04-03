from models.base_simulation import BaseSimulation
import asyncio, aiohttp, os, requests, random
from .gen_data import gen_data
from pathlib import Path

class YAML_Load(BaseSimulation):
    def __init__(self):
        super().__init__()
        self.url = 'http://127.0.0.1:8000/yaml_upload/test@exploit.com'
        self.data_dir = Path.cwd() / 'scenarios' / 'yaml_load' / 'sim' / 'yaml_files'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        gen_data(self.data_dir)

    def name(self) -> str:
        return 'YAML_Unsafe_Load'

    def get_data_dir(self):
        return 'yaml_load'

    async def worker(self, session: aiohttp.ClientSession):
        await asyncio.sleep(random.uniform(0, 5))
        files = [f'{self.data_dir}/{f}' for f in os.listdir(self.data_dir) if os.path.isfile(os.path.join(self.data_dir, f))]

        file_path = random.choice(files)
        with open(file_path, 'rb') as f:
            form = aiohttp.FormData()
            form.add_field(name='file', value=f, filename=file_path, content_type='application/x-yaml')

            async with session.post(self.url, data=form) as response:
                await response.text()

    def call_exploit(self):
        file_path = Path.cwd() / 'scenarios' / 'yaml_load' / 'exploit.yml'
        with open(file_path, 'rb') as f:
            files = {'file': (f'{file_path}', f, 'application/x-yaml')}
            requests.post(self.url, files=files)

    def cleanup(self):
        pass
