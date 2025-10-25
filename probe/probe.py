from collections import defaultdict
import threading
from .bcc import BPF
from .bcc.containers import filter_by_containers

bpf_program = """
struct syscall_data{
    u32 tid;
    u32 sid;
};

BPF_HASH(syscalls, u64, struct syscall_data);

TRACEPOINT_PROBE(raw_syscalls, sys_exit) {

    u32 key = args->id;

    if (container_should_be_filtered()) {
        return 0;
    }

    if (key > 334) {
        key = 335;
    }

    if (key == 202) {
        return 0;
    }

    u32 tid = bpf_get_current_pid_tgid();
    
    struct syscall_data sdata = {};
    sdata.tid = tid;
    sdata.sid = key;
    u64 ts = bpf_ktime_get_ns();
    syscalls.update(&ts, &sdata);

    return 0;   
}
"""

class ContainerFilter:
    def __init__(self, mntnsmap):
        self.mntnsmap = mntnsmap
        self.cgroupmap = None

class  Probe:
    def __init__(self, mntnsmap):
        self.htab_batch_ops = True if BPF.kernel_struct_has_field(b'bpf_map_ops',
        b'map_lookup_and_delete_batch') == 1 else False
        args = ContainerFilter(mntnsmap)
        bpf = filter_by_containers(args) + bpf_program
        self.bpf = BPF(text=bpf)
        # self.window_size = window_size
        self.data_lock = threading.Lock()
        self.data = []
        self.monitor_dict = threading.Thread(target=self.monitor, daemon=True)
        self.monitor_dict.start()

    def monitor(self):
        while True:
            if len(self.bpf['syscalls']) > 0:
                with self.data_lock:
                    self.data += [[k.value, v.tid, v.sid] for k, v in (sorted(self.bpf["syscalls"].items_lookup_and_delete_batch(), key=lambda kv: kv[0].value) if self.htab_batch_ops else sorted(self.bpf["syscalls"].items(), key=lambda kv: kv[0].value))] 
                if not self.htab_batch_ops: self.bpf["syscalls"].clear()

    def get_data(self):
        with self.data_lock:
            result = self.data.copy()
            self.data.clear()   
        return result
    
    def end_trace(self):
        data = [[k.value, v.tid, v.sid] for k, v in (sorted(self.bpf["syscalls"].items_lookup_and_delete_batch(), key=lambda kv: kv[0].value) if self.htab_batch_ops else sorted(self.bpf["syscalls"].items(), key=lambda kv: kv[0].value))] 
        if not self.htab_batch_ops: self.bpf["syscalls"].clear()
        self.bpf.detach_tracepoint("raw_syscalls:sys_exit")
        return data

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