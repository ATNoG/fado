from kubernetes import client, config, watch
import subprocess, socket

config.load_kube_config(config_file="/etc/kubernetes/kubelet.conf")
v1 = client.CoreV1Api()
w = watch.Watch()

MY_NODE_NAME = socket.gethostname()
print(f"Listening for Pod events exclusively on node: {MY_NODE_NAME}...")

node_selector = f"spec.nodeName={MY_NODE_NAME}"
for event in w.stream(v1.list_pod_for_all_namespaces, field_selector=node_selector):
    if type(event) != dict:
        continue

    pod = event['object']
    event_type = event['type']
    if pod.metadata.labels and 'serving.knative.dev/revision' in pod.metadata.labels:
        pod_name = pod.metadata.name

        # we need the pod to be Running to have a container ID and a Host PID
        if event_type in ('ADDED', 'MODIFIED') and pod.status.phase == 'Running':
            if not pod.status.container_statuses:
                continue

            for container_status in pod.status.container_statuses:
                # Container ID usually looks like "containerd://<hash>"
                raw_id = container_status.container_id 
                if not raw_id:
                    continue

                container_hash = raw_id.split("://")[-1]
                print(f"[{pod_name}] Found container running: {container_hash}")

                # # get PID
                # cmd = f"crictl inspect {container_hash} | grep 'pid' | head -n 1"
                # output = subprocess.check_output(cmd, shell=True, text=True)
                # print(f"[{pod_name}] PID: {output.strip()}")

        elif event_type == 'DELETED':
            print(f"[{pod_name}] Pod deleted.")
