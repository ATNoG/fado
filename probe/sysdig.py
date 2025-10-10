import subprocess
import threading
import time

class SysdigProbe:

    def __init__(self, container_id: str, sysdig_path: str = 'sysdig', extra_filter: str | None = None):
        if not container_id:
            raise ValueError("container_id must be a non-empty string")

        self.container_id = container_id.strip()
        self.sysdig_path = sysdig_path
        self.extra_filter = extra_filter

        self._proc = None
        self._reader_thread = None
        self._stderr_thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._buffer = []

    def _filter_expr(self) -> str:
        base = f'(container.id={self.container_id}) and (evt.type!=futex)'
        return f'({base}) and ({self.extra_filter})' if self.extra_filter else base

    def _build_cmd(self) -> list[str]:
        # -U => unbuffered output (flush every event)
        # -p => custom print format
        # filter expression last arg
        return [self.sysdig_path, "-p", "%evt.time|%evt.type|%evt.args|%evt.res|%thread.tid", self._filter_expr()]

    def start(self):
        if self._proc:
            raise RuntimeError("Probe already started")

        self._proc = subprocess.Popen(
            self._build_cmd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,   # we drain this in a separate thread to avoid deadlocks
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1,                # line-buffered on our side
        )

        self._stop_event.clear()
        self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._stderr_thread = threading.Thread(target=self._drain_stderr, daemon=True)
        self._reader_thread.start()
        self._stderr_thread.start()

    def _drain_stderr(self):
        # Keep stderr drained so sysdig never blocks on a full pipe; also useful for debugging
        if not self._proc or not self._proc.stderr:
            return
        while not self._stop_event.is_set():
            # print(f"Error: {self._proc.stderr.readline()}")
            if self._stop_event.is_set():
                break

    def _reader_loop(self):
        assert self._proc and self._proc.stdout
        stdout = self._proc.stdout

        # Robust loop: don't exit just because no line arrived yet; check process liveness
        while not self._stop_event.is_set():
            line = stdout.readline()
            if line == '':
                # No data right now; if process ended, we're done. Otherwise, wait a bit.
                if self._proc.poll() is not None:
                    break
                time.sleep(0.05)
                continue

            line = line.rstrip('\n')
            if not line:
                continue

            # parts = line.split('|', 6)
            # print(parts)
            # if len(parts) < 7:
            #     continue

            # ts, cid, cname, pid_s, tid_s, evtype, evargs = parts
            # try:
            #     pid = int(pid_s)
            #     tid = int(tid_s)
            # except ValueError:
            #     pid = tid = None

            with self._lock:
                self._buffer.append(line)
                # self._buffer.append((ts, cid, cname, pid, tid, evtype, evargs))

        # If we’re stopping, try to read any residual buffered lines quickly
        try:
            residual = stdout.read()
            if residual:
                for raw in residual.splitlines():
                    parts = raw.split('|', 6)
                    if len(parts) < 7:
                        continue
                    ts, cid, cname, pid_s, tid_s, evtype, evargs = parts
                    try:
                        pid = int(pid_s); tid = int(tid_s)
                    except ValueError:
                        pid = tid = None
                    with self._lock:
                        self._buffer.append((ts, cid, cname, pid, tid, evtype, evargs))
        except Exception:
            pass

    def get_data(self):
        with self._lock:
            data = list(self._buffer)
            self._buffer.clear()
        return data

    def stop(self, timeout: float = 2.0):
        if not self._proc:
            return []

        self._stop_event.set()
        try:
            self._proc.terminate()
        except Exception:
            pass

        try:
            self._proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                self._proc.kill()
            except Exception:
                pass
            self._proc.wait()

        if self._reader_thread:
            self._reader_thread.join(timeout=1.0)
        if self._stderr_thread:
            self._stderr_thread.join(timeout=1.0)

        data = self.get_data()
        self._proc = None
        self._reader_thread = None
        self._stderr_thread = None
        return data
