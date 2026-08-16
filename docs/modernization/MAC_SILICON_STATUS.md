# Mac Silicon modernization status

Last updated: 2026-08-16
Active phase: Phase 2 — dependency and toolchain modernization
Phase state: **media candidate accepted locally; hosted CI and immutable publication remain gated**

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
- Deferred publication gate: commit the `moonlight-common-c` tests in their upstream repository and update the application submodule pin when commit/push work is authorized.
- Deferred observability extension: populate session-specific crash context (renderer, codec, pixel format, display, audio, power, and thermal state) when crash-report transport is implemented; the privacy-safe startup context is complete for Phase 1.
- Deferred hosted gate: run the new sanitizer, static-analysis, and CodeQL jobs when the changes are pushed. These jobs are configured but are not recorded as passing.
- User waiver (2026-08-16): skip the formal 30-minute 2560x1600 60 Hz soak. The approximately 22-minute initial counter run, follow-up Vulkan timing run, successful Sunshine connection, and absence of observed issues are accepted as the local Phase 1 runtime evidence.

### Phase 1 local validation

- Native arm64 QtTest: 13 passed, 0 failed.
- AddressSanitizer arm64 QtTest: 13 passed, 0 failed. Leak detection is unsupported by Apple's local ASan runtime and was not claimed.
- UndefinedBehaviorSanitizer arm64 QtTest: 13 passed, 0 failed.
- `moonlight-common-c` CTest: 1 executable passed, covering linked-queue bounds/order/shutdown and audio queue lifecycle.
- Native arm64 Debug application: compiled and linked successfully.
- CLI smoke test: `Moonlight --version` returned 6.1.0 and emitted the redacted startup context with commit `256022d3d621`, dependency bundle `v12`, and architecture `arm64`.
- Operator live smoke test: the Phase 1 app launched and connected to Sunshine at 2560x1600 60 Hz successfully with no observed issues. This is the primary real-use MacBook Air scenario. It confirms basic GUI startup, host connection, and streaming at the intended resolution, but does not replace the counter capture, extended soak, peripheral, or second-machine gates.
- Operator counter capture: `benchmarks/phase1-2560x1600-60-2026-08-16.json`. The selected renderer was Vulkan (libplacebo). Sampled results were decode mean/max 3.152/6.1 ms, decoded queue 0.038/3.846 ms, input dispatch 0.019/0.040 ms, network jitter 0.5/3 ms, protocol audio pending 3.182/50 ms, and SDL audio queue 24.091/55 ms. No frame replacements or observed playback issues were reported. The initial renderer/GPU/present counters received no samples because they covered Metal only; Vulkan render and presentation-wait timing has now been added for the next validation run.
- Vulkan timing validation: `benchmarks/phase1-vulkan-2560x1600-60-2026-08-16.json`. At 2560x1600 60 Hz, sampled decode mean/max was 3.331/5.296 ms, decoded queue 0.034/0.763 ms, Vulkan render encode 0.495/0.767 ms, presentation wait 2.367/2.810 ms, input dispatch 0.017/0.030 ms, and network jitter 0.4/1 ms. All three frame stages recorded 174 samples and no frame replacements. Direct Vulkan GPU completion timing remains unavailable through the current libplacebo integration; the run contained only one sampled audio event and is not used for audio conclusions.
- Static analysis and CodeQL are configured but remain hosted-CI gates; local Xcode does not ship `scan-build`, so the workflow installs LLVM explicitly.

## Phase 2 checklist

- [x] Re-fetch application remotes without overwriting the Phase 1 worktree; `origin/master` and the local baseline are `e41fedba`, while `upstream/master` remains `256022d3`.
- [x] Clone the companion repository at `/Users/justin/Development/moonlight-qt-deps`, verify clean tag `v12` at `22355399`, and initialize its top-level pinned sources.
- [x] Add `DEPENDENCY_POLICY.md` with baseline, rollback, required decision fields, review groups, and acceptance rules.
- [x] Pin published `v12` macOS and Steam Link archive sizes and SHA-256 values in `setup-deps.py`.
- [x] Make the Python installer reject unsafe archive paths and symlinks, bound archive expansion, validate required contents, verify macOS universal slices, and replace the installed bundle atomically.
- [x] Preserve an explicit `MOONLIGHT_DEPS_TAG=v12` developer rollback override; unknown/unreviewed tags fail closed.
- [x] Add installer unit coverage for traversal, symlinks, digest failure preservation, and atomic replacement.
- [x] Add an SPDX 2.3 source/bundle SBOM and generated third-party notices from the pinned inventory.
- [x] Refresh the first media-group candidate and record versions, release dates, ABI/API notes, patch dispositions, test requirements, and explicit open security-assessment fields in `MEDIA_CANDIDATE.md`.
- [ ] Refresh candidate pins, release dates, CVEs, API/ABI notes, patch dispositions, and test requirements for each of the five update groups.
- [x] Build and test the first media candidate for both macOS slices in the dependency repository.
- [x] Run Moonlight tests and matched before/after benchmarks against the media candidate.
- [x] Correlate the exact media candidate against reviewed upstream/NVD advisories and the configured/shipped feature surface.
- [x] Record user acceptance of the media candidate, including the matched-test caveats and conditional security result.
- [ ] Publish an immutable dependency artifact and add its reviewed asset metadata; publication is not authorized by the current task.

### Phase 2 validation to date

- Python installer tests: 5 passed, covering hostile paths, symlinks, digest mismatch preservation, rollback after an injected swap failure, and successful atomic replacement.
- Real published `v12` smoke test: 28,492,950-byte archive downloaded, SHA-256 verified, safely extracted into a temporary repository, required contents validated, and `libSDL2.dylib` confirmed as `x86_64 arm64`.
- The generated SBOM and notices describe the currently pinned sources and `v12` bundle. They are a starting inventory, not a vulnerability assessment or final shipped-file SBOM.
- Media candidate: FFmpeg 9.0 to 9.0.1 and Vulkan-Headers/SDK 1.4.321/1.4.350.0 to 1.4.357; dav1d 1.5.4 and libplacebo 7.371.0 remain pinned. The exact ledger and open security fields are in `MEDIA_CANDIDATE.md`.
- Dependency tests passed for both slices: dav1d 7/7 per slice, libplacebo 12/12 per slice, and the configured FFmpeg FATE/checkasm target per slice. Sample-dependent FFmpeg FATE cases were not run.
- Local media-only archive: 16,696,236 bytes, SHA-256 `5dc5d2a7587b57b312ce893744ce540312a811d94d2f40d4449a14f106776ae2`. ZIP integrity, universal slices, macOS deployment targets, install names, and absence of developer-machine load paths passed.
- Moonlight built against the exact candidate archive as native arm64 Release and official-Qt universal Release. The universal binary targets macOS 13 and `Moonlight --version` passed under both native arm64 and Rosetta x86_64. QtTest remained 13/13 and installer tests 5/5.
- Matched v12/candidate 10-minute streaming runs completed at 2560x1600 60 Hz with Sunshine, Vulkan (libplacebo), AC power, a byte-identical executable, and only the five reviewed media dylibs changed. Mean CPU was 14.606% / 14.549% (-0.39%) and mean RSS was 257.4 / 230.8 MiB (-10.3%).
- Candidate mean decode, render-encode, and presentation-wait were -1.9%, -4.2%, and -6.7% versus v12. Both runs recorded zero replaced frames, no macOS thermal/performance warning, and no operator-observed visual/audio/input issue.
- Candidate audio-pending mean was +29.8% with a lower 80 ms maximum, and SDL queue mean was +5.9% with the same 55 ms maximum. Network/input samples were sparse, and candidate decoded-frame samples were 6.9% lower, so identical delivered-frame cadence is not proven.
- The bounded security review found no known reachable advisory in the reviewed records. It is a conditional pass rather than a vulnerability-free assertion: FFmpeg's ledger lacks a 9.0 mapping, negative advisory searches are not proof of absence, and publication requires a fresh recheck. Details are in `MEDIA_SECURITY_REVIEW.md`.
- The user accepted the media candidate on 2026-08-16 with the documented matched-test caveats and conditional security result. The `top` POWER metric remained zero and is unavailable for energy conclusions; sustained-session and privileged energy gates are explicitly deferred rather than passed. Hosted CI and immutable publication remain open. No application bundle tag or release asset was changed.

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
- Published dependency CI baseline declares macOS minimum 13.0 and Vulkan SDK/MoltenVK 1.4.350.0; the local media candidate changes the SDK workflow pin to 1.4.357.0.
- Local tools: CMake 4.4.2, Meson 1.9.1 in a temporary validation environment, Ninja 1.13.2, NASM 3.02, pkg-config 3.0.5, Python 3.14.7, Homebrew 6.0.17, Node 26.7.0, npm 11.19.0, create-dmg 8.0.0

## Findings and risks

1. Resolved in the Phase 2 foundation: `setup-deps.py` now verifies the reviewed v12 asset size and SHA-256 before safe extraction and atomic installation.
2. The native Homebrew builds pass but cannot prove the macOS 13/14 release target because their Qt frameworks require macOS 26. The universal build with official Qt correctly records minimum macOS 13.
3. `macdeployqt` copies `PlugIns/sqldrivers/libqsqlmimer.dylib`, which links to missing `/usr/local/lib/libmimerapi.dylib`. The bundle therefore fails the “no developer-machine paths” release check even though Moonlight does not use that SQL plugin.
4. `create-dmg` 8.0.0 is unpinned in CI. The local global installation currently fails to load its `macos-alias` native module under Node 26.7.0, so no DMG was claimed.
5. The local app is unsigned. Hosted CI, Intel execution, signing, notarization, Gatekeeper, clean-machine behavior, and published artifacts remain separate gates.
6. A forced-offscreen automation attempt produced the supplied Qt platform-integration abort. It was a harness error, was excluded, and the corrected normal-Cocoa runs completed twice.

## Issue triage outcome

There are no upstream-labeled P0 issues in the initial matrix. Modernization candidates #1929, #1249, #1594, #1781, #1825, and #1429 are treated as P1. #1429 is classified `fixed on master` from reporter validation of a post-SDL-update nightly; local peripheral coverage remains missing. #1427 and #1953 are `external/OS`. The remaining reports are `needs information`; none is claimed reproduced locally.

## Exit-gate decision

Phase 0 is **not closed**. Build, inventory, schema, issue-state refresh, and idle repeatability gates pass. The controlled streaming baseline and every unresolved P1 reproducer remain blocked by missing host/test-content/peripheral inputs. Phase 2 foundation work is active by user direction, but accepting a dependency pin movement still requires the applicable matched before/after evidence.

Phase 1 is **complete as of 2026-08-16**. Native logic, renderer ownership, audio policy, input replay, performance counters, crash-context redaction, sanitizer configurations, static-analysis configuration, CodeQL configuration, and `moonlight-common-c` queue coverage are implemented. Local arm64 tests, ASan, UBSan, application build, CLI smoke, Sunshine connection, and Vulkan timing validation passed. The user explicitly waived the formal 30-minute soak. Hosted execution, publication commits, and extended session crash metadata remain clearly deferred and are not represented as passed.

Phase 2 foundation work **started on 2026-08-16**. Installer integrity and extraction hardening, rollback selection, dependency policy, SBOM generation, and the companion-repository baseline are in place. The first media candidate passed local dual-architecture dependency builds/tests, native/universal Moonlight builds, matched 2560x1600 60 Hz streaming, and a bounded security correlation without an observed blocker. The user accepted it locally on 2026-08-16 with the documented caveats. Hosted CI and immutable `v13` publication remain open; watts and a sustained candidate session are explicitly unavailable/deferred and are not represented as passed.
