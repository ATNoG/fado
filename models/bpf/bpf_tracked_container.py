from models import SecurityAlert, AlertSeverity, SecurityMeasure
from config import TOLERANCE, POLICY_CONTROLLER
from numpy import isneginf, array as np_array
from collections import defaultdict, deque
from threading import Thread, Event
from pathlib import Path
from pickle import load
from queue import Queue
import requests

class BpfTrackedContainer:
    """Represents a container being tracked by eBPF"""

    def __init__(self, image: str, container_id: str, model_path: Path, queue: Queue[tuple[int, int]], apply_policies=True):
        self.image = image
        self.container_id = container_id
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
        # wake up the thread (with dummy values) just in case it is stuck waiting for queue events
        self.queue.put((-1, -1))
        self.thread_event.set()
        self.thread.join()

    def get_windows(self):
        windows = defaultdict(list[int])
        results = deque([0] * 10, maxlen=10)
        while not self.thread_event.is_set():
            tid, sid = self.queue.get(block=True, timeout=None)

            # check for dummy wake up values
            if tid == -1 and sid == -1:
                continue

            windows[tid].append(sid)
            if len(windows[tid]) > self.window_size:
                windows[tid].pop(0)

            if len(windows[tid]) == self.window_size:
                results.append(self.run_model(windows[tid]))

                if sum(results) > len(results) * TOLERANCE:
                    print('[-] Anomaly detected')
                    if self.apply_policies:
                        self.apply_policy()

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

    def apply_policy(self):
        try:
            # TODO: get node and pod names
            security_alert = SecurityAlert(node_name="", pod_name="", container_id=self.container_id, severity=AlertSeverity.High)
            response = requests.post(POLICY_CONTROLLER, json=security_alert.model_dump(), timeout=2)
            response.raise_for_status()

            # TODO: apply the policy
            security_measure = SecurityMeasure(**response.json())
        except:
            print('[WARNING] Could not get/apply policy for anomaly!')
