# Phase 2 dependency policy and update ledger

Last updated: 2026-08-16

## Baseline and rollback

- Application baseline: `e41fedbabcc7243f27edc34eec0a6f1dff4755a6` plus the preserved, uncommitted Phase 1 Vulkan timing/status evidence.
- Dependency repository: `/Users/justin/Development/moonlight-qt-deps` at pinned source tag `v12`, commit `22355399c660661d06f211845efe7ccfc5ba0484`.
- Published macOS archive: `macOS-universal.zip`, 28,492,950 bytes, SHA-256 `446228fb68d5aef4bb8791f08e5e98e38e6ecffdefac7633902fc463189a0f3c`.
- Rollback: the app defaults to `v12`; `MOONLIGHT_DEPS_TAG=v12` is the explicit developer override. A later tag cannot be selected until its asset name, size, and SHA-256 are reviewed into `setup-deps.py`.

The ten unresolved Phase 0 streaming/peripheral gates remain evidence gaps. Phase 2 may build its inventory, SBOM, installer safety, and candidate branches, but no dependency pin movement can be accepted until the applicable baseline scenario can be compared on identical hardware and settings.

## Required ledger fields

Every dependency row in `dependencies.json` must acquire these fields before the Phase 2 exit gate:

- current and candidate commit or exact version;
- current and candidate release date;
- change class: security, patch, minor, major, or unversioned commit;
- API and ABI notes, known CVEs, license and license-change result;
- local patch disposition and upstream reference;
- upstream tests run for arm64;
- Moonlight build, test, benchmark, and packaging results;
- decision, owner, risk, review date, and rollback pin.

An empty field means `not assessed`, never `no issue`. Unreleased commits require both an upstream fix reference and a local regression test.

## Review groups

| Order | Group | Components | Initial state |
|---|---|---|---|
| 1 | Media | FFmpeg, dav1d, libplacebo, Vulkan-Headers, Vulkan SDK/MoltenVK | Accepted locally on 2026-08-16 after dual-architecture dependency/app checks, matched streaming, and a conditional security pass. Power and sustained-session evidence are deferred; hosted CI and immutable publication remain open. See `MEDIA_CANDIDATE.md` and `MEDIA_SECURITY_REVIEW.md`. |
| 2 | Input/window | SDL 3, sdl2-compat, SDL_ttf, SDL GameControllerDB | Accepted locally on 2026-08-16. SDL and sdl2-compat already match the latest stable releases; SDL_ttf remains pinned under a documented unversioned exception; GameControllerDB advances to `42f28e22`. Dual-architecture dependency tests and ABI checks passed. Physical-controller confirmation remains open. See `INPUT_WINDOW_CANDIDATE.md`. |
| 3 | Security/network/audio | OpenSSL, Opus, moonlight-common-c, ENet, nanors, qmdnsengine, Discord RPC | Candidate refresh not started; Phase 1 common-c tests are preserved but not published. |
| 4 | Application/toolchain | Qt, Xcode/SDK, Apple Clang, qmake, Python, CMake, Meson, Ninja, NASM, pkg-config, create-dmg, aqtinstall | Candidate refresh not started. |
| 5 | CI supply chain | GitHub Actions, runner images, Homebrew packages, installer actions | Candidate refresh not started. |

Each group gets a separate dependency-repository branch and immutable artifact. Both macOS slices must build and pass dependency tests before the Moonlight app consumes that artifact. Tags and release assets are never replaced.

## Installer safety acceptance

- Verify expected byte size and SHA-256 before extraction.
- Reject absolute paths, parent traversal, backslash paths, symlinks, excessive entry counts, and excessive expanded size.
- Validate required layout and an arm64 slice before changing `libs/mac`. Additional slices in the rollback `v12` archive are tolerated, but new macOS archives and final application bundles must contain only arm64 Mach-O binaries.
- Stage on the target filesystem and atomically replace only after all checks pass.
- Preserve the prior install on download, verification, extraction, or validation failure.

The installer unit tests cover traversal, symlink rejection, digest failure preservation, rollback after an injected swap failure, and successful atomic replacement. A real `v12` macOS download/install smoke test also verifies the published digest and its arm64 SDL slice; its historical x86_64 slice is not required by the current policy.
