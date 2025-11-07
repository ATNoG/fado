from utils import BaseSimulation, Scenario, ScenarioManager, DB
from probe import Probe
from multiprocessing import Process, Event
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
    probe = Probe(queue, window_size, mntns)

    while True: 
        flag = 0
        if stop_sim.is_set() or (limit and counter >= limit):
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
            data.clear()

        if stop_sim.is_set():
            print("Ending trace")
            output.close()
            return
        sleep(0.5)

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
        if baseline != None:
            baseline_path = os.path.join(DB, filename.removesuffix(".csv")) + ".csv"
            cleanup(baseline_path, data_path)


        
    


