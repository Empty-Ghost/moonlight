# Phase 2 media security correlation

Review date: 2026-08-16  
Scope: the exact local media candidate recorded in `MEDIA_CANDIDATE.md`  
Result: **conditional pass — no known reachable advisory identified in the reviewed records**

This is a source-and-build correlation, not a claim that the components are vulnerability-free. The review used the official FFmpeg security ledger, NVD records returned for the exact component names, public GitHub repository advisory endpoints for the Khronos projects, candidate source, generated binaries, and archive contents. It did not include a commercial vulnerability feed, a maintainer attestation, fuzzing, or a complete transitive-code audit.

## Component decisions

| Component and exact candidate | Evidence reviewed | Reachability and decision |
|---|---|---|
| FFmpeg `bf1b838f2ab88b4f8fd83443325c782ea0e0f7fa` (9.0.1) | [FFmpeg's security ledger](https://ffmpeg.org/security.html), the fixes linked there through 2026-08-16, and NVD FFmpeg records published through the review date. | **Conditional pass.** The official ledger does not yet map a 9.0 branch, so it cannot supply a complete per-release assertion. Candidate source contains the reviewed fixes for EXR, SANM, swscale, MagicYUV, `zmqsend`, MACE6, TY, and NVDEC. Moonlight's build exports none of the reviewed EXR, SANM, MagicYUV, MACE6, Shorten, or NVDEC decoder symbols; it builds no `libavformat` runtime and ships no FFmpeg tools. The shipped and reachable swscale code contains the reviewed integer-overflow fix. |
| dav1d `54706fc6bc0cdecab7e9593974a4039cc038fca7` (1.5.4) | NVD keyword results returned [CVE-2023-32570](https://nvd.nist.gov/vuln/detail/CVE-2023-32570), affecting versions before 1.2.0, and [CVE-2024-1580](https://nvd.nist.gov/vuln/detail/CVE-2024-1580), for which the CNA recommends upgrading past 1.4.0. | **Conditional pass.** The unchanged 1.5.4 pin is later than both affected ranges. The NVD query returned no additional dav1d records. dav1d remains reachable because it is statically incorporated into FFmpeg's AV1 decoder. |
| libplacebo `4d82c6898551068d4ae6a6b5538efcddc2c7cf64` (7.371.0) | NVD exact-name keyword query and local source/patch review. | **Conditional pass with monitoring.** No NVD record surfaced for `libplacebo`; that negative search is not proof of absence. Vulkan rendering is reachable. The unversioned pin and two locally maintained patches remain the larger reviewability risk, and neither patch has a recorded upstream reference. |
| Vulkan-Headers `e3b1eec08173d6b825cd3ac88c885a63b621504a` (1.4.357) | NVD exact-name keyword query and the repository's public GitHub security-advisory endpoint. | **Conditional pass.** Both queries returned zero records as of the review. The dependency is header-only and adds no runtime dylib, but generated API definitions still remain in normal code-review scope. |
| Vulkan SDK / MoltenVK 1.4.357.0 | NVD exact-name keyword query, the MoltenVK public GitHub security-advisory endpoint, SDK provenance/signature checks recorded in `MEDIA_CANDIDATE.md`, and shipped dylib inspection. | **Conditional pass with monitoring.** Both advisory queries returned zero records as of the review; this is not proof of absence. `libMoltenVK.dylib` is runtime-reachable, so future SDK and MoltenVK advisories must be rechecked before publication if this review becomes stale. |

## FFmpeg advisory correlation

The following fixes were compared with the candidate source rather than inferred only from a version string:

| Record | Affected area | Candidate disposition |
|---|---|---|
| CVE-2025-59733 | EXR decoder | Fix content present; decoder excluded from the configured build. |
| CVE-2025-59734 | SANM decoder | Both fix changes are present in evolved candidate code; decoder excluded. |
| CVE-2025-63757 | swscale output overflow | Fix content present; swscale is shipped and reachable. |
| CVE-2026-8461 | MagicYUV decoder | All three linked fix changes are present; decoder excluded. |
| CVE-2026-30999 | `tools/zmqsend.c` | Fix content present; tools are not built or shipped. |
| [CVE-2026-66039](https://nvd.nist.gov/vuln/detail/CVE-2026-66039) | MACE6 decoder | NVD's affected range ends at 8.1.2. Fix content is present in candidate source; decoder excluded. |
| [CVE-2026-65704](https://nvd.nist.gov/vuln/detail/CVE-2026-65704) | TY demuxer / Shorten path | NVD's affected range ends at 8.1.2. Fix content is present; `libavformat` is not built and the Shorten decoder is excluded. |
| [CVE-2026-64832](https://nvd.nist.gov/vuln/detail/CVE-2026-64832) | NVDEC | NVD's affected range ends at 8.1.2. Fix content is present; NVDEC is excluded and unavailable in this macOS configuration. |

The produced media archive contains FFmpeg headers for compilation but its runtime payload is limited to `libavcodec.63.dylib`, `libavutil.61.dylib`, and `libswscale.10.dylib`. Both arm64 and x86_64 `libavcodec` slices were checked for the excluded decoder/hardware symbols.

## Remaining security boundaries

- Re-run this review immediately before any immutable v13 publication because advisory data can change after 2026-08-16.
- Treat a newly published reachable advisory, a changed pin, a changed configure surface, or a changed local patch as invalidating this result.
- Hosted dependency CI, code-signing/notarization of a final Moonlight artifact, and clean-machine verification are separate gates and were not established here.
- No formal SBOM vulnerability-scanner result or maintainer security sign-off was produced; those are optional escalation gates if project policy requires stronger assurance than this source/build correlation.
