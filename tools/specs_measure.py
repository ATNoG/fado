import sys
import psutil
from time import sleep

process_dict = {}
process = psutil.Process(int(sys.argv[1]))
prev_time = 0
avg_cpu_time = 0
avg_cpu_perc = 0
avg_mem_use = 0
counter = 0

while True:
    try:
        with process.oneshot():
            process_dict["pcpu"] = process.cpu_percent()
            process_dict["uss"] = process.memory_full_info()[0] / 1024 ** 2
            process_dict["pmem"] = process.memory_percent()
            cpu_time = sum(process.cpu_times()[:2])
            process_dict["cpu"] = cpu_time - prev_time
            prev_time = cpu_time

        counter += 1
        if counter == 1: continue
        avg_cpu_perc += process_dict["pcpu"]
        avg_cpu_time += process_dict["cpu"]
        avg_mem_use += process_dict["uss"]
        print(f"CPU Time: {process_dict["cpu"]}s")
        print(f"CPU percentage: {process_dict["pcpu"]}")
        print(f"Mem usage: {process_dict["uss"]} Mb")
        print(f"Mem percentage: {process_dict["pmem"]}")
        if counter >= 121:
            counter -= 1
            avg_cpu_perc /= counter
            avg_cpu_time /= counter
            avg_mem_use /= counter

            with open("scripts/specs.txt", 'a') as f:
                f.write(f"{sys.argv[2]}\nPCPU, {avg_cpu_perc}\nCPU, {avg_cpu_time}\nMEM, {avg_mem_use}\n")
            exit()
        sleep(1)
    except KeyboardInterrupt:
        counter -= 1
        avg_cpu_perc /= counter
        avg_cpu_time /= counter
        avg_mem_use /= counter

        with open("scripts/specs.txt", 'a') as f:
            f.write(f"{sys.argv[2]}\nPCPU, {avg_cpu_perc}\nCPU, {avg_cpu_time}\nMEM, {avg_mem_use}\n")
        exit(0)