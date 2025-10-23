from numpy import isneginf, array as np_array
from probe import Probe
from pickle import load
from collections import defaultdict, deque
import os
from utils import FILES, TOLERANCE

def trace(model_file:str, mntns:str="/sys/fs/bpf/mnt_ns_set"):
    model_file = os.path.join(FILES, model_file) + ".pkl"

    with open(model_file, 'rb') as f:
        saved_data = load(f)
        model = saved_data['model']
        threshold = saved_data['threshold']
        window_size = saved_data['window_size']
        whitelist = saved_data['whitelist']

    probe = Probe(mntns)
    results = deque([0] * 10, maxlen=10)
    data = []

    try:
        while True:
            data += probe.get_data()
            flag = 0
            
            tid_counts = defaultdict(int)
            for _, tid, _ in data:
                tid_counts[tid] += 1
            
            filtered_data = []
            grouped = defaultdict(list)

            for ts, tid, sid in data:
                if tid_counts[tid] < window_size:
                    filtered_data.append([ts, tid, sid])
                else:
                    grouped[tid].append(sid)

            if grouped:
                for tid, syscalls in grouped.items():
                    for i in range(0, len(syscalls) - window_size + 1):

                        sequence = syscalls[i:i + window_size]
                        if tuple(sequence) in whitelist:
                            results.append(0)
                        else:
                            seq = np_array(sequence).reshape(-1,1)
                            score = model.score(seq, [len(sequence)])
                            results.append(1 if score < threshold or isneginf(score) else 0)
                        if sum(results) > len(results) * TOLERANCE:
                            flag = 1

                    if flag == 1:
                        print(f"Anomaly in thread {tid}")

                grouped.clear()
            results = deque([0] * 10, maxlen=10)
            data = filtered_data

    except KeyboardInterrupt:
        data = probe.end_trace()
        flag = 0

        if len(data) > 0:
            grouped = defaultdict(list)

            for _, tid, sid in data:
                grouped[tid].append(sid)
            data.clear()

            for tid, syscalls in grouped.items():
                for i in range(0, len(syscalls) - window_size + 1):

                    sequence = syscalls[i:i + window_size]
                    seq = np_array(sequence).reshape(-1,1)
                    score = model.score(seq, [len(sequence)])
                    results.append(1 if score < threshold or isneginf(score) else 0)
                    if sum(results) > len(results) * TOLERANCE:
                        flag = 1

                if flag == 1:
                    print(f"Anomaly in thread {tid}")
            grouped.clear()