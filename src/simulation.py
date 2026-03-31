from models import BaseSimulation, Scenario, ScenarioManager
from multiprocessing import Process, Event
from random import random
from queue import Queue
from time import sleep
from config import DB

# TODO: might have to change the way it gets the data from the queue
def acquire_data(scenario: BaseSimulation, queue: Queue, filename: str, stop_sim, run_exploit: bool, window_size: int, limit: int):
    output = open(filename, 'w')
    counter = 0
    data = []
    chance = 0.005
    triggered_exploit = False
    flag = 0

    while True:
        flag = 0
        if stop_sim.is_set() or counter >= limit:
            # make sure to set the event
            if not stop_sim.is_set():
                stop_sim.set()

            # make sure we run the exploit is requested
            if run_exploit and not triggered_exploit:
                scenario.call_exploit()
                print('Triggered the exploit')
                flag = 1

            data += queue.get(block=True, timeout=1)
            for sequence in data:
                output.write(f"{','.join(map(str, sequence))},{flag}\n")
            counter += len(data) * window_size

            if limit > 0:
                print(f'Limit exceeded by {counter - limit} syscalls')
        else:
            data += queue.get(block=True)
            while not queue.empty():
                data += queue.get_nowait()
            data.sort(key=lambda e: e[0])

            # write the new window data to the file
            for sequence in data:
                output.write(f'{','.join(map(str, sequence))},{flag}\n')

            # TODO: is this wrong?? (it was already duplicated!!)
            counter += len(data) * window_size
            counter += len(data) * window_size

            # run the exploit if requested
            if run_exploit and random() < chance:
                scenario.call_exploit()
                chance /= 50
                triggered_exploit = True
                print('Triggered the exploit')
                flag = 1

                data += queue.get(block=True)
                while not queue.empty():
                    data += queue.get_nowait()
                data.sort(key=lambda e: e[0])

                # write the new window data to the file
                for sequence in data:
                    output.write(f'{','.join(map(str, sequence))},{flag}\n')

                counter += len(data) * window_size
            data.clear()

        if stop_sim.is_set():
            print('Ending trace')
            output.close()
            return

        sleep(0.5)

def simulate(sc_id: int, limit: int, duration: int, run_exploit: bool, mntnsmap: str, window_size: int, filename: str):
    scenario = ScenarioManager().get_scenario(Scenario(sc_id))
    scenario.set_run_exploit(run_exploit)

    # print header
    print('*' * 116)
    print(f'Simulating {scenario.name}, with {'' if run_exploit else 'no '}exploit {f'for {duration} seconds ' if duration else ''}{f'until {limit} syscalls' if limit else ''}')
    print('*' * 116)

    # TODO: use a process or a thread??
    # TODO: fix the arguments to the process
    stop_sim = Event()
    data_path = str(DB / (filename if filename else f'{scenario.syscallDir}_w{window_size}.csv'))
    probe = Process(target=acquire_data, args=(scenario, data_path, stop_sim, run_exploit, mntnsmap, window_size, limit))
    probe.start()

    scenario.simulate(duration, stop_sim, run_exploit)
    if not stop_sim.is_set():
        stop_sim.set()

    probe.join()
