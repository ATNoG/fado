from kubernetes import config as K8sconfig
from kubernetes.client import CoreV1Api
from models.bpf import BpfContainer
import socket, os, subprocess, json
from kubernetes.watch import Watch
from threading import Lock
from probe import BpfProbe
from probe.bcc import BPF
from queue import Queue
from utils import FILES

# maps namespace ids to the containers themselves
valid_containers: dict[int, BpfContainer] = {}
valid_images = {
    'yaml_load:v1': 'YamlLoad_5s_w2_20p',
    'sentiment_analyzer:v1': 'SentimentAnalyzer_5s_w2_10p'
}

def recreate_ebpf_map():
    if os.path.exists('/sys/fs/bpf/mnt_ns_set'):
        os.remove('/sys/fs/bpf/mnt_ns_set')

    bpf = BPF(text="""BPF_TABLE_PINNED("hash", u64, u32, mnt_ns_set, 128, "/sys/fs/bpf/mnt_ns_set");""")
    print('[+] eBPF map is setup...')
    return bpf.get_table('mnt_ns_set')

# TODO: what if this fails?
def add_container(ebpf_map, image: str, container_id: str, queue: Queue[tuple[int, int]], lock: Lock):
    # get the PID from the local container runtime and the respective namespace id
    result = subprocess.run(['crictl', 'inspect', container_id], capture_output=True, text=True, check=True)
    container_pid = json.loads(result.stdout)['info']['pid']
    ns_id = os.stat(f'/proc/{container_pid}/ns/mnt').st_ino

    model_path = FILES / (valid_images[image] + '.pkl')
    with lock:
        # don't re-add the same container
        if ns_id in valid_containers:
            return

        valid_containers[ns_id] = BpfContainer(image, container_id, model_path, queue)

    key = ebpf_map.Key(ns_id)
    value = ebpf_map.Leaf(0)
    ebpf_map[key] = value
    print(f'[+] Container created with image: {image}')

def remove_container(ebpf_map, container_id: str, lock: Lock):
    ns_id = None
    with lock:
        for c_ns_id, c in valid_containers.items():
            if c.container_id == container_id:
                ns_id = c_ns_id
                break

        if ns_id == None:
            return

        valid_containers[ns_id].stop()
        del valid_containers[ns_id]

    key = ebpf_map.Key(ns_id)
    del ebpf_map[key]
    print('[+] Container removed')

def containers_manager(ebpf_map, lock: Lock):
    K8sconfig.load_kube_config(config_file='/etc/kubernetes/kubelet.conf')
    node_selector = f'spec.nodeName={socket.gethostname()}'
    for event in Watch().stream(CoreV1Api().list_namespaced_pod, namespace='default', field_selector=node_selector):
        # the other event types are not usefull
        if type(event) != dict:
            continue

        pod = event['object']
        if not pod.metadata.labels or 'serving.knative.dev/revision' not in pod.metadata.labels:
            continue

        # example: nginxdemos/hello:plain-text
        container_image = pod.metadata.annotations['client.knative.dev/user-image'].split('/')[1]
        if container_image not in valid_images:
            continue

        if not pod.status.container_statuses:
            continue

        # TODO: this only supports a single container per pod. does this need to change??
        container_id = None
        for container_status in pod.status.container_statuses:
            if container_status.name != 'user-container' or container_status.container_id == None:
                continue

            # remove the 'containerd://' prefix
            container_id = container_status.container_id.split("://")[-1]
            break

        # TODO: should i raise an exception here? as this should 'always' work
        if container_id == None:
            continue

        event_type = event['type']
        if event_type in ('ADDED', 'MODIFIED') and pod.status.phase == 'Running' and pod.metadata.deletion_timestamp is None:
            add_container(ebpf_map, container_image, container_id, Queue(maxsize=1000), lock)

        elif event_type == 'MODIFIED' and pod.metadata.deletion_timestamp is not None:
            remove_container(ebpf_map, container_id, lock)

if __name__ == '__main__':
    lock = Lock()
    ebpf_map = recreate_ebpf_map()
    BpfProbe(valid_containers, '/sys/fs/bpf/mnt_ns_set', lock)
    containers_manager(ebpf_map, lock)
