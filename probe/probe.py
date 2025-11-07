from queue import Queue
from time import sleep
from collections import defaultdict, Counter
import threading
from .bcc import BPF
from .bcc.containers import filter_by_containers

bpf_program = """
struct syscall_data{
    u64 ts; 
    u32 tid;
    u32 sid;
};

BPF_RINGBUF_OUTPUT(events, 1 << 12);  // 4KB ring buffer

TRACEPOINT_PROBE(raw_syscalls, sys_exit) {

    if (container_should_be_filtered()) {
        return 0;
    }

    u32 key = args->id;

    if (key > 334) {
        key = 335;
    }

    if (key == 202) {
        return 0;
    }
    
    struct syscall_data sdata = {};
    sdata.ts  = bpf_ktime_get_ns();
    sdata.tid = bpf_get_current_pid_tgid();
    sdata.sid = key;
    u64 ts = bpf_ktime_get_ns();

    events.ringbuf_output(&sdata, sizeof(sdata), 0);


    return 0;   
}
"""

class ContainerFilter:
    def __init__(self, mntnsmap):
        self.mntnsmap = mntnsmap
        self.cgroupmap = None

class  Probe:
    def __init__(self, queue:Queue, window_size, mntnsmap):
        self.htab_batch_ops = True if BPF.kernel_struct_has_field(b'bpf_map_ops',
        b'map_lookup_and_delete_batch') == 1 else False
        args = ContainerFilter(mntnsmap)
        bpf = filter_by_containers(args) + bpf_program
        self.bpf = BPF(text=bpf)
        self.window_size = window_size
        self.ready = False
        self.queue = queue
        self.data = []
        self.monitor_dict = threading.Thread(target=self.monitor, daemon=True)
        self.monitor_dict.start()

    def monitor(self):
        b = defaultdict(list)

        ## UNUSED
        def handle_e(cpu, data, size):
            event = self.bpf["events"].event(data)
            self.queue.put([[event.ts, event.tid, event.sid]])

        def handle_event(cpu, data, size):
            event = self.bpf["events"].event(data)
            b[event.tid].append(event.sid)
            
            if len(b[event.tid]) > self.window_size:
                b[event.tid].pop(0)

            if len(b[event.tid]) == self.window_size:
                self.queue.put([b[event.tid][:]], block=True)  

        # register callback
        self.bpf["events"].open_ring_buffer(handle_event)

        # event-driven loop (blocks until new data)
        while True:
            # blocks until events arrive, then triggers handle_event()
            self.bpf.ring_buffer_poll()

    
    def end_trace(self):
        self.bpf.detach_tracepoint("raw_syscalls:sys_exit")

    def gen_sliding_window(self, data, window_size):
        grouped = defaultdict(list)
        for ts, tid, sid in data:
            grouped[tid].append(sid)
        threads = {}
        for tid, syscalls in grouped.items():
            grouped_syscalls = [
                syscalls[i:i + window_size]
                for i in range(0, len(syscalls) - window_size + 1)
            ]
            threads[tid] = grouped_syscalls
        grouped.clear()
        return threads



def get_data(b, flag=0):
    entry = [f"{k.value},{v.value},{flag}" for k, v in sorted(b["syscalls"].items_lookup_and_delete_batch(), key=lambda kv: kv[0].value)]
    return '\n'.join(entry) + "\n"

def trace(mntnsmap):
    args = ContainerFilter(mntnsmap)
    bpf = filter_by_containers(args) + bpf_program
    b = BPF(text=bpf)
    return b

def end_trace(b):
    b.detach_tracepoint("raw_syscalls:sys_exit")