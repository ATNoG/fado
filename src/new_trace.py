from models.bpf import BpfContainer
from threading import Lock
from probe import BpfProbe
from probe.bcc import BPF
from utils import FILES
from queue import Queue
import docker, os

# TODO: this NEEDS to be started before any containers starts or those first containers will NOT be monitored (needs to be fixed)

valid_containers: dict[int, BpfContainer] = {}
client = docker.DockerClient()
valid_images = {
    'yaml_load': 'YamlLoad_5s_w2_20p'
}

def recreate_ebpf_map():
    if os.path.exists("/sys/fs/bpf/mnt_ns_set"):
        os.remove("/sys/fs/bpf/mnt_ns_set")

    bpf = BPF(text="""BPF_TABLE_PINNED("hash", u64, u32, mnt_ns_set, 128, "/sys/fs/bpf/mnt_ns_set");""")
    print("[+] eBPF map is setup...")
    return bpf.get_table("mnt_ns_set")

def add_container(ebpf_map, image: str, container_id: str, queue: Queue[tuple[int, int]], lock: Lock):
    # TODO: what if this fails somehow?
    container_pid = client.containers.get(container_id).attrs['State']['Pid']
    ns_id = os.stat(f'/proc/{container_pid}/ns/mnt').st_ino

    model_path = FILES / (valid_images[image] + '.pkl')
    with lock:
        valid_containers[ns_id] = BpfContainer(image, container_id, model_path, queue)

    key = ebpf_map.Key(ns_id)
    value = ebpf_map.Leaf(0)
    ebpf_map[key] = value
    print("[+] Container created")

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
    print("[+] Container removed")

def containers_manager(ebpf_map, lock: Lock):
    for event in client.events(decode=True):
        if event['Type'] == 'container':
            container_action = event['Action']
            container_image = event['Actor']['Attributes']['image']
            container_id = event['Actor']['ID']

            # TODO: does it make sense to assert that this container is not in the `valid_containers` list??
            if container_action == 'start' and container_image in valid_images:
                add_container(ebpf_map, container_image, container_id, Queue(maxsize=1000), lock)

            # TODO: this seems to run more than once when a containers is getting terminated. why?
            elif container_action in ('die', 'stop', 'kill'):
                remove_container(ebpf_map, container_id, lock)

if __name__ == '__main__':
    lock = Lock()
    ebpf_map = recreate_ebpf_map()
    BpfProbe(valid_containers, 2, "/sys/fs/bpf/mnt_ns_set", lock)
    containers_manager(ebpf_map, lock)
