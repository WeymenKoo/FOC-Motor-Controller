# Bench data

The report is one level up: [`Testing/README.md`](../README.md). This folder holds what it is built from.

| Path | Contents |
|---|---|
| [`CHAR_LOG.md`](CHAR_LOG.md) | Lab notebook: every run with its conditions and numbers, including failed and repeated ones |
| `char/<test>/<timestamp>/` | Raw waveforms (`.npz`), scope screenshots, per-test JSON and CSV |
| `report/` | Report figures, regenerated from `char/` by `make_report_figs.py` |
| [`PROBE_MAP.png`](PROBE_MAP.png) | Top view with every test point and usable ground pad (`make_probe_map.py`) |
| [`CHARACTERIZATION_PLAN.md`](CHARACTERIZATION_PLAN.md) | The plan written before the tests, kept for reference |
| `instruments.py`, `analyze_edges.py`, `motor_r.py` | Scope and supply control, edge metrics, 4-wire resistance |
