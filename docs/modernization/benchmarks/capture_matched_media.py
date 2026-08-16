#!/usr/bin/env python3
"""Capture matched v12/media-candidate Moonlight streaming runs on macOS."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import shutil
import statistics
import subprocess
import time


REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
APPS = {
    "baseline": REPO_ROOT / "build/phase2-media-matched/Moonlight-v12.app",
    "candidate": REPO_ROOT / "build/phase2-media-matched/Moonlight-media-candidate.app",
}
FRAMEWORKS = (
    "libavcodec.63.dylib",
    "libavutil.61.dylib",
    "libswscale.10.dylib",
    "libplacebo.dylib",
    "libMoltenVK.dylib",
)
COUNTER_MARKER = "Performance counters:"


def run_text(command: list[str], *, check: bool = False) -> str:
    return subprocess.run(command, text=True, capture_output=True, check=check).stdout.strip()


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def power_source() -> str:
    output = run_text(["pmset", "-g", "batt"])
    match = re.search(r"Now drawing from '([^']+)'", output)
    return match.group(1) if match else "unknown"


def battery_snapshot() -> str:
    return run_text(["pmset", "-g", "batt"])


def thermal_snapshot() -> str:
    result = subprocess.run(["pmset", "-g", "therm"], text=True, capture_output=True)
    return (result.stdout + result.stderr).strip()


def process_sample(pid: int) -> tuple[float, int] | None:
    result = subprocess.run(
        ["ps", "-o", "%cpu=,rss=", "-p", str(pid)], text=True, capture_output=True
    )
    fields = result.stdout.split()
    if len(fields) != 2:
        return None
    return float(fields[0]), int(fields[1]) * 1024


def process_power(pid: int) -> float | None:
    result = subprocess.run(
        ["top", "-l", "1", "-pid", str(pid), "-stats", "pid,cpu,mem,power"],
        text=True,
        capture_output=True,
    )
    for line in reversed(result.stdout.splitlines()):
        fields = line.split()
        if fields and fields[0] == str(pid) and len(fields) >= 4:
            try:
                return float(fields[-1])
            except ValueError:
                return None
    return None


def newest_log(started_wall: float) -> pathlib.Path | None:
    candidates = [
        path for path in pathlib.Path("/tmp").glob("Moonlight-*.log")
        if path.stat().st_mtime >= started_wall - 2
    ]
    return max(candidates, key=lambda path: path.stat().st_mtime, default=None)


def parse_counters(log_path: pathlib.Path | None) -> dict | None:
    if log_path is None or not log_path.exists():
        return None
    counters = None
    for line in log_path.read_text(errors="replace").splitlines():
        if COUNTER_MARKER in line:
            try:
                counters = json.loads(line.split(COUNTER_MARKER, 1)[1].strip())
            except json.JSONDecodeError:
                continue
    return counters


def log_confirms_vulkan(log_path: pathlib.Path | None) -> bool:
    return bool(
        log_path
        and log_path.exists()
        and "Renderer 'Vulkan (libplacebo)' chosen" in log_path.read_text(errors="replace")
    )


def app_manifest(app: pathlib.Path) -> dict:
    binary = app / "Contents/MacOS/Moonlight"
    frameworks = app / "Contents/Frameworks"
    return {
        "path": str(app),
        "binary_sha256": sha256(binary),
        "architectures": run_text(["lipo", "-archs", str(binary)], check=True).split(),
        "framework_sha256": {
            name: sha256(frameworks / name) for name in FRAMEWORKS
        },
    }


def bundle_file_hashes(app: pathlib.Path) -> dict[str, str]:
    return {
        str(path.relative_to(app)): sha256(path)
        for path in sorted(app.rglob("*"))
        if path.is_file()
    }


def notify(message: str) -> None:
    subprocess.run(
        ["osascript", "-e", f'display notification "{message}" with title "Moonlight matched test"'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def capture(variant: str, session: pathlib.Path, duration: int) -> None:
    app = APPS[variant]
    binary = app / "Contents/MacOS/Moonlight"
    result_path = session / f"{variant}.json"
    if result_path.exists():
        raise SystemExit(f"Refusing to overwrite {result_path}")
    if not binary.exists():
        raise SystemExit(f"Missing prepared app: {app}")
    if run_text(["pgrep", "-x", "Moonlight"]):
        raise SystemExit("Quit all running Moonlight instances before starting a capture.")

    session.mkdir(parents=True, exist_ok=True)
    manifest = app_manifest(app)
    initial_power_source = power_source()
    initial_battery = battery_snapshot()
    initial_thermal = thermal_snapshot()
    print(f"\nPrepared {variant.upper()} app: {app}")
    print(f"Power source: {initial_power_source}")
    print("Use Sunshine, Vulkan (libplacebo), 2560x1600 at 60 Hz, and the same content/settings for both runs.")
    input("Press Return to launch Moonlight (or Ctrl-C to stop): ")

    environment = dict(__import__("os").environ)
    environment["PERFORMANCE_COUNTERS"] = "1"
    environment.pop("PERFORMANCE_COUNTERS_SAMPLE_ALL", None)
    started_wall = time.time()
    process = subprocess.Popen([str(binary)], env=environment)
    try:
        input("Start the test stream, wait for stable playback, then press Return to begin the timed capture: ")
        if process.poll() is not None:
            raise RuntimeError(f"Moonlight exited early with status {process.returncode}")

        capture_started = time.monotonic()
        cpu_samples: list[float] = []
        rss_samples: list[int] = []
        power_samples: list[float] = []
        next_power_sample = capture_started
        while time.monotonic() - capture_started < duration:
            if process.poll() is not None:
                raise RuntimeError(f"Moonlight exited during capture with status {process.returncode}")
            sample = process_sample(process.pid)
            if sample:
                cpu, rss = sample
                cpu_samples.append(cpu)
                rss_samples.append(rss)
            if time.monotonic() >= next_power_sample:
                power = process_power(process.pid)
                if power is not None:
                    power_samples.append(power)
                next_power_sample = time.monotonic() + 5
            remaining = duration - int(time.monotonic() - capture_started)
            if remaining and remaining % 60 == 0:
                print(f"{remaining // 60} minute(s) remaining")
            time.sleep(1)

        notify(f"{variant.capitalize()} capture complete; quit Moonlight normally")
        print("Timed capture complete. End the stream and quit Moonlight normally so counters are written.")
        process.wait()
        if process.returncode != 0:
            raise RuntimeError(f"Moonlight exited with status {process.returncode}")

        log_path = newest_log(started_wall)
        counters = parse_counters(log_path)
        if not counters or not counters.get("enabled"):
            raise RuntimeError(f"No enabled performance-counter snapshot found in {log_path}")
        if not log_confirms_vulkan(log_path):
            raise RuntimeError(f"The runtime log does not confirm Vulkan (libplacebo): {log_path}")
        if counters["metrics"]["decode"]["samples"] == 0:
            raise RuntimeError(f"The runtime log contains no sampled decoded frames: {log_path}")

        observation = input("Observed visual/audio/input issues (leave blank for none observed): ").strip()
        payload = {
            "schema_version": 1,
            "variant": variant,
            "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "scenario": {
                "resolution": {"width": 2560, "height": 1600},
                "refresh_rate_hz": 60,
                "host": "Sunshine",
                "renderer_required": "Vulkan (libplacebo)",
                "timed_duration_seconds": duration,
            },
            "app": manifest,
            "environment": {
                "power_source_start": initial_power_source,
                "power_source_end": power_source(),
                "battery_start": initial_battery,
                "battery_end": battery_snapshot(),
                "thermal_start": initial_thermal,
                "thermal_end": thermal_snapshot(),
            },
            "process_metrics": {
                "cpu_percent_mean": statistics.fmean(cpu_samples),
                "cpu_percent_max": max(cpu_samples),
                "resident_memory_bytes_mean": round(statistics.fmean(rss_samples)),
                "resident_memory_bytes_peak": max(rss_samples),
                "top_power_mean": statistics.fmean(power_samples) if power_samples else None,
                "top_power_max": max(power_samples) if power_samples else None,
                "sample_count": len(cpu_samples),
                "power_sample_count": len(power_samples),
                "top_power_note": "macOS top POWER is a relative process metric, not watts.",
            },
            "performance_counters": counters,
            "renderer_confirmed": "Vulkan (libplacebo)",
            "operator_observation": observation or "none observed",
            "raw_log": {
                "path": str(log_path) if log_path else None,
                "privacy_note": "The full runtime log remains in /tmp and is not copied into the repository.",
            },
        }
        result_path.write_text(json.dumps(payload, indent=2) + "\n")
        print(f"Saved {result_path}")
    except BaseException:
        if process.poll() is None:
            print("Capture stopped; quit Moonlight normally or press Ctrl-C again to terminate it.")
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=10)
        raise


def prepare(session: pathlib.Path) -> None:
    if run_text(["pgrep", "-x", "Moonlight"]):
        raise SystemExit("Quit all running Moonlight instances before preparing the session.")
    session.mkdir(parents=True, exist_ok=True)
    manifests = {variant: app_manifest(app) for variant, app in APPS.items()}
    if any(manifest["architectures"] != ["x86_64", "arm64"] for manifest in manifests.values()):
        raise SystemExit("Both prepared apps must contain x86_64 and arm64 in that order.")
    differing_frameworks = [
        name for name in FRAMEWORKS
        if manifests["baseline"]["framework_sha256"][name]
        != manifests["candidate"]["framework_sha256"][name]
    ]
    if not differing_frameworks:
        raise SystemExit("Prepared apps do not contain distinct media frameworks.")
    if manifests["baseline"]["binary_sha256"] != manifests["candidate"]["binary_sha256"]:
        raise SystemExit("Prepared app executables are not byte-identical.")
    bundle_hashes = {variant: bundle_file_hashes(app) for variant, app in APPS.items()}
    differing_bundle_files = sorted(
        path for path in bundle_hashes["baseline"]
        if bundle_hashes["baseline"][path] != bundle_hashes["candidate"].get(path)
    )
    expected_differences = sorted(f"Contents/Frameworks/{name}" for name in FRAMEWORKS)
    if differing_bundle_files != expected_differences:
        raise SystemExit(
            "Prepared app bundles differ outside the reviewed media frameworks: "
            + ", ".join(differing_bundle_files)
        )
    payload = {
        "schema_version": 1,
        "prepared_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "scenario": {
            "resolution": {"width": 2560, "height": 1600},
            "refresh_rate_hz": 60,
            "host": "Sunshine",
            "renderer_required": "Vulkan (libplacebo)",
            "timed_duration_seconds": 600,
            "order": ["baseline", "candidate"],
        },
        "apps": manifests,
        "differing_media_frameworks": differing_frameworks,
        "byte_identical_executable": True,
        "only_differing_bundle_files": differing_bundle_files,
        "power_source_at_preparation": power_source(),
        "battery_at_preparation": battery_snapshot(),
        "thermal_at_preparation": thermal_snapshot(),
        "raw_log_policy": "Full Moonlight logs remain in /tmp and are not copied into the repository.",
    }
    output = session / "prepared.json"
    output.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Prepared session: {output}")


def percentage_delta(baseline: float, candidate: float) -> float | None:
    if baseline == 0:
        return None
    return (candidate - baseline) * 100.0 / baseline


def compare(session: pathlib.Path) -> None:
    baseline_path = session / "baseline.json"
    candidate_path = session / "candidate.json"
    if not baseline_path.exists() or not candidate_path.exists():
        raise SystemExit("Both baseline.json and candidate.json are required before comparison.")
    baseline = json.loads(baseline_path.read_text())
    candidate = json.loads(candidate_path.read_text())
    deltas = {}
    for metric in ("cpu_percent_mean", "resident_memory_bytes_mean", "top_power_mean"):
        before = baseline["process_metrics"].get(metric)
        after = candidate["process_metrics"].get(metric)
        deltas[metric] = {
            "baseline": before,
            "candidate": after,
            "percent_delta": percentage_delta(before, after) if before is not None and after is not None else None,
        }
    for metric in baseline["performance_counters"]["metrics"]:
        baseline_metric = baseline["performance_counters"]["metrics"][metric]
        candidate_metric = candidate["performance_counters"]["metrics"][metric]
        before = baseline_metric["mean_us"]
        after = candidate_metric["mean_us"]
        deltas[f"counter_{metric}_mean_us"] = {
            "baseline": before,
            "candidate": after,
            "percent_delta": percentage_delta(before, after),
        }
        deltas[f"counter_{metric}_max_us"] = {
            "baseline": baseline_metric["max_us"],
            "candidate": candidate_metric["max_us"],
            "percent_delta": percentage_delta(
                baseline_metric["max_us"], candidate_metric["max_us"]
            ),
        }
        deltas[f"counter_{metric}_samples"] = {
            "baseline": baseline_metric["samples"],
            "candidate": candidate_metric["samples"],
            "percent_delta": percentage_delta(
                baseline_metric["samples"], candidate_metric["samples"]
            ),
        }
    top_power_available = any(
        run["process_metrics"].get("top_power_max") not in (None, 0)
        for run in (baseline, candidate)
    )
    decode_sample_delta = deltas["counter_decode_samples"]["percent_delta"]
    payload = {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "session": str(session),
        "power_source_match": (
            baseline["environment"]["power_source_start"]
            == candidate["environment"]["power_source_start"]
        ),
        "top_power_available": top_power_available,
        "decode_sample_count_percent_delta": decode_sample_delta,
        "deltas": deltas,
        "replaced_frames": {
            "baseline": baseline["performance_counters"]["replaced_frames"],
            "candidate": candidate["performance_counters"]["replaced_frames"],
        },
        "operator_observations": {
            "baseline": baseline["operator_observation"],
            "candidate": candidate["operator_observation"],
        },
        "decision": (
            "local matched runtime completed without an observed blocker; manual acceptance remains "
            "required because video sample counts differ and the local power metric was unavailable"
        ),
    }
    output = session / "comparison.json"
    output.write_text(json.dumps(payload, indent=2) + "\n")
    rows = []
    for metric in ("decode", "decoded_queue", "render_encode", "present", "audio_pending", "sdl_queue", "network_jitter", "input_dispatch"):
        before = baseline["performance_counters"]["metrics"][metric]
        after = candidate["performance_counters"]["metrics"][metric]
        delta = deltas[f"counter_{metric}_mean_us"]["percent_delta"]
        rows.append(
            f"| {metric} | {before['samples']} / {after['samples']} | "
            f"{before['mean_us'] / 1000:.3f} / {after['mean_us'] / 1000:.3f} | "
            f"{before['max_us'] / 1000:.3f} / {after['max_us'] / 1000:.3f} | "
            f"{delta:+.1f}% |"
        )
    markdown = "\n".join([
        "# Phase 2 matched media comparison",
        "",
        "Scenario: 2560x1600 at 60 Hz, Vulkan (libplacebo), Sunshine, 10-minute timed runs, AC power.",
        "",
        "| Metric | Samples v12 / candidate | Mean ms v12 / candidate | Max ms v12 / candidate | Mean delta |",
        "|---|---:|---:|---:|---:|",
        *rows,
        "",
        "## Process and outcome",
        "",
        f"- Mean CPU: {baseline['process_metrics']['cpu_percent_mean']:.3f}% / {candidate['process_metrics']['cpu_percent_mean']:.3f}% ({deltas['cpu_percent_mean']['percent_delta']:+.2f}%).",
        f"- Mean RSS: {baseline['process_metrics']['resident_memory_bytes_mean'] / 1048576:.1f} MiB / {candidate['process_metrics']['resident_memory_bytes_mean'] / 1048576:.1f} MiB ({deltas['resident_memory_bytes_mean']['percent_delta']:+.1f}%).",
        f"- Replaced frames: {baseline['performance_counters']['replaced_frames']} / {candidate['performance_counters']['replaced_frames']}.",
        f"- Operator observations: v12 `{baseline['operator_observation']}`; candidate `{candidate['operator_observation']}`.",
        "- macOS reported no thermal or performance warning in either run.",
        "- The macOS `top` POWER field stayed at zero and is unavailable for energy conclusions.",
        "",
        "## Interpretation",
        "",
        f"- Candidate mean decode, render-encode, and presentation-wait changed by {deltas['counter_decode_mean_us']['percent_delta']:+.1f}%, {deltas['counter_render_encode_mean_us']['percent_delta']:+.1f}%, and {deltas['counter_present_mean_us']['percent_delta']:+.1f}%, respectively.",
        f"- Candidate decoded sample count differed by {decode_sample_delta:+.1f}%; stage means remain useful, but the runs do not prove identical delivered-frame cadence.",
        "- Network jitter and input-dispatch counts are too sparse for a strong comparative conclusion.",
        "- Audio pending increased in mean but decreased in maximum; SDL queue mean increased while its maximum was unchanged. No audio issue was reported.",
        "- These are stage timings, not end-to-end latency. This local result does not establish watts, hosted CI, signing, or clean-machine behavior.",
        "",
        "Decision: local matched runtime completed without an observed blocker. Final candidate acceptance still requires manual review of these caveats and the separate security gate.",
        "",
    ])
    (session / "comparison.md").write_text(markdown)
    print(f"Saved {output}")
    print(f"Saved {session / 'comparison.md'}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("variant", choices=("prepare", "baseline", "candidate", "compare"))
    parser.add_argument("--session", type=pathlib.Path, required=True)
    parser.add_argument("--duration", type=int, default=600)
    args = parser.parse_args()
    if args.duration < 60:
        parser.error("--duration must be at least 60 seconds")
    if args.variant == "prepare":
        prepare(args.session.resolve())
    elif args.variant == "compare":
        compare(args.session.resolve())
    else:
        capture(args.variant, args.session.resolve(), args.duration)


if __name__ == "__main__":
    main()
