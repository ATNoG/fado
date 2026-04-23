import subprocess, json, re, threading, requests
from datetime import datetime
from time import sleep

# KNATIVE_URL = 'http://sentiment-analyzer.default.10.255.41.115.sslip.io/'
# KSVC_NAME   = 'sentiment-analyzer'

KNATIVE_URL = 'http://yaml-load.default.10.255.41.115.sslip.io/'
KSVC_NAME   = 'yaml-load'

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def trigger_cold_start():
    print(f'[+] Firing HTTP request to {KNATIVE_URL} to trigger cold start...')
    requests.get(KNATIVE_URL, timeout=15)

def parse_nano_timestamp(ts_string):
    ts_string = re.sub(r'(\.\d{6})\d+Z', r'\1Z', ts_string)
    ts_string = ts_string.replace('Z', '+00:00')
    return datetime.fromisoformat(ts_string)

def run_benchmark():
    threading.Thread(target=trigger_cold_start, daemon=True).start()

    # poll k8s until the new pod appears
    print(f"[+] Waiting for new '{KSVC_NAME}' pod to spin up...")
    pod_name = ''
    while not pod_name:
        pod_name = run_cmd(f"kubectl get pods -l serving.knative.dev/service={KSVC_NAME} --sort-by=.metadata.creationTimestamp -o jsonpath='{{.items[-1].metadata.name}}'")
        sleep(0.5)

    print(f'[+] Found new Pod: {pod_name}')

    # wait for the application container to start and get its container id
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

    # find exactly which node the container is running on
    node_name = run_cmd(f"kubectl get pod {pod_name} -o jsonpath='{{.spec.nodeName}}'")
    print(f'[+] Container is running on node: {node_name}')

    # find all security agents on that exact node
    raw_agents = run_cmd(f'kubectl get pods --field-selector spec.nodeName={node_name} -o custom-columns=NAME:.metadata.name --no-headers | grep security-agent')

    # split the multi-line string into a clean python list of pod names
    local_agents = [p for p in raw_agents.split('\n') if p]
    print(f'[+] Found {len(local_agents)} Security Agents on node {node_name}')

    # get the security agent that claimed the container and the 'attach' timestamp
    claiming_agent, agent_attach_time = None, None
    while not agent_attach_time or not claiming_agent:
        for agent_pod in local_agents:
            # TODO: what if more than 200 lines have been printed since?? not likely but still...
            agent_logs = run_cmd(f'kubectl logs {agent_pod} --timestamps --tail=200 | grep {container_id}')

            # find the first line that mentions the container we want
            for line in agent_logs.split('\n'):
                if container_id in line:
                    # get the timestamp use regex
                    match = re.search(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)", line)
                    if match:
                        agent_attach_time = parse_nano_timestamp(match.group(1))
                        claiming_agent = agent_pod
                        print(f'[+] Container claimed by: {agent_pod}')
                        break

            if agent_attach_time and claiming_agent:
                break

        if not agent_attach_time or not claiming_agent:
            sleep(0.5)

    # get the container start up timestamp
    runtime_start_time = None
    while not runtime_start_time:
        inspect_raw = run_cmd(f'kubectl exec {claiming_agent} -- crictl inspect {container_id}')
        if inspect_raw:
            try:
                inspect_json = json.loads(inspect_raw)
                raw_time = inspect_json.get('status', {}).get('startedAt')
                if raw_time:
                    runtime_start_time = parse_nano_timestamp(raw_time)
            except json.JSONDecodeError:
                pass

        if not runtime_start_time:
            sleep(0.5)

    print(f'[+] Container Started At: {runtime_start_time}')
    print(f'[+] Agent Claimed At:     {agent_attach_time}')

    # calculate the window of vulnerability
    if runtime_start_time and agent_attach_time:
        delta = agent_attach_time - runtime_start_time
        milliseconds = delta.total_seconds() * 1000

        print('\n' + '=' * 50)
        print('BENCHMARK RESULTS')
        print('=' * 50)
        print(f'Container Start: {runtime_start_time.strftime('%H:%M:%S.%f')[:-3]}')
        print(f'Agent Attach:    {agent_attach_time.strftime('%H:%M:%S.%f')[:-3]}')
        print(f'Latency Window:  {milliseconds:.2f} ms')
        print('=' * 50)

if __name__ == '__main__':
    run_benchmark()
