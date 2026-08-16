# Phase 2 media candidate ledger

Review date: 2026-08-16  
Owner: local execution by Codex; maintainer review unassigned  
Dependency branch: `phase2-media-v13-candidate` in `/Users/justin/Development/moonlight-qt-deps`  
Decision: **accepted locally for pin movement; not published**  
Acceptance: user accepted the matched-test caveats and conditional security result on 2026-08-16  
Rollback: published dependency bundle `v12` at companion commit `22355399c660661d06f211845efe7ccfc5ba0484`

The branch, archive, and application builds are local and uncommitted. No tag, release asset, or installer metadata was published or changed.

## Candidate inventory

| Component | Current | Candidate | Release date | Class | API / ABI and license | CVE and patch disposition |
|---|---|---|---|---|---|---|
| FFmpeg | `d32b387f2b0a484599d4587d651891f0c63c4238` (9.0) | `bf1b838f2ab88b4f8fd83443325c782ea0e0f7fa` (9.0.1) | 2026-08-03 / 2026-08-12 commit dates | Patch | Shipped ABI names remain `libavcodec.63`, `libavutil.61`, and `libswscale.10`; LGPL-2.1-or-later build remains unchanged. | Conditional security pass: reviewed fix content is present and no known reachable advisory was identified. The official ledger lacks a 9.0 mapping, so no complete per-release assertion is claimed. `ffmpeg_metal_vt.patch` applies cleanly; no upstream reference is recorded. |
| dav1d | `54706fc6bc0cdecab7e9593974a4039cc038fca7` (1.5.4) | unchanged | 2026-07-14 | No move | No API/ABI or BSD-2-Clause license change. It remains statically incorporated into FFmpeg. | Conditional security pass: the two NVD records returned affect versions before 1.2.0 and through 1.4.0; 1.5.4 is later. No candidate delta. |
| libplacebo | `4d82c6898551068d4ae6a6b5538efcddc2c7cf64` (7.371.0) | unchanged | 2026-07-30 | Retained unversioned commit | ABI remains `libplacebo.371`; LGPL-2.1-or-later unchanged. This pin is newer than the available 7.360.1 stable tag and is retained as an explicit unversioned exception. | Conditional security pass with monitoring: no NVD record surfaced, but this is not proof of absence. `libplacebo_inherit_alpha.patch` and the Windows-only `libplacebo_shaderc_win.patch` apply cleanly; neither has a recorded upstream reference. |
| Vulkan-Headers | `2cd90f9d20df57eac214c148f3aed885372ddcfe` (1.4.321) | `e3b1eec08173d6b825cd3ac88c885a63b621504a` (1.4.357) | 2025-07-04 / 2026-07-17 commit dates | Minor API header update | Header-only API update; no dylib ABI. Apache-2.0 unchanged. | Conditional security pass: exact-name NVD and public GitHub advisory queries returned zero records. No local patch. |
| Vulkan SDK / MoltenVK | 1.4.350.0 | 1.4.357.0 | 2026-05-12 / 2026-07-29 | Patch SDK update | `libMoltenVK.dylib` retains `@rpath/libMoltenVK.dylib`, both macOS slices, and minimum macOS 11. The downloaded SDK was signed and notarized by LunarG. | Conditional security pass with monitoring: exact-name NVD and public GitHub advisory queries returned zero records, which is not proof of absence. The SDK archive SHA-256 is `539433589c83522e6f31b1c7b418a4167e21597a4a361ab119e1dc0760cf3865`. |

## Dependency validation

The detailed source/build advisory correlation is recorded in `MEDIA_SECURITY_REVIEW.md`. It found no known reachable advisory in the reviewed records and is a conditional security pass, not a vulnerability-free assertion.

- dav1d 1.5.4: arm64 Meson suite 7/7 passed; x86_64 suite 7/7 passed under Rosetta, including all 2,881 checkasm cases.
- libplacebo 7.371.0: arm64 Meson suite 12/12 passed; x86_64 suite 12/12 passed under Rosetta.
- FFmpeg 9.0.1: arm64 and x86_64 shared builds passed with VideoToolbox, Vulkan, and local dav1d enabled. The configured FATE/checkasm target passed for both slices. Sample-dependent FATE coverage was not run because no `SAMPLES` corpus was supplied.
- The FFmpeg FATE harness now mirrors the packaged `Frameworks` layout while tests run, then removes that temporary layout during source cleanup.
- The x86_64 linker emits warnings for NASM objects without explicit platform load commands, and current Apple ld reports FFmpeg's `-single_module` option as obsolete. These are retained as open toolchain warnings.

## Review artifact

- Local archive: `/Users/justin/Development/moonlight-qt-deps/moonlight-media-v13-candidate-macos-universal.zip`
- Size: 16,696,236 bytes
- SHA-256: `5dc5d2a7587b57b312ce893744ce540312a811d94d2f40d4449a14f106776ae2`
- Contents: candidate FFmpeg, libplacebo, Vulkan headers, and MoltenVK only; unrelated v12 components are intentionally excluded.
- ZIP CRC validation passed. All five dylibs contain `x86_64` and `arm64`, and none has a Homebrew, `/usr/local`, or user-directory load path.
- FFmpeg and libplacebo slices target macOS 13.0; the official MoltenVK binary targets macOS 11.0.

## Moonlight validation and open gates

- Current Phase 1 source built and linked against the exact candidate archive as native arm64 Release and official-Qt universal Release.
- The universal application contains `x86_64` and `arm64` slices with minimum macOS 13.0. `Moonlight --version` returned 6.1.0 under native arm64 and Rosetta x86_64 execution.
- Native QtTest remained 13 passed, 0 failed. Installer tests remained 5 passed.
- The original `libs/mac` v12 directory was restored after each isolated candidate build.
- Matched v12/candidate streaming completed under `benchmarks/matched-media-2026-08-16`. The A/B app bundles had a byte-identical executable and differed only in the five reviewed media dylibs. Both used Sunshine, Vulkan (libplacebo), 2560x1600 at 60 Hz, 10-minute timed runs, and AC power.
- Candidate versus v12 mean CPU was -0.39% and mean RSS was -10.3%. Mean decode, Vulkan render-encode, and presentation-wait timings were -1.9%, -4.2%, and -6.7%; both runs recorded zero replaced frames, no thermal/performance warning, and no operator-observed visual/audio/input issue.
- Candidate audio-pending mean was +29.8% with a lower maximum, and SDL queue mean was +5.9% with the same 55 ms maximum. Network and input samples were sparse. Candidate decoded-frame sample count was 6.9% lower, so the comparison does not prove identical delivered-frame cadence.
- The macOS `top` POWER field stayed at zero and cannot support an energy conclusion. The user accepted the candidate with the documented comparison and security caveats. Sustained-session and privileged energy measurements remain explicitly deferred and are not represented as passed.
