import statistics
from math import sqrt
import sys
import psutil
from time import monotonic

process_dict = {}
process = psutil.Process(int(sys.argv[1]))
name = sys.argv[2]
prev_time = sum(process.cpu_times()[:2])
cpu_time = 0
cpu_pct = []
mem_use = []
process.cpu_percent()
cpu_percent = 0.0
cpu_elapsed_time = tuple()
memory_use = 0
end_time = monotonic() + 120
counter = 0

while monotonic() < end_time:
    try:
        with process.oneshot():
            cpu_elapsed_time = process.cpu_times()[:2]
            memory_use = process.memory_info()[0]

        cpu_pct.append(process.cpu_percent(interval=1))
        now_time = sum(cpu_elapsed_time)
        cpu_time += max(now_time - prev_time, 0.0)
        prev_time = now_time
        mem_use.append(memory_use)
        counter += 1
    except KeyboardInterrupt:
        print("Interrupted by user.")
        break

def sem(values):
    return statistics.stdev(values) / sqrt(len(values)) if len(values) > 1 else 0.0

avg_cpu_perc = statistics.fmean(cpu_pct)
err_cpu_perc = sem(cpu_pct)

avg_mem_use = statistics.fmean(mem_use)
err_mem_use = sem(mem_use)

avg_cpu_time = cpu_time / counter

with open("tools/performance.txt", "a") as f:
    f.write(f"\n\n\n{name}\n")

    f.write("=== CPU ===\n")
    f.write(f"Average CPU %%: {avg_cpu_perc:.2f} ± {err_cpu_perc:.2f}\n")
    f.write(f"Avg CPU time per second: {avg_cpu_time:.4f} s/s\n\n")

    f.write("=== Memory ===\n")
    f.write(f"Average RSS: {avg_mem_use / (1024*1024):.2f} MiB ± {err_mem_use / (1024*1024):.2f}\n")

print(f"Summary written")

print(f"\n{name}\n")

print("=== CPU ===\n")
print(f"Average CPU %%: {avg_cpu_perc:.2f} ± {err_cpu_perc:.2f}\n")
print(f"Avg CPU time per second: {avg_cpu_time:.4f} s/s\n\n")

print("=== Memory ===\n")
print(f"Average RSS: {avg_mem_use / (1024*1024):.2f} MiB ± {err_mem_use / (1024*1024):.2f}\n")

print(f"Iterations: {counter}")