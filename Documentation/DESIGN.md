# Rev 1 design decisions

Why the board is built the way it is. Measured behaviour, and what the bench changed, is in the
[test and bring-up report](../Testing/README.md). Where the two disagree, the report wins.

## The requirement that drives everything

One joint of a quasi-direct-drive (QDD) leg: 6:1 to 10:1 gearing, so the joint is backdrivable and joint torque tracks
motor current almost directly. Three consequences:

- **Current-sense error is torque error.** No gearbox hides it, so sensing is a primary spec, not an afterthought.
- **Impacts and stops regenerate.** Bus transients are routine, so fault state is *coast*, never brake-to-short.
- **The board hangs on a limb.** Area and mass count; an oversized power stage is a defect.

| Requirement | Value |
|---|---|
| Bus | 12S Li-ion: 36 V cutoff, 44.4 V nominal, 50.4 V full |
| Phase current | 10 A RMS continuous |
| Position | Absolute, valid at zero speed |
| PWM | Inaudible, > 20 kHz |
| Nodes | 6 boards on one bus, CAN-FD |
| Size | ≤ 80 × 80 mm (built 70 × 70) |

## How it got here

| Rev | Configuration | Lesson |
|---|---|---|
| A | STM32F405, 40 V FETs | 40 V parts on a 50.4 V bus are out of rating at rest. Check V<sub>DS</sub> against the worst transient first. |
| B | STM32G431, DRV8323S, 1.5 mΩ FETs | The lowest R<sub>DS(on)</sub> had the highest total loss. Select on figure of merit, not one parameter. |
| C | Hot-swap, dual XT60, USB-C, 3 regulators, off-board encoder, 19 sheets | Over-correction: every fault handled on every board. |
| 1 | Built | Each block classed required or discretionary, then placed on the right board. |

What Rev 1 removed and why:

| Removed | Why |
|---|---|
| LM5069 hot-swap front end | Inrush and UV/OV are bus functions: once on the power-distribution board, not six times |
| USB-C + CH340X | SWD does the job and frees the BOOT0 pin conflicts |
| Gate resistor + diode networks | DRV8323 IDRIVE sets turn-on and turn-off slew separately |
| Separate analog LDO + mux | Trimmed for area (now a Rev B item) |
| CAN node-ID resistor ladder | Deferred to Rev B |
| Off-board-only encoder | Unshielded SPI through a moving joint was the top field-failure risk |

## Decisions

**1. Power stage: 6 × ISC030N10NM6 (100 V, 3.0 mΩ max, Q<sub>g</sub> 55 nC, TDSON-8).**
100 V gives ~2× margin over 50.4 V. Chosen on R<sub>DS(on)</sub> × Q<sub>g</sub>: at 40 kHz the 1.5 mΩ part lost 5.65 W
against 4.27 W for a 2.2 mΩ part, because switching loss dominated. TDSON-8 instead of TOLL: six TOLL footprints
(~700 mm²) for under 1 W per FET was area bought for nothing.

**2. Gate driver: DRV8323S (SPI).**
SPI-set IDRIVE replaces gate resistor networks, and the charge pump (25 mA) covers three high-side gates with ~6×
margin at 25 kHz. Trade-off: with 0 Ω gate resistors, edge rate depends entirely on a register that powers up at its
fastest. The bench found that matters (report 4.3), so Rev B adds gate resistor footprints.

**3. PWM: 25 kHz centre-aligned, 40 µs control ISR.**
The requirement is audibility. 40 kHz was planned; 25 kHz leaves ISR headroom and cuts switching loss. Sanity check:
20 pole pairs × 3500 rpm ≈ 1.17 kHz electrical, ~20 samples per electrical cycle.

**4. Current sensing: 3 × 3 mΩ low-side shunts, Kelvin, DRV8323 CSA gain 20.**
Shunt and gain are one decision: ±27.5 A ideal, ±23.3 A linear (CSA output swing). Gain 40 would cap at ±13.75 A.
Noise rejection is by sample timing (TIM1 CH4 at counter peak triggers injected ADC conversions), not filtering; the
56 Ω / 2.2 nF RC only damps edges. Low-side shunts cannot see current at very high duty; that limit is in the report (4.5).

**5. DC link: 3 × 100 µF polymer + 9 × 4.7 µF / 100 V MLCC.**
Sized by ripple current (~7.8 A RMS at 10 A/phase), not capacitance. MLCCs sit ~6 mm from the FETs to close the
commutation loop (~2.4 nH estimated). Simulation showed loop inductance is the main layout variable: overshoot goes
from 53 V at 2.4 nH to 97 V at 42 nH on a 50.4 V bus.

**6. Position: AS5047P on the board, at its exact centre, under the shaft.**
A joint must hold torque at standstill, where back-EMF is zero and sensorless observers have no signal. On-board
placement removes SPI through a moving cable. An auxiliary SPI connector stays for an off-board encoder.

**7. Protection split: TVS on the board, hot-swap upstream.**
SMCJ51CA only. Continuous bus limit is therefore 51 V (TVS stand-off), not 56 V. Known gap: the clamp (82.4 V) sits
above the 65 V ratings of the DRV8323 and LMR36520, so nothing protects the 65–82 V band. Fault response is a hardware
break (nFAULT → TIM1_BKIN), independent of firmware.

**8. Power tree: LMR36520 buck to 5 V → TLV75733 LDO to 3.3 V.**
Two regulators instead of three. Analog shares the digital 3.3 V; a separate analog rail is a Rev B item.

**9. Grounding and stackup: 6 layers, L2 and L5 solid ground.**
Both ground planes are unbroken across the whole board, including under the power stage. PGND, AGND and DGND join at one
star point at the shunts. Chassis has one DC bond (R58) plus 1 nF / 1 kV at each mounting hole; a second DC bond would
make a loop through cable shields. Phase and bus terminals share one edge next to the FET row.

**10. Interfaces: CAN-FD to the host, UART to the bench GUI, SWD for debug.**
CAN-FD (TCAN1044) for six nodes on one bus; UART (FOCLINK) for the bench console; no USB on the joint board.

## Known Rev 1 compromises (decided, not discovered)

- No thermal vias under the low-side FETs (switch node kept on L1 for EMI). Rated 10 A until measured.
- Board NTC at board centre, 22 mm from the FETs; it under-reads.
- 3 bulk capacitors fitted against 5 specified.
- PB8 is both FDCAN_RX and BOOT0; option bytes must disable the pin boot.
- E-stop input follows the driver enable, so it is not independent.

Everything found on the bench, and the Rev B list that came from it, is in
[Part 5 of the test report](../Testing/README.md#part-5-what-changed-because-of-all-this).

## References

- TI DRV8323 datasheet (SLVSDJ3), SLVA714 (IDRIVE/TDRIVE), SLVAF66 (motor-drive MOSFET selection)
- Infineon ISC030N10NM6 datasheet
- ST STM32G431 datasheet (DS12589), RM0440, AN4013 (timers), AN2834 (ADC accuracy)
- ams AS5047P datasheet (DS000324)
- TI BPRA048 (Clarke and Park transforms)
- H. Ott, *Electromagnetic Compatibility Engineering* (grounding, chassis bonding)
