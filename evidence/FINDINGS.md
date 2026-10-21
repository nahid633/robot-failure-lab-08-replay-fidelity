# Recorded inputs can reproduce this component—if its state and clock are retained

Measured October 21, 2026. Lab08 executed 36 fresh-process replays using 12 complete Lab05 recordings. These are component tests on historical data, not new navigation trials.

| Replay condition | Accepted | Exact captured message fields | What diverged |
| --- | --- | --- | --- |
| Matched callback clock and reconstructed pre-fault state | 12/12 | 8,384/8,384 outputs | No changed/missing/extra packets; zero logical publication-time error in the recorded callback-time model. |
| Sensor-header time substituted for callback clock | 6/12 | 8,384/8,384 outputs | Six exceeded the declared 50 ms logical-time tolerance; per-recording maximum offsets were 18–183 ms. |
| Start at the fault with no cached pre-fault scan | 6/12 | 2,628/5,290 expected suffix outputs | All six frozen/restamped callbacks raised a missing-cache exception. 2,662 suffix outputs were missing. Fresh/missing modes reproduced their suffixes. |

All 36 processes started and completed without infrastructure failure; six completed processes retained component exceptions. They are failed replays, not passes. Every partial output and discrepancy remains available. No replay outcome was retried, replaced or used to tune the source/protocol. Four separately retained development attempts and seven comparator tests passed before the frozen main campaign.

## What the result supports

The actual archived Lab05 `Observer.scan` method reproduced the captured two-branch LaserScan content, frame, integer stamps, scalar settings, ranges and intensities when its recorded inputs, callback order/time, condition and external fault activation were supplied. The cached scan was reconstructed by processing preceding inputs and checked against the original fault-state origin/hash. Original outputs served only as comparison targets.

Logical publication time is an injected callback-entry clock. Matched zero error follows this clock model plus the observed equality of original callback/publication timestamps here; it is not an independent measurement of scheduler, DDS or real-time playback accuracy. The header-clock contrast preserved the external event order and fault time, changing only the callback's clock input. It changed no output fields/routing decisions in this dataset, but moved logical publication times enough to fail six cells. The per-recording maximum offset is the original callback/publication time minus scan acquisition stamp, not measured transport-only latency. The deliberately chosen 50 ms threshold is an interface criterion, not a production safety requirement.

Late joining intentionally removed the cached scan and preceding callback history. Fresh/missing branches did not require that cache and matched their captured suffixes. Frozen/restamped modes tried to access unavailable state on the first attempted scan, after publishing one localization output, and then stopped. All later expected suffix outputs remain counted as missing. The harness does not fill that missing state from original outputs. Component-local sequence counters restart in late-join mode; input-index labels are external comparison keys, not restored component state. Primary equality concerns message fields; original/replay provenance metadata is retained separately.

7,258 of 8,384 paired matched-replay CDR byte strings differed despite exact equality of all decoded fields. Non-field serialization representation, consistent with alignment/padding, must not be conflated with a message-value regression. This experiment establishes neither identical serialized bytes nor universal determinism.

## Practical implication

For a component regression test, retain acquisition stamps, callback/receive clock semantics, event order, configuration, required pre-roll/state and original outputs. Check message values and timing separately. A packet-only recording that begins mid-run can lack state required even by a small relay. Reproducing a misleadingly restamped scan faithfully also reproduces its misleading timestamp; replay correctness does not make an observation fresh.

## Boundaries and evidence gaps

This is a fast, file-driven interface replay, not rosbag2/DDS playback. The component callback is invoked without constructing a ROS node/context; publication goes only to local files. The observer-only obstacle-hit counting branch is disabled and is outside the claim. No control/actuator publisher or live robot is created. Whole Nav2, controller outputs, TF, timer/executor scheduling, sensor QoS, discovery and physics are not replayed.

The existing recordings do not retain complete TF, `/clock` history, node state and full causal event order needed to support a faithful whole-stack replay. Callback timestamps are available for this interface, not a global schedule. No fresh closed-loop trajectory was generated or compared; original robot motion/goal/contact evidence remains solely Lab05's result. Feeding original observations into a changed controller cannot establish what observations its changed actions would create. A future closed-loop comparison requires a separate frozen experiment and new instrumentation.

Twelve source recordings from one route, one relay implementation and one environment provide a bounded compatibility result. They do not establish physical fidelity, general failure rates, cross-platform/clean-machine reproducibility, product value or Vektor integration. Live Vektor `src/replay.cpp` was inspected at `d9e64ecc0db91a4c2572062d14d1a851a843b65b`; its bounded adapter/provenance machinery was neither invoked nor changed.

The main protocol, source/configuration/input hashes and exact 36-cell order were frozen before the first main process. All original Lab05/Lab07 archives, raw sources and canonical data were preserved. Keep these 36 replays separate from the 39 earlier navigation-task trials and 56 Lab07 bounded oracle evaluations. Lab06 remains proposed.

## Package

REPORT.md and ALL-REPLAYS.csv contain all 36 rows. Each main/ cell has request, process log, attempt result, full expected/actual CDR packets, injected clocks, mismatch list and exception text. EVIDENCE-VALIDATION.json independently verifies all fields, counts, order, timing calculations, original routing provenance and frozen hashes. The full reproduction instructions, package/environment manifests, excluded development evidence and reviewed plots are included. Fresh-machine reproduction remains untested; no publication or outbound message occurred.
