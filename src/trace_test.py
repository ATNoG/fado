from numpy import isneginf, array as np_array
from collections import defaultdict
from utils import FILES, TOLERANCE
from collections import deque
from threading import Lock
from queue import Queue
from probe import Probe
from pickle import load
from time import sleep
from sys import exit
import os

def trace(mntns: str):
    # model_file = os.path.join(FILES, model_file) + ".pkl"
    # # load the model
    # with open(model_file, 'rb') as f:
    #     saved_data = load(f)
    #     # model = saved_data['model']
    #     # threshold = saved_data['threshold']
    #     window_size = saved_data['window_size']
    #     # whitelist = saved_data['whitelist']

    lock = Lock()
    queues = Probe(2, mntns, lock).get_queues()

    print("started")
    # bruh = defaultdict(int)
    while True:
        with lock:
            for key in queues.keys():
                print(f"size: {queues[key]} ", end='', flush=False)
            print("\t\t\t\t\t\t\t\r", end='', flush=True)
            sleep(0.1)

            # bruh[event.mnt_ns_id] += 1
            # # print(f"\rmnt ns id: {event.mnt_ns_i}", end='', flush=True)
            # for key in bruh.keys():
            #     print(f"size: {bruh[key]} ", end='', flush=False)
            # print("\t\t\t\t\t\r", end='', flush=True)

    # while True:
    #     for key in queues.copy().keys():
    #         queues[key].get()
    #         counter = 1
    #         while not queues[key].empty():
    #             queues[key].get_nowait()
    #             counter += 1
    #         print(f"size: {counter} ", end='')
    #     print("\n", end='', flush=True)

    # results = deque([0] * 10, maxlen=10)
    # data = []
    # try:
    #     while True:
    #         data += queue.get()
    #         while not queue.empty():
    #             data += queue.get_nowait()
    #         data.sort(key=lambda e: e[0])
    #         flag = 0
    #         for sequence in data:
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
    #             print(f"Anomaly detected")
    #         data.clear()
    # except KeyboardInterrupt:
    #     probe.end_trace()
    #     data = queue.get(block=True)

if __name__ == "__main__":
    import sys
    trace("/sys/fs/bpf/mnt_ns_set")
