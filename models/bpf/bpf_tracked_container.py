from ..security_alert import SecurityAlert, AlertSeverity, SecurityMeasure
from config import TOLERANCE, POLICY_CONTROLLER
from numpy import isneginf, array as np_array
from collections import defaultdict, deque
from threading import Thread, Event
import requests, subprocess
from pathlib import Path
from pickle import load
from queue import Queue

class BpfTrackedContainer:
    """Represents a container being tracked by eBPF"""

    def __init__(self, image: str, container_id: str, model_path: Path, pod_name: str, node_name: str, queue: Queue[tuple[int, int]], apply_policies=True):
        self.image = image
        self.container_id = container_id
        self.pod_name = pod_name
        self.node_name = node_name
        self.queue = queue
        self.apply_policies = apply_policies
        self.thread_event = Event()
        self.thread = Thread(target=self.get_windows, daemon=True)
        self.thread.start()

        # load the model
        with open(model_path, 'rb') as f:
            saved_data = load(f)
            self.model = saved_data['model']
            self.threshold = saved_data['threshold']
            self.window_size = saved_data['window_size']
            self.whitelist = saved_data['whitelist']

    def stop(self):
        self.thread_event.set()
        self.thread.join()

    def get_windows(self):
        windows = defaultdict(list[int])
        results = deque([0] * 10, maxlen=10)
        while not self.thread_event.is_set():
            try:
                tid, sid = self.queue.get(block=True, timeout=0.1)
            except:
                continue

            windows[tid].append(sid)
            if len(windows[tid]) > self.window_size:
                windows[tid].pop(0)

            if len(windows[tid]) == self.window_size:
                results.append(self.run_model(windows[tid]))

                if sum(results) > len(results) * TOLERANCE:
                    print('[-] Anomaly detected')
                    if self.apply_policies and self.apply_policy():
                        return

    def run_model(self, window: list[int]) -> int:
        # data = []
        # while True:
            # data += queue.get()
            # while not queue.empty():
            #     data += queue.get_nowait()
            # data.sort(key=lambda e: e[0]) # TODO: why the sort??

        if tuple(window) in self.whitelist:
            return 0

        seq = np_array(window).reshape(-1,1)
        score = self.model.score(seq, [len(window)])
        return (1 if score < self.threshold or isneginf(score) else 0)

    def apply_policy(self) -> bool:
        # TODO: what to do with the thread after applying the policy??
        try:
            security_alert = SecurityAlert(node_name=self.node_name, pod_name=self.pod_name, container_id=self.container_id, severity=AlertSeverity.High)
            response = requests.post(f'{POLICY_CONTROLLER}/api/alerts', json=security_alert.model_dump(mode='json'), timeout=2)
            response.raise_for_status()

            security_measure = SecurityMeasure(response.json())
            match security_measure:
                case SecurityMeasure.Nothing:
                    pass
                case SecurityMeasure.Kill:
                    subprocess.run(['crictl', 'stop', '--timeout', '0', self.container_id], capture_output=True, text=True, check=True)
                    print('Got "kill" as a security policy')
                    return True
                case _:
                    raise RuntimeError('Invalid SecurityMeasure value.')
        except Exception as e:
            print(e)
            print('[WARNING] Could not get/apply policy for anomaly!')

        return False
