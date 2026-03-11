#!/usr/bin/env python3
import docker
import os
from .bcc import BPF

# 1. Define the eBPF Map using the PINNED macro in C
# Syntax: BPF_TABLE_PINNED(type, key_type, value_type, name, max_entries, pinned_path)
bpf_text = """
BPF_TABLE_PINNED("hash", u64, u32, mnt_ns_set, 128, "/sys/fs/bpf/mnt_ns_set");
"""

print("[*] Initializing BPF and attaching to pinned map...")
# Initialize BPF - this automatically creates/pins the map or attaches to the existing one
b = BPF(text=bpf_text)

# Grab the map reference just like before
mnt_ns_table = b.get_table("mnt_ns_set")

# Initialize Docker client
client = docker.from_env()

# Cache to store container_id -> inode mappings
monitored_containers = {}

def get_mnt_ns_inode(container_id):
    """Helper function to get the mount namespace inode of a container."""
    try:
        container = client.containers.get(container_id)
        pid = container.attrs['State']['Pid']

        if pid == 0:
            print(f"[-] Container {container_id[:12]} is not running.")
            return None

        mnt_ns_path = f"/proc/{pid}/ns/mnt"
        return os.stat(mnt_ns_path).st_ino
    except Exception as e:
        print(e)
        return None

def add_container(container_id):
    """Calculates the inode and adds it to the pinned eBPF map."""
    if container_id in monitored_containers:
        print(f"[*] Container {container_id[:12]} is already being monitored.")
        return

    inode = get_mnt_ns_inode(container_id)
    if inode:
        # Write to eBPF Map using BCC's key/leaf types
        key = mnt_ns_table.Key(inode)
        value = mnt_ns_table.Leaf(1) 
        mnt_ns_table[key] = value
        
        monitored_containers[container_id] = inode
        print(f"[+] Added container {container_id[:12]} (inode: {inode}) to eBPF map.")

def remove_container(container_id):
    """Removes the container's inode from the pinned eBPF map."""
    inode = monitored_containers.get(container_id)

    if not inode:
        print(f"[-] Cannot remove: Container {container_id[:12]} is not tracked.")
        return
    
    key = mnt_ns_table.Key(inode)
    try:
        del mnt_ns_table[key]
        del monitored_containers[container_id]
        print(f"[+] Removed container {container_id[:12]} (inode: {inode}) from eBPF map.")
    except KeyError:
        print(f"[*] Container {container_id[:12]} (inode: {inode}) was already missing.")

# # ==========================================
# # Example Usage
# # ==========================================
# if __name__ == "__main__":
#     print("--- eBPF Container Manager Ready ---")    
#     # my_container = "YOUR_CONTAINER_ID_HERE"
#     # add_container(my_container)
#     # remove_container(my_container)
