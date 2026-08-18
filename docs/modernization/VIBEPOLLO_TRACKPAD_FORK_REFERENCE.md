# Vibepollo fork reference: native Mac trackpad passthrough

Status: design and implementation handoff; no Vibepollo fork or protocol IDs have been published  
Prepared: 2026-08-17  
Target host: Windows 11 Vibepollo  
Target client: Moonlight Qt on arm64 macOS  
Protocol library: `moonlight-common-c`

## Purpose

Use this file when creating a bounded fork of Vibepollo for native Mac trackpad passthrough. The feature must preserve device-relative, multi-contact trackpad semantics from Moonlight to Windows rather than converting the trackpad into a screen-mapped touchscreen or a controller touch surface.

The host implementation is only one part of a three-repository contract:

1. Moonlight Qt captures supported macOS indirect-trackpad contacts and retains legacy mouse translation until negotiation succeeds.
2. `moonlight-common-c` owns a versioned trackpad capability and wire format that is distinct from touchscreen and controller-touch packets.
3. The Vibepollo fork validates those packets, maintains per-session contact state, and injects a Windows `PT_TOUCHPAD` device.

## Fork baseline

- Upstream repository: <https://github.com/Nonary/Vibepollo>
- Observed default branch: `master`
- Reconnaissance commit: `b85bd588431030c998f3b0e6968317554d046252`
- Suggested fork branch: `feature/native-trackpad-passthrough-v1`
- Recheck the upstream head and the Microsoft API contract before implementation; both are active and may change.

Keep the first host pull request restricted to packet handling, Windows injection, tests, logging, and an opt-in configuration switch. Do not combine it with display, capture, encoder, web-UI redesign, or unrelated input work.

## Current Vibepollo integration points

These paths and responsibilities were confirmed at the reconnaissance commit:

| Path | Existing responsibility | Trackpad work |
|---|---|---|
| `src/platform/common.h` | Platform capability bits and cross-platform input types | Reserve a distinct trackpad capability and add a device-relative trackpad frame type. Do not reuse `pen_touch` or `controller_touch`. |
| `src/platform/windows/input.cpp` | Dynamically loads synthetic pointer APIs; owns per-client pen/touch state; injects `PT_TOUCH` and `PT_PEN`; advertises Windows input capabilities | Add the dynamic `CreateSyntheticPointerDevice2` probe, per-client `PT_TOUCHPAD` handle/state, frame injection, cancellation, and capability gating. |
| `src/input.cpp` | Packet size validation, logging, batching, dispatch, and conversion to platform input types | Recognize the new packet magic only after it is assigned with `moonlight-common-c`; strictly validate version, sizes, counts, ranges, transitions, and sequence. |
| `src/input_validation_policy.cpp` | Independent input packet size policy | Add the same bounded trackpad packet rules and tests so the two validators cannot drift. |
| `src/rtsp.cpp` | Advertises `a=x-ss-general.featureFlags` using `platf::get_capabilities()` | Advertise trackpad support only when the runtime and configuration gates pass. |
| `src/config.h`, `src/config.cpp`, `docs/configuration.md` | Defines, parses, exposes, and documents input settings such as `native_pen_touch` | Add an off-by-default `native_trackpad` switch for the experimental fork. |
| `tests/unit/test_input.cpp` | Exercises input packet validation | Add malformed, truncated, oversized, unsupported-version, contact-count, and transition cases. |
| `tests/unit/test_rtsp_startup_snapshot.cpp` | Covers RTSP startup behavior | Verify capability advertisement is present only when the trackpad backend is available and enabled. |

Useful discovery command after rebasing the fork:

```sh
git grep -n -E 'SS_TOUCH_MAGIC|SS_CONTROLLER_TOUCH_MAGIC|packet_size_bounds|get_capabilities|CreateSyntheticPointerDevice|InjectSyntheticPointerInput|native_pen_touch' -- src tests docs
```

## Capability and fallback contract

Allocate the final capability value and packet magic in the same reviewed protocol change in `moonlight-common-c` and Vibepollo. This reference intentionally does not guess numeric values.

The host capability must be separate from the existing pen/touch and controller-touch bits. Vibepollo advertises it only when all of these conditions are true:

- the host is a supported Windows 11 build;
- `CreateSyntheticPointerDevice2`, `InjectSyntheticPointerInput`, and `DestroySyntheticPointerDevice` are available from `User32.dll`;
- the fork's experimental `native_trackpad` setting is enabled.

Capability advertisement means the host is prepared to attempt device creation, not that creation has already succeeded. The protocol therefore needs a versioned activation acknowledgement on the encrypted control channel after the device description is processed. If `PT_TOUCHPAD` creation fails, the host returns a bounded failure result, clears trackpad state, and rejects trackpad frames for that activation generation.

The client must not suppress translated mouse motion, click, secondary-click, or high-resolution scrolling merely because the user enabled the preference. It switches to raw trackpad packets only after both the negotiated host flag and a successful activation acknowledgement are present. A rejection or acknowledgement timeout leaves the legacy mouse path active. If later validation or injection fails, cancel host-side contacts and signal deactivation so the client can restore legacy mouse input without reconnecting.

Never fall back from `PT_TOUCHPAD` to `PT_TOUCH`. A touchscreen has screen-mapped semantics and is not an acceptable substitute. Windows 10 also falls back to the legacy Moonlight mouse path; a virtual-HID or kernel-driver solution is outside this fork.

## Proposed version 1 wire contract

Finalize this contract in `moonlight-common-c` before implementing host-specific parsing. Prefer one bounded frame packet over independent contact packets because Windows injection consumes the current contact frame as a contiguous array.

### Device description packet

Send reliably before the first frame and whenever the source device changes:

| Field | Requirement |
|---|---|
| Protocol version | Exactly `1` for this design. Unknown versions are rejected without changing input mode. |
| Device generation | Monotonically changes when the client replaces or reconfigures the source trackpad. |
| Maximum contacts | `1..5`; the client may report less than five. |
| Width and height | Nonzero unsigned HIMETRIC dimensions, where one unit is 0.01 mm. Apply reviewed upper bounds before allocation or multiplication. |
| Options | Versioned bit field. Version 1 should default to physical touchpad behavior; do not enable gesture-only behavior unless it becomes a separate negotiated option. |

The host destroys the previous device, cancels its contacts, clears IDs and sequence state, then creates the replacement device. It must not carry contacts across device generations.

### Activation result

After processing a device description, the host returns a small versioned result containing the device generation, success/failure status, and a stable non-sensitive reason code. Do not send raw Win32 error strings or local paths over the protocol. The host accepts contact frames only after returning success; the client continues legacy mouse delivery until it receives that success.

### Contact-frame packet

Each frame contains a sequence number, device generation, frame flags, and zero to five contact records. Every normal frame includes the full current active-contact set plus any edge records required to deliver an up or cancel transition. A dedicated cancel-all flag is valid with zero contacts.

Each contact record needs:

- a session-scoped stable pointer ID;
- an explicit down, move, up, or cancel state;
- normalized device-relative X and Y in the closed range `0..1`;
- optional normalized pressure and contact-area major/minor values with explicit unknown sentinels;
- reserved bytes initialized to zero for forward compatibility.

Rules:

- Reject duplicate pointer IDs, more than five contacts, non-finite floats, out-of-range values, stale device generations, decreasing sequences, and illegal state transitions.
- Down, up, cancel, cancel-all, and device-description packets are reliable and ordered.
- Move-only frames may be coalesced or sent unreliably only if each transmitted packet still describes the complete active state. Do not merge across an edge transition or device generation.
- On a sequence gap, malformed frame, queue overflow, focus loss, session stop, desktop switch failure, or injection error, cancel all contacts before accepting a new down sequence.
- Keep packet parsing independent of C/C++ structure padding. Use packed protocol definitions with explicit endian conversion and compile-time size assertions on both sides.

## Windows 11 injection contract

Microsoft currently marks the API documentation as prerelease. Revalidate it against the Windows SDK and the minimum tested Windows 11 build before shipping.

Create the synthetic device with these parameters:

```text
pointerType  = PT_TOUCHPAD
maxCount     = clamp(clientMaxContacts, 1, 5)
feedbackMode = POINTER_FEEDBACK_NONE
hMonitor     = nullptr
deviceWidth  = validated width in HIMETRIC units
deviceHeight = validated height in HIMETRIC units
options      = SDCO_PHYSICAL_SIZE
```

Do not add `SDCO_TOUCHPAD_GESTURE_ONLY` for version 1. Without that option, Windows can treat the injected device like a physical touchpad, including pointer movement and clicks; gesture-only mode would intentionally prevent those behaviors.

Implementation requirements:

- Load `CreateSyntheticPointerDevice2` dynamically. Prefer the exported name and current SDK declaration; keep any compatibility declaration isolated and guarded. Do not assume the older `CreateSyntheticPointerDevice` can create a touchpad.
- Populate `POINTER_TYPE_INFO` using the touch information fields, with both the outer and nested pointer type set consistently to `PT_TOUCHPAD` as required by the tested SDK.
- Convert normalized coordinates to the validated physical device rectangle and set `ptHimetricLocation` and `ptHimetricLocationRaw`. Do not use `ptPixelLocation` for contact position.
- Inject a contiguous array containing at most five records through `InjectSyntheticPointerInput()`.
- Preserve stable Windows pointer IDs for the lifetime of each client contact. Remove a slot only after its up/cancel frame has been injected successfully.
- Map down, update, up, and cancel edges deliberately to `POINTER_FLAGS`; clear edge-triggered flags before the next frame.
- Destroy the synthetic device and clear every contact during per-client teardown, stream termination, input disable, device-generation change, or fatal injection failure.
- Keep device and contact state inside Vibepollo's per-client input context. Never share active contacts across streaming sessions.
- Measure whether Windows cancels idle touchpad contacts before copying the existing 50 ms touchscreen refresh behavior. Add a refresh only if a reproducible test proves it is necessary.

Official references:

- [CreateSyntheticPointerDevice2](https://learn.microsoft.com/en-us/windows/win32/input-precisiontouchpad/createsyntheticpointerdevice2)
- [InjectSyntheticPointerInput](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-injectsyntheticpointerinput)
- [Precision Touchpad reference](https://learn.microsoft.com/en-us/windows/win32/input-precisiontouchpad/precision-touchpad-reference)
- [GetPointerTouchpadInfo behavior](https://learn.microsoft.com/en-us/windows/win32/input-precisiontouchpad/getpointertouchpadinfo)

## Host state machine

```text
legacy mouse
  -> capability advertised and client opts in
  -> valid device description
  -> PT_TOUCHPAD created
  -> activation success acknowledged
  -> accepting frames
  -> cancel all contacts on any boundary or fault
  -> destroy device
  -> legacy mouse
```

Required boundaries include client disconnect, stream stop, focus/capture loss reported by the client, device removal, device-generation change, configuration disable, Windows input-desktop transition failure, sleep, and host shutdown.

## Validation matrix

### Automated host tests

- Capability absent on unsupported Windows, missing API, or a disabled setting.
- Device-creation failure returns an activation rejection, clears all state, rejects frames for that generation, and leaves client legacy mouse delivery active.
- Packet validator rejects short headers, length mismatches, unknown versions, invalid generations, more than five contacts, duplicate IDs, NaN/infinity, out-of-range coordinates, invalid flags, and illegal transitions.
- State tests cover one through five contacts, simultaneous down/up, reordered IDs, dropped move frames, stale sequences, cancel-one, cancel-all, device replacement, session teardown, and injection failure.
- Legacy touchscreen and controller-touch packet tests remain unchanged and passing.
- Fuzz the new packet parser and state transition layer before enabling the feature by default anywhere.

### Windows 11 integration tests

- Confirm Windows identifies the injected source as a touchpad rather than a touchscreen.
- Verify pointer movement, physical click, tap-to-click, secondary click, two-finger scrolling, pinch, and supported three-/four-finger gestures.
- Exercise one through five simultaneous contacts and compare direction, scale, velocity, and palm/contact behavior with the physical Mac trackpad.
- Repeat focus loss, capture release, disconnect/reconnect, sleep/wake, input-desktop changes, service restart, and configuration toggles; no contact may remain stuck.
- Use an external mouse concurrently and verify no duplicate motion or click delivery.
- Verify unsupported Vibepollo, upstream Sunshine, Windows 10, and a disabled host preference keep the Moonlight legacy mouse path.

### Performance and diagnostics

- Record received, rejected, coalesced, and injected frame counts; active contact count; cancellation reason; last Win32 error; and injection duration.
- Do not log raw coordinates, gesture content, host identity, or persistent device identifiers by default.
- Reject the feature if it causes input loss or ordering regressions, or exceeds the modernization plan's 5% unaffected-scenario CPU, energy, or latency budget.

## Recommended pull-request sequence

1. `moonlight-common-c`: reserve capability and packet IDs, define version 1 structures, add endian/size/state tests, and document rollback.
2. Vibepollo fork: parser/validator and inert platform abstraction behind `native_trackpad=false`.
3. Vibepollo fork: Windows 11 dynamic API probe, `PT_TOUCHPAD` injection, lifecycle cleanup, diagnostics, and unit/integration tests.
4. Moonlight Qt: macOS capability probe and trace fixtures, still translating to the legacy mouse path.
5. Moonlight Qt: opt-in negotiation, raw frame transmission, duplicate-event suppression, kill switch, and fallback tests.
6. Matched client/host hardware validation before either side enables the feature outside test builds.

## Stop conditions and rollback

Stop and disable the capability if the host reports itself as a touchscreen, contacts stick after any lifecycle boundary, duplicate mouse/trackpad events occur, pointer IDs are reused while active, device dimensions are ignored, unsupported hosts lose mouse fallback, or the Microsoft contract changes incompatibly.

Rollback is independent on each side:

- host: disable `native_trackpad` and stop advertising the capability;
- protocol: retain the assigned IDs but stop emitting version 1 packets;
- client: disable the per-host preference and immediately restore legacy mouse translation.

No rollback path should require a reconnect, kernel driver removal, or user cleanup of a persistent virtual device.
