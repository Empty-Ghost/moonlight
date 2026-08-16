#!/usr/bin/env python3
"""Capture a repeatable local startup/idle sample for a deployed Moonlight app."""

from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import subprocess
import time


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("app", type=pathlib.Path)
    parser.add_argument("--duration", type=int, default=30)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--platform", help="Optional Qt platform override; normal macOS runs should omit this")
    args = parser.parse_args()
    binary = args.app / "Contents/MacOS/Moonlight"
    started = time.monotonic()
    command = [str(binary)]
    if args.platform:
        command.extend(["-platform", args.platform])
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
    cpu, rss = [], []
    try:
        while time.monotonic() - started < args.warmup + args.duration:
            row = subprocess.run(["ps", "-o", "%cpu=,rss=", "-p", str(process.pid)],
                                 text=True, capture_output=True, check=True).stdout.split()
            if len(row) == 2 and time.monotonic() - started >= args.warmup:
                cpu.append(float(row[0]))
                rss.append(int(row[1]) * 1024)
            if process.poll() is not None:
                raise RuntimeError(f"Moonlight exited early with status {process.returncode}")
            time.sleep(1)
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    payload = {
        "duration_seconds": args.duration,
        "warmup_seconds": args.warmup,
        "cpu_percent_mean": round(statistics.fmean(cpu), 3),
        "resident_memory_bytes_mean": round(statistics.fmean(rss)),
        "resident_memory_bytes_peak": max(rss),
        "sample_count": len(cpu),
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
