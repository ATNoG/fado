# TODO: this is a hack to make this code work on older versions of Python. Should i switch to uv??
from __future__ import annotations

from ..security_alert import SecurityAlert, AlertSeverity
from multiprocessing import Process, Event, Queue
from config import TOLERANCE, POLICY_CONTROLLER
from numpy import isneginf, array as np_array
from ..policy_config import ActionType
import requests, subprocess, logging
from collections import deque
from pathlib import Path
from pickle import load

class BpfTrackedContainer:
    '''Represents a container being tracked by eBPF'''

    def __init__(self, image: str, container_id: str, model_path: Path, pod_name: str, node_name: str, queue: Queue[list[list[int]]], run_process: bool=True, apply_policies=True):
        self.image = image
        self.container_id = container_id
        self.pod_name = pod_name
        self.node_name = node_name
        self.queue = queue
        self.run_process = run_process

        # load the model
        with open(model_path, 'rb') as f:
            saved_data = load(f)

        self.model = saved_data['model']
        self.threshold = saved_data['threshold']
        self.window_size = saved_data['window_size']
        self.whitelist = saved_data['whitelist']

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        if not self.logger.hasHandlers():
            self.logger.addHandler(handler)

        if self.run_process:
            self.apply_policies = apply_policies
            self.process_event = Event()
            self.process = Process(target=self.run, daemon=True)
            self.process.start()

    def stop(self):
        if self.run_process:
            self.process_event.set()
            self.process.join()

    def run(self):
        results = deque([0] * 10, maxlen=10)
        windows = []

        while not self.process_event.is_set():
            try:
                windows += self.queue.get(block=True, timeout=0.1)
            except:
                continue

            while not self.queue.empty():
                windows += self.queue.get_nowait()
            windows.sort(key=lambda e: e[0])

            for window in windows:
                if tuple(window) in self.whitelist:
                    results.append(0)
                    continue
                else:
                    seq = np_array(window).reshape(-1, 1)
                    score = self.model.score(seq, [len(window)])
                    results.append(1 if score < self.threshold or isneginf(score) else 0)

                if sum(results) > len(results) * TOLERANCE:
                    print('[-] Anomaly detected')
                    if self.apply_policies and self.apply_policy(window):
                        return

            windows.clear()

    def apply_policy(self, window: list[int]) -> bool:
        try:
            security_alert = SecurityAlert(node_name=self.node_name, pod_name=self.pod_name, container_id=self.container_id, severity=AlertSeverity.High, window=window)
            response = requests.post(f'{POLICY_CONTROLLER}/api/alerts', json=security_alert.model_dump(mode='json'), timeout=2)
            response.raise_for_status()

            for action in response.json()['actions']:
                action_type = ActionType(action)
                match action_type:
                    case action_type.NOTHING:
                        pass
                    case action_type.LOG:
                        print('Logging the anomaly...')
                        self.logger.warning(f'SECURITY ALERT | '
                            f'Node: {security_alert.node_name} | '
                            f'Pod: {security_alert.node_name} | '
                            f'Container ID: {security_alert.container_id} | '
                            f'Alert severity: {security_alert.severity} | '
                            f'Window: {security_alert.window}'
                        )
                    case action_type.KILL:
                        subprocess.run(['crictl', 'stop', '--timeout', '0', self.container_id], capture_output=True, text=True, check=True)
                        print('Kiling the container...')
                        return True
                    case _:
                        raise RuntimeError('Invalid ActionType value.')
        except Exception as e:
            print(e)
            print('[WARNING] Could not get/apply policy for anomaly!')

        return False
