from models import BpfTrackedContainer, BpfProbe, BpfTrackedContainersRegistry, PolicyRule
from config import MODELS, IMAGE_MODEL_MAPPINGS, MNTNSMAP, MAX_QUEUE_SIZE
from multiprocessing import Process, Queue, set_start_method, Manager
from kubernetes.client import CoreV1Api, CustomObjectsApi
from kubernetes import config as K8sconfig
import socket, os, subprocess, json
from kubernetes.watch import Watch
from bcc.table import HashTable
from bcc import BPF

def recreate_ebpf_map(mntnsmap: str):
    bpf = BPF(text=f'''BPF_TABLE_PINNED("hash", u64, u32, mnt_ns_set, 128, "{mntnsmap}");''')
    bpf_map = bpf.get_table('mnt_ns_set')
    assert isinstance(bpf_map, HashTable)
    bpf_map.clear()
    print('[+] eBPF map is setup...')
    return bpf_map

def add_container(ebpf_map, containers_registry: BpfTrackedContainersRegistry, image: str, container_id: str, pod_name: str, node_name: str, active_policies):
    # get the PID from the local container runtime and the respective namespace id
    result = subprocess.run(['crictl', 'inspect', container_id], capture_output=True, text=True, check=True)
    container_pid = json.loads(result.stdout)['info']['pid']

    ns_id = os.stat(f'/proc/{container_pid}/ns/mnt').st_ino
    model_path = MODELS / (IMAGE_MODEL_MAPPINGS[image] + '.pkl')
    bpf_tracked_container = BpfTrackedContainer(image, container_id, model_path, pod_name, node_name, Queue(maxsize=MAX_QUEUE_SIZE), active_policies)
    if not containers_registry.add_container(ns_id, bpf_tracked_container):
        return

    key = ebpf_map.Key(ns_id)
    value = ebpf_map.Leaf(0)
    ebpf_map[key] = value
    print(f'[+] Container created with image: {image} and ID: {container_id}')

def remove_container(ebpf_map, containers_registry: BpfTrackedContainersRegistry, container_id: str):
    ns_id = containers_registry.remove_container(container_id)
    if ns_id == None:
        return

    key = ebpf_map.Key(ns_id)
    del ebpf_map[key]
    print(f'[+] Container removed with ID: {container_id}')

def containers_manager(ebpf_map, active_policies, containers_registry: BpfTrackedContainersRegistry):
    K8sconfig.load_kube_config(config_file='/etc/kubernetes/kubelet.conf')
    node_name = socket.gethostname()
    node_selector = f'spec.nodeName={node_name}'
    for event in Watch().stream(CoreV1Api().list_namespaced_pod, namespace='default', field_selector=node_selector):
        # the other event types are not usefull
        if type(event) != dict:
            continue

        pod = event['object']
        if not pod.metadata.labels or 'serving.knative.dev/revision' not in pod.metadata.labels:
            continue

        # example: nginxdemos/hello:plain-text
        container_image = pod.metadata.annotations['client.knative.dev/user-image'].split('/')[1]
        if container_image not in IMAGE_MODEL_MAPPINGS:
            continue

        if not pod.status.container_statuses:
            continue

        event_type = event['type']
        pod_name = pod.metadata.name
        old_cid = containers_registry.get_pod_container_id(pod_name)
        if event_type == 'MODIFIED' and pod.metadata.deletion_timestamp is not None:
            # container got removed/deleted
            if old_cid != None:
                remove_container(ebpf_map, containers_registry, old_cid)

            continue

        if event_type in ('ADDED', 'MODIFIED') and pod.status.phase == 'Running' and pod.metadata.deletion_timestamp is None:
            for container_status in pod.status.container_statuses:
                if container_status.name != 'user-container' or not container_status.container_id:
                    continue

                # ensure that the container is actually up and running
                if not container_status.state or not container_status.state.running:
                    continue

                current_cid = container_status.container_id.split('://')[-1]
                if old_cid == None or old_cid != current_cid:
                    # the container was restarted, we must clean up and re-add the container
                    if old_cid != None:
                        remove_container(ebpf_map, containers_registry, old_cid)
                        print('    ⮡ Container restart')

                    add_container(ebpf_map, containers_registry, container_image, current_cid, pod_name, node_name, active_policies)

                break

def watch_policies(active_policies):
    print('[+] Starting Policy Engine...')
    K8sconfig.load_kube_config(config_file='/etc/kubernetes/kubelet.conf')
    stream = Watch().stream(CustomObjectsApi().list_cluster_custom_object, group='security.ua.com', version='v1', plural='securitypolicies')
    for event in stream:
        # the other event types are not usefull
        if type(event) != dict:
            continue

        event_type = event['type']
        obj = event['object']
        policy_name = obj['metadata']['name']

        if event_type in ['ADDED', 'MODIFIED']:
            try:
                rule = PolicyRule(**obj['spec'])
                active_policies[policy_name] = rule
                print(f'[Policy Engine] Loaded/Updated: {policy_name}')
            except Exception as e:
                print(f'[Policy Engine] Parse Error "{policy_name}": {e}')

        elif event_type == 'DELETED':
            if policy_name in active_policies:
                del active_policies[policy_name]
                print(f'[Policy Engine] Removed: {policy_name}')

if __name__ == '__main__':
    set_start_method('spawn')

    # policies watcher
    active_policies = Manager().dict()
    policy_process = Process(target=watch_policies, args=(active_policies,), daemon=True)
    policy_process.start()

    # eBPF probing
    ebpf_map = recreate_ebpf_map(MNTNSMAP)
    containers_registry = BpfTrackedContainersRegistry()
    BpfProbe(containers_registry, MNTNSMAP)

    # k8s container events
    containers_manager(ebpf_map, active_policies, containers_registry)
