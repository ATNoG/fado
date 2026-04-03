from models import BaseSimulation, Scenario, ScenarioManager
from multiprocessing import Process, Event, Queue
from random import random
from time import sleep
from config import DB

# TODO: add a type for the 'event'

def acquire_data(scenario: BaseSimulation, queue: Queue[list[list[int]]], filename: str, run_exploit: bool, window_size: int, limit: int, stop_sim):
    output = open(filename, 'w')
    counter = 0
    data = []
    chance = 0.005
    triggered_exploit = False
    flag = 0

    while True:
        flag = 0
        if stop_sim.is_set() or (limit > 0 and counter >= limit):
            # make sure to set the event
            if not stop_sim.is_set():
                stop_sim.set()

            # make sure we run the exploit is requested
            if run_exploit and not triggered_exploit:
                scenario.call_exploit()
                print('Triggered the exploit')
                flag = 1

            # TODO: is the timeout a good idea?
            data += queue.get(block=True, timeout=1)
            for sequence in data:
                output.write(f'{','.join(map(str, sequence))},{flag}\n')
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

def simulate(sc_id: int, queue: Queue[list[list[int]]], limit: int, duration: int, run_exploit: bool, window_size: int, filename: str):
    scenario = ScenarioManager().get_scenario(Scenario(sc_id))
    scenario.set_run_exploit(run_exploit)

    # print header
    print('*' * 116)
    print(f'Simulating {scenario.name()}, with {'' if run_exploit else 'no '}exploit {f'for {duration} seconds ' if duration else ''}{f'until {limit} syscalls' if limit else ''}')
    print('*' * 116)

    stop_sim = Event()
    data_path = f'{DB / (filename.removesuffix('.csv') if filename else f'{scenario.syscall_dir}_w{window_size}')}.csv'
    probe = Process(target=acquire_data, args=(scenario, queue, data_path, run_exploit, window_size, limit, stop_sim))
    probe.start()

    scenario.simulate(duration, stop_sim, run_exploit)
    if not stop_sim.is_set():
        stop_sim.set()

    probe.join()
