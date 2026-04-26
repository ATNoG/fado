from datetime import datetime, timezone
import subprocess, time, csv, os
from time import sleep

MNT_NS_SET = '/sys/fs/bpf/mnt_ns_set'

LEGACY_AGENT_CMD = ['sudo', 'venv/bin/python', '-u', '-m', 'src.main', '-m', 'YamlLoad_5s_w2_20p']
EXPLOIT_CMD = ['curl', '-X', 'POST', 'http://127.0.0.1:8000/yaml_upload/test@exploit.com', '-F', 'file=@exploit.yml']
EXPLOIT_CWD = 'scenarios/yaml_load'

NUM_RUNS = 20
CSV_FILENAME = 'data/perf_tests/mttd_latency_legacy.csv'
ALERT_LOG_STRING = 'Anomaly detected'

def fire_exploit():
    print('[+] Firing exploit payload...')
    subprocess.run(EXPLOIT_CMD, cwd=EXPLOIT_CWD, capture_output=True)
    return datetime.now(timezone.utc)

def run_legacy_test():
    print('[+] Starting Legacy Agent in the background...')

    # launch the legacy agent and pipe its output directly into this script
    agent_proc = subprocess.Popen(LEGACY_AGENT_CMD, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    # just wait for the legacy agent to start
    print('[+] Cooldown (10s) before firing exploit...')
    sleep(10)

    # fire the exploit
    exploit_time = fire_exploit()

    print('[+] Monitoring legacy agent stdout for anomaly detection...')

    # watch the stream in real-time
    agent_alert_time = None
    assert agent_proc.stdout != None
    for line in iter(agent_proc.stdout.readline, ''):
        if ALERT_LOG_STRING in line:
            agent_alert_time = datetime.now(timezone.utc)
            break

    # calculate latency
    assert agent_alert_time != None
    latency_ms = (agent_alert_time - exploit_time).total_seconds() * 1000

    print('[+] Test complete. Killing legacy agent...')
    agent_proc.terminate()
    agent_proc.wait()

    print('\n' + '=' * 50)
    print(f'Exploit Fired:    {exploit_time.strftime('%H:%M:%S.%f')[:-3]}')
    print(f'Legacy Detection: {agent_alert_time.strftime('%H:%M:%S.%f')[:-3]}')
    print(f'MTTD Latency:     {latency_ms:.2f} ms')
    print('=' * 50)

    return {
        'exploit_time': exploit_time.strftime('%H:%M:%S.%f')[:-3],
        'alert_time': agent_alert_time.strftime('%H:%M:%S.%f')[:-3],
        'latency_ms': round(latency_ms, 2),
    }

if __name__ == '__main__':
    if os.path.exists(CSV_FILENAME):
        f = open(CSV_FILENAME, mode='a', newline='')
        writer = csv.writer(f)
    else:
        f = open(CSV_FILENAME, mode='w', newline='')
        writer = csv.writer(f)
        writer.writerow(['Exploit Time', 'Legacy Alert Time', 'Latency (ms)'])
        f.flush()

    if not os.path.exists(MNT_NS_SET):
        print(f"[!] '{MNT_NS_SET}' is not created! Please make sure that the eBPF map is ready.")
        exit(1)

    for i in range(1, NUM_RUNS + 1):
        if i != 1:
            print()

        print(f"{'=' * 50}\nSTARTING LEGACY RUN {i}/{NUM_RUNS}\n{'=' * 50}")
        data = run_legacy_test()
        writer.writerow([data['exploit_time'], data['alert_time'], data['latency_ms']])
        f.flush()

        if i < NUM_RUNS:
            print('[+] Cooldown (3s) before next run...')
            time.sleep(3)

    f.close()
    print('\n' + '=' * 50)
    print(f'LEGACY BENCHMARK COMPLETE. Data appended to {CSV_FILENAME}')
    print('=' * 50)
