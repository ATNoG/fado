from models import BpfTrackedContainer, BpfProbe, BpfTrackedContainersRegistry
from config import MODELS, IMAGE_MODEL_MAPPINGS, MNTNSMAP
from probe.bcc import BPF
from queue import Queue
import docker, os

# TODO: this NEEDS to be started before any containers starts or those first containers will NOT be monitored (needs to be fixed)

client = docker.DockerClient()

def recreate_ebpf_map(mntnsmap: str):
    if os.path.exists(mntnsmap):
        os.remove(mntnsmap)

    bpf = BPF(text=f"""BPF_TABLE_PINNED("hash", u64, u32, mnt_ns_set, 128, "{mntnsmap}");""")
    print('[+] eBPF map is setup...')
    return bpf.get_table('mnt_ns_set')

def add_container(ebpf_map, containers_registry: BpfTrackedContainersRegistry, image: str, container_id: str, pod_name: str, node_name: str):
    # TODO: what if this fails somehow?
    container_pid = client.containers.get(container_id).attrs['State']['Pid']
    ns_id = os.stat(f'/proc/{container_pid}/ns/mnt').st_ino

    model_path = MODELS / (IMAGE_MODEL_MAPPINGS[f'{image}:v1'] + '.pkl')
    bpf_tracked_container = BpfTrackedContainer(image, container_id, model_path, pod_name, node_name, Queue(maxsize=1000), apply_policies=False)
    if not containers_registry.add_container(ns_id, bpf_tracked_container):
        return

    key = ebpf_map.Key(ns_id)
    value = ebpf_map.Leaf(0)
    ebpf_map[key] = value
    print('[+] Container created')

def remove_container(ebpf_map, containers_registry: BpfTrackedContainersRegistry, container_id: str):
    ns_id = containers_registry.remove_container(container_id)
    if ns_id == None:
        return

    key = ebpf_map.Key(ns_id)
    del ebpf_map[key]
    print('[+] Container removed')

def containers_manager(ebpf_map, containers_registry: BpfTrackedContainersRegistry):
    for event in client.events(decode=True):
        if event['Type'] == 'container':
            container_action = event['Action']
            container_image = event['Actor']['Attributes']['image']
            container_id = event['Actor']['ID']

            if container_action == 'start' and f'{container_image}:v1' in IMAGE_MODEL_MAPPINGS:
                add_container(ebpf_map, containers_registry, container_image, container_id, 'docker_pod', 'docker_node')

            elif container_action in ('die', 'stop', 'kill'):
                remove_container(ebpf_map, containers_registry, container_id)

if __name__ == '__main__':
    ebpf_map = recreate_ebpf_map(MNTNSMAP)
    containers_registry = BpfTrackedContainersRegistry()
    BpfProbe(containers_registry, MNTNSMAP)
    containers_manager(ebpf_map, containers_registry)
