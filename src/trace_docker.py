from models import BpfTrackedContainer, BpfProbe, BpfTrackedContainersRegistry, Scenario
from config import MODELS, IMAGE_MODEL_MAPPINGS, MNTNSMAP
from multiprocessing import Queue, set_start_method
from probe.bcc import BPF
import docker, os

# TODO: this NEEDS to be started before any containers starts or those first containers will NOT be monitored (needs to be fixed)

client = docker.DockerClient()

def recreate_ebpf_map(mntnsmap: str):
    if os.path.exists(mntnsmap):
        os.remove(mntnsmap)

    bpf = BPF(text=f"""BPF_TABLE_PINNED("hash", u64, u32, mnt_ns_set, 128, "{mntnsmap}");""")
    print('[+] eBPF map is setup...')
    return bpf.get_table('mnt_ns_set')

def add_container(ebpf_map, containers_registry: BpfTrackedContainersRegistry, image: str, container_id: str, pod_name: str, node_name: str, run_process: bool=True) -> int | None:
    # TODO: what if this fails somehow?
    container_pid = client.containers.get(container_id).attrs['State']['Pid']
    ns_id = os.stat(f'/proc/{container_pid}/ns/mnt').st_ino

    model_path = MODELS / (IMAGE_MODEL_MAPPINGS[f'{image}:v1'] + '.pkl')
    bpf_tracked_container = BpfTrackedContainer(image, container_id, model_path, pod_name, node_name, Queue(maxsize=1000), run_process=run_process, apply_policies=False)
    if not containers_registry.add_container(ns_id, bpf_tracked_container):
        return None

    key = ebpf_map.Key(ns_id)
    value = ebpf_map.Leaf(0)
    ebpf_map[key] = value
    print(f'[+] Container created with image: {image} and ID: {container_id}')
    return ns_id

def remove_container(ebpf_map, containers_registry: BpfTrackedContainersRegistry, container_id: str):
    ns_id = containers_registry.remove_container(container_id)
    if ns_id == None:
        return

    key = ebpf_map.Key(ns_id)
    del ebpf_map[key]
    print(f'[+] Container removed with ID: {container_id}')

def containers_manager(ebpf_map, containers_registry: BpfTrackedContainersRegistry, track_scenario: Scenario | None = None) -> Queue[list[list[int]]]:
    set_start_method('spawn')
    if track_scenario:
        print(f'[+] Waiting for a container with image {track_scenario.image_name} to start')

    for event in client.events(decode=True):
        if event['Type'] != 'container':
            continue

        container_action = event['Action']
        container_image = event['Actor']['Attributes']['image']
        container_id = event['Actor']['ID']

        if container_action == 'start':
            if not track_scenario and f'{container_image}:v1' in IMAGE_MODEL_MAPPINGS:
                add_container(ebpf_map, containers_registry, container_image, container_id, 'docker_pod', 'docker_node')

            elif track_scenario and container_image == track_scenario.image_name:
                ns_id = add_container(ebpf_map, containers_registry, container_image, container_id, 'docker_pod', 'docker_node', run_process=False)
                assert ns_id != None

                queue = containers_registry.get_container_queue(ns_id)
                assert queue != None

                print("[WARNING] Please don't stop the container until the training is completed!")
                return queue

        elif container_action in ('die', 'stop', 'kill') and not track_scenario:
            remove_container(ebpf_map, containers_registry, container_id)

    assert False, "Unreachable"

if __name__ == '__main__':
    ebpf_map = recreate_ebpf_map(MNTNSMAP)
    containers_registry = BpfTrackedContainersRegistry()
    BpfProbe(containers_registry, MNTNSMAP)
    containers_manager(ebpf_map, containers_registry)
