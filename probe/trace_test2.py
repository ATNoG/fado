from collections import defaultdict
from threading import Thread, Lock
from probe import Probe
from time import sleep
from .bcc import BPF
import docker, os

# TODO: this NEEDS to be started before any containers starts or those first containers will NOT be monitored (needs to be fixed)

client = docker.DockerClient()
valid_images = [
    'yaml_load'
]

class ValidContainer:
    def __init__(self, image: str, ns_id: int):
        self.image = image
        self.ns_id = ns_id

def get_ebpf_map():
    bpf = BPF(text="""BPF_TABLE_PINNED("hash", u64, u32, mnt_ns_set, 128, "/sys/fs/bpf/mnt_ns_set");""")
    print("[+] eBPF map is setup...")
    return bpf.get_table("mnt_ns_set")

def add_container_to_ebpf_map(ebpf_map, container: ValidContainer):
    key = ebpf_map.Key(container.ns_id)
    value = ebpf_map.Leaf(0) 
    ebpf_map[key] = value

def remove_container_from_ebpf_map(ebpf_map, container: ValidContainer):
    key = ebpf_map.Key(container.ns_id)
    del ebpf_map[key]

def containers_manager(ebpf_map, queues, lock: Lock):
    valid_containers = {}
    for event in client.events(decode=True):
        if event['Type'] == 'container':
            container_action = event['Action']
            container_image = event['Actor']['Attributes']['image']
            container_id = event['Actor']['ID']

            # TODO: does it make sense to assert that this container is not in the `valid_containers` list??
            if container_action == 'start' and container_image in valid_images:
                container_pid = client.containers.get(container_id).attrs['State']['Pid']
                ns_id = os.stat(f'/proc/{container_pid}/ns/mnt').st_ino
                valid_containers[container_id] = ValidContainer(container_image, ns_id)
                add_container_to_ebpf_map(ebpf_map, valid_containers[container_id])
                queues[ns_id] = 0 # add a defualt value to the queue
                print(f"[+] Container created with mnt ns id of: {ns_id}")

            # TODO: this seems to run more than once when a containers is getting terminated. why?
            elif container_action in ('die', 'stop', 'kill') and container_id in valid_containers:
                remove_container_from_ebpf_map(ebpf_map, valid_containers[container_id])
                with lock:
                    del queues[valid_containers[container_id].ns_id]
                del valid_containers[container_id]
                print("[+] Container removed")

if __name__ == '__main__':
    # valid_containers = []
    # new_containers, old_containers = bruh(valid_containers)
    # add_container_to_ebpf_map(ebpf_map, new_containers[0])

    lock = Lock()
    ebpf_map = get_ebpf_map()
    queues = dict()
    Probe(queues, 2, "/sys/fs/bpf/mnt_ns_set", lock)
    Thread(target=containers_manager, args=(ebpf_map, queues, lock), daemon=True).start()
    # containers_manager(ebpf_map, queues, lock)

    print("started")
    while True:
        with lock:
            for key in queues.keys():
                print(f"size: {queues[key]} ", end='', flush=False)
            print("\t\t\t\t\t\t\t\t\r", end='', flush=True)
            sleep(0.1)
