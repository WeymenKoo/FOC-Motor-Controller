# Rev 1 power-stage characterization — no encoder, no mechanical load

**Purpose:** measure what the firmware team must design around (a written safety envelope) and collect the evidence for Rev B.
**Equipment:** Rigol DHO804 (4 ch, 10x passive probes, ground springs), Korad KA3005P (30 V / 5 A), DMM (10 A range, K-type
thermocouple), board NTC. Motor: T-Motor MN601-S, used as a **stationary inductive load** — a DC current vector holds the rotor
still (no shaft load, no fixture), and its windings (Ld 7.9 / Lq 11 µH, R 98 mΩ/phase) are the inductor for switching tests.
**Not covered (separate project):** shaft-load efficiency, sustained regeneration, torque under encoder feedback, EMC.

Why this works without a load: phase current is not the supply current. A 10 A DC vector needs only ~1.5 V across the windings
(1.5 × 98 mΩ × 10 A), ~15 W, i.e. ~0.5 A from a 30 V supply. The bridge still hard-switches 30 V at 10 A every period.

## 0. Setup

- USB: **UART (CP2102) + scope + PSU** plugged in; ST-Link swapped in only to flash. Everything below phase F runs on the
  firmware already on the board (0.6.1+sl: PWM_TEST, SL_POSITION hold up to 5 A, HFI_SCAN, protections, telemetry).
- Scope: SCPI over USB (USB-TMC, pyvisa-py). Every capture is saved as
  raw CSV/NPZ + screenshot + the settings and board telemetry at that moment (`Testing/Bench/char/<test>/<timestamp>/`).
- PSU: KA3005P over its USB serial (set V/I, read V/I). Its readback (±1 %) is cross-checked against the DMM once.
- **E-stop on Rev 1 is the PSU output switch** (no hardware E-stop input; PC3/BKIN2 follows DRV_ENABLE). The PSU's current limit
  is the second line; the firmware's ISR over-current trip (`p_i_peak`, ≤ 7 A cap in the sensorless modes) the third.
- Probe safety with passive probes: every probe ground is the board's GND (= PSU negative). Measure **only** ground-referenced
  nodes directly (switch nodes, low-side Vgs, shunts, SOx, rails). High-side Vgs = math (GHx − SHx) with two probes — timing
  only, amplitude is not trustworthy (common-mode error of two 10x probes). A differential probe is a Rev-B-test wish.

## Energy tiers (who runs what)

| Tier | Limits | Who |
|---|---|---|
| **L** | bus ≤ 30 V, phase current ≤ 3 A, ≤ 60 s per run, rotor only snaps to the hold angle | Claude, unattended |
| **M** | phase current 3–5 A, thermal soaks up to 10 min, deliberate decel steps at ≤ 1000 rpm | Claude **asks first**, user in the room |
| **H** | phase current > 5 A (firmware cap change), DRV8323 OCP trip tests, dead-time / IDRIVE changes, spinning > 1000 rpm | **user supervises**, motor held down |

## Pre-test checklist

- [ ] Board powered from the KA3005P only; PSU limit set for the tier (L: 1 A, M: 2 A, H: as planned).
- [ ] Motor phase leads tight in their terminals (a loose lead at 10 A arcs/heats); motor resting flat (it will twitch at ALIGN).
- [ ] Thermocouple taped to the hottest FET (low side of phase A first) with Kapton; DMM logging or photographed per minute.
- [ ] Scope probe grounds on the board's GND test point near the bridge, ground springs on switch-node captures.
- [ ] `p_ov_limit` / `p_uv_limit` set in RAM for the bus under test (flash still holds 12 V protections — the board faults at boot on 30 V).
- [ ] Nothing saved to flash during characterization (`SAVE` never sent).

## Phases

### A. Supply, rails and measurement chain (tier L)

| # | Test | Method | Output for firmware / Rev B |
|---|---|---|---|
| A1 | Bus-voltage reading accuracy | PSU 8 → 30 V in 2 V steps; `vbat_voltage` vs DMM at the bus caps | gain/offset of `p_vbat_div`; error band used by OV/UV and the coast-safe speed |
| A2 | UV / OV trip thresholds and latency | set `p_uv_limit` 20, ramp PSU down slowly; set `p_ov_limit` 25, ramp up; scope bus + phase A | actual trip voltage vs setting; time from threshold to outputs off (the 100 Hz slow loop: expect ≤ 10–20 ms) |
| A3 | Rails at idle and switching | 3V3, 5V/12V (if present), DRV VCP/VGLS, LMR36520 SW node; DC + ripple; idle, then PWM_TEST 50 % open, then 3 A hold | ripple and droop under switching; analog rail coupling (Rev-1 known: analog shares digital 3V3) |
| A4 | CSA offset, noise, drift | `RUN CSA_CAL` ×10 at 12/24/30 V, cold vs warm | offset spread, noise floor → minimum resolvable current (already: 1619–1649 mV, 11–14 mA rms) |
| A5 | CSA gain vs DMM | DMM (10 A) in series with phase A; SL_POSITION hold 0.5 → 3 A (tier L) → 5 A (M) | gain error per channel, linearity, phase C sign; calibration constants |

### B. Switching under current (tier L → M)

The bridge switching a known DC phase current: SL_POSITION hold at angle 0 puts +I on phase A, −I/2 on B and C, so phase A
switch node commutates +I (one edge hard, one soft) and B/C −I/2 (the opposite). Moving the hold angle by 180° swaps them.

| # | Test | Method | Output |
|---|---|---|---|
| B1 | Switch-node edges vs current | phase A SW node (spring), shunt A, SOA; hold 0, 1, 3 A (L), 5 A (M); 12/24/30 V | dV/dt, overshoot, ring frequency/decay vs I and V → **max bus voltage with margin** to the 100 V FETs and the DRV8323's ratings (60 V recommended VM; check SHx/VM abs-max in the datasheet before quoting a margin) |
| B2 | Dead-time as the bridge sees it | same captures: plateau between INL off and the SW edge (and INH off → edge) for +I and −I | real dead-time (MCU 200 ns + DRV insertion) and the **voltage error vs current** — the number that limits HFI and torque linearity |
| B3 | Low-side Vgs + Miller | GLA–GND, with B1 | gate drive margin, Miller bump, dV/dt-induced turn-on risk at 30 V → `p_drv_idrive` default |
| B4 | IDRIVE sweep | `p_drv_idrive` 3 settings (set while DISARMED), repeat B1 at 3 A / 30 V | edge speed vs overshoot trade-off → recommended IDRIVE for firmware, and for Rev B gate resistors |
| B5 | Bus ripple at the caps | AC-coupled bus at the bulk cap, hold 3 A (L) / 5 A (M) at 25 kHz | ripple voltage → cap ripple-current estimate → Rev B bulk/ceramic sizing |
| B6 | High-side gate timing | math GHA − SHA (timing only) | INH→edge delays; consistency with B2 |

### C. Current-sense validity vs duty (tier L)

| # | Test | Method | Output |
|---|---|---|---|
| C1 | Sample window | PWM_TEST with a small differential duty (≈ 1–2 A) shifted to a high common-mode duty: 50 → 80 → 90 → 95 → 98 % | current-reading error vs low-side on-time; SOx settling after the edge → **max duty / modulation index** the firmware may use with 3-shunt sensing |
| C2 | Sample instant | scope SOA with the PWM centre (CH4 trigger on phase SW); confirm the ADC samples in the flat part | ADC trigger offset recommendation |
| C3 | CSA under ringing | C1 at 30 V vs 12 V | whether switching noise reaches the reading (Rev B layout / filter) |

### D. Protection and turn-off timing (tier L)

| # | Test | Method | Output |
|---|---|---|---|
| D1 | Firmware OC trip | hold 2 A, then set `p_i_peak` 1.5 A live → trip; scope SW node + SOA | trip latency (current crosses → outputs off), measured trip current vs setting |
| D2 | Watchdog / dead-man | hold 1 A, stop the heartbeat; scope SW node | heartbeat-loss → outputs off time (expect ≈ `p_wd_timeout`) |
| D3 | STOP / DISARM path | hold 1 A, STOP; scope | command → outputs off |
| D4 | Coast behaviour | after D1–D3 the windings freewheel: scope bus + SW node | bus kick at turn-off with current flowing (energy in L: ½ L I², small) |
| D5 | nFAULT → break | DRV fault injection needs tier H (VDS OCP) — see F2 | hardware break latency |

### E. Thermal (tier M)

| # | Test | Method | Output |
|---|---|---|---|
| E1 | Steady thermal rise | SL_POSITION hold 3 A → 5 A, 10 min each at 30 V; thermocouple on hottest FET, board NTC, motor case; PSU V·I logged | °C/W board→ambient, thermal time constant, NTC vs FET offset → **continuous current derating** and the firmware's `p_ot_limit` margin (extrapolated to 10 A, labelled as extrapolation) |
| E2 | Loss split | PSU power − 1.5 R I² (copper) − idle | switching + conduction loss vs I → efficiency estimate for Rev B FET choice |

### F. Supervised (tier H, motor held down, firmware cap change, each with its own go)

| # | Test | Why it is H | Output |
|---|---|---|---|
| F1 | Hold 7 → 10 A (needs `APP_SL_HW_I_MAX_A` raised) | 10 A design current; heats FETs/shunts/motor | thermal at design current (replaces the E1 extrapolation) |
| F2 | DRV8323 VDS OCP trip | lowest `p_drv_vds_lvl` trips at ~15–20 A | real OCP current vs setting, nFAULT → MOE-off latency (hardware break) |
| F3 | Regen bus rise | spin 500–1000 rpm, one controlled decel step with `p_ov_limit` low | bus rise per joule; **why motoring-only**: rotor energy at 1000 rpm ≈ 0.44 J vs ~0.16 J in the ~350 µF bus at 30 V — full regeneration could push the bus toward ~50 V |
| F4 | Shorter dead-time | MCU DTG / DRV DEAD_TIME down one step, shoot-through check on the shunt | whether the dead-time error (HFI blocker) can shrink safely |

## Measurement log (one table per test; record numbers as measured)

| Test | Condition (V, I, setting) | Quantity | Expected | Measured | Instrument / file | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |

**Unexplained list** (do not round away): R 98 mΩ measured vs 39 mΩ datasheet; KV 284 measured vs 320; HFI −18° systematic offset.

## Findings so far (as findings)

1. Switch node at 12 V, open outputs: edges/overshoot captured and correlated with LTspice (Simulation/02). Not yet under current or at 30 V.
2. Hot-plug at 30 V: correlated with LTspice (Simulation/01).
3. CSA offsets 1619–1649 mV, noise 11–14 mA rms, stable over today's 10+ calibrations; DRV CAL mode not usable on Rev 1.
4. The control ISR runs 30–32 µs of 40 µs in the sensorless modes (encoder read skipped): ~8 µs headroom; the encoder SPI read costs 3.5 µs of busy-wait at 5.3 MHz.
5. PWM latency is 1–2 periods (I/f needed 2 periods of lead; HFI demodulation confirmed the range).
6. Dead-time voltage error (~0.12 V at 12 V, ~0.3 V at 30 V, estimated) is comparable to a usable HFI injection on this 9 µH motor → closed-loop HFI under torque fails (host sim).
7. Bus capacitance holds far less energy than the rotor at speed → stops must coast; the firmware is motoring-only.

## Rev B wishes (each tied to a finding)

| Wish | From |
|---|---|
| Hardware E-stop input independent of DRV_ENABLE | Rev-1 PC3/BKIN2 quirk; E-stop is the PSU switch |
| Faster SPI1 or DMA for the encoder (no ISR busy-wait) | finding 4 |
| Shorter / tunable dead-time path, verified (or gate resistors for faster edges) | finding 6, test B2/F4 |
| Separate analog 3V3 (VDDA) rail | Rev-1 known issue, test A3 |
| Bus capacitance / brake resistor (or clamp) sized for regeneration | finding 7, test F3 |
| Debug test points: switch nodes, shunts, SOx, GND spring points; one spare GPIO as a scope trigger | this plan (probing effort) |
| Differential-probe-friendly high-side gate test points | B6 limitations |
