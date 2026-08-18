# Codex plan: Moonlight library modernization, bug fixing, and Apple Silicon optimization

Status: proposed execution plan  
Prepared: 2026-08-14  
Updated: 2026-08-17 (macOS arm64-only support decision)
Primary repository: `moonlight-stream/moonlight-qt`  
Companion dependency repository: `moonlight-stream/moonlight-qt-deps`

## 1. Objective

Modernize every direct and bundled dependency, fix reproducible macOS bugs, and improve Moonlight's latency, frame pacing, audio stability, image quality, energy use, and packaging on Apple Silicon without regressing the other supported platforms.

This is a controlled modernization program, not a one-shot "update everything" change. Codex should use small branches and independently reviewable pull requests, record baselines before optimizing, and keep the last known-good dependency bundle available for immediate rollback.

## 2. Current baseline

The plan is based on the following verified local state:

- The worktree is clean on `master` at `2e13ed99` from 2026-08-06 and matches both `origin/master` and `upstream/master`.
- The application version file remains `6.1.0`, even though `master` contains substantial post-release work.
- The local test machine is a 10-core Apple M4 MacBook Air with 16 GB RAM, a 10-core GPU, Metal 4, and a 2560 x 1664 Retina display.
- The local environment is macOS 26.6.1, Xcode 26.6, Apple Clang 21, macOS SDK 26.5, and Qt 6.11.1.
- The historical production macOS build targeted macOS 13 or later and created a universal `x86_64 arm64` app. On 2026-08-17, the project explicitly changed the macOS target to arm64-only; `v12` remains the rollback bundle but is not the architecture contract for `v13`.
- The macOS implementation uses VideoToolbox plus Metal or `AVSampleBufferDisplayLayer`; the main Apple Silicon Metal path uses `CAMetalDisplayLink` on macOS 14 or later.
- The current dependency bundle is `moonlight-qt-deps` tag `v12`, built on 2026-08-06. It is already recent, so upgrades must be based on a fresh compatibility and security audit rather than an assumption that every component is stale.
- There is no application unit-test, benchmark, sanitizer, fuzzing, or static-analysis suite in this repository. CI primarily proves compilation and packaging, with only qmake feature compile tests for EGL and Steam Link.
- `setup-deps.py` downloads and extracts the prebuilt archive without checking a digest or signature.

## 3. Scope and constraints

### In scope

- All application submodules, bundled libraries, Qt/toolchain pins, CI actions, build tools, packaging tools, controller mappings, and macOS system-framework integrations.
- Native arm64 correctness and performance on Apple M-series hardware.
- Arm64-only correctness for the distributed macOS app and every packaged Mach-O dependency.
- macOS input, networking diagnostics, decoding, rendering, HDR/color, HiDPI, audio, controllers, window lifecycle, power, signing, notarization, and update behavior.
- Regression tests, performance harnesses, observability, dependency integrity, SBOM generation, and release gates.

### Constraints

- macOS `x86_64` support is dropped as of 2026-08-17. Do not spend build, test, packaging, or release-gate capacity on the Intel Mac slice. This decision does not drop Windows x64 or Linux x86_64.
- Preserve Linux, Windows, and Steam Link behavior. Shared-code changes must pass all existing platform builds.
- Do not bulk-merge upstream feature pull requests. Rebase, review, test, and split them as needed.
- Do not work around Wi-Fi jitter by silently disabling AWDL, AirDrop, or other system services. The application may diagnose and document OS-level interference, but it must not make privileged persistent network changes.
- Do not raise the minimum macOS version merely to simplify an implementation. Any deployment-target increase requires a separate compatibility decision with usage data.
- Treat signing, notarization, hosted CI, and clean-machine execution as distinct validation gates. A local successful build does not prove any of them.

## 4. Definition of done

The program is complete only when all of these conditions are met:

1. A generated dependency inventory covers every item in section 7, including transitive dynamic libraries, exact versions or commit SHAs, licenses, source URLs, build options, and known patches.
2. Every dependency is either updated to the newest compatible stable release available at execution time or has a written exception with owner, reason, risk, and review date.
3. Clean native arm64 Debug and Release builds pass, and the distributable Release bundle contains only arm64 Mach-O binaries.
4. All packaged Mach-O binaries have the expected slices, deployment target, install names, rpaths, signatures, and no Homebrew or developer-machine paths.
5. Confirmed P0 and P1 macOS issues have regression coverage and are fixed. P2 issues are fixed or explicitly deferred with evidence.
6. The benchmark matrix in section 10 is recorded before and after each performance change. No accepted change regresses median or p95 input latency, frame pacing, dropped frames, audio underruns, CPU, GPU, memory, or energy by more than 5% in its unaffected scenarios.
7. At least one material Apple Silicon improvement is demonstrated in a repeatable benchmark. The initial goal is a 15% improvement in the targeted metric; if hardware or OS constraints prevent that, preserve any smaller statistically significant improvement and document the limit.
8. A 30-minute soak passes at 1080p60, 1440p120, and 4K60 for supported H.264, HEVC, and AV1 combinations. The highest supported refresh/HDR scenarios receive shorter thermal and stability checks if the hardware cannot sustain the full matrix on battery.
9. AddressSanitizer/UndefinedBehaviorSanitizer, static analysis, dependency vulnerability scanning, packaging validation, signing, notarization, Gatekeeper assessment, and update-feed smoke tests pass at the applicable release gate.
10. A canary build is tested by multiple Apple Silicon generations before the stable release, with a documented rollback path to the prior dependency bundle and application build.

## 5. Execution rules for Codex

For every phase, Codex must follow this loop:

1. Synchronize `upstream/master`, verify the worktree, submodule state, and active toolchain, and record the starting commit. Do not overwrite unrelated local changes.
2. Open or update the modernization status document with the phase, linked issues, baseline evidence, planned files, risks, and acceptance checks.
3. Reproduce or measure before editing. A bug report against release 6.1.0 is not proof that current `master` is affected.
4. Make the smallest coherent change, add automated coverage where practical, and retain diagnostic logging needed to validate it.
5. Run targeted checks first, then the full local macOS gates, then hosted cross-platform CI.
6. Compare before/after results on identical hardware, power mode, display mode, network path, server, codec, resolution, refresh rate, and bitrate.
7. Commit one concern at a time. Do not push, open a pull request, sign, notarize, or publish unless the user has authorized that action.
8. Update the status document with exact results and residual risks. Revert the phase if it fails a release gate rather than layering workarounds on an unproven base.

## 6. Work breakdown and order

### Phase 0 - Baseline, ownership, and issue triage

Deliverables:

- `docs/modernization/MAC_SILICON_STATUS.md` as the live checklist and evidence log.
- `docs/modernization/dependencies.json` generated from both repositories.
- `docs/modernization/benchmarks/baseline-<machine>-<date>.json` plus a readable Markdown summary.
- An issue matrix classifying each macOS report as `reproduced on master`, `fixed on master`, `external/OS`, `needs information`, or `not reproduced`.

Tasks:

- Record app commit, submodule SHAs, dependency-bundle tag, dynamic-library versions, Qt/Xcode/SDK versions, deployment target, compiler flags, and CI action pins.
- Build native arm64 Debug and Release apps. Preserve prior universal evidence as historical baseline evidence only.
- Capture startup time, idle resource use, stream resource use, thermal state, memory high-water mark, decoder/render/present timing, audio queue depth, input event-to-send delay, packet loss/jitter, and dropped frames.
- Add a machine-readable benchmark schema before collecting results so later phases cannot cherry-pick metrics.
- Reproduce reported problems using current `master` and a controlled Sunshine host. Keep release 6.1.0 only as a comparison build.

Exit gate: baseline artifacts are reproducible by a second run within normal noise, and every P0/P1 candidate has a clear reproducer or a documented evidence gap.

### Phase 1 - Test and observability foundation

Add the safety net before dependency or performance changes.

Tasks:

- Add a small native test target for pure logic: scaling/HiDPI rectangles, color-range and color-space selection, frame-rate selection, bandwidth calculations, settings migration, address parsing, and mouse-coordinate transforms.
- Add protocol and queue tests in `moonlight-common-c` where the behavior belongs there rather than in the Qt client.
- Add a headless or mockable renderer contract test for frame ownership, replacement, reset, and color-space changes.
- Add deterministic audio queue tests for normal cadence, jitter bursts, device loss, sample-rate change, and backpressure.
- Add input trace capture/replay for absolute mouse, relative mouse, touchpad, 125/500/1000 Hz USB mouse, high-resolution scrolling, and controller axes.
- Preserve the input source in traces: distinguish mouse motion, macOS indirect trackpad contacts, direct touchscreen contacts, and controller touchpads. Record normalized contacts only; do not record user-identifying device serials or raw gesture content outside the bounded test trace.
- Add structured performance counters for decode, queue, render encode, GPU completion, present, input dispatch, audio pending duration, SDL queue duration, and network jitter. Counters must be cheap and disabled or sampled in normal builds.
- Add crash-context metadata: app commit, dependency bundle, architecture, macOS build, machine identifier, active renderer, codec, pixel format, display refresh/scale, audio device, and power/thermal state. Redact host names, user paths, tokens, and addresses by default.
- Add AddressSanitizer and UndefinedBehaviorSanitizer jobs for native arm64 Debug where supported; add Clang static analysis and CodeQL or an equivalent C/C++ scanner.

Exit gate: new tests fail when representative faults are injected and pass on the untouched baseline behavior.

### Phase 2 - Dependency and toolchain modernization

This phase spans both repositories. Update and validate `moonlight-qt-deps` first; only then change the application bundle tag.

#### 2.1 Inventory and policy

- Generate a single ledger containing current pin, candidate pin, release date, ABI/API changes, CVEs, license, patches, upstream tests, Moonlight tests, and rollback pin.
- Classify updates as security, patch, minor, major, or unversioned commit movement.
- Prefer released commits from maintained stable branches. An unreleased dependency commit requires a linked upstream fix and a local regression test.
- Preserve all local dependency patches as separate documented patch files. Rebase each patch independently and delete it if upstream has incorporated the change.
- Generate SPDX or CycloneDX SBOMs and third-party notices for the final app and dependency archive.

#### 2.2 Update groups

Run each group through its own dependency-repository branch and artifact:

1. Media stack: FFmpeg, dav1d, libplacebo, Vulkan-Headers, Vulkan SDK/MoltenVK, and related local patches.
2. Input/window stack: SDL 3, `sdl2-compat`, SDL_ttf, and SDL GameControllerDB.
3. Security/network/audio stack: OpenSSL, Opus, `moonlight-common-c`, ENet, qmdnsengine, and Discord RPC.
4. Application/toolchain stack: Qt, Xcode/macOS SDK compatibility, Apple Clang flags, qmake modules, Python, CMake, Meson, Ninja, NASM, pkg-config, `create-dmg`, and `aqtinstall`.
5. CI supply chain: all GitHub Actions, runner images, Homebrew packages, and installer actions.

For each group:

- Review release notes and migrations between the old and candidate pins.
- Build the arm64 slice with macOS 13 as the deployment target.
- Run the dependency's tests on arm64. Do not keep `tests=false` as the only validation path; production archives can still omit test binaries.
- Run ABI and exported-symbol comparisons, `lipo` checks, `otool` dependency checks, and license diffs.
- Run the Moonlight test and benchmark matrix with only that group changed.
- Save a uniquely versioned, immutable artifact and checksum; never replace an existing tag asset.

#### 2.3 Handoff to the app repository

- Publish the validated dependency bundle as the next immutable tag, expected to be `v13` unless the dependency project chooses another version.
- Record SHA-256 values in the app repository and make `setup-deps.py` verify the selected asset before extraction.
- Harden archive extraction against absolute paths, `..` traversal, symlink escapes, partial downloads, and interrupted replacement.
- Download to a temporary directory, verify, extract, validate contents/architectures, and atomically replace `libs/mac` only after success.
- Update library names in `app/app.pro` only when the ABI major actually changes.
- Keep `v12` selectable for one release cycle through an explicit developer override to make rollback and bisecting fast.

Exit gate: every item in section 7 has an accepted candidate or documented exception; app CI and the benchmark matrix pass against the new immutable bundle.

### Phase 3 - Fix confirmed macOS bugs

Do not fix issues solely because they are open. First reproduce them on the current master build.

#### 3.1 Input latency and high-rate devices

Primary issues: [#1929](https://github.com/moonlight-stream/moonlight-qt/issues/1929), [#1249](https://github.com/moonlight-stream/moonlight-qt/issues/1249), [#1224](https://github.com/moonlight-stream/moonlight-qt/issues/1224), and related cursor/capture reports.

- Instrument AppKit/HID event timestamp, SDL delivery, event coalescing, Moonlight dispatch, protocol send, host receipt if available, decode, render, and present. Separate input latency from host-cursor display latency.
- Verify absolute and relative paths independently for USB mice, Bluetooth mice, and the built-in trackpad.
- Characterize the built-in Mac trackpad separately from mice: record whether SDL exposes indirect absolute/relative contacts, contact IDs, pressure, contact area, and physical dimensions on each supported macOS/SDL combination. Do not depend on private Apple frameworks or infer multi-touch contacts from already-translated mouse events.
- Measure the current SDL event batching. Ensure batching collapses redundant absolute positions while preserving the complete relative delta and button ordering.
- Prototype a native CoreHID/IOHID path behind a runtime feature flag. Review any forthcoming upstream pull request for permissions, sandboxing, accessibility prompts, device hotplug, multiple mice, scroll behavior, and fallback to SDL.
- Re-test AppKit mouse coalescing only as a documented control; upstream issue discussion indicates it did not materially help.
- Keep local cursor rendering as a separate protocol feature. It can improve perceived desktop cursor latency but must not be reported as a reduction in actual remote input latency.
- Add 125/500/1000 Hz replay tests and a stress test ensuring input cannot starve frame presentation or networking.

Acceptance: no event loss or ordering regressions; p95 event-to-send latency and high-rate CPU load improve on the M4 baseline; fallback behavior remains correct on supported arm64 macOS releases.

#### 3.2 Video decode, rendering, frame pacing, and energy

Primary issues: [#753](https://github.com/moonlight-stream/moonlight-qt/issues/753), [#1249](https://github.com/moonlight-stream/moonlight-qt/issues/1249), [#1594](https://github.com/moonlight-stream/moonlight-qt/issues/1594), and stutter reports.

- Break the displayed "decoding latency" metric into VideoToolbox decode, decoded-frame queue, Metal encode, GPU completion, drawable availability, and display-present delay.
- Audit `CAMetalDisplayLink` scheduling, `preferredFrameLatency = 1`, preferred frame-rate range, ProMotion refresh changes, V-Sync off, display migration, sleep/wake, and fullscreen transitions.
- Benchmark the current synchronous `waitUntilCompleted` path. Prototype a bounded asynchronous completion-handler path with one frame in flight; reject it if it increases latency, memory, or stale-frame presentation even when throughput improves.
- Preserve the latest-frame replacement behavior under overload and count replaced frames separately from network drops and decoder failures.
- Precompile/package Metal shader libraries if it measurably improves startup and removes runtime compilation variability without harming deployment compatibility.
- Audit CVPixelBuffer-to-Metal texture caching, buffer allocation, overlay uploads, autorelease pools, storage modes, and per-frame state changes. Reuse immutable buffers and pipelines safely.
- Ensure E-cores are used for low-priority housekeeping while decode/present deadlines are not delayed by background work. Use QoS only after Instruments shows a scheduling problem.
- Profile with Instruments Time Profiler, Metal System Trace, Energy Log, Allocations, and System Trace. Correlate Moonlight counters with OS traces.
- Test thermal and battery behavior with 60/120 fps, SDR/HDR, H.264/HEVC/AV1, V-Sync on/off, overlays on/off, and built-in/external displays.

Acceptance: stable frame pacing with no additional queued frame, no leak across repeated sessions, no thermal-state regression, and a repeatable improvement in the targeted latency, CPU, GPU, or energy metric.

#### 3.3 Audio stability and device handling

Primary issue: [#1781](https://github.com/moonlight-stream/moonlight-qt/issues/1781) and related open audio-queue work.

- Instrument incoming audio cadence, `LiGetPendingAudioDuration()`, SDL queued duration, underruns, drops caused by the 30 ms pending limit, 50 ms SDL backpressure, and device status changes.
- Reproduce V-Sync-linked crackle on built-in speakers, HDMI/USB, AirPods/Bluetooth, and virtual devices at 44.1/48 kHz and stereo/5.1/7.1.
- Replace magic queue limits with a tested policy. If a user setting is retained, define safe bounds and keep an automatic low-latency default.
- Detect default-device changes, removal, sample-rate changes, Bluetooth profile switches, sleep/wake, and reconnect without leaking or deadlocking.
- Evaluate a native CoreAudio renderer separately from spatial-audio features. First prove lower underruns and equal or better latency/power in plain stereo and multichannel passthrough.
- Treat spatial audio as an optional feature phase only after the base renderer is production-ready and privacy/entitlement behavior is understood.

Acceptance: zero audible underruns in the controlled 30-minute test, bounded latency after jitter bursts, correct recovery on device changes, and no A/V sync regression.

#### 3.4 Network stability and diagnostics

Primary issues: [#1427](https://github.com/moonlight-stream/moonlight-qt/issues/1427), [#1825](https://github.com/moonlight-stream/moonlight-qt/issues/1825), and [#1953](https://github.com/moonlight-stream/moonlight-qt/issues/1953).

- Reproduce high-bitrate freezes using a controlled packet generator and at 10, 30, 50, 100, 150, and 250 Mbps. Compare Wi-Fi 5/6/6E and Ethernet while holding codec and render settings constant.
- Instrument receive-buffer saturation, packet reordering, loss bursts, FEC recovery, retransmission, socket errors, and event-loop stalls.
- Verify current `moonlight-common-c` and ENet changes before altering Qt networking. Host discovery/control and stream transport must be analyzed separately.
- Detect likely AWDL/channel interference and provide a clear diagnostic with links to troubleshooting. Do not disable AWDL or change Wi-Fi channels from the app.
- Treat macOS 27 beta failures as a compatibility watch item. Issue #1953 is currently labeled external; only add a client workaround if current Qt reproduces the failure and the workaround is supported by Apple/Qt.
- Test local-network privacy permission, Bonjour discovery, manual IPv4/IPv6 addresses, VPNs, interface changes, sleep/wake, and network handoff.

Acceptance: no Moonlight-specific throughput cliff in the controlled test, actionable diagnostics for OS/network interference, and graceful reconnect or error reporting for interface changes.

#### 3.5 HiDPI, color, HDR, and displays

Primary issues: [#1185](https://github.com/moonlight-stream/moonlight-qt/issues/1185), [#1213](https://github.com/moonlight-stream/moonlight-qt/issues/1213), and HDR/display reports.

- Define logical points, drawable pixels, stream pixels, safe-area pixels, and backing scale explicitly at every Qt, SDL, Metal, and input boundary.
- Add tests for 1x, 2x, and fractional Retina scaling; native/notch-excluded modes; windowed/borderless/fullscreen; internal/external displays; and live display migration.
- Inspect texture sampling and destination rectangles for unnecessary resampling at fractional scaling. Provide a pixel-perfect path when stream and drawable dimensions match.
- Validate Rec. 601/709/2020, limited/full range, 8/10-bit formats, chroma siting, PQ, EDR metadata, SDR-on-HDR, HDR-on-SDR, and wide-gamut displays with objective color bars and reference captures.
- Recreate Metal pipelines only when the format requires it; verify colorspace and EDR lifetime during stream changes.
- Add display capability discovery and a recommended mode that accounts for native pixels, notch-safe area, refresh range, HDR, and bandwidth. Never change the host/display automatically without confirmation.

Acceptance: pixel-reference tests pass for supported transforms, no double scaling, color errors stay within the selected objective tolerance, and HDR transitions do not black-screen or leak stale metadata.

#### 3.6 Controllers and lifecycle

- Verify that the wired XInput axis fix reported in [#1429](https://github.com/moonlight-stream/moonlight-qt/issues/1429) is present and passes on current master, then add a regression mapping test and close/annotate the issue rather than reimplementing it.
- Test Xbox, DualSense, Switch Pro, and common third-party controllers over USB and Bluetooth; include hotplug, battery, motion, touchpad, rumble, adaptive triggers, and multiple-controller ordering.
- Test launch/quit, Cmd+Q, minimize, Spaces, focus/capture, fullscreen transitions, monitor unplug, sleep/wake, and repeated stream cycles.
- Update SDL GameControllerDB independently so a mapping-data update can be rolled back without changing SDL itself.

Exit gate for Phase 3: all reproduced P0/P1 problems have automated or scripted regression coverage and pass the full validation matrix.

### Phase 4 - Feature optimization

Only start this phase after the core bug and performance gates pass.

Priority order:

1. Automatic display recommendations: propose resolution, refresh, HDR, codec, and bitrate using measured client/server capabilities; require confirmation before applying.
2. Low-latency cursor mode: coordinate protocol work with Sunshine and `moonlight-common-c` to send cursor image/hotspot/visibility and render it locally. Keep a host-cursor fallback.
3. Native macOS input option: graduate the CoreHID prototype only if it is measurably better and permission/fallback behavior is production-safe.
4. Native Mac trackpad passthrough: add an opt-in, feature-negotiated path that preserves multi-contact trackpad semantics to a compatible host. Keep the current mouse path as the default and fallback.
5. Native CoreAudio renderer: ship passthrough and recovery first; add spatial audio as an opt-in follow-up.
6. Per-display and per-host profiles: let users preserve tested settings without globally changing defaults.
7. Video super resolution: evaluate open upstream work, but accept it on Apple Silicon only when quality is objectively better and its added latency, GPU time, energy, and thermal load meet explicit budgets. Default it off initially.
8. Adaptive bitrate: evaluate current upstream work using controlled loss/jitter tests and ensure it cannot oscillate, hide local client bottlenecks, or exceed the user's cap.

#### 4.1 Native Mac trackpad passthrough

This is a coordinated client/protocol/host feature, not a relabeling of existing mouse input. Moonlight currently routes non-direct SDL touch devices through the mouse path, generic native touch packets represent a screen-mapped touchscreen, and controller-touchpad packets represent a game controller. Preserve those distinct meanings.

Host-fork implementation reference: [`docs/modernization/VIBEPOLLO_TRACKPAD_FORK_REFERENCE.md`](docs/modernization/VIBEPOLLO_TRACKPAD_FORK_REFERENCE.md).

Moonlight and `moonlight-common-c` tasks:

- Add a macOS capability probe for indirect trackpad contacts. Prefer supported SDL APIs when they provide stable contact IDs and required metadata; use a public CoreHID/IOHID path only if SDL is insufficient. Do not use Apple's private `MultitouchSupport.framework`.
- Capture bounded per-contact down, move, up, and cancel events with stable IDs, normalized device-relative coordinates, pressure/contact area when available, and the trackpad's physical width and height. Explicitly cancel all active contacts on focus loss, stream termination, device removal, sleep, or input-mode changes.
- Extend `moonlight-common-c` with versioned trackpad packets and a separate host feature flag. Do not overload `LiSendTouchEvent()` or `LiSendControllerTouchEvent*()` in a way that causes legacy hosts to interpret a trackpad as a touchscreen or game controller.
- Negotiate the feature before suppressing mouse translation. Unsupported or rejected negotiation must retain today's mouse movement, click, secondary-click, and high-resolution scrolling behavior without reconnecting.
- Add a per-host opt-in setting and an emergency runtime kill switch. Prevent duplicate delivery when macOS/SDL emits both translated mouse events and raw contacts for the same gesture.
- Keep local macOS gestures that Moonlight or the OS owns, including stream shortcuts and capture release, deterministic and documented. Define whether each gesture is handled locally, forwarded as contacts, or translated to legacy mouse input.

Companion host contract:

- Coordinate a bounded Vibepollo/Sunshine host change that advertises the new capability and preserves device-relative contacts rather than screen-mapping them.
- On supported Windows 11 builds, dynamically probe the documented `CreateSyntheticPointerDevice2` API and create `PT_TOUCHPAD` with a physical size and at most five simultaneous contacts. Treat Microsoft's current prerelease API status as a release risk until the API and SDK contract are stable: [CreateSyntheticPointerDevice2](https://learn.microsoft.com/en-us/windows/win32/input-precisiontouchpad/createsyntheticpointerdevice2).
- Do not silently fall back to `PT_TOUCH`, which would expose a touchscreen rather than a Precision Touchpad. Fall back to Moonlight's legacy mouse path instead.
- Treat Windows 10 native Precision Touchpad emulation as unsupported unless a separately reviewed, signed virtual-HID solution exists. A new kernel driver, driver distribution, or signing workflow is outside this Moonlight client feature and requires its own security and release plan.

Acceptance:

- A compatible Windows 11 Vibepollo/Sunshine host identifies the stream input as a touchpad and receives one through five ordered contacts without stuck fingers, duplicate clicks, pointer jumps, or gesture leakage after focus/session changes.
- Windows pointer movement, physical click, tap-to-click, secondary click, two-finger scroll, pinch, and supported three-/four-finger gestures match a local Precision Touchpad closely enough to pass a documented gesture matrix. Record expected OS-reserved differences.
- Unsupported Vibepollo/Sunshine versions, upstream Sunshine without the feature, Windows 10, external mice, and accessibility-denied/native-capture failure cases retain the existing mouse behavior.
- The feature adds no measurable input-event loss, does not regress mouse/controller/touchscreen handling, and stays within the plan's 5% unaffected-scenario CPU, energy, and latency budget.

Each feature needs telemetry that can be viewed locally, a kill switch, settings migration tests, accessibility review, localization updates, and independent rollback.

### Phase 5 - CI, packaging, security, and release engineering

Tasks:

- Use a native arm64 build/test job and an arm64-only packaging job. Reject a macOS artifact containing any non-arm64 Mach-O slice.
- Make the arm64 job run tests, sanitizers, static analysis, and a short no-display or virtual-display smoke test.
- Pin GitHub Actions by full commit SHA with a readable version comment; enable Dependabot or Renovate for actions, submodules, and any new manifest formats.
- Cache only immutable inputs. Include dependency tag and checksum in cache keys.
- Produce reproducible build metadata, checksums, SBOM, third-party notices, dSYM, build UUIDs, and symbol-to-build mapping.
- Validate the app before DMG creation and again after extraction from the DMG.
- Recursively inspect every Mach-O file with `lipo`, `file`, `otool`, and `vtool`; reject unexpected architectures, absolute build paths, missing rpaths, ad-hoc nested signatures in a signed build, or deployment-target drift.
- Sign inside-out with hardened runtime and explicit entitlements; avoid relying on `codesign --deep` as the signing strategy.
- Notarize, staple, verify the ticket, run `codesign --verify --strict`, assess with Gatekeeper, and launch from a clean user account or clean VM.
- Test Sparkle or the active updater path, downgrade prevention, interrupted downloads, signature failures, and migration from the previous stable release.
- Run secret scanning, dependency vulnerability scanning, binary malware scanning, and source/license provenance checks.

Exit gate: the final DMG passes clean-machine install, launch, stream, quit, update, signature, notarization, architecture, and dependency-path verification.

### Phase 6 - Canary and stable release

- Publish an internal or opt-in canary with symbols and a privacy-safe diagnostic bundle.
- Test at minimum one first-generation Apple Silicon machine, the local M4, and another generation if available; cover both a MacBook and a desktop when possible.
- Cover multiple Apple Silicon generations; Intel Mac execution is no longer a release gate.
- Run 30-minute sessions for the core matrix and a longer 4-hour soak for the most demanding stable configuration.
- Compare crash-free sessions, disconnects, input p95, frame-time variance, audio underruns, energy impact, and memory against the recorded baseline.
- Freeze dependencies during the canary unless a blocking security fix is required.
- Publish release notes separating dependency/security changes, bug fixes, measurable performance improvements, feature changes, known limitations, and minimum OS requirements.
- Retain the prior app and `v12` dependency bundle for rollback. Document the exact commit/tag pair for both the new and rollback builds.

## 7. Complete dependency ledger to audit

Codex must account for every row. "Current" means the pin visible on 2026-08-14; candidate versions must be refreshed when execution begins.

| Area | Current source/pin | Required action |
|---|---|---|
| Qt | 6.11.1 in macOS/Windows CI | Review all newer compatible patch releases, Qt Quick changes, macdeployqt behavior, deployment target, and known macOS fixes. |
| FFmpeg | `moonlight-qt-deps` commit `d32b387f...`, branch `release/8.1` | Review VideoToolbox/Metal/AV1 changes and rebase the local Metal/VT patch. |
| OpenSSL | commit `aae016bf...`, branch `openssl-3.6` | Update for security fixes, run arm64 tests, and verify disabled-feature assumptions. |
| SDL | commit `147a8ee3...`, branch `release-3.4.x` | Review macOS HID, event loop, audio, Metal, controller, fullscreen, and power changes. |
| sdl2-compat | commit `a53b6ad9...` | Verify every Moonlight SDL2 API used on macOS and compare behavior with native SDL3 where useful. |
| SDL_ttf | commit `a883e490...`, SDL2 branch | Update with the compatibility layer and test overlay/text rendering. |
| SDL GameControllerDB | app submodule commit `8d9fefd7...` | Update independently and run mapping regression tests. |
| dav1d | commit `54706fc6...` | Update and validate arm64 optimized paths plus software-decode fallback. |
| libplacebo | commit `4d82c689...` | Rebase local patches, run tests, and measure Vulkan/MoltenVK fallback behavior. |
| Vulkan-Headers | commit `2cd90f9d...` | Keep aligned with the selected Vulkan SDK and MoltenVK. |
| Vulkan SDK/MoltenVK | 1.4.350.0 in dependency CI | Update as a matched set and validate arm64-only archive contents. |
| Opus | commit `ddbe4838...` | Run codec tests/benchmarks for arm64 and audio latency/quality integration tests. |
| moonlight-common-c | app submodule commit `e41355ea...` | Update protocol/network code with its nested ENet and nanors dependencies; run protocol tests. |
| ENet | nested commit `aca87840...` | Audit Apple socket handling, high-bitrate behavior, IPv6, loss, and reconnect paths. |
| nanors | nested commit `b1e3c22c...` | Review pin, maintenance state, license, and parser compatibility. |
| qmdnsengine | app submodule commit `b7a5a9f2...` | Update and test Bonjour/mDNS, IPv4/IPv6, local-network privacy, and interface changes. |
| Discord RPC fork | commit `7bcf3b3f...` | Review maintenance/security; remove from macOS if unused or replace only through a separate compatibility decision. |
| Metal/VideoToolbox/CoreVideo/AVFoundation/CoreMedia/CoreGraphics/AppKit/QuartzCore | macOS SDK frameworks | Audit API availability guards, deprecations, ownership, threading, and deployment-target annotations. |
| `create-dmg` | installed unpinned through npm | Pin exact package/version/integrity or replace with a deterministic packaging process. |
| `aqtinstall` | source repository pinned by commit | Review the pin and validate installer integrity/caching. |
| CMake/Meson/Ninja/NASM/pkg-config/Python/Homebrew packages | runner-provided or unpinned | Record exact versions, constrain supported ranges, and make build failures actionable. |
| GitHub Actions | mixed version tags such as checkout/upload/download/install-qt | Update, pin immutable SHAs, minimize permissions, and review changelogs. |
| Compiler/SDK/runner | Apple Clang/Xcode/macOS runner | Maintain a current job plus the minimum supported SDK/deployment-target validation. |
| Bundled font, icons, shaders, translations, mappings | repository resources | Verify license, integrity, build inclusion, scaling, and stale/generated artifacts. |

Windows-only components such as Detours and AntiHooking remain in the global "all libraries" audit even though Apple Silicon performance work does not modify them. Their build must remain green.

## 8. Initial issue disposition

This is a starting triage list, not a declaration that each item is still reproducible:

| Issue | Initial disposition on 2026-08-14 |
|---|---|
| [#1929 macOS mouse latency](https://github.com/moonlight-stream/moonlight-qt/issues/1929) | High-priority current candidate. Instrument SDL/AppKit/HID and evaluate the reported CoreHID approach. |
| [#1249 M-series decode latency tied to mouse movement](https://github.com/moonlight-stream/moonlight-qt/issues/1249) | High-priority measurement problem. Split decode, render, GPU, and present timing before changing code. |
| [#1594 Apple Silicon battery drain](https://github.com/moonlight-stream/moonlight-qt/issues/1594) | High-priority power benchmark at HDR/120 fps; correlate with frame scheduling and GPU waits. |
| [#1781 V-Sync audio crackle](https://github.com/moonlight-stream/moonlight-qt/issues/1781) | High-priority audio queue/device investigation; compare the open queue-threshold proposal with an automatic policy. |
| [#1825 high-bitrate macOS freezes](https://github.com/moonlight-stream/moonlight-qt/issues/1825) | Reproduce on current master with controlled traffic; separate transport, event-loop, and render backpressure. |
| [#1427 Sequoia Wi-Fi jitter](https://github.com/moonlight-stream/moonlight-qt/issues/1427) and [#753 M1 stutter](https://github.com/moonlight-stream/moonlight-qt/issues/753) | Evidence strongly implicates AWDL/channel interaction for some users. Add diagnostics and documentation, then isolate any client-side contribution. |
| [#1185 fractional HiDPI blur](https://github.com/moonlight-stream/moonlight-qt/issues/1185) | Reproduce with fractional backing scale and add pixel-reference tests. |
| [#1213 macOS wide-gamut color](https://github.com/moonlight-stream/moonlight-qt/issues/1213) | Build an objective color-management test before changing layer colorspaces. |
| [#1429 wired XInput Y axis](https://github.com/moonlight-stream/moonlight-qt/issues/1429) | Reported fixed in current nightly/master by commit `179857f1`; verify, add regression coverage, and update the issue. |
| [#1953 macOS 27 beta network error](https://github.com/moonlight-stream/moonlight-qt/issues/1953) | Currently labeled external. Track Qt/Apple resolution and avoid an unsupported workaround unless current dependencies reproduce it. |

Codex should query the current issue and pull-request state again when each phase starts because labels, fixes, and upstream branches can change.

## 9. Pull-request sequence

Recommended review units:

1. Baseline schema, benchmark runner, and modernization status document.
2. Pure-logic unit-test target and macOS instrumentation.
3. CI sanitizers/static analysis and native arm64 test job.
4. Dependency inventory, SBOM, download integrity, and safe extraction.
5. Media dependency bundle update.
6. SDL/input/audio dependency bundle update.
7. Crypto/protocol/network dependency update.
8. Qt/toolchain/CI action update.
9. Confirmed input fixes.
10. Trackpad capability probe, trace fixtures, and `moonlight-common-c` protocol extension, disabled by default until a compatible host exists.
11. Native Mac trackpad UI/input integration after the protocol contract and host implementation are independently reviewed.
12. Confirmed Metal/VideoToolbox/frame-pacing fixes.
13. Confirmed audio fixes.
14. Confirmed networking/diagnostic fixes.
15. HiDPI/color/HDR fixes.
16. Other feature changes, one feature per pull request.
17. Packaging, signing, notarization, and release-hardening changes.

Each pull request must state its dependency bundle, baseline commit, hardware/OS, test matrix, before/after results, known limitations, and rollback method.

## 10. Validation matrix

### Hardware and architecture

- Apple M1 or M1 Pro, local M4, and one additional M-series generation when available.
- Built-in Retina display and an external 4K/HDR display.
- Native arm64 execution on each available Apple Silicon generation.

### Stream scenarios

- 1080p60, 1440p120, 4K60, and supported 4K120.
- H.264 8-bit, HEVC 8/10-bit, AV1 8/10-bit.
- SDR, HDR10/EDR, full and limited range, 4:2:0 and supported 4:4:4.
- V-Sync on/off, frame pacing on/off, windowed/borderless/fullscreen.
- 10/30/50/100/150/250 Mbps, clean Ethernet, clean Wi-Fi, injected jitter/loss/reordering, and reconnect.
- Mouse 125/500/1000 Hz; built-in Mac trackpad in legacy-mouse and native-passthrough modes; keyboard shortcuts; controllers; direct touch; and high-resolution scroll.
- For native trackpad passthrough: compatible Windows 11 Vibepollo/Sunshine host, unsupported host fallback, Windows 10 fallback, one through five contacts, focus loss, capture release, disconnect/reconnect, sleep/wake, and an external mouse used concurrently.
- Built-in speaker, USB/HDMI, Bluetooth, stereo, 5.1, and 7.1 where hardware supports them.

### Measurements

- Startup-to-ready time and stream-start time.
- Decode median/p95/p99, render CPU time, GPU completion time, present delay, frame-time variance, drawable starvation, and replaced/dropped frames.
- Input event-to-send median/p95/p99 and host-visible response where synchronized measurement is possible.
- Audio pending/queued duration, underruns, overflows, dropped samples, A/V drift, and device-recovery time.
- Network throughput, packet loss, recovered loss, jitter, retransmissions, socket errors, and reconnect time.
- CPU by thread/QoS, GPU utilization/time, resident and peak memory, allocations per frame, wakeups, energy impact, battery discharge, and thermal state.
- Color difference for reference patches, pixel-scale correctness, and HDR metadata/state transitions.

### Required test durations

- Five-minute quick check for every local edit.
- Thirty-minute gate for each dependency group and bug-fix pull request.
- Four-hour soak for release candidates in the most demanding stable scenario.
- Twenty launch/stream/quit cycles plus sleep/wake, display unplug, audio-device change, and network handoff loops.

## 11. Rollback and stop conditions

Stop and revert the active change if any of these occurs:

- A dependency update cannot be tied to an immutable source commit or verified archive.
- An arm64 slice is missing, any packaged Mach-O contains another architecture, or a binary links to a developer-machine path.
- A shared change breaks another supported platform and cannot be isolated cleanly.
- Input loss/order, stale-frame presentation, A/V drift, color correctness, crash rate, or energy regresses beyond the agreed tolerance.
- Native trackpad mode produces duplicate mouse/touchpad input, stuck contacts, unbounded gesture state, or suppresses legacy mouse fallback after capability negotiation fails.
- Signing/notarization requires broader entitlements than the reviewed feature needs.
- Benchmark results are not reproducible or mix multiple uncontrolled variables.

Rollback order:

1. Disable the affected runtime feature flag.
2. Revert the application change while retaining added diagnostics/tests.
3. Point the app back to the `v12` dependency bundle and its checksum.
4. Re-release the previous signed/notarized artifact if a canary escaped.
5. File a focused upstream dependency issue with the minimal reproducer and captured evidence.

## 12. First Codex milestone

The first executable milestone is Phase 0 plus the smallest part of Phase 1:

1. Create the modernization status document and dependency-inventory generator.
2. Download `v12` with integrity recorded, build native arm64 Debug/Release, and validate the bundle structure without publishing it. The completed universal build remains historical evidence from before the 2026-08-17 support decision.
3. Add only the non-invasive timing counters required to separate decode, render, GPU completion, present, input dispatch, and audio queue latency.
4. Capture repeatable M4 baselines for 1080p60, 1440p120, and 4K60 on Ethernet using a fixed Sunshine host and fixed test content.
5. Triage the ten issues in section 8 on current master and propose the first single-problem implementation branch.

Do not begin library updates or performance tuning until this milestone is reviewed. It establishes the evidence needed to tell a genuine improvement from a shifted bottleneck.
