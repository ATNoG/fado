from .bpf_tracked_containers_registry import BpfTrackedContainersRegistry
from bcc.containers import filter_by_containers
from collections import defaultdict
from dataclasses import dataclass
from threading import Thread
from bcc import BPF

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
        tmp_windows = defaultdict(list)

        def handle_event(cpu, data, size):
            event = self.bpf['events'].event(data)
            tmp_windows[event.tid].append(event.sid)

            queue = self.container_registry.get_container_queue(event.mnt_ns_id)
            window_size = self.container_registry.get_container_window_size(event.mnt_ns_id)
            if not queue or not window_size:
                return

            if len(tmp_windows[event.tid]) > window_size:
                tmp_windows[event.tid].pop(0)

            if len(tmp_windows[event.tid]) == window_size:
                try:
                    # TODO: should this have a timeout just to avoid unnecessary data losses?
                    # we cannot hold the probe back if some consumer thread/process decides to hang or is just too slow
                    queue.put([tmp_windows[event.tid][:]], block=False, timeout=None)
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
