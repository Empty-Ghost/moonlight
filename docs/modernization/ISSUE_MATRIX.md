# macOS issue matrix

Triaged against `moonlight-qt` master `256022d3d62175da0f9b263ed152851cdadc8eac` on 2026-08-15. GitHub state and comments were refreshed on that date. “Needs information” means the report was not treated as reproduced without the required host, peripheral, display, or synchronized measurement.

| Issue | Classification | Priority candidate | Current-master evidence / required reproducer |
|---|---|---:|---|
| [#1929](https://github.com/moonlight-stream/moonlight-qt/issues/1929) mouse latency | needs information | P1 | Open; report is against 6.1.0 and has no trace or quantitative reproducer. Needs the same Mac/host compared with SDL/AppKit timestamps and a 125/500/1000 Hz mouse. |
| [#1249](https://github.com/moonlight-stream/moonlight-qt/issues/1249) decode latency changes with mouse movement | needs information | P1 | Open; report predates current master and conflates displayed decode latency with scheduling/present. Needs fixed 1440p144 content and split timing counters. |
| [#1594](https://github.com/moonlight-stream/moonlight-qt/issues/1594) battery drain | needs information | P1 | Open; 30%/hour was reported on M1 Pro at 120 fps/HDR/130 Mbps. Needs controlled battery, brightness, renderer, thermal, and Energy Log runs. |
| [#1781](https://github.com/moonlight-stream/moonlight-qt/issues/1781) V-Sync audio crackle | needs information | P1 | Open; report is 6.1.0 on M4 at 1440p120/150 Mbps. Needs current-master audio queue counters and built-in/USB/Bluetooth device matrix. |
| [#1825](https://github.com/moonlight-stream/moonlight-qt/issues/1825) high-bitrate freeze | needs information | P1 | Open; reporter supplied a useful 10/30/50 Mbps threshold and logs, but no controlled Sunshine host is available locally. Re-run 10–250 Mbps on Ethernet and Wi-Fi while holding codec/render constant. |
| [#1427](https://github.com/moonlight-stream/moonlight-qt/issues/1427) Sequoia Wi-Fi jitter | external/OS | P2 | Report isolates Sequoia Wi-Fi from Ethernet and older macOS; issue discussion points to AWDL/channel interference. Confirm with Wi-Fi channel/AWDL diagnostics without changing system services. |
| [#753](https://github.com/moonlight-stream/moonlight-qt/issues/753) M1 stutter | needs information | P2 | Open report is from Moonlight 3.2.0/macOS 12.3 and does not establish current-master behavior. Needs current hardware or an equivalent M1-generation machine. |
| [#1185](https://github.com/moonlight-stream/moonlight-qt/issues/1185) fractional HiDPI blur | needs information | P2 | Open report gives a clear visual procedure, but the local 2560×1664 internal panel and controlled host were not available as a paired test. Capture pixel references at native and scaled modes. |
| [#1213](https://github.com/moonlight-stream/moonlight-qt/issues/1213) wide-gamut color | needs information | P2 | Open; requires a wide-gamut host/client reference chart and objective capture. The local internal display alone cannot reproduce the Windows host color-management setup. |
| [#1429](https://github.com/moonlight-stream/moonlight-qt/issues/1429) wired XInput Y axis | fixed on master | P1 | SDL fixed the macOS mapping upstream; two reporters confirmed a nightly built at `179857f1` worked. Current master contains that commit and a newer SDL v12 bundle. Local peripheral regression coverage remains an evidence gap. |
| [#1953](https://github.com/moonlight-stream/moonlight-qt/issues/1953) macOS 27 beta network error | external/OS | P2 | Still open and labeled `external issue` on 2026-08-15. Local machine runs macOS 26.6.1, so the beta-only report cannot be reproduced here. |

No issue in this list is currently labeled P0 by upstream. The P1 designations above are modernization-program candidates, not upstream severity labels.
