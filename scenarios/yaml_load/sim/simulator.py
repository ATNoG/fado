from models.base_simulation import BaseSimulation
import asyncio, aiohttp, os, requests, random
from pathlib import Path

class YAML_Load(BaseSimulation):
    @property
    def name(self) -> str:
        return 'YAML_Unsafe_Load'

    def get_data_dir(self):
        return 'yaml_load'

    def cleanup(self):
        pass

    async def worker(self, session:aiohttp.ClientSession):
        await asyncio.sleep(random.uniform(0, 5))
        dataDir = Path.cwd() / 'yaml_files'
        url = 'http://127.0.0.1:8000/yaml_upload/test@exploit.com'
        files = [f'{dataDir}/{f}' for f in os.listdir(dataDir) if os.path.isfile(os.path.join(dataDir, f))]
        try:
            filePath = random.choice(files)
            with open(filePath, 'rb') as f:
                form = aiohttp.FormData()
                form.add_field(
                    name='file',
                    value=f,
                    filename=filePath,
                    content_type='application/x-yaml'
                )

                async with session.post(url, data=form) as response:
                    await response.text()
        except:
            pass

    def call_exploit(self):
        filePath = Path.cwd() / 'exploit.yaml'
        url = 'http://127.0.0.1:8000/yaml_upload/test@exploit.com'

        with open(filePath, 'rb') as f:
            files = {'file': (f'{filePath}', f, 'application/x-yaml')}
            requests.post(url, files=files)
