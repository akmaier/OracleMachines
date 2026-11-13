#!/usr/bin/env python3
"""Fresh-process replay of the same transported and locally acquired facts."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_probe_continuation import sha


def run(report, output):
    samples = []; started = time.perf_counter()
    for repeat in range(2):
        for history in ((True, False) if repeat == 0 else (False, True)):
            command = [sys.executable, 'experiments/compare_cnf_lemma_transport.py', 'validate', str(report)]
            if history: command.append('--history')
            start = time.perf_counter(); process = subprocess.run(command, text=True, capture_output=True, check=True)
            elapsed = time.perf_counter()-start; sample = json.loads(process.stdout)
            if samples and sample['results'] != samples[0]['results']: raise ValueError('Different checked facts')
            sample.update(mode='history' if history else 'compact', repeat=repeat, process_wall_seconds=elapsed)
            samples.append(sample); print(json.dumps(dict(mode=sample['mode'], seconds=elapsed)), flush=True)
    output.write_text(json.dumps(dict(report_sha256=sha(report), script_sha256=sha(__file__),
        samples=samples, pipeline_seconds=time.perf_counter()-started,
        limitations=['Same checked augmentation and obstruction facts; history mode additionally verifies their inventory ancestry.',
            'Compact mode verifies explicit mathematical premises, not full inventory ancestry or structural coverage.',
            'Process startup/imports/teardown included; OS caches not flushed; only two samples per mode.',
            'Export and past acquisition remain charged separately; disk size is not peak RAM.']), sort_keys=True, indent=2)+'\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('report', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); run(a.report, a.output)
