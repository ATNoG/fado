from utils import BaseSimulation, Scenario, ScenarioManager, DB
from probe import Probe, SysdigProbe
from multiprocessing import Lock, Process, Event
from .cleanup_data import cleanup
from queue import Queue
import os
from random import random
from time import sleep

def monitor_data(
        scenario:BaseSimulation,
        data_path:str, 
        stop_sim, 
        exploit_flag, 
        mntns:str, 
        window_size:int, 
        limit:int
        ):
    
    output = open(data_path, "w")
    counter = 0
    queue = Queue(maxsize=1000)
    data = []
    chance = 0.005
    triggered_exploit = False
    flag = 0
    # counters = {}
    # output_list = {}
    # windows = [2, 3, 4, 6, 8, 10]

    # for i in windows:
    #     # counters[i] = 0
    #     fn = data_path.replace("WSIZE", str(i))
    #     output_list[i] = open(fn, 'w')

    probe = Probe(queue, window_size, mntns)

    while True: 
        flag = 0
        if stop_sim.is_set() or (limit and counter >= limit):
        # if stop_sim.is_set():
            if not stop_sim.is_set(): stop_sim.set()
            if exploit_flag and not triggered_exploit:
                scenario.call_exploit()
                print("Exploit")
                flag = 1
            probe.end_trace()
            data += queue.get(block=True, timeout=1)
            for sequence in data:
                    output.write(f"{','.join(map(str, sequence))},{flag}\n")
            counter += len(data) * window_size
            # for window in windows:
            #     output = output_list[window]
            #     entry = probe.gen_sliding_window(data, window)
            #     for sequence in entry:
            #         output.write(f"{','.join(map(str, sequence))},{flag}\n")
            # data.clear()

            if limit > 0: print(f"Limit exceeded by {counter - limit} syscalls")
        else:
            data += queue.get(block=True)
            while not queue.empty():
                data += queue.get_nowait()
            data.sort(key=lambda e: e[0])

            for sequence in data:
                    output.write(f"{','.join(map(str, sequence))},{flag}\n")
            counter += len(data) * window_size

            counter += len(data) * window_size

            if exploit_flag and random() < chance:
                scenario.call_exploit()
                chance /= 50
                triggered_exploit = True
                print("Exploit")
                flag = 1

                data += queue.get(block=True)
                while not queue.empty():
                    data += queue.get_nowait()
                data.sort(key=lambda e: e[0])

                for sequence in data:
                    output.write(f"{','.join(map(str, sequence))},{flag}\n")
                counter += len(data) * window_size

            # for window in windows:
            #     output = output_list[window]
            #     entry_dict = probe.gen_sliding_window(data, window)
            #     for _, syscalls in entry_dict.items():
            #         if syscalls == []:
            #             continue
            #         for sequence in syscalls:
            #             output.write(f"{','.join(map(str, sequence))},{flag}\n")
            #         if window == 10:
            #             counter += len(syscalls)
            #     if counter >= 2000000:
            #         print(counter)
            #         stop_sim.set()
            data.clear()
            # data = probe.get_data()

        # if data:
            

        #     for sequence in data:
        #         print(sequence)
                # exit()
                # output.write(f"{','.join(map(str, sequence))},{0}\n")
            # tid_dict = probe.gen_sliding_window(data, window_size)
            # for _, syscalls in tid_dict.items():
            #     counter += len(syscalls)
            #     if syscalls == []:
            #         continue
            #     for syscall_window in syscalls:
            #         output.write(f"{','.join(map(str, syscall_window))},{0}\n")

            # new_window = []
            # for i in windows:
            #     output = output_list[i]
            #     tid_dict = probe.gen_sliding_window(data, i)
            #     for _, syscalls in tid_dict.items():
            #         counters[i] += len(syscalls)
            #         if syscalls == []:
            #             continue
            #         for syscall_window in syscalls:
            #             output.write(f"{','.join(map(str, syscall_window))},{0}\n")
            #     if limit and counters[i] >= limit:
            #         print(f"Limit exceeded by {counters[i] - limit} syscalls for window {i}")
            #     else:
            #         new_window.append(i)
            # windows = new_window

            # if len(windows) == 0:
            #     stop_sim.set()

        if stop_sim.is_set():
            print("Ending trace")
            # output.close()
            return
        sleep(0.5)


def sysdig_monitor(
        data_path: str,
        stop_sim,          # threading.Event
        exploit_flag,      # threading.Event
        mntns: str,        # here: container_id or unique prefix for SysdigProbe
        window_size: int,  # unused (kept for signature compatibility)
        limit: int
    ):
    """
    Stream raw sysdig events to CSV as they are traced (no sliding window).

    CSV columns (no header):
      ts, container_id, container_name, pid, tid, evt_type, evt_args, 0
    """

    # Treat mntns as the target container ID/prefix for SysdigProbe
    container_id = mntns

    # Start probe (this SysdigProbe version already filters on container_id and ignores futex)
    probe = SysdigProbe(container_id=container_id)

    # Open output file (line-buffered via newline='' + csv.writer)
    writer = open(data_path, "w", newline="")
    # writer = csv.writer(f)

    counter = 0  # number of events written

    def write_batch(events):
        nonlocal counter
        if not events:
            return 0
        written = 0
        # If limit is set, only write up to the remaining budget
        remaining = (limit - counter) if limit else None
        for e in (events if remaining is None else events[:max(0, remaining)]):
            writer.write(e + "\n")
            # ts, cid, cname, pid, tid, evtype, evargs = e
            # writer.writerow([ts, cid, cname, pid, tid, evtype, evargs, 0])
            written += 1
        counter += written
        return written

    probe.start()
    try:
        while True:
            # Stop conditions
            if stop_sim.is_set() or (limit and counter >= limit):
                if not stop_sim.is_set():
                    stop_sim.set()

                # Wait for exploit to finish (matches your original behavior)
                while not exploit_flag.is_set():
                    sleep(0.2)

                # Stop probe and flush remaining events (respect limit)
                remaining_events = probe.stop()

                if limit and counter < limit:
                    # write only up to limit
                    write_batch(remaining_events)
                elif not limit:
                    write_batch(remaining_events)

                if limit > 0 and counter > limit:
                    print(f"Limit exceeded by {counter - limit} events")

                print("Ending trace")
                writer.close()
                return

            # Normal streaming: get current events and write them
            batch = probe.get_data()
            write_batch(batch)

            sleep(0.5)
    finally:
        # Best-effort cleanup if something goes wrong
        try:
            probe.stop()
        except Exception:
            pass
        try:
            writer.close()
        except Exception:
            pass

def simulate(
        scenarioID:int, 
        limit:int=None, 
        duration:int=None, 
        exploit:bool=False, 
        mntns:str="/sys/fs/bpf/mnt_ns_set", 
        window_size=3,
        baseline:str=None,
        filename:str=None,
        ):
    
    if not (duration or limit): 
        print("Undifined duration")
        exit(-1)
    
    scenario = ScenarioManager().get_scenario(Scenario(scenarioID))
    if exploit: scenario.is_exploit()

    print("*" * 116 + "\n" +
          f"Simulating {scenario.name}, with {"exploit " if exploit else "no exploit "}{f"for {duration} seconds " if duration else ""}{f"until {limit} syscalls" if limit else ""}\n" +
          "*" * 116 + "\n")

    data_path = os.path.join(DB, filename.removesuffix(".csv") if filename else scenario.syscallDir + f"_w{window_size}") + ".csv"

    stop_sim = Event() 

    probe_thread = Process(target=monitor_data, args=(scenario, data_path, stop_sim, exploit, mntns, window_size, limit))
    probe_thread.start()
    
    scenario.simulate(duration, stop_sim, exploit=exploit)
    if not stop_sim.is_set():
        stop_sim.set()
    
    probe_thread.join()

    if exploit:
        for i in [2, 3, 4, 6, 8, 10]:
            bn = baseline.replace("WSIZE", str(i))
            fn = data_path.replace("WSIZE", str(i))
            if baseline != None:
                bn += ".csv"
                bn = os.path.join(DB, bn)   
                cleanup(bn, fn)


        
    


