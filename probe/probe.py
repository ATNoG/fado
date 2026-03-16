from .bcc.containers import filter_by_containers
from models.bpf import BpfContainer
from threading import Thread, Lock
from .bcc import BPF

bpf_program = """
struct syscall_data{
    u64 ts;
    u32 tid;
    u32 sid;
    u64 mnt_ns_id;
};

BPF_RINGBUF_OUTPUT(events, 1); // 16MB ring buffer

TRACEPOINT_PROBE(raw_syscalls, sys_exit) {
    if (container_should_be_filtered()) {
        return 0;
    }

    u32 key = args->id;
    if (key > 334) {
        key = 335;
    }

    if (key == 202) { // ignore futex syscalls
        return 0;
    }

    struct syscall_data sdata = {};
    sdata.ts  = bpf_ktime_get_ns();
    sdata.tid = bpf_get_current_pid_tgid();
    sdata.sid = key;

    struct task_struct *task = (struct task_struct *)bpf_get_current_task();
    sdata.mnt_ns_id = task->nsproxy->mnt_ns->ns.inum;

    events.ringbuf_output(&sdata, sizeof(sdata), 0);
    return 0;
}
"""

class ContainerFilter:
    def __init__(self, mntnsmap: str):
        self.mntnsmap = mntnsmap
        self.cgroupmap = None

# TODO: should this be in the "models"?
class BpfProbe:
    """Attaches to specific containers for probing"""

    def __init__(self, queues: dict[int, BpfContainer], window_size: int, mntnsmap: str, lock: Lock):
        args = ContainerFilter(mntnsmap)
        bpf = filter_by_containers(args) + bpf_program
        self.bpf = BPF(text=bpf, cflags=["-Wno-microsoft-anon-tag", "-fms-extensions"])
        self.window_size = window_size
        self.queues = queues
        self.lock = lock
        self.thread = Thread(target=self.monitor, daemon=True)
        self.thread.start()

    def monitor(self):
        def handle_event(cpu, data, size):
            event = self.bpf["events"].event(data)
            with self.lock:
                if event.mnt_ns_id in self.queues:
                    self.queues[event.mnt_ns_id].queue.put((event.tid, event.sid), block=True)

            # # b[event.tid].append(event.sid)
            # thread_window = b[event.mnt_ns_id][event.tid]
            # thread_window.append(event.sid)
            # if len(thread_window) > self.window_size:
            #     thread_window.pop(0)
            # if len(thread_window) == self.window_size:
            #     self.queues[event.mnt_ns_id].put([thread_window[:]], block=True)

        # register callback
        self.bpf["events"].open_ring_buffer(handle_event)

        # event-driven loop (blocks until new data)
        while True:
            # blocks until events arrive, then triggers handle_event()
            self.bpf.ring_buffer_poll()

    def end_trace(self):
        self.bpf.detach_tracepoint(b"raw_syscalls:sys_exit")
