from threading import Thread
from queue import Queue

class BpfContainer:
    """Represents a container being tracked by eBPF"""

    def __init__(self, image: str, container_id: str, queue: Queue[int]):
        self.image = image
        self.container_id = container_id
        self.queue = queue
        self.thread = Thread(target=self.track, daemon=True)
        self.thread.start()

        # TODO: get model info
        self.window_size = 0

    def track(self):
        window = []
        while True:
            while not self.queue.empty() and len(window) < self.window_size:
                window.append(self.queue.get_nowait())

            if len(window) < self.window_size:
                continue

            assert len(window) == self.window_size
            window.sort(key=lambda e: e[0])


            # flag = 0
            # for sid in window:
            #     if tuple(sequence) in whitelist:
            #         results.append(0)
            #         continue
            #     else:
            #         seq = np_array(sequence).reshape(-1,1)
            #         score = model.score(seq, [len(sequence)])
            #         results.append(1 if score < threshold or isneginf(score) else 0)
            #     if sum(results) > len(results) * TOLERANCE:
            #         flag = 1
            # if flag == 1:
            #     print(f"Anomaly detected")
            # data.clear()
