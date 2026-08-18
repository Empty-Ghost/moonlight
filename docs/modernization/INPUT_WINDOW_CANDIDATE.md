# Phase 2 input/window candidate ledger

> Architecture note (2026-08-17): x86_64, Rosetta, and universal results below are retained as historical evidence from before macOS x86_64 support was dropped. New macOS artifacts and gates are arm64-only.

Review date: 2026-08-16  
Owner: local execution by Codex; maintainer review unassigned  
Decision: **accepted locally; SDL binaries retained and GameControllerDB pin advanced**  
Rollback: dependency bundle `v12` and GameControllerDB commit `8d9fefd7b810f2541f78cc7a8ccbd185bc84c7a5`

The published `v12` bundle already contains the latest stable SDL and sdl2-compat releases. No dependency-repository source or binary changed, so generating a byte-equivalent replacement archive would not create a useful immutable artifact. The only accepted delta is the application repository's unversioned SDL GameControllerDB submodule. No tag, release asset, or installer metadata was published or changed.

## Candidate inventory

| Component | Current | Reviewed candidate | Release / commit date | Decision and rationale |
|---|---|---|---|---|
| SDL | `147a8ee32dbf9ac02f3794964490687b6bbda1bc` (3.4.14) | unchanged | 2026-08-03 | Retain. This is the latest stable release and includes the current macOS clipboard and duplicate-controller fixes. ABI, Zlib license, and local patch disposition are unchanged; Moonlight carries no SDL source patch. |
| sdl2-compat | `a53b6ad90ecd2d0ccfe01d5cfd2059793acf8c12` (2.32.70) | unchanged | 2026-06-08 | Retain. This is the latest stable release. ABI, Zlib license, and patch disposition are unchanged; Moonlight carries no local patch. |
| SDL_ttf | `a883e490e30fb44a5336ea3dcb990c6982c5216f` (reports 2.25.0) | retain current pin; do not move to `d67ca21c8e0701f3c7bab3cca14f1d1a6daa235d` | 2026-04-05 / 2026-07-05 | Documented unversioned exception. The four newer SDL2-branch commits only change autotools/CMake-package framework flags and do not affect Moonlight's vendored CMake build. Moving to another unreleased commit would add risk without a linked runtime fix. Re-review by 2026-11-16 or when SDL_ttf publishes a stable SDL2 release. Zlib license and local patch disposition are unchanged. |
| SDL GameControllerDB | `8d9fefd7b810f2541f78cc7a8ccbd185bc84c7a5` | `42f28e22d20761e7004e8db91c4ad86402fdf600` | 2026-07-15 / 2026-08-12 | Accept the 15 upstream data commits. They add mappings and correct existing entries, including the upstream 8BitDo SN30 Pro macOS fix. This repository is intentionally unversioned data; the exact commit is the immutable pin and the previous commit is the rollback. Zlib license is unchanged. |

## Security and provenance review

- The public GitHub repository-advisory endpoints returned zero advisories for SDL, sdl2-compat, and SDL_ttf. This is a bounded negative search, not proof that no vulnerability exists.
- NVD exact-keyword review returned no sdl2-compat records. The SDL results were old SDL2/SDL2_image issues, and the single SDL_ttf record, CVE-2022-27470, affects SDL_ttf 2.0.18 and earlier; the retained pin reports 2.25.0.
- The GameControllerDB range changes only `README.md` and `gamecontrollerdb.txt`. Its Zlib license file is unchanged. No executable source was imported.
- A fresh advisory and release recheck remains required before publication.

## Dual-architecture dependency validation

- SDL 3.4.14: the 25 registered noninteractive CTest cases passed on arm64 and x86_64. The x86_64 all-target build initially discovered Homebrew's arm64-only FFmpeg and failed only its optional FFmpeg demo link; the registered SDL suite was isolated, fully built, and passed 25/25. This host-tool contamination is not counted as a dependency defect or as a passed FFmpeg demo.
- sdl2-compat 2.32.70: 13/13 registered CTest cases passed on arm64 and x86_64.
- SDL_ttf: vendored FreeType builds passed for arm64 and x86_64. Its installed CMake-package consumer linked and ran successfully natively and under Rosetta.
- Fresh universal dylibs contain `x86_64 arm64`, target macOS 13.0 for both slices, and retain the expected `@rpath/libSDL3.dylib`, `@rpath/libSDL2.dylib`, and `@rpath/libSDL2_ttf.dylib` IDs.
- Exported-symbol comparisons against the installed `v12` libraries were identical for each architecture: SDL3 1,271 symbols, SDL2 837 symbols, and SDL2_ttf 88 symbols, with zero diff lines.
- The candidate GameControllerDB passed its upstream duplicate-key checker. The exact `v12` SDL2 parser accepted 317 mappings from the 603,507-byte candidate file.

## Application validation and open gates

- The GameControllerDB remains embedded through `app/resources.qrc` and loaded by `MappingManager` through `SDL_GameControllerAddMappingsFromRW`; no application API change is required.
- Native arm64 Release and official-Qt universal Release application rebuilds passed, including regeneration of the embedded `resources.qrc` payload. The universal executable contains `x86_64 arm64`, targets macOS 13.0 for both slices, and returned Moonlight 6.1.0 under native arm64 and Rosetta x86_64. Native QtTest remained 13/13.
- The first native CLI attempt used an old deployed-framework directory in the reused build tree and aborted after loading duplicate Homebrew and bundled Qt classes. Re-running with one explicit Homebrew Qt framework path passed. The clean official-Qt universal build is the distributable architecture/deployment-target evidence.
- No physical controller was available for this review. Device-specific confirmation of the changed mappings, including the 8BitDo SN30 Pro macOS entry, remains a peripheral gate and is not represented as passed.
- Because the SDL binaries are unchanged and the only accepted delta is a controller database, the prior media benchmark is not reused as performance evidence and no new performance claim is made. A controller smoke test with affected hardware remains the meaningful runtime gate.
