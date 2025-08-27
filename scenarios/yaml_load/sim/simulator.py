import time
import asyncio
import aiohttp
import os
import requests
import random
from utils.abstract_scenario import BaseSimulation

class YAML_Load(BaseSimulation):
    @property
    def name(self) -> str:
        return "YAML_Unsafe_Load"
    
    def get_data_dir(self):
        return "yaml_load" 
    
    def cleanup(self):
        pass
    
    async def worker(self, session:aiohttp.ClientSession):
        await asyncio.sleep(random.uniform(0, 5))
        base_dir = os.path.dirname(os.path.abspath(__file__))
        dataDir = os.path.join(base_dir, "yaml_files")
        url = "http://0.0.0.0:8000/yaml_upload/testuser@example.com"
        files = [f"{dataDir}/{f}" for f in os.listdir(dataDir) if os.path.isfile(os.path.join(dataDir, f))]
        try:
            filePath = random.choice(files)
            with open(filePath, "rb") as f:
                form = aiohttp.FormData()
                form.add_field(
                    name="file",
                    value=f,
                    filename=filePath,
                    content_type="application/x-yaml"
                )
                async with session.post(url, data=form) as response:
                    response_text = await response.text()
        except Exception as e:
            pass

    def call_exploit(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        filePath = f"{base_dir}/exploit.yaml" 
        url = "http://0.0.0.0:8000/yaml_upload/exploituser@example.com"

        with open(filePath, 'rb') as f:
            files = {"file": (filePath, f, "application/x-yaml")}
            response = requests.post(url, files=files)
        f.close()
