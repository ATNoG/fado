from numpy import isneginf, array as np_array
from collections import defaultdict, deque
from threading import Thread
from utils import TOLERANCE
from pathlib import Path
from pickle import load
from queue import Queue

class BpfContainer:
    """Represents a container being tracked by eBPF"""

    def __init__(self, image: str, container_id: str, model_path: Path, queue: Queue[tuple[int, int]]):
        self.image = image
        self.container_id = container_id
        self.queue = queue
        # TODO: need to stop the thread when container get removed
        self.thread = Thread(target=self.get_windows, daemon=True)
        self.thread.start()

        # load the model
        with open(model_path, 'rb') as f:
            saved_data = load(f)
            self.model = saved_data['model']
            self.threshold = saved_data['threshold']
            self.window_size = saved_data['window_size']
            self.whitelist = saved_data['whitelist']

    def get_windows(self):
        windows = defaultdict(list[int])
        results = deque([0] * 10, maxlen=10)
        while True:
            # while not self.queue.empty():
            tid, sid = self.queue.get(block=True, timeout=None)
            windows[tid].append(sid)

            if len(windows[tid]) > self.window_size:
                windows[tid].pop(0)

            if len(windows[tid]) == self.window_size:
                results.append(self.run_model(windows[tid]))

                if sum(results) > len(results) * TOLERANCE:
                    print(f"Anomaly detected")

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
