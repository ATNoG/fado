from queue import Queue
from numpy import isneginf, array as np_array
from probe import Probe
import os
from pickle import load
from collections import deque
import os
from utils import FILES, TOLERANCE

def trace(model_file:str, mntns:str="/sys/fs/bpf/mnt_ns_set"):
    model_file = os.path.join(FILES, model_file) + ".pkl"
    queue = Queue(maxsize=1000)
    print(os.getpid())

    with open(model_file, 'rb') as f:
        saved_data = load(f)
        model = saved_data['model']
        threshold = saved_data['threshold']
        window_size = saved_data['window_size']
        whitelist = saved_data['whitelist']


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

            # for ts, tid, sid in data:
            #     grouped[tid].append(sid)

            # if grouped:
            #     for tid, syscalls in grouped.items():
            #         for i in range(0, len(syscalls) - window_size + 1):

            #             sequence = syscalls[i:i + window_size]
            #             if tuple(sequence) in whitelist:
            #                 results.append(0)
            #                 continue
            #             else:
            #                 seq = np_array(sequence).reshape(-1,1)
            #                 score = model.score(seq, [len(sequence)])
            #                 results.append(1 if score < threshold or isneginf(score) else 0)
            #             if sum(results) > len(results) * TOLERANCE:
            #                 flag = 1

            #         if flag == 1:
            #             print(f"Anomaly in thread {tid}")
            #     grouped.clear()

    except KeyboardInterrupt:
        probe.end_trace()
        data = queue.get(block=True)
        # flag = 0

        # if len(data) > 0:
        #     grouped = defaultdict(list)

        #     for _, tid, sid in data:
        #         grouped[tid].append(sid)
        #     data.clear()

        #     for tid, syscalls in grouped.items():
        #         for i in range(0, len(syscalls) - window_size + 1):

        #             sequence = syscalls[i:i + window_size]
        #             seq = np_array(sequence).reshape(-1,1)
        #             score = model.score(seq, [len(sequence)])
        #             results.append(1 if score < threshold or isneginf(score) else 0)
        #             if sum(results) > len(results) * TOLERANCE:
        #                 flag = 1

        #         if flag == 1:
        #             print(f"Anomaly in thread {tid}")
        #     grouped.clear()


if __name__ == "__main__":
    trace("Log4Shell_50s_w3_10p")