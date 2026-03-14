from .bcc.containers import filter_by_containers
from collections import defaultdict
from threading import Thread, Lock
from queue import Queue
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

class  Probe:
    def __init__(self, queues: dict[int, int], window_size: int, mntnsmap: str, lock: Lock):
        # self.htab_batch_ops = BPF.kernel_struct_has_field(b'bpf_map_ops', b'map_lookup_and_delete_batch') == 1
        args = ContainerFilter(mntnsmap)
        bpf = filter_by_containers(args) + bpf_program
        self.bpf = BPF(text=bpf, cflags=["-Wno-microsoft-anon-tag", "-fms-extensions"])
        self.window_size = window_size
        # self.ready = False
        self.queues = queues # defaultdict(int) # queues: dict[int, Queue]
        # self.data = []
        self.lock = lock
        self.monitor_dict = Thread(target=self.monitor, daemon=True)
        self.monitor_dict.start()

    # def get_queues(self) -> dict[int, int]:
    #     return self.queues

    def monitor(self):
        # b = defaultdict(list)
        # b = defaultdict(lambda: defaultdict(list))
        # bruh = defaultdict(int)

        # TODO: do i really need to do this by threads?
        def handle_event(cpu, data, size):
            event = self.bpf["events"].event(data)
            with self.lock:
                if event.mnt_ns_id in self.queues:
                    self.queues[event.mnt_ns_id] += 1

            # bruh[event.mnt_ns_id] += 1
            # # print(f"\rmnt ns id: {event.mnt_ns_i}", end='', flush=True)
            # for key in bruh.keys():
            #     print(f"size: {bruh[key]} ", end='', flush=False)
            # print("\t\t\t\t\t\r", end='', flush=True)

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

    # def gen_sliding_window(self, data, window_size):
    #     grouped = defaultdict(list)
    #     for ts, tid, sid in data:
    #         grouped[tid].append(sid)
    #     threads = {}
    #     for tid, syscalls in grouped.items():
    #         grouped_syscalls = [syscalls[i:i + window_size] for i in range(0, len(syscalls) - window_size + 1)]
    #         threads[tid] = grouped_syscalls
    #     grouped.clear()
    #     return threads

# def get_data(b, flag: int = 0):
#     entry = [f"{k.value},{v.value},{flag}" for k, v in sorted(b["syscalls"].items_lookup_and_delete_batch(), key=lambda kv: kv[0].value)]
#     return '\n'.join(entry) + "\n"
