# FoC Motor Controller · Rev 1

A single-axis, sensored field-oriented-control (FOC) motor controller for one joint of a cat-scale bipedal robot: 70 × 70 mm, 6 layers, built for a 12S bus. Six boards (one per joint) are planned, sharing the bus and talking over CAN-FD.

<p align="center">
  <img src="Documentation/images/photo_rev1_boards.jpg" width="640" alt="Two Rev 1 boards from the first JLCPCB run: assembled top side in front, bare bottom side held up behind">
</p>

**Status:** Rev 1 is design-frozen, fabricated, brought up and bench-characterized up to 30 V and 10 A (2026-11-22). What it can and cannot do, test by test, is in the [test and bring-up report](Testing/README.md). Not yet tested on the 12S bus, under shaft load, or with the encoder.

| | |
|---|---|
| Bus | 12S LiPo: 44.4 V nominal, 50.4 V full, 56 V max |
| Phase current | 10 A RMS continuous (design target) |
| MCU | STM32G431RB, 170 MHz Cortex-M4F |
| Gate driver | TI DRV8323S (SPI, 3 integrated current-sense amplifiers) |
| Power stage | 6 × Infineon ISC030N10NM6, 100 V, TDSON-8 |
| Current sensing | 3 × 3 mΩ low-side shunts, Kelvin-connected |
| Position | AS5047P 14-bit magnetic encoder, on the back of the board under the motor shaft |
| Comms | CAN-FD (TCAN1044), UART to the bench GUI, SWD |
| Power tree | SMCJ51CA TVS → LMR36520 buck to 5 V → LDO to 3.3 V |
| Board | 70 × 70 mm, 6 layers, KiCad 10, fabricated and assembled by JLCPCB |

---

## Renders

<p align="center">
  <img src="Documentation/images/render_pair.jpg" width="100%" alt="Render of two boards on brass standoffs, one top side up and one flipped">
</p>

<table>
  <tr>
    <td><img src="Documentation/images/render_top.jpg" alt="Top side render"></td>
    <td><img src="Documentation/images/render_bottom.jpg" alt="Bottom side render"></td>
  </tr>
  <tr>
    <td align="center">Top: bridge, DRV8323S, STM32G431, bulk caps, connectors</td>
    <td align="center">Bottom: power bus, phase pads, AS5047P encoder</td>
  </tr>
</table>

Rendered in Blender (Cycles) from the KiCad board and the fabrication Gerbers, on brass M3 standoffs.

## On the motor

Rendered with the ODrive M8325s (100 KV, 20 pole pairs), the reference motor for the leg joint, on the 3D-printed test upright.

<p align="center">
  <img src="Documentation/images/render_bench_board_side.jpg" width="100%" alt="Board mounted on the test upright with the M8325s motor behind it, phase leads, bus leads and JST-GH cables attached">
</p>

<table>
  <tr>
    <td><img src="Documentation/images/render_bench_motor_side.jpg" alt="Motor side of the test upright"></td>
    <td><img src="Documentation/images/render_encoder_ghost_motor.jpg" alt="Transparent motor over the bottom of the board showing the encoder magnet above the AS5047P"></td>
  </tr>
  <tr>
    <td align="center">Motor side of the test upright</td>
    <td align="center">Motor shown transparent: the diametric magnet sits on the shaft axis over the AS5047P</td>
  </tr>
</table>

<p align="center">
  <img src="Documentation/images/render_connection_map.jpg" width="70%" alt="Top-down connection map: phase outputs to the motor, DC bus input, CAN-FD, UART, I2C, encoder AUX, motor temperature, E-stop and SWD">
</p>

## PCB layout

<p align="center">
  <img src="Documentation/images/layout_stack.jpg" width="100%" alt="Exploded view of the six copper layers">
</p>

Stackup: L1 signal + power, L2 ground, L3 / L4 signal + power, L5 ground (identical to L2), L6 signal + power. Phase and bus current run in outer-layer pours; the DRV8323S sits next to the bridge to keep the gate loops short.

<p align="center">
  <img src="Documentation/images/layout_layers_overview.jpg" width="100%" alt="Per-layer cards L1 to L6 and all signal layers">
</p>

<details>
<summary>All signal layers, full size</summary>
<img src="Documentation/images/layout_all_signal_layers.jpg" width="100%" alt="All four routing layers overlaid">
</details>

Plots of every copper, mask, paste and silkscreen layer are in [`Hardware/Project Outputs/PCB Layers PDF/`](Hardware/Project%20Outputs/PCB%20Layers%20PDF/). The full board drawing is [`FoC_Motor_Controller_PCB_Artwork.pdf`](Documentation/FoC_Motor_Controller_PCB_Artwork.pdf).

## Testing

Brought up and characterized on the bench up to 30 V and 10 A: switching, current sense, protection, braking and
sensorless closed-loop speed to 3000 rpm, with three LTspice decks checked against scope captures.

**[Test and bring-up report →](Testing/README.md)**: every test in order, what it found, what it changed in firmware,
and the Rev 2 list that came out of it.

<p align="center">
  <img src="Documentation/images/photo_bench_setup.jpg" width="100%" alt="Bench setup: Rev 1 board and MN601-S motor, Rigol DHO804 scope, Korad KA3005P supply at 30 V, DMM reading a thermocouple">
</p>

## Bench GUI: FOCLINK

FOCLINK is the bench console: a PySide6 app styled as a NERV operations terminal, talking to the firmware over UART. The GUI holds no safety logic; it only requests, and the firmware decides what is allowed. The firmware and GUI live in a separate repository.

<p align="center">
  <img src="Documentation/images/gui_dashboard.png" width="100%" alt="FOCLINK dashboard: safety and arming, live tiles, trend charts, subsystem status">
</p>

<table>
  <tr>
    <td><img src="Documentation/images/gui_magi.png" alt="MAGI view: three votes summarising power stage, subsystems and link"></td>
    <td><img src="Documentation/images/gui_motor_bringup.png" alt="Motor bring-up: preflight sync, bench confirmations, settings and run sequence"></td>
  </tr>
  <tr>
    <td align="center"><b>MAGI 合議</b>: power stage, subsystems and link summarised as three votes</td>
    <td align="center"><b>Motor bring-up 起動試験</b>: preflight sync, then phase check, R and L identification</td>
  </tr>
  <tr>
    <td><img src="Documentation/images/gui_spin_control.png" alt="Spin control: bench sync, limits, throttle and live run data"></td>
    <td><img src="Documentation/images/gui_terminal.png" alt="Terminal: console and parameter table"></td>
  </tr>
  <tr>
    <td align="center"><b>Spin control 回転制御</b>: limits first, then the open-loop I/f throttle</td>
    <td align="center"><b>Terminal 端末</b>: console, parameters, scope, DRV8323 registers</td>
  </tr>
</table>

Screenshots are from the GUI's built-in board simulator (`python -m focgui --sim foclink-spin`), not a live board.

---

## Documents

| File | What it is |
|---|---|
| [`FoC_Motor_Controller_Schematic.pdf`](Documentation/FoC_Motor_Controller_Schematic.pdf) | Full schematic, 12 hierarchical sheets |
| [`FoC_Motor_Controller_PCB_Artwork.pdf`](Documentation/FoC_Motor_Controller_PCB_Artwork.pdf) | Board drawing |
| [`DESIGN.md`](Documentation/DESIGN.md) | Design decisions and why: requirements, revision history, part choices |
| [`Testing/README.md`](Testing/README.md) | Test and bring-up report |

## Repository layout

| Path | Contents |
|---|---|
| `Documentation/` | Schematic and PCB artwork PDFs, design decisions, images |
| `Hardware/FoC Motor Controller.kicad_pro` / `.kicad_sch` / `.kicad_pcb` | KiCad 10 project, root sheet and board |
| `Hardware/Schematics/` | Hierarchical sheets: power input and generation, MCU, gate driver, MOSFETs, sensing, CAN-FD, interconnects, position, LEDs |
| `Hardware/Libraries/` | Project-local symbols, footprints and 3D models (`${KIPRJMOD}/Libraries/`) |
| `Testing/Simulation/` | LTspice decks, results and the matching scope captures |
| `Testing/README.md` | **The test and bring-up report**: every test in order, why, what was found, what changed |
| `Testing/Bench/` | Lab notebook, raw captures, report figures, probe map |
| `Hardware/Project Outputs/` | BOM, pick-and-place, netlist, Rev 1 fabrication package, per-layer PDFs |

Open `Hardware/FoC Motor Controller.kicad_pro` in KiCad 10. Vendor datasheets and the KiCad worksheet templates are not included; without the templates KiCad falls back to its default title block.
