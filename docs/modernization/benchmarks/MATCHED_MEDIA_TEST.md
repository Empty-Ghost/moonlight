# Phase 2 matched media test

Prepared: 2026-08-16

## Fixed scenario

- Client: primary MacBook Air
- Host: the same Sunshine machine for both runs
- Resolution and refresh: 2560x1600 at 60 Hz
- Renderer: Vulkan (libplacebo), confirmed in each Moonlight log
- Content, codec, bitrate, HDR state, audio device, controller/input activity, and network path: identical for both runs
- Timed capture: 10 minutes after playback stabilizes
- Order: v12 baseline, cooldown, media candidate
- Power source: either battery or AC is acceptable, but it must remain unchanged across both captures

The two test bundles are clones of one current Phase 1 official-Qt universal build. Their executable and every non-media file are byte-identical; only the five reviewed media dylibs differ. The harness verifies that invariant, refuses to run while another Moonlight instance exists, and refuses to overwrite a completed result.

## Commands

From the repository root:

```sh
python3 docs/modernization/benchmarks/capture_matched_media.py prepare \
  --session docs/modernization/benchmarks/matched-media-2026-08-16

python3 docs/modernization/benchmarks/capture_matched_media.py baseline \
  --session docs/modernization/benchmarks/matched-media-2026-08-16
```

After the baseline completes, wait at least five minutes and confirm `pmset -g therm` reports no warning. Keep Sunshine, content, settings, and power source unchanged, then run:

```sh
python3 docs/modernization/benchmarks/capture_matched_media.py candidate \
  --session docs/modernization/benchmarks/matched-media-2026-08-16
```

Generate the neutral comparison report:

```sh
python3 docs/modernization/benchmarks/capture_matched_media.py compare \
  --session docs/modernization/benchmarks/matched-media-2026-08-16
```

Quit Moonlight normally when the timed-capture notification appears. Normal shutdown is required for the internal performance-counter snapshot. The full Moonlight log remains under `/tmp`; only hashes, system samples, counters, and the operator observation are written into the benchmark directory.

## Interpretation boundary

FFmpeg decode, decoded-queue, Vulkan render-encode, and presentation-wait measurements are stage timings, not end-to-end latency. macOS `top` reports a relative `POWER` score, not watts. This local A/B run does not prove signing, notarization, hosted CI, Intel GUI behavior, or clean-machine behavior.
