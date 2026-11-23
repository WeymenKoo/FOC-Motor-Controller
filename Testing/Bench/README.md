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

**Status of the numbers:** voltages, timings, temperatures and currents are measured. The current-sense scale was
cross-checked with a floating DMM across the phase A shunt (correct within 1–2 %), and the motor's winding resistance was
measured 4-wire: **17.97 mΩ per phase** (35.9 mΩ line-line, matching the datasheet's 39 mΩ) — not the 98 mΩ identified earlier.

## Results at a glance (30 V bus)

| Area | Result |
|---|---|
| Bus-voltage measurement | Reads 0.36 % low at 30 V (DMM 30.04 V vs 29.93 V); OV / UV trips within 0.1 V of their settings |
| Supply rails | +3V3 at the scope noise floor, +1 mV rms while spinning; +5V carries ~100 mV p-p at 120–160 kHz from its own converter at light load (not from the bridge) |
| Switch node, 3 A | Hard edge 7.9 ns (3.1 V/ns), overshoot +0.9 V on 30 V; soft edge 38 ns (current-driven). Scope-limited: real edges are faster |
| Switch node, phase sinking 3 A | Low-side turn-on is the hard edge: 7.3 ns, **undershoot −9.5 V below ground** (−7.8 V at 1 A), ringing ~80–100 MHz for ~80 ns; soft edge mirrors the sourcing case |
| Shunt-side pins at the low-side hard edge (3 A) | −4.6 / +3.1 V across the shunt at the default gate current (rating ±3 V transient); −2.4 / +1.7 V at 440/880 mA. All other edges within ±1.8 V |
| Dead-time | 189–213 ns at the switch node (the MCU's 200 ns); body-diode plateau −1.0 V. Voltage error ≈ 0.3 V at 30 V |
| Gate-drive strength (DRV8323 IDRIVE) | High-side edge, 1000 → 440 → 190 mA: rise 7.8 → 15.9 → 25.5 ns, overshoot 0.97 → 0.61 → 0.11 V. **Low-side edge: undershoot 9.5 → 2.1 → 0.2 V** for 7.1 → 8.9 → 18.4 ns |
| Bus ripple | Static hold: ~20 mV p-p between edges, ±0.45 V / 20 ns spikes at hard edges. Under real load (21 W at 3000 rpm): 79 mV p-p |
| Idle / overhead power | MCU + regulators 0.39 W, gate driver awake +0.36 W, switching at zero current +0.81 W |
| No-load input power | 6.1 W at 1000 rpm, 13.3 W at 2000 rpm, 21.1 W at 3000 rpm (sensorless closed loop) |
| Firmware over-current trip | Outputs off ~19 µs after the ADC sample that sees it; worst case ≈ 60 µs → overload protection only |
| Current-sense scale | Floating DMM across the shunt: board reading correct within 1–2 % (3 A and 5 A) |
| Current-sense offsets / noise | Offsets move < 0.4 mV from 12 to 30 V, repeat within 1.1 mV; 20–27 mA rms per sample whether switching or not |
| Motor winding (4-wire, motor unplugged) | 17.65 / 18.19 / 18.08 mΩ per phase, mean 17.97 mΩ; the bench supply's leads alone add 110–145 mΩ |
| Three-shunt current sensing | Phase C is sampled 0.87–1.45 µs after the window centre (second in its ADC's sequence): valid only for low-side windows ≥ ~3 µs. Phases A/B valid to ~1.2 µs |
| Stop paths | Heartbeat loss → outputs off at 501 ms (500 ms setting), every time; STOP / DISARM acknowledged in 11–44 ms over USB-serial |
| Sensorless start-up | 50 / 50 starts to 1000 rpm; closed loop 2.449 ± 0.011 s after RUN |
| Brown-out | Runs down to 5 V, restarts at 5–6 V; clean power-on reset, no latch-up; analog supply steady at 3.30 V throughout |
| Thermal (rotor parked, 10 min each) | FET case +7.5 °C at 3 A, +10.2 °C at 5 A; fit: 6.0 °C fixed + 0.17 °C/A². Board NTC reads 1.5–2 °C above the FET case |

## What the firmware has to design around (provisional envelope)

- **Short-circuit protection is the gate driver's VDS monitor, not the firmware.** The firmware trip needs up to ~60 µs; a
  phase-to-phase fault at 56 V through ~19 µH rises ~3 A/µs. The driver's trip point still has to be verified on the bench.
- **Current sensing at high duty:** reconstruct phase C as −(ia + ib), or keep its low-side window ≥ 3 µs (duty ≤ ~92 %).
- **Switch-node undershoot:** −8 to −10 V below ground for ~10 ns at every low-side hard turn-on (phase sinking current), at
  30 V / 3 A with the default gate current (2.7 V at 440/880 mA, none at 190/380 mA). **The driver's absolute maximum on
  the switch-node pin is −7 V for 200 ns**, so the default gate current puts this board outside the rating — and likewise on the shunt-side pins (−4.6 V measured, ±3 V rated).
- **Dead-time voltage error ≈ 1 % of the bus** (0.3 V at 30 V) for |I| ≳ 1 A, current-dependent below. It limits low-speed
  torque linearity and blocks high-frequency-injection sensing on this low-inductance motor; compensation or a shorter
  (verified) dead-time is needed.
- **Over-voltage limit ≥ ~1.15 × the operating bus**, or the regen guard that refuses to lower the speed reference near OV is
  permanently active.
- **Stops must coast.** The bus capacitance (~350 µF) holds far less energy than the rotor at speed; the bench supply cannot
  sink regenerated energy.
- **Gate drive: do not use the driver's default (IDRIVE 1000/2000 mA).** At 440/880 mA the low-side undershoot drops from
  9.5 V to 2.1 V for 1.8 ns of extra edge time; at 190/380 mA it is gone. Recommended default 440/880 mA.
- **Motor constants:** the stored phase resistance (98 mΩ) is ~5.5× the winding's 18 mΩ; identification at ≤ 1 A is biased by
  the dead-time error. The loop sees winding + bridge path (~47 mΩ effective from an energy balance). Re-identify at several
  amps or with dead-time compensation.
- **Thermal:** 5 A continuous in one phase costs +10 °C on the FET case; extrapolated +23 °C at 10 A (two points — to be confirmed).

## Rev B candidates

| Item | Evidence |
|---|---|
| Route all three current-sense outputs to inputs both ADCs can sample | Phase C sampling-order failure (C1 / C1b) |
| Hardware E-stop input independent of the gate-driver enable | Rev 1: the E-stop is the bench supply's switch |
| Lower-inductance low-side source path (shunt placement, Kelvin return), snubber or low-side gate resistor | −8 to −10 V switch-node undershoot at low-side turn-on vs +0.9 V overshoot at high-side turn-on (B1 / B1neg) |
| Shorter or tunable dead-time, gate resistors for edge control | Dead-time error (B1), IDRIVE trade-off (B4) |
| Encoder read without blocking the control interrupt (faster SPI or DMA) | 3.5 µs of a 40 µs control period spent waiting on SPI |
| Bus capacitance / braking path sized for regeneration | Rotor energy vs bus energy |
| Probe-friendly test points: switch nodes, shunts, gates with ground next to each, wider spacing | Gate and switch-node pads are 1.3 mm apart — unsafe to probe by hand while powered |
| 5 V converter: fixed-frequency mode or more output capacitance, if anything sensitive hangs on +5V | ~100 mV p-p light-load ripple (A3) |

## Open items

1. **Re-identify the loop resistance in firmware** (winding 18 mΩ + bridge path) and update the current-loop / observer constants.
2. Phases B and C, 12 V / 24 V points; undershoot at the driver IC's own pins and at higher current / bus voltage.
3. Back-EMF capture while coasting (motor flux constant independent of the current sense).
4. Gate driver over-current trip point and latency; 10 A thermal hold; regeneration step; shorter dead-time (all supervised).
5. Not possible on this bench: efficiency under shaft load, bus-capacitor ripple at full power, high-side gate amplitude
   (needs a differential probe), EMC.
