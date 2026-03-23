from kubernetes import config as K8sconfig
from kubernetes.client import CoreV1Api
from models.bpf import BpfContainer
import socket, os, subprocess, json
from kubernetes.watch import Watch
from threading import Lock
from probe.bcc import BPF

# maps namespace ids to the containers themselves
valid_containers: dict[int, BpfContainer] = {}
valid_images = {
    'yaml_load': 'YamlLoad_5s_w2_20p'
}

def recreate_ebpf_map():
    if os.path.exists("/sys/fs/bpf/mnt_ns_set"):
        os.remove("/sys/fs/bpf/mnt_ns_set")

    bpf = BPF(text="""BPF_TABLE_PINNED("hash", u64, u32, mnt_ns_set, 128, "/sys/fs/bpf/mnt_ns_set");""")
    print("[+] eBPF map is setup...")
    return bpf.get_table("mnt_ns_set")

def get_pid(container_id: str) -> int:
    # remove the 'containerd://' or 'docker://' prefix
    container_id = container_id.split("://")[-1]

    # ask the local container runtime for the full state in JSON format
    result = subprocess.run(["crictl", "inspect", container_id], capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    return data['info']['pid']

# def add_container(ebpf_map, image: str):
#     # TODO: make sure the container is not already present
#     print(f"Pod started with image: {image}")

def containers_manager(ebpf_map, lock: Lock):
    K8sconfig.load_kube_config(config_file="/etc/kubernetes/kubelet.conf")
    node_selector = f"spec.nodeName={socket.gethostname()}"
    for event in Watch().stream(CoreV1Api().list_namespaced_pod, namespace="default", field_selector=node_selector):
        # the other event types are not usefull
        if type(event) != dict:
            continue

        pod = event['object']
        if not pod.metadata.labels or 'serving.knative.dev/revision' not in pod.metadata.labels:
            continue

        event_type = event['type']
        if event_type in ('ADDED', 'MODIFIED') and pod.status.phase == 'Running' and pod.metadata.deletion_timestamp is None:
            if not pod.status.container_statuses:
                continue

            for container_status in pod.status.container_statuses:
                # TODO: only pods with a single container are supported!
                if container_status.name != 'user-container':
                    continue

                if not container_status.state or not container_status.state.running:
                    continue

                host_pid = get_pid(container_status.container_id)
                image = pod.metadata.annotations['client.knative.dev/user-image'] # example: nginxdemos/hello:plain-text
                print(f"Pod started with image: {image} and PID: {host_pid}")
                break
        elif event_type == 'MODIFIED' and pod.metadata.deletion_timestamp is not None:
            print(f"Pod terminated...")

if __name__ == '__main__':
    lock = Lock()
    ebpf_map = recreate_ebpf_map()
    # BpfProbe(valid_containers, 2, "/sys/fs/bpf/mnt_ns_set", lock)
    containers_manager(ebpf_map, lock)
