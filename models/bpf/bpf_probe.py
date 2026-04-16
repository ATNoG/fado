from .bpf_tracked_containers_registry import BpfTrackedContainersRegistry
from collections import defaultdict
from threading import Thread
from queue import Full
from bcc import BPF

class BpfProbe:
    '''Attaches to specific containers for probing'''

    def __init__(self, container_registry: BpfTrackedContainersRegistry, ebpf: BPF):
        self.container_registry = container_registry
        self.ebpf = ebpf

        self.thread = Thread(target=self.monitor, daemon=True)
        self.thread.start()

    def monitor(self):
        tmp_windows = defaultdict(list)

        def handle_event(cpu, data, size):
            event = self.ebpf['events'].event(data)
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
                except Full:
                    pass

        # register callback
        self.ebpf['events'].open_ring_buffer(handle_event)

        # event-driven loop (blocks until new data)
        while True:
            # blocks until events arrive, then triggers handle_event()
            self.ebpf.ring_buffer_poll()

    # TODO: what about stopping the thread??
    def stop(self):
        self.ebpf.detach_tracepoint(b'raw_syscalls:sys_exit')
