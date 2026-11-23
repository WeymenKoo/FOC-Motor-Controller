# Characterization log — Rev 1 (CHARACTERIZATION_PLAN.md)

Bench 2026-11-22. KA3005P 30.0 V, DHO804 (70 MHz, 10x passive, hand-held), MN601-S as a stationary inductive load,
firmware 0.6.1+sl (bench build). Raw data per test under `char/<test>/<timestamp>/` (npz + screenshots + json).
Probe points: `PROBE_MAP.png`. Every probe change with the PSU output off (user rule).

## A1 — bus-voltage reading (no probes) · `char/A12/20261122_170402`
| PSU (V) | 30 | 24 | 18 | 12 | 8 |
|---|---|---|---|---|---|
| board `vbat_voltage` (V) | 29.940 | 23.929 | 17.951 | 11.953 | 7.964 |
| error | −0.20 % | −0.30 % | −0.27 % | −0.39 % | −0.45 % |
Fit: board = 0.99894 × PSU − 0.035 V. Noise 3–18 mV rms. No up/down hysteresis. Reference = PSU readback (±1 %); DMM cross-check pending.

## A2 — OV / UV thresholds (no probes)
| Limit | Tripped at (board / PSU) | Step |
|---|---|---|
| OV 25 V (DISARMED) | 25.04 V / 25.10 V | 0.1 V, 0.45 s |
| UV 20 V (ARMED idle) | 19.93 V / 20.00 V | 0.1 V, 0.45 s |
Idle supply current 13 mA @ 30 V, 40 mA @ 8 V.

## B1 — phase A switch node vs current, 30 V · `char/B1/20261122_171957`
CH1 H1 (phase A) ref R22-GND (shunt A ground end); CH2 TP20 (SOA). SL_POSITION hold at angle 0 (+I on phase A).
| Hold | Edge | t10–90 | dV/dt | Overshoot | Ring | Note |
|---|---|---|---|---|---|---|
| 1 A | rising (hard) | 15.4 ns | 1.6 V/ns | +0.61 V | 128 MHz | diode plateau −0.95 V for 189 ns before |
| 1 A | falling (soft) | 129 ns | 0.19 V/ns | +0.16 V | 88 MHz | current-driven |
| 3 A | rising (hard) | 7.9 ns | 3.1 V/ns | +0.93 V (peak 30.48 V on 29.95 V) | 105 MHz | diode plateau −1.03 V for 203 ns |
| 3 A | falling (soft) | 38 ns | 0.64 V/ns | +0.58 V | 146 MHz | undershoot −1.39 V |
- Dead-time at the switch node 189–213 ns (MCU DTG 200 ns; the DRV8323 adds ~none).
- Effective switch-node capacitance from the soft edge: I·t/ΔV ≈ 5 nF (1 A: 129 ns, 3 A: 38 ns over 24 V).
- Dead-time voltage error ≈ 2 × 200 ns / 40 µs × Vbus ≈ 0.3 V at 30 V for |I| ≳ 1 A; smaller and current-dependent below (soft edge longer than the dead time).
- **Limits of the measurement:** 70 MHz scope (~5 ns own rise time) → the 8 ns edge and the 100–150 MHz ringing are under-reported; overshoot values are lower bounds. CH2 (SOA) shows ±0.1 V for ~150 ns after each hard edge (board + ground-loop).

## B4 — IDRIVE sweep, 3 A, 30 V · `char/B4/20261122_172801`
DRV8323 registers read back: r3/r4 = 0x3FF/0x7FF (code 15), 0x3BB/0x7BB (11), 0x377/0x777 (7).
| Code (src/sink) | Rise t10–90 | dV/dt | Overshoot | Fall | Dead time |
|---|---|---|---|---|---|
| 15 (1000/2000 mA, default) | 7.8 ns | 3.14 V/ns | +0.97 V | 38.1 ns | 213 ns |
| 11 (440/880 mA) | 15.9 ns | 1.53 V/ns | +0.61 V | 39.2 ns | 200 ns |
| 7 (190/380 mA) | 25.5 ns | 0.96 V/ns | +0.11 V | 42.6 ns | 209 ns |
Hard-edge energy ½VIt: 0.35 → 1.15 µJ per edge at 3 A (≈ 9 → 29 mW per leg at 25 kHz). Soft edge and dead time unaffected.
**Recommendation (provisional, re-check at higher current/thermal):** IDRIVE 11 as the firmware default.

## D1 — firmware over-current trip · `char/D1C1/20261122_173504`
PWM_TEST 50/50/50 → 53/50/50 at 30 V (phase A current ramps ~45 A/ms), `p_i_peak` 2.5 A.
| Time | Phase A current (SOA plateau, low-side window) |
|---|---|
| ADC sample ~9 µs | 1.98 A (no trip) |
| ADC sample ~49 µs | 3.60 A → trip |
| 68.4 µs | last switching edge (outputs off), ~3.7 A |
- Sample → outputs off: **~19 µs**. Worst-case detection latency ≈ 40 µs (sample interval) + 19 µs ≈ **60 µs**; overshoot = di/dt × ~60 µs.
- Fault path verified: `@EV FAULT code=OVERCURRENT`, `pwm_off_reason` FAULT, fault clears normally.
- **Envelope:** firmware OC is an overload protection, not short-circuit protection (a 56 V phase-phase short through ~19 µH rises ~3 A/µs). Short-circuit protection = DRV8323 VDS OCP → verify in F2.
- Scope vs ADC at SOA idle: 1.651 V vs 1.649 V (2 mV).

## C1 — current-reading validity vs low-side on-time · `char/D1C1/20261122_173504`
PWM_TEST (cm+0.8, cm, cm) %, open loop (~1–1.7 A; the current itself varies with duty because 0.8 % ≈ the dead-time drop).
| Common mode | A low-side window | ia | ib | ic | ia+ib+ic |
|---|---|---|---|---|---|
| 50 % | 19.7 µs | +1.237 | −0.612 | −0.604 | +0.020 |
| 80 % | 7.7 µs | +1.328 | −0.645 | −0.623 | +0.060 |
| 90 % | 3.7 µs | +1.057 | −0.493 | −0.506 | +0.058 |
| 95 % | 1.7 µs | +1.726 | −0.802 | **−0.399** | **+0.525** |
| 97 % | 0.9 µs | +1.561 | −0.830 | **−0.183** | +0.549 |
| 98 % | 0.5 µs | +1.283 | −0.610 | **−0.074** | +0.598 |
| 98.8 % | 0.16 µs | +0.550 | −0.414 | −0.044 | +0.092 (all wrong) |
- **Phase C's reading fails first** (window < ~2 µs), although B runs the same duty and stays consistent; A and B hold to ~0.5 µs.
  Phase C's shunt is the one wired reversed on Rev 1 (SNC/SPC swapped) — suspected cause, to confirm on SOC.
- **Envelope (provisional):** keep every phase's low-side window ≥ ~2 µs (duty ≤ 95 %) when using all three shunts, or
  reconstruct the highest-duty phase from the other two (A/B valid to ~0.5 µs).

## C1b — phase C failure reproduced and explained · `char/C1b/20261122_173922`
Same PWM_TEST pattern; board readings (scope CH2 clipped — hand-held contact; the ADC data does not depend on it):
| C low-side window | 20 µs | 4.0 µs | 2.0 µs | 1.2 µs | 0.8 µs |
|---|---|---|---|---|---|
| ia + ib + ic (A) | −0.017 | +0.004 | +0.487 | +0.604 | +0.593 |
| ic (true ≈ −0.8 at 2.0 µs) | −0.601 | −0.500 | −0.389 | −0.140 | −0.068 |

**Root cause: ADC sampling order, not the reversed shunt.** Filters are identical on all three phases (56 Ω + 2.2 nF,
τ 123 ns). SOA → ADC2 (PB11, rank 1); SOB → ADC1 rank 1 (PB12); **SOC → ADC1 rank 2 (PB14)**. ADC clock 170/4 = 42.5 MHz,
injected sample 24.5 + conversion 12.5 cycles = 0.87 µs per rank: A and B are sampled 0–0.58 µs after the window centre,
**C 0.87–1.45 µs after it**. C is therefore only valid when its low-side window ≥ ~3 µs (2 × 1.45 µs + filter settling) —
exactly the measured transition (OK at 3.7–4 µs, failing at 2 µs).

Firmware options (no hardware change): reconstruct ic = −(ia + ib) (A, B simultaneous and valid to ~1.2 µs windows); or
shorten the injected sample time (12.5 cycles → C ends ~0.9 µs after centre); or move the ADC trigger ~0.7 µs before the
centre so the samples straddle it. Rev B: put all three SOx on ADC12 shared inputs so the firmware can sample the two phases
with the longest low-side windows simultaneously every period (sector-based selection). Confirmation test (no probes,
needs a reflash): swap SOB/SOC ranks → phase B should then fail instead of C.

**Envelope (current sensing):** with the present ADC setup, keep phase C's low-side window ≥ 3 µs (its duty ≤ ~92 %) or
reconstruct C from A and B; A/B valid to ~1.2 µs windows (duty ≤ ~97 %).

## B5 — bus at the input terminals (H8 / H9) · `char/B5/20261122_174829`
CH1 H8 (+VPROT) ref H9 (GND), AC-coupled after a DC check (29.33 V); CH2 phase A switch node (timing). SL_POSITION hold, 30 V.
| Hold | Ripple between edges (±1 µs excluded) | Edge spike | > 100 mV for |
|---|---|---|---|
| 1 A | 21 mV p-p (2.6 mV rms) | +310 / −299 mV | ~17 ns |
| 3 A | 20 mV p-p (2.5 mV rms) | +446 / −404 mV | ~23 ns |
- Spikes at every hard edge, scaling with current (commutation-loop L·di/dt; terminal measurement includes the trace from the caps). 
- **Gap:** a static hold draws almost no net bus current (A's current returns through B/C high sides), so this is NOT the capacitor
  ripple under motoring. Bulk-cap ripple current needs net power flow (speed or load) — out of scope without a load.

## B5b — bus under a real (inertial + friction) load: sensorless spin · `char/B5b/20261122_180422` (+ runs 175710, 175911, 180144)
SENSORLESS closed loop, 30 V, PSU limit 2 A. CH1 H8/H9 AC 100 mV/div (set once, 3 s settle), CH2 phase A (trigger).
| Speed | PSU current | Input power | Bus ripple between edges p-p / rms | Edge spikes p-p | iq / id |
|---|---|---|---|---|---|
| 1000 rpm | 0.203 A | 6.1 W | 58 mV / 6.1 mV | 173 mV | 0.55 / 0.42 A |
| 2000 rpm | 0.442 A | 13.3 W | 67 mV / 11.3 mV | 108 mV | 0.20 / 0.65 A |
| 2635 rpm (coasting) | 0.606 A | 18.2 W | 79 mV / 11.1 mV | 201 mV | 0.26 / 0.09 A |
| 3000 rpm | 0.704 A | 21.1 W | 79 mV / 12.3 mV | 281 mV | ≈0 / 0.87 A |
- PSU current repeatable to ±1 % over four runs. Load = cogging + friction + windage of the unloaded MN601-S.
- Step 1000 → 3000 rpm: iq ~1.0 A while accelerating at the firmware cap (1000 rpm/s); PSU 0.20 → 0.67 A. Scope capture of the
  step at 50 ms/div returned 2 points (DHO804 readout at slow timebases) — not captured; board/PSU logs only.
- **Firmware finding:** the regen guard ("never lower the speed reference while bus > 0.9 × p_ov_limit") blocked deceleration
  with p_ov_limit 33 V on a 30 V bus (0.9 × 33 = 29.7 V ≈ bus). Envelope: **p_ov_limit ≥ ~1.15 × operating bus**.
- id up to ~0.9 A at speed although commanded 0 → observer angle offset at high speed (consistent with the host sim's 1.5–2
  period delay uncertainty); costs efficiency, worth a `APP_SL_VDELAY_FRAC` tune later.
- **Scope lessons (in instruments.py):** STOP must hold 0.4 s after a reconfiguration; never switch a channel DC→AC on a 30 V
  signal right before a fine-scale capture (front-end overdrive needs seconds); fine-scale DC offsets of ~30 V are out of range.

## A3 — +3V3 and +5V rails · `char/A3/20261122_181829`
CH1 TP9 (+3V3) ref C41 GND; CH2 TP7 (+5V) ref C10 GND; AC 10 mV/div; random-time captures (:SINGle + :TFORce).
| State | +3V3 p-p / rms (full BW) | +3V3 (20 MHz) | +5V p-p / rms (full BW) | +5V (20 MHz) |
|---|---|---|---|---|
| Noise floor (board unpowered, probes in place) | 14.6 / 2.4 mV | 7.4 / 1.3 mV | 2.9 / 0.6 mV | 2.2 / 0.4 mV |
| Idle (DISARMED) | 15.1 / 2.7 mV | 15.5 / 2.4 mV | 117 / 9.9 mV | 54 / 5.2 mV |
| Armed (DRV awake, not switching) | 15.1 / 2.5 mV | 14.0 / 2.3 mV | 112 / 9.8 mV | 36 / 4.9 mV |
| Spinning 2000 rpm (13 W) | 23.0 / 3.2 mV | 17.3 / 3.0 mV | 102 / 8.9 mV | 103 / 9.4 mV |
- **+3V3 is at the noise floor** at idle; motor switching adds ~1 mV rms. (Rev-1 concern "analog shares digital 3V3": no
  measurable switching pickup on the rail at 13 W; the ADC-side effect is what matters — C1 data.)
- **+5V: ~100 mV p-p at 120–160 kHz (+ 4.1 MHz edge content), same at idle and spinning** → the 5 V converter's light-load
  (pulse-skipping) ripple, not the bridge. Board load ~12 mA. Check against what +5V feeds; Rev B: FPWM / more output C if it matters.
- DC: scope +3V3 = 3.243–3.252 V, +5V = 5.011–5.022 V; MCU VDDA reads 3.299–3.301 V. **Unexplained:** ~50 mV between TP9 and
  the MCU's VDDA measurement (probe/ground offset or a real drop) — DMM check pending.
- Scope lesson: `:SINGle` with AUTO sweep can return the previous record; noise/ripple captures use NORMal + `:TFORce`.

## DMM spot checks (board idle, PSU 30.00 V) · `char/DMM/dmm_points.csv`
| Point | DMM | Board | Scope (earlier) | Conclusion |
|---|---|---|---|---|
| Bus H8/H9 | 30.04 V | vbat 29.933 V; PSU readback 30.000 V | 29.33–29.44 V (10 V/div) | PSU readback good to −0.13 %; board reads **−0.107 V (−0.36 %)** → `p_vbat_div` × 1.0036 would null it |
| +3V3 TP9 | 3.295 V | VDDA 3.304 V | 3.243–3.252 V | **No real drop**: DMM and MCU agree within 9 mV; the A3 "50 mV" was a scope DC offset (~1.5 %) — removed from the unexplained list |
| +5V TP7 | 5.018 V | — | 5.011–5.022 V | agrees |

## E1 — thermal, SL_POSITION hold (rotor parked), 30 V · `char/E1/20261122_182816` (log.csv + tc_readings.csv)
K-type thermocouple (user DMM) taped to the phase A low-side FET case; board NTC from telemetry; PSU V·I.
| Hold | Time | FET case | Board NTC | PSU | Slope at end |
|---|---|---|---|---|---|
| start | — | 26.5 °C | 27.4 °C | — | — |
| 3 A (ia 3.00, ib/ic −1.5) | 10 min | 34.0 °C (+7.5) | 36.7 °C (+9.3) | 1.80 W | NTC +0.12 °C/min |
| 5 A (ia 5.01, ib/ic −2.5) | 10 min | 36.7 °C (+10.2) | 38.2 °C (+10.8) | 2.52 W | NTC +0.09 °C/min |
- One TC reading (32.0 °C at 18:48) rejected as an outlier (−4.3 °C step while the NTC was flat; next reading 36.7 °C).
- Fit rise = a + b·I² (FET case): **a ≈ 6.0 °C** (current-independent: gate drive, switching, regulators), **b ≈ 0.17 °C/A²**.
  Extrapolation (2 points, case not junction, labelled as such): 10 A DC in one phase ≈ +23 °C, 15 A ≈ +44 °C. F1 (10 A hold) to confirm.
- Board NTC reads 1.5–2 °C above the phase A FET case: the 80 °C `p_ot_limit` is a fair proxy for FET case temperature.
- **Unexplained (energy balance):** at 5 A the reported phase currents imply R × (ia² + ib² + ic²) = 0.098 × (25 + 6.25 + 6.25) = **3.7 W** of motor
  copper at R = 98 mΩ/phase, but the PSU delivered **2.52 W total**. Candidates: PSU current readback (10 mA = 0.3 W resolution, accuracy
  unverified), CSA gain over-reading, or a lower real phase R (datasheet 39 mΩ). → A5 (CSA gain vs DMM) and a DMM on the supply current.

## A5 (supply side) — DMM (10 A range) in series with the PSU + lead · `char/A5/20261122_185408` (+ dmm.csv)
| Stage | DMM | PSU readback | Board ia / ib / ic |
|---|---|---|---|
| idle (DISARMED) | 13 mA | 12 mA | — |
| armed (DRV awake) | 25 mA | 24 mA | — |
| PWM 50/50/50, zero current | 52 mA | 48 mA | ~0 |
| hold "1 A" | 48 mA | 45 mA | +0.804 / −0.394 / −0.390 |
| hold "3 A" | 61 mA | 54 mA | +2.396 / −1.207 / −1.198 |
| hold "5 A" | 84 mA | 76 mA | +4.014 / −1.989 / −1.983 |
- PSU current readback 1–8 mA (5–10 %) low vs the DMM. Overheads at 30 V: MCU+regulators 0.39 W, DRV awake +0.36 W,
  switching at zero current +0.81 W (gate charge + switch-node capacitance at 25 kHz).
- **Energy balance (differences, so overheads cancel):** 1 → 5 A: ΔP = 1.08 W for ΔΣi² = 23.05 A² → **R_eff ≈ 47 mΩ/phase**
  (incl. FET + shunt ≈ 5 mΩ); 1 → 3 A: ≈ 51 mΩ. Inconsistent with the 98 mΩ/phase used so far. Either (H1) motor R ≈ 40–45 mΩ
  (datasheet 39) and the 98 mΩ included lead/connector resistance, or (H2) R = 98 mΩ and the CSA over-reads by ~1.45×.
  **Must be resolved before the current numbers in this log are trusted for the envelope** → DMM in series with a phase lead.
- **Unexplained:** this run's holds settled at 0.80 × command at all three currents (B1/E1 reached 1.00×). Not yet understood.
