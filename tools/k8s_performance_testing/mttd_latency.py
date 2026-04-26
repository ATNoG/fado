import subprocess, time, re, csv, os, requests, json
from datetime import datetime, timezone
from threading import Thread
from time import sleep

TIMEOUT = 10
ALERT_LOG_STRING = '[SECURITY ALERT]'
CSV_FILENAME = 'data/perf_tests/mttd_latency.csv'
NUM_RUNS = 10

# KNATIVE_URL = 'http://sentiment-analyzer.default.10.255.41.115.sslip.io/'
# KSVC_NAME   = 'sentiment-analyzer'

KNATIVE_URL = 'http://yaml-load.default.10.255.41.115.sslip.io/'
KSVC_NAME   = 'yaml-load'
EXPLOIT_CMD = ['curl', '-X', 'POST', 'http://yaml-load.default.10.255.41.115.sslip.io/yaml_upload/test@exploit.com', '-F', 'file=@exploit.yml']
EXPLOIT_CWD = 'scenarios/yaml_load'

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def trigger_cold_start():
    print(f'[+] Firing HTTP request to {KNATIVE_URL} to trigger cold start...')
    try:
        requests.get(KNATIVE_URL, timeout=15)
    except:
        pass

def parse_nano_timestamp(ts_string):
    ts_string = re.sub(r'(\.\d{6})\d+Z', r'\1Z', ts_string)
    ts_string = ts_string.replace('Z', '+00:00')
    return datetime.fromisoformat(ts_string)

def fire_exploit():
    print(f'[+] Firing exploit payload at {KSVC_NAME}...')
    subprocess.run(EXPLOIT_CMD, cwd=EXPLOIT_CWD, capture_output=True)
    return datetime.now(timezone.utc)

def get_wazuh_alert_time(container_id, exploit_time):
    print(f'[*] Polling Wazuh Manager via SSH for Rule 100002...')

    wazuh_alert_time = None
    timeout = time.time() + TIMEOUT
    while not wazuh_alert_time and time.time() < timeout:
        raw_alerts = run_cmd(f"ssh ubuntu@10.255.41.108 'sudo grep {container_id} /var/ossec/logs/alerts/alerts.json'")
        if raw_alerts:
            for line in raw_alerts.strip().split('\n'):
                try:
                    alert_json = json.loads(line)

                    # make sure we get the timestamp from the correct rule
                    if str(alert_json.get('rule', {}).get('id')) == '100002':
                        raw_wazuh_time = alert_json.get('timestamp')
                        if raw_wazuh_time:
                            parsed_wazuh_time = parse_nano_timestamp(raw_wazuh_time)

                            # ensure the alert fired after our exploit trigger
                            if parsed_wazuh_time > exploit_time:
                                wazuh_alert_time = parsed_wazuh_time
                                break

                except json.JSONDecodeError:
                    continue

        if not wazuh_alert_time:
            time.sleep(1)

    return wazuh_alert_time

def run_mttd_test():
    Thread(target=trigger_cold_start, daemon=True).start()

    # poll k8s until a strictly 'Running' pod appears
    print(f"[+] Waiting for a fresh 'Running' '{KSVC_NAME}' pod...")
    pod_name = ''
    while not pod_name:
        raw_output = run_cmd(f'kubectl get pods -l serving.knative.dev/service={KSVC_NAME} --sort-by=.metadata.creationTimestamp --no-headers')
        if raw_output:
            lines = raw_output.strip().split('\n')
            for line in reversed(lines):
                if 'Running' in line:
                    pod_name = line.split()[0]
                    break

        if not pod_name:
            sleep(0.5)

    print(f'[+] Target Pod: {pod_name}')

    # get the container id
    print('[+] Waiting for container ID...')
    container_id = ''
    while not container_id:
        raw_output = run_cmd(f"kubectl get pod {pod_name} -o jsonpath='{{range .status.containerStatuses[*]}}{{.name}}::{{.containerID}}{{\"\\n\"}}{{end}}'")
        if raw_output:
            for line in raw_output.strip().split('\n'):
                if not line or 'queue-proxy' in line or 'istio-proxy' in line:
                    continue

                parts = line.split('::')
                if len(parts) == 2 and parts[1]: 
                    container_id = parts[1].split('://')[-1]
                    break

        if not container_id:
            sleep(0.5)

    print(f'[+] Container ID extracted: {container_id}')

    # get the security agents running in the same node as the container
    node_name = run_cmd(f"kubectl get pod {pod_name} -o jsonpath='{{.spec.nodeName}}'")
    raw_agents = run_cmd(f"kubectl get pods --field-selector spec.nodeName={node_name} -o custom-columns=NAME:.metadata.name --no-headers | grep security-agent")
    local_agents = [p for p in raw_agents.split('\n') if p]

    # wait for the container to start and for the agent to claim it
    print('[+] Cooldown (10s) before firing exploit...')
    sleep(10)

    exploit_time = fire_exploit()
    print('[+] Searching Agent logs for the detection alert...')
    agent_alert_time = None

    # timeout just in case the ML model misses it
    timeout = time.time() + TIMEOUT
    while not agent_alert_time and time.time() < timeout:
        for agent_pod in local_agents:
            agent_logs = run_cmd(f'kubectl logs {agent_pod} --timestamps --tail=200 | grep {container_id}')

            for line in agent_logs.split('\n'):
                if container_id in line and ALERT_LOG_STRING in line:
                    match = re.search(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)", line)
                    if match:
                        found_time = parse_nano_timestamp(match.group(1))

                        # ensure that we don't accidentally grab an old alert
                        if found_time > exploit_time:
                            agent_alert_time = found_time
                            break

            if agent_alert_time:
                break

        if not agent_alert_time:
            time.sleep(0.1)

    if not agent_alert_time:
        print('[!] Detection failed or timed out! Did the model catch it?')
        run_cmd(f'kubectl delete pod {pod_name} --wait=false')
        return None

    wazuh_alert_time = get_wazuh_alert_time(container_id, exploit_time)
    if not wazuh_alert_time:
        print('[!] Wazuh alert not found! Is the alerts system working?')
        run_cmd(f'kubectl delete pod {pod_name} --wait=false')
        return None

    latency_ms = (agent_alert_time - exploit_time).total_seconds() * 1000
    wazuh_latency_ms = (wazuh_alert_time - exploit_time).total_seconds() * 1000
    print('\n' + '=' * 50)
    print(f'Exploit Fired:    {exploit_time.strftime('%H:%M:%S.%f')[:-3]}')
    print(f'Agent Detection:  {agent_alert_time.strftime('%H:%M:%S.%f')[:-3]}')
    print(f'MTTD Latency:     {latency_ms:.2f} ms')
    print(f"Wazuh SIEM Alert: {wazuh_alert_time.strftime('%H:%M:%S.%f')[:-3]} ({wazuh_latency_ms:.2f} ms)")
    print('=' * 50)

    run_cmd(f'kubectl delete pod {pod_name} --wait=false')
    return {
        'container_id'    : container_id,
        'exploit_time'    : exploit_time.strftime('%H:%M:%S.%f')[:-3],
        'alert_time'      : agent_alert_time.strftime('%H:%M:%S.%f')[:-3],
        'latency_ms'      : round(latency_ms, 2),
        'wazuh_time'      : wazuh_alert_time.strftime('%H:%M:%S.%f')[:-3],
        'wazuh_latency_ms': round(wazuh_latency_ms, 2)
    }

if __name__ == '__main__':
    if os.path.exists(CSV_FILENAME):
        f = open(CSV_FILENAME, mode='a', newline='')
        writer = csv.writer(f)
    else:
        f = open(CSV_FILENAME, mode='w', newline='')
        writer = csv.writer(f)
        writer.writerow(['Container ID', 'Exploit Time', 'Alert Time', 'Latency (ms)', 'Wazuh Time', 'Wazuh latency (ms)'])
        f.flush()

    for i in range(1, NUM_RUNS + 1):
        if i != 1:
            print()

        print(f"{'='*50}\nSTARTING MTTD RUN {i}/{NUM_RUNS}\n{'='*50}")
        data = run_mttd_test()
        if data:
            writer.writerow([data['container_id'], data['exploit_time'], data['alert_time'], data['latency_ms'], data['wazuh_time'], data['wazuh_latency_ms']])
            f.flush()

        if i < NUM_RUNS:
            print('[+] Cooldown (3s) before next run...')
            time.sleep(3)

    f.close()
    print('\n' + '=' * 50)
    print(f'MTTD BENCHMARK COMPLETE. Data appended to {CSV_FILENAME}')
    print('=' * 50)
