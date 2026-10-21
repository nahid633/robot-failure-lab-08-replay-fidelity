# Lab08: all replay outcomes

Executed October 21, 2026. Each row is one fresh Python process on a preserved Lab05 recording, not a new navigation trial. Four excluded development replays are separately retained under development/ and all passed. Seven comparator tests passed before main. All 36 main process starts completed; component exceptions are outcomes inside those completed processes, not successful replays.

The exact target is the originally captured LaserScan on each branch/input index; fields include frame, stamps, scalar settings, ranges and intensities. CDR padding bytes are reported separately. Logical time is injected at callback entry, so this is not a measured DDS or wall scheduling latency. The declared 50 ms limit is an interface tolerance.

| # | Original recording | Mode | Exact / target | Changed | Missing / extra | Max time error (ms) | Result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | block-1-fresh | matched | 654/654 | 0 | 0/0 | 0.000 | pass |
| 2 | block-1-fresh | header_clock | 654/654 | 0 | 0/0 | 183.000 | mismatch |
| 3 | block-1-fresh | late_join | 378/378 | 0 | 0/0 | 0.000 | pass |
| 4 | block-1-missing | matched | 736/736 | 0 | 0/0 | 0.000 | pass |
| 5 | block-1-missing | header_clock | 736/736 | 0 | 0/0 | 144.000 | mismatch |
| 6 | block-1-missing | late_join | 504/504 | 0 | 0/0 | 0.000 | pass |
| 7 | block-1-frozen | matched | 726/726 | 0 | 0/0 | 0.000 | pass |
| 8 | block-1-frozen | header_clock | 726/726 | 0 | 0/0 | 18.000 | pass |
| 9 | block-1-frozen | late_join | 1/506 | 0 | 505/0 | 0.000 | callback exception |
| 10 | block-1-restamped | matched | 714/714 | 0 | 0/0 | 0.000 | pass |
| 11 | block-1-restamped | header_clock | 714/714 | 0 | 0/0 | 18.000 | pass |
| 12 | block-1-restamped | late_join | 1/516 | 0 | 515/0 | 0.000 | callback exception |
| 13 | block-2-fresh | header_clock | 726/726 | 0 | 0/0 | 111.000 | mismatch |
| 14 | block-2-fresh | late_join | 458/458 | 0 | 0/0 | 0.000 | pass |
| 15 | block-2-fresh | matched | 726/726 | 0 | 0/0 | 0.000 | pass |
| 16 | block-2-missing | header_clock | 722/722 | 0 | 0/0 | 30.000 | pass |
| 17 | block-2-missing | late_join | 510/510 | 0 | 0/0 | 0.000 | pass |
| 18 | block-2-missing | matched | 722/722 | 0 | 0/0 | 0.000 | pass |
| 19 | block-2-frozen | header_clock | 726/726 | 0 | 0/0 | 96.000 | mismatch |
| 20 | block-2-frozen | late_join | 1/494 | 0 | 493/0 | 0.000 | callback exception |
| 21 | block-2-frozen | matched | 726/726 | 0 | 0/0 | 0.000 | pass |
| 22 | block-2-restamped | header_clock | 726/726 | 0 | 0/0 | 39.000 | pass |
| 23 | block-2-restamped | late_join | 1/516 | 0 | 515/0 | 0.000 | callback exception |
| 24 | block-2-restamped | matched | 726/726 | 0 | 0/0 | 0.000 | pass |
| 25 | block-3-fresh | late_join | 264/264 | 0 | 0/0 | 0.000 | pass |
| 26 | block-3-fresh | matched | 476/476 | 0 | 0/0 | 0.000 | pass |
| 27 | block-3-fresh | header_clock | 476/476 | 0 | 0/0 | 21.000 | pass |
| 28 | block-3-missing | late_join | 508/508 | 0 | 0/0 | 0.000 | pass |
| 29 | block-3-missing | matched | 738/738 | 0 | 0/0 | 0.000 | pass |
| 30 | block-3-missing | header_clock | 738/738 | 0 | 0/0 | 57.000 | mismatch |
| 31 | block-3-frozen | late_join | 1/518 | 0 | 517/0 | 0.000 | callback exception |
| 32 | block-3-frozen | matched | 716/716 | 0 | 0/0 | 0.000 | pass |
| 33 | block-3-frozen | header_clock | 716/716 | 0 | 0/0 | 141.000 | mismatch |
| 34 | block-3-restamped | late_join | 1/118 | 0 | 117/0 | 0.000 | callback exception |
| 35 | block-3-restamped | matched | 724/724 | 0 | 0/0 | 0.000 | pass |
| 36 | block-3-restamped | header_clock | 724/724 | 0 | 0/0 | 36.000 | pass |

## Aggregate diagnostics

```json
{
  "matched": {
    "accepted": 12,
    "executions": 12,
    "expected_packets": 8384,
    "actual_packets": 8384,
    "field_exact_packets": 8384,
    "changed": 0,
    "missing": 0,
    "extra": 0,
    "callback_exceptions": 0,
    "cdr_byte_differences": 7258,
    "max_logical_time_error_ms": 0.0
  },
  "header_clock": {
    "accepted": 6,
    "executions": 12,
    "expected_packets": 8384,
    "actual_packets": 8384,
    "field_exact_packets": 8384,
    "changed": 0,
    "missing": 0,
    "extra": 0,
    "callback_exceptions": 0,
    "cdr_byte_differences": 5882,
    "max_logical_time_error_ms": 183.0000000000007
  },
  "late_join": {
    "accepted": 6,
    "executions": 12,
    "expected_packets": 5290,
    "actual_packets": 2628,
    "field_exact_packets": 2628,
    "changed": 0,
    "missing": 2662,
    "extra": 0,
    "callback_exceptions": 6,
    "cdr_byte_differences": 1941,
    "max_logical_time_error_ms": 0.0
  }
}
```

## Evidence and reproduction

FROZEN-PROTOCOL.json binds order/source/input hashes before all main starts. Every cell retains request.json, attempt.json, process.log, evidence/result.json (all discrepancies/exception text), original expected packets, actual packets and injected clocks. INPUT-MANIFEST.json maps copied recordings to their immutable Lab05 paths. EVIDENCE-VALIDATION.json checks metrics independently against original targets and the original routing rule, plus output order and frozen hashes. ENVIRONMENT.json records Python/ROS packages and inspected Vektor commit. README.md describes reproduction.

Interpretation and limits are in FINDINGS.md. Reusing historical data does not add independent trials to Lab05, and 36 component replays must not be pooled with 39 prior navigation trials or 56 Lab07 oracle evaluations. No physical hardware, ROS transport, controller, whole Nav2, new closed-loop simulation, Vektor integration or external reproduction was tested.
