from utils import BaseSimulation, Scenario, ScenarioManager, DB
from probe import Probe, SysdigProbe
from multiprocessing import Lock, Process, Event
from .cleanup_data import cleanup
import os
from random import random
from time import sleep

def monitor_data(
        data_path:str, 
        stop_sim, 
        exploit_flag, 
        mntns:str, 
        window_size:int, 
        limit:int
        ):
    
    # output = open(data_path, "w")
    # counter = 0
    counters = {}
    output_list = {}
    windows = [2, 3, 4, 6, 8, 10]

    for i in windows:
        counters[i] = 0
        fn = data_path.replace("WSIZE", str(i))
        output_list[i] = open(fn, 'w')

    probe = Probe(mntns)

    while True: 
        # if stop_sim.is_set() or (limit and counter >= limit):
        if stop_sim.is_set():
            if not stop_sim.is_set(): stop_sim.set()
            while not exploit_flag.is_set():
                sleep(0.2)
            data = probe.end_trace()
            # if limit > 0: print(f"Limit exceeded by {counter - limit} syscalls")
        else:
            data = probe.get_data()

        if data:
            # tid_dict = probe.gen_sliding_window(data, window_size)
            # for _, syscalls in tid_dict.items():
            #     counter += len(syscalls)
            #     if syscalls == []:
            #         continue
            #     for syscall_window in syscalls:
            #         output.write(f"{','.join(map(str, syscall_window))},{0}\n")

            new_window = []
            for i in windows:
                output = output_list[i]
                tid_dict = probe.gen_sliding_window(data, i)
                for _, syscalls in tid_dict.items():
                    counters[i] += len(syscalls)
                    if syscalls == []:
                        continue
                    for syscall_window in syscalls:
                        output.write(f"{','.join(map(str, syscall_window))},{0}\n")
                if limit and counters[i] >= limit:
                    print(f"Limit exceeded by {counters[i] - limit} syscalls for window {i}")
                else:
                    new_window.append(i)
            windows = new_window

            if len(windows) == 0:
                stop_sim.set()

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

def gen_exploit(scenario:BaseSimulation, stop_sim, exploit_flag):
    """
    Occasionally trigger exploits while simulation is running.
    Ensures at least one exploit is fired before exit.
    """

    lock = Lock()
    counter = 0 

    chance = 0.01

    while not stop_sim.is_set():  # keep going until stop signal
        # Random chance to fire exploit
        if random() < chance:
            with lock:
                print("Exploiting")
                scenario.call_exploit()
            exploit_flag.set()
            counter += 1
            chance = 0
        sleep(0.5)  # control loop frequency (every 2000ms)

    # Guarantee at least one exploit before stopping
    if not exploit_flag.is_set():
        print("Triggering Exploit Before Terminating")
        with lock:
            scenario.call_exploit()
        sleep(5)
        exploit_flag.set()
        counter += 1
    print(f"{counter} exploits")


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
    exploit_flag = Event()

    if not exploit:
        exploit_flag.set()
    else:
        exploit_thread = Process(target=gen_exploit, args=(scenario, stop_sim, exploit_flag))
        exploit_thread.start()


    if mntns == "/sys/fs/bpf/mnt_ns_set":
        probe_thread = Process(target=monitor_data, args=(data_path, stop_sim, exploit_flag, mntns, window_size, limit))
    else:
        probe_thread = Process(target=sysdig_monitor, args=(data_path, stop_sim, exploit_flag, mntns, window_size, limit))
    probe_thread.start()
    
    scenario.simulate(duration, stop_sim, exploit=exploit)
    if not stop_sim.is_set():
        stop_sim.set()
    
    probe_thread.join()

    if exploit:
        exploit_thread.join()
        for i in [2, 3, 4, 6, 8, 10]:
            bn = baseline.replace("WSIZE", str(i))
            fn = data_path.replace("WSIZE", str(i))
            if baseline != None:
                bn += ".csv"
                bn = os.path.join(DB, bn)
                cleanup(bn, fn)


        
    


