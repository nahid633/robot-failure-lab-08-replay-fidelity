# Lab08: component replay fidelity — protocol before development/main

Selected October 21, 2026: founder menu choice 18. Sequence Lab08; Lab06 stays proposed. This experiment has no new navigation goals or simulator calls. It reuses Lab05's 12 main recordings; these are neither 36 new robot trials nor independent new measurements of physical behavior. Lab07's 56 oracle evaluations remain separate from the earlier 39 navigation trials.

## Question and scope

Can the archived Lab05 Observer.scan callback reproduce its captured two-branch LaserScan outputs in a fresh process when given original serialized inputs, callback order/time, condition, and external fault activation? What changes if sensor-header time substitutes for callback clock, or replay joins at the fault with no cached pre-fault scan?

Execute the actual archived Python method, not a rewritten fault model. Inject clock and publication ports. Do not initialize rclpy or construct a ROS node, publisher, controller or simulator. Output packets go only to local evidence files. Disable the method's observer-only obstacle-hit counting branch by leaving world/appearance unavailable; it does not affect routing decisions. This is an interface-level component test, not executor/DDS/rosbag timing, Nav2 behavior, closed-loop trajectory, Vektor integration or physical fidelity.

Inputs: complete raw-scans.jsonl plus scans.csv callback sequence/timestamps, condition from result.json, FAULT_START.json external event. Reconstruct matched cache by executing all preceding scans; verify origin/hash against captured fault state. Original published CSV and CDR are comparison targets only; never use them to generate outputs. Copy and hash all inputs before main; preserve original immutable archives. Sensor stamps alone are not a full /clock trace; callback time is an explicit logical replay clock, not recovered global scheduling.

## Budget and freeze

Development: at most six fresh-process attempts on separately retained Lab05 excluded verification recordings, with four matched checks (fresh/missing/frozen/restamped) required. Retain every invocation, error and revision. Comparator tests deliberately perturb stamp, range, branch, packet count and timing and handle nonfinite scan values. If the gate cannot pass within budget, stop before main and record a concrete limitation. No outcome-driven main tuning.

Main: 12 recorded runs x three modes = 36 fresh processes, exactly one per cell, at most 30 wall seconds each. Fixed block/condition order; rotate mode order by block. No retries, replacements or changes after freeze. Before main, retain this protocol, executable source, source/input/package manifests, exact order and acceptance. Process/startup failures consume their slot; all outcomes remain visible.

## Predeclared metrics and acceptance

Per invocation: expected/actual counts, exact canonical field equality (frame, integer sec/nanosec, seven float32 scalar fields, ranges/intensities including nonfinite bit patterns), missing/extra/changed output keys indexed by original input and branch; paired header-stamp error; paired logical publication time p95/max error; CDR byte differences separately; wall runtime and exceptions. CDR transport padding is not semantic data and is not required to match.

Acceptance: no callback exception, all expected fields exactly equal, no missing/extra outputs, and maximum absolute logical publication-time error <=0.050 simulated seconds. This is a declared interface tolerance, not a hardware safety requirement. Report every discrepancy and every cell; diagnostics are not required to fail or pass. Late join compares the original suffix from the first attempted input; retain any first partial callback and count all later missing outputs. Do not fill missing cache from original outputs or retrospectively rerun failures.

No fresh closed-loop trajectory is generated here. The full original TF/clock/event/executor/internal controller state is unavailable, so a faithful full-stack replay would require new instrumentation and a different experiment. A replayed observation stream cannot establish how a robot's changed actions would alter future observations.
