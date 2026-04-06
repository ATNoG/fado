from models import BpfTrackedContainer, BpfProbe, BpfTrackedContainersRegistry
from config import MODELS, IMAGE_MODEL_MAPPINGS, MNTNSMAP, MAX_QUEUE_SIZE
from multiprocessing import Queue, set_start_method
from kubernetes import config as K8sconfig
from kubernetes.client import CoreV1Api
import socket, os, subprocess, json
from kubernetes.watch import Watch
from probe import BPF

def recreate_ebpf_map(mntnsmap: str):
    if os.path.exists(mntnsmap):
        os.remove(mntnsmap)

    bpf = BPF(text=f"""BPF_TABLE_PINNED("hash", u64, u32, mnt_ns_set, 128, "{mntnsmap}");""")
    print('[+] eBPF map is setup...')
    return bpf.get_table('mnt_ns_set')

def add_container(ebpf_map, containers_registry: BpfTrackedContainersRegistry, image: str, container_id: str, pod_name: str, node_name: str):
    # get the PID from the local container runtime and the respective namespace id
    result = subprocess.run(['crictl', 'inspect', container_id], capture_output=True, text=True, check=True)
    container_pid = json.loads(result.stdout)['info']['pid']

    ns_id = os.stat(f'/proc/{container_pid}/ns/mnt').st_ino
    model_path = MODELS / (IMAGE_MODEL_MAPPINGS[image] + '.pkl')
    bpf_tracked_container = BpfTrackedContainer(image, container_id, model_path, pod_name, node_name, Queue(maxsize=MAX_QUEUE_SIZE))
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

def containers_manager(ebpf_map, containers_registry: BpfTrackedContainersRegistry):
    set_start_method('spawn')
    node_name = socket.gethostname()
    K8sconfig.load_kube_config(config_file='/etc/kubernetes/kubelet.conf')
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

                current_cid = container_status.container_id.split("://")[-1]
                if old_cid == None or old_cid != current_cid:
                    # the container was restarted, we must clean up and re-add the container
                    if old_cid != None:
                        remove_container(ebpf_map, containers_registry, old_cid)
                        print('    ⮡ Container restart')

                    add_container(ebpf_map, containers_registry, container_image, current_cid, pod_name, node_name)

                break

if __name__ == '__main__':
    ebpf_map = recreate_ebpf_map(MNTNSMAP)
    containers_registry = BpfTrackedContainersRegistry()
    BpfProbe(containers_registry, MNTNSMAP)
    containers_manager(ebpf_map, containers_registry)
