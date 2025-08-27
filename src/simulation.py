from utils import BaseSimulation, Scenario, ScenarioManager
from probe import Probe
from multiprocessing import Lock, Process, Event
from .cleanup_data import cleanup
import os
from random import random
from time import sleep

DB = os.path.join(os.path.abspath(os.curdir), "data/logs")

def monitor_data(
        data_path:str, 
        stop_sim, 
        exploit_flag, 
        mntns:str, 
        window_size:int, 
        limit:int
        ):
    
    output = open(data_path, "w")
    counter = 0
    probe = Probe(mntns, window_size)

    while True: 
        if stop_sim.is_set() or (limit and counter >= limit):
            if not stop_sim.is_set(): stop_sim.set()
            while not exploit_flag.is_set():
                sleep(0.2)
            data = probe.end_trace()
            if limit > 0: print(f"Limit exceeded by {counter - limit} syscalls")
        else:
            data = probe.get_data()

        if data:
            tid_dict = probe.gen_sliding_window(data)
            for _, syscalls in tid_dict.items():
                counter += len(syscalls)
                if syscalls == []:
                    continue
                for syscall_window in syscalls:
                    output.write(f"{','.join(map(str, syscall_window))},{0}\n")

        if stop_sim.is_set():
            print("Ending trace")
            output.close()
            return
        sleep(0.5)

def gen_exploit(scenario:BaseSimulation, stop_sim, exploit_flag):
    """
    Occasionally trigger exploits while simulation is running.
    Ensures at least one exploit is fired before exit.
    """

    lock = Lock()
    counter = 0 

    chance = 0.005

    while not stop_sim.is_set():  # keep going until stop signal
        # Random chance to fire exploit
        if random() < chance:
            with lock:
                scenario.call_exploit()
            exploit_flag.set()
            counter += 1
            chance /= 10
        sleep(2)  # control loop frequency (every 200ms)

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

    data_path = os.path.join(DB, f"{filename}_{scenario.syscallDir}" if filename else scenario.syscallDir) + f"_w{window_size}.csv"

    # stop_sim = Event() 
    # exploit_flag = Event()

    # if not exploit:
    #     exploit_flag.set()
    # else:
    #     exploit_thread = Process(target=gen_exploit, args=(scenario, stop_sim, exploit_flag))
    #     exploit_thread.start()

    # probe_thread = Process(target=monitor_data, args=(data_path, stop_sim, exploit_flag, mntns, window_size, limit))
    # probe_thread.start()
    
    # scenario.simulate(duration, stop_sim, exploit=exploit)
    # if not stop_sim.is_set():
    #     stop_sim.set()
    
    # probe_thread.join()

    if exploit:
        # exploit_thread.join()

        if baseline != None:
            baseline += ".csv"
            baseline = os.path.join(DB, baseline)
            cleanup(baseline, data_path)


        
    


