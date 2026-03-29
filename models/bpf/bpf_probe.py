from .bpf_tracked_containers_registry import BpfTrackedContainersRegistry
from probe import BPF, filter_by_containers
from dataclasses import dataclass
from threading import Thread

class BpfProbe:
    """Attaches to specific containers for probing"""

    @dataclass
    class BpfProbeFilter:
        def __init__(self, mntnsmap: str):
            self.mntnsmap = mntnsmap
            self.cgroupmap = None

    def __init__(self, container_registry: BpfTrackedContainersRegistry, mntnsmap: str):
        args = self.BpfProbeFilter(mntnsmap)
        bpf = filter_by_containers(args) + open('./models/bpf/bpf.program', 'r').read()
        self.bpf = BPF(text=bpf, cflags=['-Wno-microsoft-anon-tag', '-fms-extensions'])
        self.container_registry = container_registry
        self.thread = Thread(target=self.monitor, daemon=True)
        self.thread.start()

    def monitor(self):
        def handle_event(cpu, data, size):
            event = self.bpf['events'].event(data)
            queue = self.container_registry.get_container_queue(event.mnt_ns_id)
            if queue != None:
                try:
                    # TODO: does it make sense to use a timeout here??
                    # we cannot hold the probe back if some consumer thread decides to hang or is just too slow
                    queue.put((event.tid, event.sid), block=False, timeout=None)
                except:
                    pass

        # register callback
        self.bpf['events'].open_ring_buffer(handle_event)

        # event-driven loop (blocks until new data)
        while True:
            # blocks until events arrive, then triggers handle_event()
            self.bpf.ring_buffer_poll()

    # TODO: what about stopping the thread??
    def stop(self):
        self.bpf.detach_tracepoint(b'raw_syscalls:sys_exit')
