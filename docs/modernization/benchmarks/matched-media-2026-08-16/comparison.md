# Phase 2 matched media comparison

Scenario: 2560x1600 at 60 Hz, Vulkan (libplacebo), Sunshine, 10-minute timed runs, AC power.

| Metric | Samples v12 / candidate | Mean ms v12 / candidate | Max ms v12 / candidate | Mean delta |
|---|---:|---:|---:|---:|
| decode | 420 / 391 | 3.082 / 3.022 | 7.624 / 8.920 | -1.9% |
| decoded_queue | 419 / 390 | 0.259 / 0.020 | 94.538 / 0.491 | -92.1% |
| render_encode | 419 / 390 | 0.437 / 0.419 | 1.005 / 0.635 | -4.2% |
| present | 419 / 390 | 2.582 / 2.408 | 18.678 / 17.823 | -6.7% |
| audio_pending | 2550 / 2244 | 0.745 / 0.967 | 90.000 / 80.000 | +29.8% |
| sdl_queue | 3185 / 3152 | 39.052 / 41.374 | 55.000 / 55.000 | +5.9% |
| network_jitter | 12 / 12 | 0.583 / 0.750 | 2.000 / 2.000 | +28.6% |
| input_dispatch | 14 / 29 | 0.014 / 0.013 | 0.029 / 0.024 | -8.1% |

## Process and outcome

- Mean CPU: 14.606% / 14.549% (-0.39%).
- Mean RSS: 257.4 MiB / 230.8 MiB (-10.3%).
- Replaced frames: 0 / 0.
- Operator observations: v12 `none`; candidate `none`.
- macOS reported no thermal or performance warning in either run.
- The macOS `top` POWER field stayed at zero and is unavailable for energy conclusions.

## Interpretation

- Candidate mean decode, render-encode, and presentation-wait changed by -1.9%, -4.2%, and -6.7%, respectively.
- Candidate decoded sample count differed by -6.9%; stage means remain useful, but the runs do not prove identical delivered-frame cadence.
- Network jitter and input-dispatch counts are too sparse for a strong comparative conclusion.
- Audio pending increased in mean but decreased in maximum; SDL queue mean increased while its maximum was unchanged. No audio issue was reported.
- These are stage timings, not end-to-end latency. This local result does not establish watts, hosted CI, signing, or clean-machine behavior.

Decision: local matched runtime completed without an observed blocker. Final candidate acceptance still requires manual review of these caveats and the separate security gate.
