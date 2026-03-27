from models import BpfTrackedContainer, BpfProbe, BpfTrackedContainersRegistry
from probe.bcc import BPF
from config import FILES
from queue import Queue
import docker, os

# TODO: this NEEDS to be started before any containers starts or those first containers will NOT be monitored (needs to be fixed)

container_registry: BpfTrackedContainersRegistry = BpfTrackedContainersRegistry()
client = docker.DockerClient()
valid_images = {
    'yaml_load': 'YamlLoad_5s_w2_20p'
}

def recreate_ebpf_map():
    if os.path.exists('/sys/fs/bpf/mnt_ns_set'):
        os.remove('/sys/fs/bpf/mnt_ns_set')

    bpf = BPF(text="""BPF_TABLE_PINNED("hash", u64, u32, mnt_ns_set, 128, "/sys/fs/bpf/mnt_ns_set");""")
    print('[+] eBPF map is setup...')
    return bpf.get_table('mnt_ns_set')

def add_container(ebpf_map, image: str, container_id: str):
    # TODO: what if this fails somehow?
    container_pid = client.containers.get(container_id).attrs['State']['Pid']
    ns_id = os.stat(f'/proc/{container_pid}/ns/mnt').st_ino

    model_path = FILES / (valid_images[image] + '.pkl')
    if not container_registry.add_container(ns_id, BpfTrackedContainer(image, container_id, model_path, Queue(maxsize=1000), apply_policies=False)):
        return

    key = ebpf_map.Key(ns_id)
    value = ebpf_map.Leaf(0)
    ebpf_map[key] = value
    print('[+] Container created')

def remove_container(ebpf_map, container_id: str):
    ns_id = container_registry.remove_container(container_id)
    if ns_id == None:
        return

    key = ebpf_map.Key(ns_id)
    del ebpf_map[key]
    print('[+] Container removed')

def containers_manager(ebpf_map):
    for event in client.events(decode=True):
        if event['Type'] == 'container':
            container_action = event['Action']
            container_image = event['Actor']['Attributes']['image']
            container_id = event['Actor']['ID']

            if container_action == 'start' and container_image in valid_images:
                add_container(ebpf_map, container_image, container_id)

            elif container_action in ('die', 'stop', 'kill'):
                remove_container(ebpf_map, container_id)

if __name__ == '__main__':
    ebpf_map = recreate_ebpf_map()
    BpfProbe(container_registry, '/sys/fs/bpf/mnt_ns_set')
    containers_manager(ebpf_map)
