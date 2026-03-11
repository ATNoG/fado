from .bcc import BPF
import docker, os

client = docker.DockerClient()
valid_images = [
    'yaml_load'
]

class ValidContainer:
    def __init__(self, id: str, image: str, ns_id: int):
        self.id = id
        self.image = image
        self.ns_id = ns_id

def get_ebpf_map():
    bpf_program = """
    BPF_TABLE_PINNED("hash", u64, u32, mnt_ns_set, 128, "/sys/fs/bpf/mnt_ns_set");
    """

    # Initialize BPF - this automatically creates/pins the map or attaches to the existing one
    bpf = BPF(text=bpf_program)

    # Grab the map reference just like before
    return bpf.get_table("mnt_ns_set")

# TODO: is the byte order correct??
def add_container_to_ebpf_map(ebpf_map, container: ValidContainer):
    key = ebpf_map.Key(container.ns_id)
    value = ebpf_map.Leaf(0) 
    ebpf_map[key] = value

def remove_container_from_ebpf_map(ebpf_map, container: ValidContainer):
    key = ebpf_map.Key(container.ns_id)
    try:
        del ebpf_map[key]
        # del monitored_containers[container_id]
        # print(f"[+] Removed container {container_id[:12]} (inode: {inode}) from eBPF map.")
    except Exception as e:
        print(e)

# # TODO: what if a container ID gets repeated??
# def bruh(valid_containers: list[ValidContainer]) -> tuple[list[ValidContainer], list[ValidContainer]]:
#     valid_running_containers = []
#     for c in client.containers.list():
#         if c.id != None and any(i in str(c.image) for i in valid_images):
#             valid_running_containers.append(c)
#     old_containers = list(filter(lambda c: all(c.id != vrc.id for vrc in valid_running_containers), valid_containers))
#     new_containers = []
#     for vrc in valid_running_containers:
#         if all(vrc.id != c.id for c in valid_containers):
#             ns_id = os.stat(f'/proc/{vrc.attrs['State']['Pid']}/ns/mnt').st_ino
#             new_containers.append(ValidContainer(vrc.id, str(vrc.image), ns_id))
#     return (new_containers, old_containers)

def containers_manager():
    for event in client.events(decode=True):
        if event.get('Type') == 'container':
            action = event.get('Action')
            # container_id = event.get('id')

            if action == 'start':
                print("Container started")

            # 'die' triggers when a container process exits, 'stop' when gracefully halted
            elif action in ('die', 'stop', 'kill'):
                print("Container stopped")

# # TODO: this could be optimized by only adding new containers and removing stopped ones
# def get_valid_containers() -> list[ValidContainer]:
#     valid_containers = []
#     for c in client.containers.list():
#         # get all containers with a valid ID and one of the supported images
#         if c.id != None and any(i in str(c.image) for i in valid_images):
#             ns_id = os.stat(f'/proc/{c.attrs['State']['Pid']}/ns/mnt').st_ino
#             valid_containers.append(ValidContainer(c.id, str(c.image), ns_id))
#     return valid_containers

if __name__ == '__main__':
    # ebpf_map = get_ebpf_map()

    # valid_containers = []
    # new_containers, old_containers = bruh(valid_containers)
    # add_container_to_ebpf_map(ebpf_map, new_containers[0])
    containers_manager()
