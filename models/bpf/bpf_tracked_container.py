# TODO: this is a hack to make this code work on older versions of Python. Should i switch to uv??
from __future__ import annotations

from multiprocessing import Process, Event, Queue
from numpy import isneginf, array as np_array
from ..alert_severity import AlertSeverity
from ..policy_rule import ActionType
from collections import deque
from config import TOLERANCE
import subprocess, logging
from pathlib import Path
from pickle import load

class BpfTrackedContainer:
    '''Represents a container being tracked by eBPF'''

    def __init__(self, image: str, container_id: str, model_path: Path, pod_name: str, node_name: str, queue: Queue[list[list[int]]], active_policies, run_process: bool=True, apply_policies=True):
        self.image = image
        self.container_id = container_id
        self.pod_name = pod_name
        self.node_name = node_name
        self.queue = queue
        self.run_process = run_process
        self.active_policies = active_policies

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
                    # TODO: always high alert severity??
                    if self.apply_policies and self.apply_policy(AlertSeverity.High, window):
                        return

            windows.clear()

    def evaluate_alert(self, alert_severity: AlertSeverity) -> list[ActionType]:
        # must be a list to ensure action order
        triggered_actions: list[ActionType] = []

        for rule in self.active_policies.values():
            if rule.match.alert_severity != alert_severity:
                continue

            for action in rule.actions:
                if action not in triggered_actions:
                    triggered_actions.append(action)

        if not triggered_actions:
            return [ActionType.NOTHING]

        return triggered_actions

    def apply_policy(self, alert_severity: AlertSeverity, window: list[int]) -> bool:
        for action in self.evaluate_alert(alert_severity):
            match action:
                case ActionType.NOTHING:
                    pass
                case ActionType.LOG:
                    self.logger.warning(f'SECURITY ALERT | '
                        f'Node: {self.node_name} | '
                        f'Pod: {self.pod_name} | '
                        f'Container ID: {self.container_id} | '
                        f'Alert severity: {alert_severity} | '
                        f'Window: {window}'
                    )
                case ActionType.KILL:
                    subprocess.run(['crictl', 'stop', '--timeout', '0', self.container_id], capture_output=True, text=True, check=True)
                    return True
                case _:
                    raise RuntimeError('Invalid ActionType value.')

        return False
