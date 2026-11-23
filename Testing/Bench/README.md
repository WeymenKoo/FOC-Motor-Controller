# Rev 1 bench characterization — findings so far

Power-stage characterization of the Rev 1 board **without an encoder and without a mechanical load**: the motor
(T-Motor MN601-S) is used as a stationary inductive load (a DC current vector parks the rotor) and, for real power flow,
spun unloaded up to 3000 rpm. Bench: Korad KA3005P at 30 V, Rigol DHO804 (70 MHz, 10x passive probes, hand-held), DMM,
K-type thermocouple. Work in progress — this page is updated as tests are added.

| File | What it is |
|---|---|
| [`CHAR_LOG.md`](CHAR_LOG.md) | Every test: conditions, measured numbers, limits of the measurement, conclusions |
| [`CHARACTERIZATION_PLAN.md`](CHARACTERIZATION_PLAN.md) | The plan: phases A–F, energy tiers, pre-test checklist, Rev B wishes |
| [`PROBE_MAP.png`](PROBE_MAP.png) / `.pdf` | Top view with every test point and usable ground pad, colour-coded by probing risk (`make_probe_map.py` regenerates it from the KiCad board) |
| `char/<test>/<timestamp>/` | Raw waveforms (`.npz`), scope screenshots, per-test JSON/CSV |
| `instruments.py`, `analyze_edges.py` | Scope / PSU control and the edge-metric extraction used for the tables |

**Status of the numbers:** voltages, timings and temperatures below are measured. **Current values are provisional** until the
current-sense scale is cross-checked against the shunt voltage (open item 1) — an energy balance suggests either the
motor's phase resistance is ~40–45 mΩ (not the 98 mΩ identified earlier) or the current sense over-reads by ~1.45×.

## Results at a glance (30 V bus)

| Area | Result |
|---|---|
| Bus-voltage measurement | Reads 0.36 % low at 30 V (DMM 30.04 V vs 29.93 V); OV / UV trips within 0.1 V of their settings |
| Supply rails | +3V3 at the scope noise floor, +1 mV rms while spinning; +5V carries ~100 mV p-p at 120–160 kHz from its own converter at light load (not from the bridge) |
| Switch node, 3 A | Hard edge 7.9 ns (3.1 V/ns), overshoot +0.9 V on 30 V; soft edge 38 ns (current-driven). Scope-limited: real edges are faster |
| Dead-time | 189–213 ns at the switch node (the MCU's 200 ns); body-diode plateau −1.0 V. Voltage error ≈ 0.3 V at 30 V |
| Gate-drive strength (DRV8323 IDRIVE) | 1000 → 440 → 190 mA source: rise 7.8 → 15.9 → 25.5 ns, overshoot 0.97 → 0.61 → 0.11 V; soft edge and dead-time unaffected |
| Bus ripple | Static hold: ~20 mV p-p between edges, ±0.45 V / 20 ns spikes at hard edges. Under real load (21 W at 3000 rpm): 79 mV p-p |
| Idle / overhead power | MCU + regulators 0.39 W, gate driver awake +0.36 W, switching at zero current +0.81 W |
| No-load input power | 6.1 W at 1000 rpm, 13.3 W at 2000 rpm, 21.1 W at 3000 rpm (sensorless closed loop) |
| Firmware over-current trip | Outputs off ~19 µs after the ADC sample that sees it; worst case ≈ 60 µs → overload protection only |
| Three-shunt current sensing | Phase C is sampled 0.87–1.45 µs after the window centre (second in its ADC's sequence): valid only for low-side windows ≥ ~3 µs. Phases A/B valid to ~1.2 µs |
| Thermal (rotor parked, 10 min each) | FET case +7.5 °C at 3 A, +10.2 °C at 5 A; fit: 6.0 °C fixed + 0.17 °C/A². Board NTC reads 1.5–2 °C above the FET case |

## What the firmware has to design around (provisional envelope)

- **Short-circuit protection is the gate driver's VDS monitor, not the firmware.** The firmware trip needs up to ~60 µs; a
  phase-to-phase fault at 56 V through ~19 µH rises ~3 A/µs. The driver's trip point still has to be verified on the bench.
- **Current sensing at high duty:** reconstruct phase C as −(ia + ib), or keep its low-side window ≥ 3 µs (duty ≤ ~92 %).
- **Dead-time voltage error ≈ 1 % of the bus** (0.3 V at 30 V) for |I| ≳ 1 A, current-dependent below. It limits low-speed
  torque linearity and blocks high-frequency-injection sensing on this low-inductance motor; compensation or a shorter
  (verified) dead-time is needed.
- **Over-voltage limit ≥ ~1.15 × the operating bus**, or the regen guard that refuses to lower the speed reference near OV is
  permanently active.
- **Stops must coast.** The bus capacitance (~350 µF) holds far less energy than the rotor at speed; the bench supply cannot
  sink regenerated energy.
- **Gate drive:** IDRIVE 440/880 mA is a reasonable default (one third less overshoot, lower EMI, small switching-loss cost) —
  to be confirmed at higher current.
- **Thermal:** 5 A continuous in one phase costs +10 °C on the FET case; extrapolated +23 °C at 10 A (two points — to be confirmed).

## Rev B candidates

| Item | Evidence |
|---|---|
| Route all three current-sense outputs to inputs both ADCs can sample | Phase C sampling-order failure (C1 / C1b) |
| Hardware E-stop input independent of the gate-driver enable | Rev 1: the E-stop is the bench supply's switch |
| Shorter or tunable dead-time, gate resistors for edge control | Dead-time error (B1), IDRIVE trade-off (B4) |
| Encoder read without blocking the control interrupt (faster SPI or DMA) | 3.5 µs of a 40 µs control period spent waiting on SPI |
| Bus capacitance / braking path sized for regeneration | Rotor energy vs bus energy |
| Probe-friendly test points: switch nodes, shunts, gates with ground next to each, wider spacing | Gate and switch-node pads are 1.3 mm apart — unsafe to probe by hand while powered |
| 5 V converter: fixed-frequency mode or more output capacitance, if anything sensitive hangs on +5V | ~100 mV p-p light-load ripple (A3) |

## Open items

1. **Current-sense scale** — measure the shunt voltage directly against the amplifier output (gain should be 20 V/V).
2. Opposite-polarity hard edge, phases B and C, 12 V / 24 V points.
3. Back-EMF capture while coasting (motor flux constant independent of the current sense).
4. Gate driver over-current trip point and latency; 10 A thermal hold; regeneration step; shorter dead-time (all supervised).
5. Not possible on this bench: efficiency under shaft load, bus-capacitor ripple at full power, high-side gate amplitude
   (needs a differential probe), EMC.
