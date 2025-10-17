from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Iterable, Optional
from probe.bcc.syscall import syscalls

@dataclass(frozen=True)
class Event:
    ts_ns: int
    tid: int
    syscall_id: int  # mapped via syscall_map


def parse_events_from_csv(
    path: str | Path,
    syscall_map: Dict[str, int],
    require_in_map: bool = True,
) -> List[Event]:
    """
    Parse a whitespace-delimited 'CSV' like the sample.
    Keeps only rows with direction '<'. Maps syscall to ID via syscall_map.

    Columns expected (at least first 7 tokens):
      0 ts_ns, 1 cpu, 2 pid, 3 comm, 4 tid, 5 syscall, 6 direction ('<' or '>')
    """
    events: List[Event] = []
    p = Path(path)
    with p.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # We only need first 7 tokens; the rest is args we ignore.
            # Split conservatively to avoid exploding on long arg strings.
            parts = line.split(maxsplit=6)
            if len(parts) < 7:
                continue
            ts_s, _cpu, _pid, _comm, tid_s, syscall, direction_and_rest = parts
            
            # direction_and_rest starts with '<' or '>' then the remainder.
            direction = direction_and_rest.split(maxsplit=1)[0]

            if direction != "<":
                continue

            if (sid := syscall_map.get(syscall)) is None:
                if require_in_map:
                    # Skip unknown syscalls strictly
                    continue
                else:
                    # Or assign a fallback ID (e.g., -1) if you prefer
                    sid = -1

            try:
                ts_ns = int(ts_s)
                tid = int(tid_s)
            except ValueError:
                continue

            events.append(Event(ts_ns=ts_ns, tid=tid, syscall_id=sid))
    # Ensure chronological order
    events.sort(key=lambda e: e.ts_ns)

    return events


def group_windows_by_interval_and_tid(
    events: List[Event],
    n: int,
    interval_seconds: int = 5,
) -> Dict[int, Dict[int, List[Tuple[int, ...]]]]:
    """
    Returns:
      windows[interval_index][tid] = list of windows (each window is a tuple of syscall_ids)

    - interval_index = (ts - start_ts) // (interval_seconds * 1e9)
    - If a TID has fewer than n entries in an interval (even after carry-in),
      the entries are carried over to the *next* interval; no windows produced yet.
    - If there are >= n entries (after carry-in), windows are produced from *all*
      accumulated entries for that interval, then carry is cleared.
    """
    if n <= 0:
        raise ValueError("Window size n must be > 0")
    if not events:
        return {}

    interval_ns = interval_seconds * 1_000_000_000
    start_ts = events[0].ts_ns
    end_ts = events[-1].ts_ns


    # Bucket events into interval -> tid -> list[syscall_id]
    buckets: Dict[int, Dict[int, List[int]]] = defaultdict(lambda: defaultdict(list))
    for e in events:
        idx = (e.ts_ns - start_ts) // interval_ns
        buckets[idx][e.tid].append(e.syscall_id)

    # Carry-over per TID (across intervals)
    carry: Dict[int, List[int]] = defaultdict(list)

    # Produce windows
    windows: Dict[int, Dict[int, List[Tuple[int, ...]]]] = defaultdict(lambda: defaultdict(list))

    for interval_idx in sorted(buckets.keys()):
        per_tid = buckets[interval_idx]

        # Ensure we also process TIDs that only have carry and no new events this interval
        all_tids = set(per_tid.keys()) | set(carry.keys())

        for tid in sorted(all_tids):
            seq = []
            if carry.get(tid):
                seq.extend(carry[tid])
            if per_tid.get(tid):
                seq.extend(per_tid[tid])

            if len(seq) < n:
                # Not enough yet: carry forward wholly; no windows emitted
                carry[tid] = seq
                continue

            # Enough entries: create step-1 sliding windows from the accumulated seq
            tid_windows: List[Tuple[int, ...]] = []
            for i in range(0, len(seq) - n + 1):
                tid_windows.append(tuple(seq[i : i + n]))

            windows[interval_idx][tid].extend(tid_windows)

            # Clear carry because we only carry when insufficient
            carry[tid] = []

    return windows


# ---- Example usage ----
if __name__ == "__main__":
    syscalls = {v.decode(): k for k, v in syscalls.items()}

    events = parse_events_from_csv("models/abundant_buck_7911.sc", syscalls)
    windows = group_windows_by_interval_and_tid(events, n=3, interval_seconds=5)

    # Pretty-print result
    counter = 0
    with open("models/lid.txt", 'w') as f:
        for ival in sorted(windows):
            for tid in sorted(windows[ival]):
                for window in windows[ival][tid]:
                    counter += 1
                    f.write(str(ival) + " " + ",".join([str(w) for w in window]) + "\n")

    f.close()
    print(counter)