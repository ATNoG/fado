from __future__ import annotations

from multiprocessing import Process, Event, Queue
from ..policy_alerts import AlertSeverity, Alert
from numpy import isneginf, array as np_array
from collections import deque
from queue import Full, Empty
from config import TOLERANCE
from pathlib import Path
from pickle import load

class BpfTrackedContainer:
    '''Represents a container being tracked by eBPF'''

    def __init__(self, image: str, container_id: str, model_path: Path, pod_name: str, node_name: str, queue: Queue[list[list[int]]], alerts: Queue[Alert] | None, run_process: bool=True):
        self.image = image
        self.container_id = container_id
        self.pod_name = pod_name
        self.node_name = node_name
        self.queue = queue
        self.run_process = run_process
        self.alerts = alerts

        # load the model
        with open(model_path, 'rb') as f:
            saved_data = load(f)

        self.model = saved_data['model']
        self.threshold = saved_data['threshold']
        self.window_size = saved_data['window_size']
        self.whitelist = saved_data['whitelist']

        if self.run_process:
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
            except Empty:
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
                    # print('[-] Anomaly detected')
                    # TODO: always high alert severity?? this should probably be dependent on the syscall sequence
                    if self.alerts != None:
                        try:
                            # TODO: should this have a timeout just to avoid unnecessary alert losses?
                            # we cannot hold this process back if the alert manager decides to hang or is just too slow
                            alert = Alert(self.node_name, self.pod_name, self.container_id, AlertSeverity.High, window)
                            self.alerts.put(alert, block=False, timeout=None)
                        except Full:
                            pass

            windows.clear()
