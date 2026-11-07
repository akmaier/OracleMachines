"""Elapsed resource ledger and deadline-aware subprocess communication.

Elapsed phases are disjoint. This measures execution; it is not a formal
instruction count or a hard real-time OS guarantee. Native deadlines kill an
unresponsive worker, and bounded Python loops must call Deadline.check().
"""
from contextlib import contextmanager
import os
import resource
import selectors
import subprocess
import sys
import time


class BudgetExceeded(RuntimeError):
    pass


class Deadline:
    def __init__(self, seconds):
        self.end = time.monotonic() + seconds

    def remaining(self):
        left = self.end - time.monotonic()
        if left <= 0:
            raise BudgetExceeded("Query deadline exceeded; no unchecked decision was accepted")
        return left

    def check(self):
        self.remaining()


class Ledger:
    def __init__(self):
        self.start = time.perf_counter_ns()
        self.cpu = time.process_time_ns()
        self.children_cpu = children_cpu_ns()
        self.phases = {}
        self.stack = []

    @contextmanager
    def phase(self, name):
        frame = [name, time.perf_counter_ns(), 0]
        self.stack.append(frame)
        try:
            yield
        finally:
            elapsed = time.perf_counter_ns() - frame[1]
            self.stack.pop()
            self.phases[name] = self.phases.get(name, 0) + elapsed - frame[2]
            if self.stack:
                self.stack[-1][2] += elapsed

    def finish(self):
        wall = time.perf_counter_ns() - self.start
        phases = dict(self.phases)
        phases["control"] = wall - sum(phases.values())
        assert phases["control"] >= 0
        return dict(wall_ns=wall, phase_ns=phases,
                    service_cpu_ns=time.process_time_ns() - self.cpu,
                    reaped_children_cpu_ns=children_cpu_ns() - self.children_cpu,
                    service_peak_rss_bytes=peak_rss(resource.RUSAGE_SELF),
                    reaped_children_peak_rss_bytes=peak_rss(resource.RUSAGE_CHILDREN))


def peak_rss(who):
    rss = resource.getrusage(who).ru_maxrss
    return int(rss if sys.platform == "darwin" else rss * 1024)


def children_cpu_ns():
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return int((usage.ru_utime + usage.ru_stime) * 1e9)


def bounded_run(command, directory, deadline, seconds, max_output, proof, max_proof):
    """File-backed output avoids unbounded pipe capture; monitor files every 20ms.

    File growth can overshoot between polls. Limits bound accepted/read data,
    not physical disk allocation. Every exit path reaps the owned child.
    """
    local = Deadline(min(seconds, deadline.remaining()))
    stdout, stderr = directory / "stdout.txt", directory / "stderr.txt"
    process = None
    def limits():
        deadline.check()
        local.check()
        if stdout.stat().st_size + stderr.stat().st_size > max_output:
            raise BudgetExceeded("External output exceeds the configured byte limit")
        if proof.exists() and proof.stat().st_size > max_proof:
            raise BudgetExceeded("LRAT proof exceeds the configured byte limit")
    try:
        with stdout.open("wb") as out, stderr.open("wb") as err:
            process = subprocess.Popen(command, stdout=out, stderr=err)
            while process.poll() is None:
                limits()
                try:
                    process.wait(timeout=min(0.02, local.remaining(), deadline.remaining()))
                except subprocess.TimeoutExpired:
                    pass
            limits()
        return subprocess.CompletedProcess(command, process.returncode,
                                           stdout.read_text(), stderr.read_text())
    finally:
        stop_process(process)


def stop_process(process):
    """Terminate only this owned process and reap it, with bounded cleanup."""
    if process is None:
        return
    if process.poll() is None:
        process.kill()
    process.wait(timeout=2)
    for stream in (process.stdin, process.stdout, process.stderr):
        if stream is not None:
            stream.close()


def exchange(process, payload, deadline, max_bytes):
    """One newline-delimited request/response, including blocked writes."""
    if len(payload) > max_bytes:
        raise BudgetExceeded("Request exceeds the configured message byte limit")
    incoming = bytearray()
    sent = 0
    read_fd, write_fd = process.stdout.fileno(), process.stdin.fileno()
    os.set_blocking(read_fd, False)
    os.set_blocking(write_fd, False)
    with selectors.DefaultSelector() as selector:
        selector.register(write_fd, selectors.EVENT_WRITE)
        selector.register(read_fd, selectors.EVENT_READ)
        while True:
            ready = selector.select(deadline.remaining())
            if not ready:
                deadline.check()
            for key, _ in ready:
                if key.fd == write_fd:
                    try:
                        count = os.write(write_fd, payload[sent:sent + 65536])
                    except BlockingIOError:
                        continue
                    sent += count
                    if sent == len(payload):
                        selector.unregister(write_fd)
                else:
                    try:
                        chunk = os.read(read_fd, 65536)
                    except BlockingIOError:
                        continue
                    if not chunk:
                        raise RuntimeError("Solver exited without a complete response")
                    incoming.extend(chunk)
                    if len(incoming) > max_bytes:
                        raise BudgetExceeded("Solver response exceeds the configured message byte limit")
                    if b"\n" in chunk:
                        line, extra = incoming.split(b"\n", 1)
                        if extra:
                            raise ValueError("Solver emitted unsolicited response data")
                        deadline.check()
                        return line.decode("utf-8")
