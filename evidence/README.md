# Lab08 reproduction and evidence guide

This is a standalone component replay package. No simulator, physical robot, ROS node/context or network publisher is started. ROS message support is imported for deserialization and the actual archived callback is called through injected clock/publication ports. See FINDINGS.md for the precise limits.

Tested environment: Ubuntu 24.04 / WSL2, Python 3.12.3, ROS 2 Jazzy. ENVIRONMENT.json and replay-packages.txt identify the current message/runtime packages; original-packages.txt identifies the original capture environment. Original parameter YAML and Lab05 executable protocol are preserved for context. Only the component condition, fault event/cache and scan packets/callback clocks affect the tested callback. No whole-stack environment equivalence is claimed.

Use persistent local storage for all evidence. Paths below assume a shell with this extracted folder as its working directory:

```bash
source /opt/ros/jazzy/setup.bash
python3 -m unittest discover -s source -p test_replay.py -v
```

The original main evidence is immutable. To reproduce all 36 executions in a separate new directory:

```bash
replay_new="$PWD/../lab08-fresh-reproduction"
mkdir "$replay_new"
cp -r component source inputs development-inputs "$replay_new/"
cp FROZEN-PROTOCOL.json "$replay_new/"
python3 "$replay_new/source/run.py" main "$replay_new"
python3 reporting/analyze.py "$replay_new"
```

`mkdir` must succeed on a new directory. The coordinator refuses an existing main/ folder, verifies frozen source/component/input hashes, enforces 30 seconds per fresh process and does not retry any result. The six late-join exceptions and six header-clock tolerance failures are recorded outcomes, not reasons to rerun a cell. New CDR padding bytes can differ while decoded fields match. Timings in results are injected logical simulation timestamps, not wall playback timing.

To run one separately labelled diagnostic without changing the archived campaign:

```bash
python3 source/replay.py inputs/block-1-restamped component matched ../lab08-single-new-output
```

`reporting/analyze.py` is a post-main independent comparator/audit/renderer, retained separately from frozen execution sources. It checks the frozen hashes, source targets, branch order and all metrics and writes two PNGs, REPORT.md, SUMMARY.json, ALL-REPLAYS.csv and EVIDENCE-VALIDATION.json. Findings and narrative protocol are reviewed human-readable artifacts, not generated experiment outcomes. SHA256SUMS.txt covers every packaged file except itself; PACKAGE-VERIFICATION.json is retained beside the ZIP to avoid self-reference.

Layout: component/ (unchanged archived trial/core/support); source/ (frozen harness/coordinator/comparator tests); inputs/ (12 copied original recordings); development-inputs/ and development/ (four excluded checks); main/ (36 process attempts); reporting/ (post-main audit/plots); manifests and reports at root. Each replay's expected target is independently checked against the copied original published packets; no target generates replay outputs. INPUT-MANIFEST.json maps copies back to the KB archive.

Historical prepare/development/freeze commands in run.py expect the original KB layout. Standalone reproduction uses the packaged frozen main interface above. It needs no private KB beyond the included inputs and component source. No fresh-machine reproduction has yet been performed. Lab05/Lab07 immutable archives, raw/ and data/ were not modified.
