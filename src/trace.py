from numpy import isneginf, array as np_array
from utils import FILES, TOLERANCE
from collections import deque
from queue import Queue
from probe import Probe
from pickle import load
import os

def trace(model_file: str, mntns: str):
    model_file = os.path.join(FILES, model_file) + ".pkl"

    # load the model
    with open(model_file, 'rb') as f:
        saved_data = load(f)
        model = saved_data['model']
        threshold = saved_data['threshold']
        window_size = saved_data['window_size']
        whitelist = saved_data['whitelist']

    queue = Queue(maxsize=1000)
    probe = Probe(queue, window_size, mntns)
    results = deque([0] * 10, maxlen=10)
    data = []

    try:
        while True:
            data += queue.get()
            while not queue.empty():
                data += queue.get_nowait()
            data.sort(key=lambda e: e[0])

            flag = 0
            for sequence in data:
                if tuple(sequence) in whitelist:
                    results.append(0)
                    continue
                else:
                    seq = np_array(sequence).reshape(-1,1)
                    score = model.score(seq, [len(sequence)])
                    results.append(1 if score < threshold or isneginf(score) else 0)
                if sum(results) > len(results) * TOLERANCE:
                    flag = 1

            if flag == 1:
                print(f"Anomaly detected")
            data.clear()

    except KeyboardInterrupt:
        probe.end_trace()
        data = queue.get(block=True)

if __name__ == "__main__":
    import sys
    trace(sys.argv[1], "/sys/fs/bpf/mnt_ns_set")
