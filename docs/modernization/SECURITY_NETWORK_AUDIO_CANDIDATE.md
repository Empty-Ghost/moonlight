# Phase 2 security/network/audio candidate ledger

Review date: 2026-08-17  
Owner: local execution by Codex; maintainer review unassigned  
Dependency branch: `phase2-security-v13-candidate` in `/Users/justin/Development/moonlight-qt-deps-phase2-security`  
Decision: **local build/test candidate complete; physical streaming and release gates remain open; not published**  
Rollback: published dependency bundle `v12` at companion commit `22355399c660661d06f211845efe7ccfc5ba0484`

## Architecture policy

This is the first dependency group evaluated after macOS x86_64 support was explicitly dropped on 2026-08-17. Its acceptance gates are arm64-only. Windows x64 and Linux x86_64 remain supported and hosted cross-platform CI remains a separate gate.

## Pin review

| Component | Baseline | Candidate | Disposition |
|---|---|---|---|
| OpenSSL | `aae016bfd52fcad2bc9657c2c782cfdf73b1ed5f` (3.6.3) | unchanged | Retain: latest 3.6 release at review time and includes the 2026-06-09 security fixes. The 3.6 branch reaches end of life on 2026-11-01, so the application/toolchain group must choose a supported branch before a release after that date. |
| Opus | `ddbe48383984d56acd9e1ab6a090c54ca6b735a6` (1.5.2) | `22244de5a79bd1d6d623c32e72bf1954b56235be` (1.6.1) | Advance to the latest stable release. |
| moonlight-common-c | `e41355ea01670fd4c830b384009d31dd0339a705` | unchanged | Retain current upstream head. The pin descends from the fixes for the three historical high-severity GitHub-reviewed advisories found during this review. |
| ENet | `aca87840b57f045a1f7f9299e4b1b9b8e2a5e2f1` | unchanged | Retain the current Moonlight fork head. |
| nanors | `b1e3c22ca0cdc0bb83e3cd6ed1a2fc77869ed99a` | unchanged | Retain the version intentionally selected by current moonlight-common-c; do not move the nested parser independently. |
| qmdnsengine | `b7a5a9f225d5e14b39f9fd1f905c4f505cf2ee99` | unchanged | Retain current Moonlight branch head. |
| Discord RPC | `7bcf3b3fdd02d4d5072971ef1d5b4e6dd3a765dc` | unchanged | Retain current Moonlight fork head pending the separate remove-or-replace compatibility decision. |

The GitHub advisory search returned no reviewed advisories for Opus, ENet, nanors, qmdnsengine, or the Discord RPC fork. This is a bounded negative result, not proof that those projects have no vulnerabilities. OpenSSL was reviewed against its own vulnerability list in addition to GitHub data.

## Local validation

- Opus 1.6.1 arm64 shared and static builds completed at macOS deployment target 13.
- The test-capable static Opus build passed all 5 registered upstream tests on arm64. A shared production-style configuration registered no tests; that run is explicitly not counted as a test pass.
- Opus ABI comparison found no removed exports. The candidate retains `@rpath/libopus.0.dylib`, raises the current version from 0.10.1 to 0.11.1, and adds seven 24-bit API symbols.
- moonlight-common-c built on arm64 using the reviewed bundled OpenSSL. Its registered queue test passed 1/1 when run with the bundle library path. A broad OpenSSL search path had selected an unrelated Homebrew library during an earlier diagnostic build; the isolated rerun is the accepted result.
- OpenSSL 3.6.3 full arm64 test suite passed: 353 files and 3,944 tests, with configuration-dependent skips reported by upstream (`Result: PASS`).
- Moonlight QtTest: 13/13 passed on arm64.
- Installer hardening tests: 7/7 passed, including arm64-only acceptance and x86_64-only rejection.
- qmake accepted `QMAKE_APPLE_DEVICE_ARCHS=arm64` and rejected `x86_64` with `Moonlight for macOS supports arm64 only`.
- A clean official-Qt arm64 Release application build passed at minimum macOS 13. After deployment, the Opus 1.6.1 candidate replaced the baseline library; dyld confirmed that exact app-bundle path was loaded and `Moonlight --version` returned 6.1.0.
- The deployed application contained 105 Mach-O files. Every file was verified as arm64-only after the packaging thinning step.
- The media-only arm64 archive script produced a ZIP with a valid CRC and five arm64-only dylibs. The complete dependency archive was not generated because all dependency-group build outputs were not staged together; that remains part of the immutable `v13` gate.

## Open gates

- Hosted Windows/Linux/macOS CI.
- Immutable arm64-only `v13` archive, checksum, and publication.
- The pre-existing deployed `libqsqlmimer.dylib` reference to `/usr/local/lib/libmimerapi.dylib` still fails the no-developer-machine-path packaging gate; it is unrelated to Opus and is not represented as fixed here.
- Signing, notarization, Gatekeeper, and clean-machine install/launch.
- Physical audio streaming and sustained soak tests.

None of the open gates is represented as passed.
