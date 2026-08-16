# Mac Silicon modernization status

Last updated: 2026-08-15  
Active phase: Phase 1 — test and observability foundation  
Phase state: **in progress; native foundation implemented and locally validated**

## Ownership and scope

| Area | Working owner | Evidence / rollback |
|---|---|---|
| Application and macOS build | Moonlight Qt maintainers; local execution by Codex | Start `2e13ed99`; synchronized baseline `256022d3`; rollback app commit `2e13ed99`. |
| Dependency bundle | moonlight-qt-deps maintainers | Immutable tag `v12`, commit `22355399`, archive SHA-256 in `dependencies.json`; rollback remains `v12`. |
| Controlled Sunshine host and test content | Unassigned | Required before stream baselines or most issue reproducers can run. |
| Signing/notarization and hosted CI | Release maintainers | Not authorized or executed in Phase 0. |

## Phase 0 checklist

- [x] Preserve the user-supplied modernization plan and unrelated worktree state.
- [x] Fetch and fast-forward to current `upstream/master` (`256022d3`).
- [x] Record application and recursive submodule SHAs.
- [x] Clone and inspect `moonlight-qt-deps` tag `v12` (`22355399`).
- [x] Download the v12 macOS asset and independently record SHA-256 and size.
- [x] Generate `dependencies.json` from both repositories, including pins, licenses, source URLs, action pins, direct libraries, and the deployed transitive Mach-O closure.
- [x] Record local Qt/Xcode/SDK/Clang and build-tool versions.
- [x] Build native arm64 Debug.
- [x] Build native arm64 Release.
- [x] Build universal Release with the official Qt 6.11.1 universal package.
- [x] Define a machine-readable benchmark schema before accepting measurements.
- [x] Capture and repeat a warm idle baseline within the stated noise bounds.
- [x] Refresh and classify all ten issue rows (eleven issue IDs) in the plan.
- [ ] Capture startup-to-ready with a real readiness marker.
- [ ] Capture 1080p60, 1440p120, and 4K60 stream baselines on controlled Ethernet.
- [ ] Capture decoder/render/present, audio, input, loss/jitter, dropped-frame, energy, and thermal metrics during streaming.
- [ ] Run P0/P1 reproducers on current master with required peripherals and host.
- [ ] Have a second machine/operator reproduce the complete baseline.

## Phase 1 checklist

- [x] Add a native QtTest target for pure stream logic and address formatting.
- [x] Move aspect-fit, normalized-coordinate, bitrate, and display-mode selection into deterministic production helpers.
- [x] Add a single-slot renderer ownership contract with replacement, take, generation, and reset behavior.
- [x] Add a deterministic audio queue policy and apply it to the existing SDL protocol/device queue limits without changing the thresholds.
- [x] Add JSON input trace capture/replay primitives covering absolute/relative mouse, touchpad, scrolling, device rates, and controller axes.
- [x] Add sampled, normally disabled counters and instrument FFmpeg decode, decoded-frame queueing, Metal encoding/GPU/present completion, mouse/touch/keyboard/controller dispatch, protocol/SDL audio queue duration, and network RTT variance.
- [x] Add privacy-safe startup crash context with app commit, dependency bundle, architecture, and OS version; hash user-selected audio device labels rather than storing them.
- [x] Add native arm64 AddressSanitizer and UndefinedBehaviorSanitizer jobs, Clang static analysis, and root CodeQL configuration.
- [x] Prove representative fault coverage for stale renderer frames, queue overload/device loss, malformed input traces, and crash-context redaction.
- [x] Add direct settings-migration coverage for macOS/Wayland fullscreen defaults and the deprecated HEVC-HDR split.
- [x] Add deterministic color-range/color-space selection coverage, including requested-value fallback for unspecified frame metadata.
- [x] Add `moonlight-common-c` lifecycle/bounds/interruption tests for the linked blocking queue and audio FEC queue.
- [ ] Commit the `moonlight-common-c` tests in their upstream repository and update the application submodule pin through its own reviewable change.
- [ ] Populate session-specific crash context (renderer, codec, pixel format, display, audio, power, and thermal state).
- [ ] Run the new hosted sanitizer, static-analysis, and CodeQL jobs.

### Phase 1 local validation

- Native arm64 QtTest: 13 passed, 0 failed.
- AddressSanitizer arm64 QtTest: 13 passed, 0 failed. Leak detection is unsupported by Apple's local ASan runtime and was not claimed.
- UndefinedBehaviorSanitizer arm64 QtTest: 13 passed, 0 failed.
- `moonlight-common-c` CTest: 1 executable passed, covering linked-queue bounds/order/shutdown and audio queue lifecycle.
- Native arm64 Debug application: compiled and linked successfully.
- CLI smoke test: `Moonlight --version` returned 6.1.0 and emitted the redacted startup context with commit `256022d3d621`, dependency bundle `v12`, and architecture `arm64`.
- Static analysis and CodeQL are configured but remain hosted-CI gates; local Xcode does not ship `scan-build`, so the workflow installs LLVM explicitly.

## Baseline evidence

- Machine-readable results: `benchmarks/baseline-mac16-12-2026-08-15.json`
- Human summary: `benchmarks/baseline-mac16-12-2026-08-15.md`
- Schema: `benchmarks/benchmark.schema.json`
- Repeat harness: `benchmarks/capture_idle.py`
- Build harness: `build_baseline_macos.sh`
- Dependency inventory: `dependencies.json`
- Issue triage: `ISSUE_MATRIX.md`

## Toolchain and flags

- App version: 6.1.0
- macOS: 26.6.1 (25G76); Xcode 26.6 (17F113); SDK 26.5
- Compiler: Apple Clang 21.0.0; language standard C++17
- Universal CI-equivalent Qt: 6.11.1 `clang_64`, both x86_64 and arm64, deployment target 13.0
- Local Homebrew Qt: 6.11.1 arm64-only, built for macOS 26; qmake selects deployment target 14.0 and emits compatibility warnings
- Release flags observed: `-O2 -g -DNDEBUG`; official package script additionally sets ThinLTO for packaged builds
- Dependency CI declares macOS minimum 13.0 and Vulkan SDK/MoltenVK 1.4.350.0
- Local tools: CMake 4.4.2, Meson not installed, Ninja 1.13.2, NASM 3.02, pkg-config 3.0.5, Python 3.14.7, Homebrew 6.0.17, Node 26.7.0, npm 11.19.0, create-dmg 8.0.0

## Findings and risks

1. The v12 dependency asset is reproducibly identified, but `setup-deps.py` still performs no digest verification. That fix belongs to Phase 2.
2. The native Homebrew builds pass but cannot prove the macOS 13/14 release target because their Qt frameworks require macOS 26. The universal build with official Qt correctly records minimum macOS 13.
3. `macdeployqt` copies `PlugIns/sqldrivers/libqsqlmimer.dylib`, which links to missing `/usr/local/lib/libmimerapi.dylib`. The bundle therefore fails the “no developer-machine paths” release check even though Moonlight does not use that SQL plugin.
4. `create-dmg` 8.0.0 is unpinned in CI. The local global installation currently fails to load its `macos-alias` native module under Node 26.7.0, so no DMG was claimed.
5. The local app is unsigned. Hosted CI, Intel execution, signing, notarization, Gatekeeper, clean-machine behavior, and published artifacts remain separate gates.
6. A forced-offscreen automation attempt produced the supplied Qt platform-integration abort. It was a harness error, was excluded, and the corrected normal-Cocoa runs completed twice.

## Issue triage outcome

There are no upstream-labeled P0 issues in the initial matrix. Modernization candidates #1929, #1249, #1594, #1781, #1825, and #1429 are treated as P1. #1429 is classified `fixed on master` from reporter validation of a post-SDL-update nightly; local peripheral coverage remains missing. #1427 and #1953 are `external/OS`. The remaining reports are `needs information`; none is claimed reproduced locally.

## Exit-gate decision

Phase 0 is **not closed**. Build, inventory, schema, issue-state refresh, and idle repeatability gates pass. The controlled streaming baseline and every unresolved P1 reproducer remain blocked by missing host/test-content/peripheral inputs and by timing counters explicitly assigned to Phase 1. Beginning dependency updates or performance tuning would violate the plan’s stop conditions.
