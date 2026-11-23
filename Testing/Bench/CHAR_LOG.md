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

## A5b — shunt voltage vs SOA with the scope · `char/A5b/20261122_194728` — INCONCLUSIVE
CH1 R22-S ref R22-GND (5 mV/div, 20 MHz), CH2 TP20 (SOA) ref J7-5. Holds reached the full command (ia 3.017 / 5.022 A).
| Hold | V_shunt step (on − off window) | I if R = 3.000 mΩ | SOA step | Apparent gain |
|---|---|---|---|---|
| 3 A | −10.70 mV | 3.57 A | 176.6 mV | 16.5 V/V |
| 5 A | −17.14 mV | 5.71 A | 296.5 mV | 17.3 V/V |
**Not usable as a calibration:** with the high side on (zero shunt current) CH1 sits ~6 mV above its idle level — a ground-loop
error (two probe grounds + USB grounds; bridge return current in the ground plane) of the same size as the signal. The apparent
gain is uncertain by roughly ±30 %; neither "CSA correct, motor ~40 mΩ" nor "CSA over-reads 1.45×" is excluded.
→ Repeat with a floating instrument: DMM (mV DC) across the shunt during a static hold: V_avg = −I · R · (shunt conduction
fraction ≈ 1 − duty_a + 0.5 %), no ground loop. Or measure the motor's line-line resistance directly (4-wire, PSU in CC + DMM).

## A5c — floating DMM across the phase A shunt · `char/A5c/20261122_195039` — current-sense scale CONFIRMED
DMM (mV DC, battery-powered: no ground loop) on R22-S / R22-GND during SL_POSITION holds; no scope on the board.
Expected V_avg = −ia · 3 mΩ · (1 − duty_a + t_dead/T).
| Hold | Board ia | duty_a | Shunt conducts | Expected | DMM | Ratio |
|---|---|---|---|---|---|---|
| 5 A | 4.999 A | 50.81 % | 49.69 % | −7.45 mV | **−7.57 mV** | 1.016 |
| 3 A | 3.004 A | 50.66 % | 49.84 % | −4.49 mV | **−4.52 mV** | 1.007 |
- **The board's phase-current measurement is correct within 1–2 %** (shunt tolerance 1 % + DMM). The "CSA over-reads 1.45×"
  hypothesis is rejected; all current values in this log stand.
- Therefore the energy balance (A5) means **the motor's phase resistance is ~40–60 mΩ, not 98 mΩ** (datasheet 39 mΩ; the
  balance is ±30 %: switching loss falls as the soft edge completes inside the dead time). Likely causes of the earlier 98 mΩ:
  the ID_R test runs at ≤ 1 A, where the dead-time voltage error still varies with current (B1) and adds to the V–I slope; the
  DC cross-check included the supply leads. **Firmware: `p_phase_r` (0.098 Ω) is suspect** — it sets the current-loop Ki and
  the observer's R·i term. → Direct 4-wire measurement of the motor (PSU in CC + DMM at the pins) to pin the value.
- Lesson: millivolt measurements on a switching board need a floating instrument (A5b's scope attempt was ±30 %).

## No-probe batch (UART + PSU only) · `char/NP/20261122_195422/results.json`

### CSA offsets vs bus voltage (8 calibrations each; ARM → CSA_CAL → DISARM)
| Bus | Offset A | Offset B | Offset C | Cal noise A / B / C |
|---|---|---|---|---|
| 12 V | 1648.04 ± 0.38 mV | 1631.22 ± 0.35 mV | 1620.72 ± 0.27 mV | 14.1 / 13.0 / 11.5 mA rms |
| 18 V | 1648.17 ± 0.55 | 1631.38 ± 0.56 | 1620.76 ± 0.69 | 14.2 / 12.8 / 11.6 |
| 24 V | 1648.35 ± 1.01 | 1631.59 ± 1.11 | 1621.09 ± 0.98 | 13.8 / 12.5 / 11.7 |
| 30 V | 1648.24 ± 0.65 | 1631.37 ± 0.57 | 1621.03 ± 0.54 | 13.7 / 12.5 / 11.5 |
Offsets move < 0.4 mV (< 7 mA) from 12 to 30 V; repeatability ≤ 1.1 mV (≤ 18 mA) between wake cycles. Channel spread A–C 27 mV.

### Reported phase currents, bridge at zero current (120 samples each)
| State | ia | ib | ic |
|---|---|---|---|
| Armed, not switching | +0.013 ± 0.024 A | +0.012 ± 0.022 | −0.014 ± 0.019 |
| PWM 50 / 50 / 50 % | +0.009 ± 0.024 | −0.009 ± 0.021 | −0.006 ± 0.023 |
| PWM 90 / 90 / 90 % | −0.015 ± 0.022 | +0.052 ± 0.023 | −0.011 ± 0.026 |
| PWM 96 / 96 / 96 % | +0.066 ± 0.027 | −0.039 ± 0.023 | −0.022 ± 0.018 |
**Switching adds no measurable noise** (20–27 mA rms per sample in every state). Mean shifts of up to ±66 mA appear at 90–96 %
duty (short low-side windows). ISR peak 20.4 µs, 0 overruns.

### Stop-path timing (PWM_TEST running, outputs verified off afterwards)
| Path | Result |
|---|---|
| STOP → ACK (host round trip, n = 8) | 23 ms mean, 11–44 ms (USB-serial latency dominates) |
| DISARM → ACK (n = 8) | 21 ms mean, 12–31 ms |
| Heartbeat lost → DISARMED (`p_wd_timeout` 500 ms, n = 5) | firmware `age_ms` 501 every time; outputs off, state DISARMED |

### Sensorless start reliability (2 A start, hand-over 600 rpm, target 1000 rpm, 30 V)
**50 / 50 starts reached closed loop at 1000 ± 30 rpm, no faults.** RUN → CLOSED: 2.449 ± 0.011 s (2.43–2.47 s).
Flux estimate at hand-over 1.036 ± 0.005 (1.029–1.045).

### Brown-out sweep (DISARMED, PSU 30 → 4 → 30 V in 1 V steps)
| Bus | Supply current | Board |
|---|---|---|
| 30 V | 13 mA | alive, VDDA 3.299 V |
| 12 V | 27 mA | alive |
| 6 V | 53 mA | alive, VDDA still 3.299 V |
| 5 V | 64 mA | alive (falling), **dead on the way back up** (36 mA, no answer) |
| 4 V | 3 mA | off |
Constant-power input (regulators): current rises as the bus falls. Runs down to 5 V, restarts between 5 and 6 V (≈ 1 V hysteresis).
VDDA holds 3.30 V down to 5 V. After recovery: `reset_cause` = power-on, parameters reloaded from flash, and the 12 V-era
over-voltage limit faults the board again above 14 V — expected, no latch-up, no corrupted state.

## Motor winding resistance, 4-wire · `char/MOTOR_R/motor_r.csv`
Motor unplugged from the board. KA3005P in constant current (3 V compliance) through two motor pins; DMM (mV DC) directly on
the same pins. Room temperature, motor slightly warm from earlier runs.
| Pins | DMM @ 1.999 A | DMM @ 2.999 A | Line-line | PSU terminal reading (incl. its leads) |
|---|---|---|---|---|
| 1–2 | 71.7 mV | 107.4 mV | 35.84 mΩ | 180–182 mΩ |
| 2–3 | 72.5 mV | 108.8 mV | 36.27 mΩ | 164–170 mΩ |
| 1–3 | 71.4 mV | 107.2 mV | 35.73 mΩ | 145–149 mΩ |
- **Phase resistances (wye): 17.65 / 18.19 / 18.08 mΩ, mean 17.97 mΩ**, balanced ±1.7 %, linear 2 → 3 A.
- Datasheet "39 mΩ" is therefore a line-line figure (measured 35.9 mΩ). **Resolves the long-standing "98 mΩ vs 39 mΩ" item:**
  the bench supply's leads and clips add 110–145 mΩ (they dominated the 2026-09-27 DC cross-check, 195 mΩ line-line), and the
  firmware's ID_R (≤ 1 A, 12 V) reads high because the dead-time voltage error still varies with current in that range.
- **Firmware: `p_phase_r` = 0.098 Ω is ~5.5× the winding resistance.** What the current loop sees is winding + bridge path
  (FET, shunt, traces, connector): the A5 energy balance gives ~47 mΩ effective per phase, so ~29 mΩ of path/loss on top of
  18 mΩ of copper. Re-identify with dead-time compensation or at several amps; current-loop Ki and the observer's R·i term
  follow from it.

## B1neg — phase A switch node, phase SINKING current (opposite polarity) · `char/B1neg/20261122_202142` (10 V/div), `…_201958` (5 V/div, clipped)
SL_POSITION hold rotated 180° electrical (REF POS 0.0357 turns): ia = −I, ib = ic = +I/2. CH1 H1 ref R22-GND. 30 V.
| | −1 A | −3 A |
|---|---|---|
| Falling edge (low-side turn-on, HARD) t10–90 | 6.6 ns (3.7 V/ns) | 7.3 ns (3.4 V/ns) |
| **Undershoot below ground** | **−7.8 V** | **−9.5 V** |
| Ringing | ~80–100 MHz, decays in ~80 ns | same |
| Dead-time plateau before the edge | bus + 0.65 V (high-side body diode) | bus + 0.65 V |
| Rising edge (high-side turn-on, SOFT) t10–90 | 129 ns | 35 ns |
- Soft edge and dead-time plateau mirror B1 exactly (129 / 35 ns; ±diode drop): the half-bridge is symmetric there.
- **Hard edges are asymmetric:** high-side turn-on overshoots the bus by +0.9 V (B1); low-side turn-on undershoots ground by
  −8 to −10 V, nearly independent of load current (edge-driven: node-capacitance charging / diode recovery current through
  the inductance of the low-side source path = shunt + its ground connection). Measured to the shunt's ground end; 70 MHz
  scope, so the true peak is larger.
- **DRV8323 absolute maximum (datasheet p. 11): SHx −7 V for a 200 ns transient (−5 V continuous); SPx/SNx/SLx −3 V
  transient.** The −9.5 to −10 V measured at IDRIVE 15 is **beyond the SHx rating** (measured at the H1 pad against the
  shunt's ground end, not at the IC pin, with a 70 MHz scope). IDRIVE 11 (−2.7 V) and 7 (−0.8 V) are inside it. The shunt-side
  pins were not measured. Explains the ~100 ns disturbance on SOx after each edge.
- The first capture (5 V/div) clipped at −6.85 V and showed a false "22 MHz ±5 V" ringing — scope input overdrive, discarded.
- Next: repeat at IDRIVE 11 and 7 on this polarity (a slower edge should shrink the undershoot far more than it did the
  +0.9 V overshoot). Rev B: lower-inductance shunt placement / Kelvin source return, RC snubber or gate resistor on the low side.

## B4neg — IDRIVE sweep on the low-side hard edge (phase A sinking 3 A, 30 V) · `char/B4neg/20261122_202344`
Registers read back: r3/r4 = 0x3FF/0x7FF (15), 0x3BB/0x7BB (11), 0x377/0x777 (7). CH1 10 V/div.
| IDRIVE (src/sink) | Falling edge t10–90 | dV/dt | Minimum | Undershoot below the settled level | > 1 V below for |
|---|---|---|---|---|---|
| 15 (1000/2000 mA, DRV8323 power-on default, in use) | 7.1 ns | 3.45 V/ns | −10.0 V | 9.5 V | 22.5 ns |
| 11 (440/880 mA) | 8.9 ns | 2.75 V/ns | −2.7 V | 2.1 V | 8.0 ns |
| 7 (190/380 mA) | 18.4 ns | 1.33 V/ns | −0.76 V | 0.2 V | 0 ns |
- The undershoot collapses with a modest reduction of the gate current: **IDRIVE 11 costs 1.8 ns of edge time and removes
  78 % of it; IDRIVE 7 removes it.** Together with B4 (high-side edge: overshoot 0.97 → 0.61 → 0.11 V) the trade-off is one-sided.
- **Recommendation (no longer provisional): do not run IDRIVE 15 on this layout. Default `p_drv_idrive` = 11, or 7 if the
  driver's negative-transient rating or EMI calls for it** (hard-edge loss at 3 A / 30 V: 0.35 → ~0.4 → ~0.8 µJ per edge).
  Re-check at 10 A / higher bus under supervision.

## B6 — shunt-side pins during the hard edges (phase A, 3 A, 30 V) · `char/B6/20261122_202903`
CH1 R22-S ref R22-GND, 2 V/div (voltage across shunt A = SPA–SNA, and the low-side source SLA against the shunt's ground end).
CH2 H1, trigger only (long ground lead: its amplitude is not a measurement — it read −16.7 V where the short-loop B1neg read −9.5 V).
| IDRIVE | Polarity | Edge | Shunt-side min / max | Beyond ±3 V for | Beyond ±1 V for |
|---|---|---|---|---|---|
| 15 | sourcing | high-side on (hard) | −1.74 / +1.07 V | 0 | — |
| 15 | sourcing | high-side off | −1.10 / +1.02 V | 0 | — |
| 15 | sinking | low-side off | −0.99 / +0.62 V | 0 | — |
| 15 | **sinking** | **low-side on (hard)** | **−4.58 / +3.07 V** | 4.5 ns | 44 ns |
| 11 | sourcing | high-side on (hard) | −1.13 / +0.96 V | 0 | — |
| 11 | sourcing | high-side off | −0.54 / +0.53 V | 0 | — |
| 11 | sinking | low-side off | −0.81 / +0.51 V | 0 | — |
| 11 | sinking | low-side on (hard) | −2.43 / +1.66 V | 0 | 17 ns |
- DRV8323 absolute maximum on SPx / SNx / SLx: ±3 V for a 200 ns transient, ±1 V continuous. **IDRIVE 15 exceeds it on the
  low-side hard edge (−4.6 V); IDRIVE 11 stays inside (−2.4 V), with ~20 % margin.** Every other edge is within ±1.8 V.
- The ringing (~90 MHz, ~80 ns) is the same burst seen on the switch node: ~1.5 V of shunt-side voltage per ~3 V of
  switch-node undershoot, i.e. roughly half of the undershoot is dropped across the shunt's own inductance and its returns.
- Limits: measured at the shunt, not at the IC pins (ground bounce between shunt and driver not captured); 70 MHz scope and
  a hand-held ×10 probe, so peaks are under-read; 3 A / 30 V only.
- Second, independent reason not to run IDRIVE 15. Rev B: low-inductance shunt (wide/reverse-geometry or paralleled),
  Kelvin sense routing with an RC filter at the amplifier inputs, shunt close to the FET source.

## FW — firmware changes from the findings, verified on the board · `char/FW/20261122_204048/results.json`
Flashed 2026-11-22 (parameter page untouched). UART + PSU only, 30 V.
| Change | Check | Result |
|---|---|---|
| Gate drive capped at IDRIVE 11 (a saved 15 is rejected at load) | value after boot; `SET p_drv_idrive 15`; DRV registers | 11; refused (RANGE); r3/r4 = 0x3BB / 0x7BB |
| Shunt reconstruction: the phase with the shortest low-side window (< 4 µs; C counted 1.8 µs shorter) is rebuilt from the other two | C1 repeat, duties (cm + 0.8, cm, cm) | see table |
| Over-current check moved ahead of the encoder SPI read | — | not re-measured (needs the scope); expected gain ≤ 3.5 µs in encoder modes only |

| Common mode | ia | ib | ic | Rebuilt | Before the change (ic) |
|---|---|---|---|---|---|
| 50 % | +1.139 | −0.558 | −0.562 | none | −0.604 |
| 80 % | +1.225 | −0.607 | −0.535 | none | −0.623 |
| 90 % | +0.986 | −0.405 | −0.575 | C | −0.506 |
| 95 % | +1.581 | −0.804 | **−0.787** | C | **−0.399** |
| 97 % | +1.395 | −0.857 | −0.523 | C | −0.183 |
- **95 %: fixed** (ic now matches ib; it read half before). 97 %: phase A's own window is 0.9 µs, so two phases are invalid
  and no reconstruction can help — duty ≤ ~95 % remains the limit for the highest phase.
- Open: B and C differ by 70–170 mA at 80 % and 90 % (they should be equal). 80 % is without reconstruction, so this is in
  the raw readings: a duty-dependent offset (the no-probe batch saw ±66 mA at zero current at 90–96 %). Needs SOB / SOC on the scope.

### Loop resistance from the hold-voltage slope (SL_POSITION holds, v_alpha from the duties)
| Hold | v_alpha | V / I | Local slope |
|---|---|---|---|
| 1 A | 143 mV | 143 mΩ | — |
| 2 A | 226 mV | 112 mΩ | 82 mΩ |
| 3 A | 270 mV | 90 mΩ | 44 mΩ |
| 4 A | 304 mV | 76 mΩ | 34 mΩ |
| 5 A | 334 mV | 67 mΩ | 30 mΩ |
- The slope is still falling at 5 A: the dead-time / device voltage error is not constant even there. Fit 2–5 A: 36 mΩ with a
  157 mV offset; the 4–5 A slope, 30 mΩ, is the better upper bound. Consistent with 18 mΩ winding + shunt 3 + FET ~3 + connector
  and traces. **Loop resistance ≈ 25–30 mΩ per phase; the stored 98 mΩ is what V / I looks like near 1–3 A.**
- This also quantifies the voltage error for compensation: ~150 mV at 1 A rising to ~190 mV at 5 A (v_alpha minus 30 mΩ × I).

### Sensorless at 1000 rpm, stored R (98 mΩ) vs measured (36 mΩ), two runs each
| R used | Flux ratio | id | iq |
|---|---|---|---|
| 98 mΩ | 1.035 / 1.032 | −0.06 / +0.01 A | 0.47 / 0.41 A |
| 36 mΩ | 1.046 / 1.046 | −0.02 / 0.00 A | 0.43 / 0.44 A |
- **No meaningful difference at 1000 rpm**: R × i is ~20 mV against ~2 V of back-EMF. The 3–5 % flux excess is therefore not
  a resistance effect (candidates: the flux constant itself, the voltage-error model). The earlier "id ≈ 0.9 A at speed" was
  seen at higher speed and is not reproduced here; it needs a 3000 rpm run to revisit.

## BEMF — back-EMF while coasting · `char/BEMF/20261122_205105` (`analysis.json`)
Sensorless to 1000 rpm, STOP (outputs off), capture ~50 ms later, 20 ms record. CH1 H1 (A), CH2 H2 (B), ground at the shunts.
Line-line = A − B, sine fit on each half of the record (the speed falls ~28 rpm in 10 ms).
| Run | Speed in the record (from the frequency) | Line-line peak | λ first / second half |
|---|---|---|---|
| 0 | 872 → 843 rpm | 3.04 V | 1.402 / 1.398 mV·s |
| 1 | 840 → 812 rpm | 2.91 V | 1.396 / 1.388 mV·s |
| 2 | 900 → 869 rpm | 3.14 V | 1.397 / 1.396 mV·s |
- **Flux constant λ = 1.396 mV·s ± 0.5 % between runs** (probe / scope gain ±2 %): KV 282, Kt 0.0293 N·m/A. The stored value
  (1.389, from the September I/f recordings) is 0.5 % lower — **confirmed independently of the current sense and the observer.**
- So the observer's 3–5 % flux excess is not the flux constant and not the resistance (FW check). What is left is the voltage
  it assumes: a 150–190 mV error on ~2 V of back-EMF at 1000 rpm is the right size (→ dead-time compensation).
- With the outputs off the phases float up to the bus: the highest phase sits at +30.5 V (bus + a high-side body-diode
  drop at leakage current), the others below it by the line-line back-EMF (minimum 26.8 V). No current flows; nothing is stressed.
- Coast-down: ~2900 rpm/s at ~860 rpm → ~24 mN·m of drag with J ≈ 8e-5 kg·m² (estimate), i.e. ~2.1 W of friction + iron loss.

## C2 — B vs C current mismatch at 50–95 % duty · `char/C2/B_20261122_205513`, `C_20261122_205622`
PWM_TEST (cm + 0.8, cm, cm). CH1 the phase's switch node, CH2 its sense output; ADC raw voltage read over UART.
| Common mode | SOB, scope at the sample instant | SOB, ADC | ia | ib | ic | Sum (where all three are sampled) |
|---|---|---|---|---|---|---|
| 50 % | −36.7 mV | −36.9 mV | +1.111 | −0.602 | −0.505 | +0.004 |
| 80 % | −43.9 mV | −39.7 mV | +1.168 | −0.642 | −0.483 | +0.043 |
| 90 % | −30.6 mV | −27.5 mV | +0.941 | −0.461 | (rebuilt) | — |
| 95 % | −55.8 mV | −51.9 mV | +1.503 | −0.860 | (rebuilt) | — |
Second run (probes on phase C): 50 %: +1.096 / −0.673 / −0.461, sum −0.038; 80 %: +1.108 / −0.674 / −0.461, sum −0.027.
- **The mismatch is real current, not a sensing error.** SOB on the scope matches the ADC within 4 mV (70 mA), and with all three
  phases sampled the readings sum to zero within 45 mA — while B and C differ by 100–210 mA, already at 50 % duty.
- Cause: in this open-loop test B and C get the same duty, and the loop resistance is only ~25 mΩ, so **1 mV of difference
  between the two legs' effective voltage moves ~40 mA** from one phase to the other. The split wandered between runs
  (−0.56 / −0.56, −0.60 / −0.51, −0.67 / −0.46). It is a property of the open-loop test, not of closed-loop current control.
- The SOC scope capture of the second run is invalid (CH2 made contact late: 1.39 V at the probe check, then clipped) and was
  not repeated — the sum check answers the question; SOC against the ADC was already measured in C1b.

## D1b — firmware over-current trip latency, re-measured on two switch nodes · `char/D1b/20261122_210005`
PWM_TEST 50/50/50 → 53/50/50, trip 2.5 A, firmware of 2026-11-22 (over-current check before the encoder read). CH1 phase A,
CH2 phase B; timeout trigger (fires 30 µs after phase A's last edge). Times relative to the trigger, 4 trips.
| Event (run 0; runs 1–3 within 0.2 µs) | Time |
|---|---|
| Phase B falls (low-side window starts) | −50.8 µs |
| ADC sample = centre of B's low-side window | −40.9 µs |
| Phase A rises (its normal 53 % edge) | −31.6 µs |
| **Phase A forced low again; phase B forced high (outputs off)** | **−31.4 µs** |
- **Sample → outputs off: 9.5 µs, identical in 4 of 4 trips** (the ADC sequence, interrupt entry and the checks ahead of the trip).
  Worst case from the current crossing the limit: 40 µs sample interval + 9.5 µs ≈ **50 µs**.
- The earlier 19 µs (D1) was derived from an assumed sample instant read off the SOA trace; this measurement takes the sample
  instant from the PWM pattern itself. The two are not a before/after comparison, so the gain from moving the check ahead of
  the encoder read is not established (≤ 3.5 µs expected). The first attempt of this test (`…_205844`) caught ordinary
  switching records (free-running trigger) and is not used.
- Conclusion unchanged: overload protection only; a short circuit needs the gate driver's own trip.

## B7 — phases B and C switch nodes, 3 A, 30 V, IDRIVE 11 (as flashed) · `char/B7/B_20261122_210217`, `C_20261122_210316`
Hold vector rotated onto the phase (120° / 240° electrical, +180° for sinking). CH1 H2 / R27-GND, H3 / R32-GND. Phase A values from B4 / B4neg.
| | Phase A | Phase B | Phase C |
|---|---|---|---|
| High-side turn-on (hard, sourcing) t10–90 | 15.9 ns | 16.8 ns | 16.2 ns |
| Overshoot above the settled level | +0.6 V | +0.5 V | **+3.0 V** (32.4 V peak) |
| Low-side turn-on (hard, sinking) t10–90 | 8.9 ns | 8.9 ns | 9.6 ns |
| Minimum / undershoot below the settled level | −2.7 V / 2.1 V | −3.1 V / 2.5 V | **−4.5 V / 3.9 V** |
| Soft edges t10–90 | 35–38 ns | 36–38 ns | 35 ns falling, 78 ns rising |
- A and B are alike. **Phase C rings about twice as hard on both hard edges** — larger commutation-loop inductance for that
  leg (distance to the bus capacitors / its shunt return). Still inside the −7 V SHx rating at 3 A with IDRIVE 11, but C is
  the leg that sets the limit: all margins for higher current must be taken on phase C, not A.
- Rev B: check phase C's half-bridge loop (capacitor placement, shunt and return path) against A and B.

## B8 — phase A edges and bus ripple at 12 V and 24 V, 3 A, IDRIVE 11 · `char/B8/20261122_210544` (12 V), `…_210736` (24 V)
CH1 H1 / R22-GND; CH2 H8 / H9 AC-coupled. 30 V column from B4 / B4neg / B5. (First pass lost the last two 24 V captures to the
firmware's 15 s run limit; 24 V was repeated on its own.)
| | 12 V | 24 V | 30 V |
|---|---|---|---|
| High-side turn-on (hard) t10–90 | 9.1 ns | 9.2 ns | 15.9 ns |
| Overshoot above the settled level | +2.0 V | +0.8 V | +0.6 V |
| Low-side turn-on (hard) t10–90 | 9.9 ns | 9.4 ns | 8.9 ns |
| Minimum / undershoot below the settled level | −2.70 / 2.1 V | −2.76 / 2.2 V | −2.66 / 2.1 V |
| Soft edges t10–90 | 20 ns | 31–32 ns | 35–38 ns |
| Bus ripple between edges (5–95 %) | 25–27 mV | 8–30 mV | ~20 mV |
| Bus spikes at the edges, p-p | 0.43–0.68 V | 0.27–0.79 V | ~0.9 V |
- **The low-side undershoot does not depend on the bus voltage (12 → 30 V) at IDRIVE 11: −2.7 V throughout.** It is set by the
  gate-drive rate and the current, so the open scaling question is current, not voltage — good news for the 56 V design
  point, still to be shown above 30 V.
- Soft-edge time scales with voltage as expected (fixed current charging the node capacitance: ~5 nF).
- The high-side overshoot is larger at 12 V (+2.0 V) than at 30 V, and the 30 V high-side edge reads slower (15.9 ns vs 9 ns);
  not explained — FET capacitance rises steeply at low voltage, which changes both. No rating is at stake (≤ 14 V peak on a 12 V bus).

## DTC — observer voltage-error compensation sweep (`p_sl_dtc_v`, observer side, firmware of 2026-11-22) · `char/DTC/20261122_210918`
Sensorless 1000 rpm, 30 V, no load (phase currents ~0.45 A peak). No probes.
| Compensation | Flux ratio | Flux ripple (sd) | id | iq |
|---|---|---|---|---|
| 0 | 1.033 | 0.006 | +0.01 A | 0.45 A |
| 50 mV | 1.009 | 0.011 | −0.08 | 0.42 |
| 100 mV | 0.984 | 0.019 | +0.03 | 0.44 |
| 150 mV | 0.971 | 0.028 | +0.06 | 0.43 |
| 200 mV | 0.949 | 0.046 | −0.07 | 0.46 |
| 0 (repeat) | 1.033 | 0.006 | −0.06 | 0.46 |
- **The 3 % flux excess is the uncompensated bridge voltage error**: the ratio crosses 1.00 at ~65–70 mV. That matches the hold
  data (≈ 85 mV per phase at 1 A, ≈ 140 mV above 2 A) scaled to 0.45 A — a compensation of 0.14 V × sat(i / 1 A) fits both.
- A fixed step with a 0.2 A knee (this implementation) over-corrects around the current zero crossings: ripple grows with the value.

## DTC2 — output-side voltage-error compensation (firmware 2026-11-22b) · `char/DTC2/20261122_211302`
`p_sl_dtc_v` × sat(i_phase / 1 A) is now added to the output vector (sensorless modes, hardware); the observer uses the command as is.
| Hold | Commanded vd, off | Commanded vd, 0.14 V | Bridge output (from the duties), either case |
|---|---|---|---|
| 1 A | 144 mV (143 mΩ) | 5 mV | 144–145 mV |
| 2 A | 226 mV (113 mΩ) | 41 mV | 226–227 mV |
| 3 A | 269 mV (90 mΩ) | 82 mV | 269 mV |
| 4 A | 304 mV (76 mΩ) | 117 mV | 304 mV |
| 5 A | 334 mV (67 mΩ) | 149 mV (30 mΩ) | 334–335 mV |
With compensation the plant the current loop sees is close to linear: 36 mΩ slope 2–5 A (slightly over-corrected at 1 A).

| Sensorless 1000 rpm | Flux ratio | Flux sd | Speed sd | Input power |
|---|---|---|---|---|
| 0 | 1.035 | 0.005 | 1.3 rpm | 6.12 W |
| 0.10 V | 1.012 | 0.014 | 2.3 rpm | 6.15 W |
| 0.14 V | 1.017–1.020 | 0.022–0.024 | 3.2–4.3 rpm | 6.24 W |
| 0.18 V | 1.022 | 0.033 | 7.5 rpm | 6.42 W |
- At speed and light current (0.45 A peak, inside the 1 A knee) the compensation follows the **measured** current, so current
  noise feeds back into the voltage: ripple × 3–5. **Left off by default (0).** Useful for standstill / low-speed holds
  (~0.10 V). Next step: drive it from the current reference (or a filtered current) instead of the raw measurement.
- ISR peak 33.5 µs of 40, 0 overruns. Flash 95.1 %, RAM 96.6 %.

## B9 — switch node on the driver's sense trace (TP38, SHA) · `char/B9/20261122_212218`
Phase A sinking 3 A, **12 V** (chosen so that a probe slip onto the gate test point 1.3 mm away stays under the 13.5 V gate-pin
rating; B8 showed the undershoot does not depend on the bus voltage). CH1 TP38 (9.6 mm from the driver) ref R27-GND, hand-held.
| IDRIVE | Low-side turn-on (hard) t10–90 | Minimum at TP38 | Minimum at the phase pad H1 (B8 / B4neg) |
|---|---|---|---|
| 11 (440 / 880 mA) | 8.8 ns | −2.62 V | −2.70 V |
| 7 (190 / 380 mA) | 16.8 ns | −0.42 V (no undershoot beyond the −0.2 V plateau) | −0.76 V at 30 V |
- **The sense trace delivers the same spike to the driver as the phase pad shows (−2.6 vs −2.7 V): no filtering along it.** The
  pad measurements are therefore a fair proxy for the SHx pin, as far as a shunt-ground reference goes.
- Not covered: the driver's own ground against the shunt ground (the nearest driver-ground pad is 14 mm from TP38), and phase C.
- IDRIVE 7 removes the undershoot entirely for ~8 ns of extra edge time — the setting to use if more margin is needed at higher current.

### B9 at 30 V · `char/B9/20261122_212347`
| IDRIVE | Low-side turn-on (hard) t10–90 | Minimum at TP38 | Minimum at the phase pad H1, 30 V |
|---|---|---|---|
| 11 | 7.6 ns | **−4.18 V** (3.6 V below the settled level) | −2.66 V |
| 7 | 18.2 ns | −0.87 V (0.3 V below) | −0.76 V |
- **At 30 V the sense trace shows 1.5 V more undershoot than the pad at IDRIVE 11** (at 12 V the two agreed: −2.62 / −2.70 V). The
  12 V result does not carry over, and the expectation written before this run (little new information) was wrong.
  One capture per point; part of the difference may be the larger probe loop here (ground 4.8 mm away) — not separable by hand.
- Margin to the −7 V SHx rating on phase A at 3 A / 30 V / IDRIVE 11: ~2.8 V at TP38, not the 4.3 V the pad suggested. Phase C
  rings about 1.8 V harder at the pad (B7), so its sense trace may sit near −6 V: **little margin left at IDRIVE 11, at only 3 A.**
- IDRIVE 7 is clean at both points and both voltages. **Recommendation changed: IDRIVE 7 (190 / 380 mA) as the default**, 11 as
  the upper limit; hard-edge loss rises from ~0.4 to ~0.8 µJ per edge (≈ +20 mW per phase at 25 kHz), negligible.

## B10 — phase C hard edges vs current, 30 V · `char/B10/20261122_212919`
CH1 H3 / R32-GND. Low-side turn-on with C sinking, high-side turn-on with C sourcing. (A first pass, `…_212737`, captured
nothing — no probe contact — and ran all steps without the guard having data; the script now checks the probe at zero current
and stops on a missed capture.)
| IDRIVE | Current | Low-side turn-on: t10–90 / minimum | High-side turn-on: t10–90 / peak |
|---|---|---|---|
| 7 | 3 A | 17.7 ns / −3.54 V | 25.5 ns / 31.4 V (+2.1 V) |
| 7 | 5 A | 17.3 ns / −3.51 V | 25.1 ns / 31.3 V (+2.1 V) |
| 11 | 3 A | 8.8 ns / −4.73 V | 16.5 ns / 32.4 V (+3.1 V) |
| 11 | 4 A | 8.6 ns / −4.85 V | 16.7 ns / 32.3 V (+3.1 V) |
| 11 | 5 A | 8.1 ns / −4.95 V | 17.3 ns / 32.3 V (+3.1 V) |
- **Current dependence is weak: about −0.1 V per amp at IDRIVE 11, none measurable at IDRIVE 7.** The ringing is set by the edge
  (gate-drive rate and the leg's loop inductance), not by the load current. A straight-line extrapolation to 10 A gives about
  −5.5 V at the pad for IDRIVE 11 — inside −7 V only if the sense trace adds nothing, and B9 says it adds ~1.5 V on phase A.
- **Phase C still undershoots −3.5 V at IDRIVE 7**, where phase A is clean (−0.8 V): the slower gate drive halves the problem
  on this leg but does not remove it. Its source is the layout of leg C.
- Envelope: IDRIVE 7 keeps the worst leg at ≈ −3.5 V (pad) up to 5 A with no trend in current; IDRIVE 11 is not recommended.
  Below 7 (codes 4–6: 60–120 mA source) is the next thing to try if more margin is wanted. Rev B: fix leg C's loop.

## B10b — phase C, IDRIVE 7 / 6 / 5 / 4 at 5 A, 30 V · `char/B10/20261122_213218`
Same placement throughout (CH1 H3 / R32-GND, one hold of the probe). Input power is the whole board during the hold.
| IDRIVE | Low-side turn-on: t10–90 / minimum | High-side turn-on: t10–90 / peak | Input power |
|---|---|---|---|
| 7 | 18.2 ns / −1.01 V | 26.6 ns / 29.4 V (no overshoot) | 2.58 W |
| 6 | 20.3 ns / −0.77 V | 28.8 ns / 29.4 V | 2.58–2.61 W |
| 5 | 24.7 ns / −0.84 V | 34.2 ns / 29.4 V | 2.61–2.67 W |
| 4 | 29.8 ns / −0.76 V | 38.8 ns / 29.4 V | 2.67–2.70 W |
- Within this run there is nothing left to gain below IDRIVE 7: the minimum is the body-diode plateau plus ~0.3 V at every
  code; slower codes only add edge time (18 → 30 ns) and ~0.1 W. No gate-drive faults down to code 4.
- **Repeatability problem:** the same point (IDRIVE 7, 5 A, phase C) read −3.51 V / 31.3 V peak in the previous run and
  −1.01 V / 29.4 V here, with the probe re-seated in between. The edge is as fast here (max slew 2.3 vs 1.9 V/ns), so this is
  not a band-limited contact; the earlier, larger reading is more likely pickup in a larger ground-spring loop, or a different
  spot on the pad. **Hand-held readings of the ringing are placement-dependent by ~2.5 V.** Trends inside one placement hold
  (IDRIVE sweeps, current sweeps); comparisons across placements — phase C vs A / B (B7), TP38 vs the pad at 30 V (B9) — are
  not established until repeated. The conservative (larger) values are kept for the envelope.

## B11 — repeatability of the ringing readings: three fresh probe placements per phase · `char/B11/C_*`, `char/B11/A_*`
3 A, 30 V; low-side turn-on minimum (phase sinking) and high-side turn-on peak (phase sourcing). All same-day placements listed.
| Phase | IDRIVE 11: minimum | IDRIVE 11: peak | IDRIVE 7: minimum | IDRIVE 7: peak |
|---|---|---|---|---|
| A, placements 1–3 | −2.81 / −3.04 / −3.04 V | 29.8 / 29.7 / 29.8 V | −0.80 / −0.86 / −0.80 V | 29.5 / 29.4 / 29.4 V |
| A, earlier (B4neg, B8) | −2.66 / −2.70 V | — | −0.76 V | — |
| C, placements 1–3 | −4.56 / −5.15 / −4.63 V | 32.2 / 29.5 / 32.3 V | −3.34 / **−0.81** / −3.47 V | 31.1 / **29.5** / 31.3 V |
| C, earlier (B7, B10, B10b) | −4.46 / −4.73 V | 32.4 / 32.4 V | −3.54 / **−1.01** V | 31.4 / **29.4** V |
- **Phase A is repeatable to ±0.2 V** across five placements. The method is sound there.
- **Phase C is worse than A at IDRIVE 11 in 5 of 5 placements** (−4.5 to −5.2 V against −2.7 to −3.0 V): that finding stands.
- **Phase C is bimodal at IDRIVE 7 and on the overshoot side**: four placements show −3.4 V / +2 V overshoot, two show the
  clean picture (−0.9 V, no overshoot). Not explained — a different spot on the large H3 pad, or the ground-spring loop
  coupling to leg C's own loop. The envelope keeps the larger value. A soldered coax pigtail at H3 would settle it.
- B9's "sense trace 1.5 V worse than the pad at 30 V" (−4.18 V vs −2.66 to −3.04 V on phase A) is larger than phase A's
  placement spread, so it is probably real, but it rests on a single TP38 capture.
