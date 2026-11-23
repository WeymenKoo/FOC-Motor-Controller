#!/usr/bin/env python3
"""make_report_figs.py -- annotated report figures from the saved waveforms / result tables in char/ -> report/*.png.
Run: uv run --no-project --python 3.12 --with numpy --with matplotlib python make_report_figs.py"""
import csv, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

H = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(H, "report"); os.makedirs(OUT, exist_ok=True)
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"; INK, MUTED, GRID, SURF, CRIT = "#1f1f1e", "#6b6a64", "#e4e3de", "#fcfcfb", "#c8322f"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF, "font.size": 10, "font.family": "DejaVu Sans",
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
                     "lines.linewidth": 2.0, "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left"})
def Z(*p): return np.load(os.path.join(H, "char", *p))
def save(fig, name): fig.savefig(os.path.join(OUT, name), dpi=160, bbox_inches="tight"); plt.close(fig); print("wrote", name)
def limit(ax, y, text, x=0.99):
    ax.axhline(y, color=CRIT, lw=1.2, ls=(0, (5, 3))); ax.text(x, y, text, color=CRIT, fontsize=9, ha="right", va="bottom", transform=ax.get_yaxis_transform())

# 1 -- low-side hard turn-on vs gate-drive strength
fig, ax = plt.subplots(figsize=(8.2, 4.4))
for code, col, lab in ((15, ORANGE, "IDRIVE 15  (1000 / 2000 mA, driver default)"), (11, BLUE, "IDRIVE 11  (440 / 880 mA)"), (7, AQUA, "IDRIVE 7  (190 / 380 mA)")):
    z = Z("B4neg", "20261122_202344", f"ID{code}_fall.npz"); t, v = z["t"] * 1e9, z["ch1"]; m = (t > -40) & (t < 160)
    ax.plot(t[m], v[m], color=col, label=lab); k = np.where(m)[0][np.argmin(v[m])]; ax.plot(t[k], v[k], "o", color=col, ms=6, mec=SURF, mew=1.5)
    ax.annotate(f"IDRIVE {code}: {v[k]:.1f} V", (t[k], v[k]), xytext={15: (22, -10.6), 11: (-36, -4.2), 7: (60, 3.2)}[code], color=INK, fontsize=9, va="center",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
limit(ax, -7, "DRV8323 SHx absolute maximum: −7 V (200 ns transient)")
ax.set(xlabel="time from the edge (ns)", ylabel="switch node, phase A (V)", ylim=(-13, 34), title="Low-side hard turn-on (phase A sinking 3 A, 30 V bus): undershoot vs gate-drive strength")
ax.legend(frameon=False, loc="center right"); ax.text(-38, 32.0, "dead-time plateau: bus + body-diode drop", fontsize=9, color=MUTED)
save(fig, "fig1_gate_drive_undershoot.png")

# 2 -- what the undershoot depends on (one placement per sweep)
fig, axs = plt.subplots(1, 4, figsize=(11.5, 3.5), sharey=True)
def dots(ax, xs, ys, title, xl, col=BLUE, lab=None):
    ax.plot(range(len(xs)), ys, "-o", color=col, ms=7, mec=SURF, mew=1.5, label=lab)
    for i, y in enumerate(ys): ax.annotate(f"{y:.1f}", (i, y), xytext=(0, -13 if col != ORANGE else 9), textcoords="offset points", ha="center", fontsize=8.5, color=INK)
    ax.set_xticks(range(len(xs))); ax.set_xticklabels(xs); ax.set_xlabel(xl); ax.set_title(title, fontsize=10); ax.set_xlim(-0.5, len(xs) - 0.5)
dots(axs[0], ["15", "11", "7"], [-10.03, -2.66, -0.76], "Gate-drive code (A, 3 A, 30 V)", "IDRIVE")
dots(axs[1], ["12 V", "24 V", "30 V"], [-2.70, -2.76, -2.66], "Bus voltage (A, 3 A, IDRIVE 11)", "bus")
dots(axs[2], ["3 A", "4 A", "5 A"], [-4.73, -4.85, -4.95], "Current (C)", "phase current", ORANGE, "IDRIVE 11")
axs[2].plot([0, 1, 2], [-0.82, -0.92, -1.11], "-o", color=AQUA, ms=7, mec=SURF, mew=1.5, label="IDRIVE 7 (5 / 7.5 / 10 A)")
for i, y in enumerate([-0.82, -0.92, -1.11]): axs[2].annotate(f"{y:.1f}", (i, y), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=8.5)
axs[2].legend(frameon=False, fontsize=8, loc="lower left")
dots(axs[3], ["A", "B", "C"], [-2.9, -3.1, -4.7], "Phase (3 A, 30 V, IDRIVE 11)", "leg")
for a in axs: limit(a, -7, "−7 V" if a is not axs[0] else "SHx rating −7 V"); a.set_ylim(-11.5, 1)
axs[0].set_ylabel("switch-node minimum (V)")
fig.suptitle("Low-side turn-on undershoot: set by gate drive and layout, not by bus voltage or load current", x=0.01, ha="left", fontsize=11, fontweight="bold")
fig.tight_layout(); save(fig, "fig2_undershoot_dependencies.png")

# 3 -- shunt-side pins
fig, ax = plt.subplots(figsize=(8.2, 4.0))
for code, col in ((15, ORANGE), (11, BLUE)):
    z = Z("B6", "20261122_202903", f"ID{code}_sink_fall.npz"); t, v = z["t"] * 1e9, z["ch1"]; m = (t > -40) & (t < 200)
    ax.plot(t[m], v[m], color=col, label=f"IDRIVE {code}"); k = np.argmin(v); ax.annotate(f"{v[k]:.1f} V", (t[k], v[k]), xytext=(t[k] + 8, v[k]), fontsize=9, va="center")
limit(ax, -3, "SPx / SNx / SLx absolute maximum: ±3 V (200 ns transient)"); ax.axhline(3, color=CRIT, lw=1.2, ls=(0, (5, 3)))
ax.set(xlabel="time from the edge (ns)", ylabel="across shunt A (V)", ylim=(-5.5, 4.2), title="Voltage across the phase A shunt at the low-side hard turn-on (3 A, 30 V)")
ax.legend(frameon=False, loc="lower right"); save(fig, "fig3_shunt_pins.png")

# 4 -- bridge voltage error
fig, ax = plt.subplots(figsize=(7.6, 4.0)); I = [1, 2, 3, 5]
for ys, col, lab, off in (([162, 213, 225, 229], ORANGE, "IDRIVE 7, driver dead-time 100 ns", 8), ([127, 171, 184, 186], AQUA, "IDRIVE 7, driver dead-time 50 ns", -14),
                          ([114, 166, 179, 184], BLUE, "IDRIVE 11, driver dead-time 100 ns", -14)):
    ax.plot(I, ys, "-o", color=col, ms=7, mec=SURF, mew=1.5, label=lab)
ax.annotate("229 mV", (5, 229), xytext=(6, 0), textcoords="offset points", fontsize=9, va="center"); ax.annotate("186 / 184 mV", (5, 185), xytext=(6, 0), textcoords="offset points", fontsize=9, va="center")
ax.set(xlabel="hold current, phase A (A)", ylabel="output-vector error (mV)", xlim=(0.6, 6.2), ylim=(0, 260), xticks=[1, 2, 3, 4, 5],
       title="Bridge voltage error vs hold current (30 V bus)")
ax.text(0.65, 12, "error = commanded vector − 30 mΩ × I.  MCU dead-time 100 ns and 200 ns give identical curves.", fontsize=8.5, color=MUTED)
ax.legend(frameon=False, loc="center right", bbox_to_anchor=(1.0, 0.33)); save(fig, "fig4_voltage_error.png")

# 5 -- gate-driver VDS trip
z = Z("F2", "20261122_214445", "ceil22_3.npz"); t, a, s = z["t"] * 1e6, z["a"], (z["soa"] - float(z["idle"])) / 0.060; m = (t > -420) & (t < 60)
fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.6, 5.2), sharex=True, gridspec_kw={"height_ratios": [1, 1.5]})
a1.plot(t[m], a[m], color=BLUE, lw=1.2); a1.set(ylabel="phase A node (V)", title="Gate-driver V$_{DS}$ over-current trip at the 0.06 V setting: phase A ramped by a duty step, 30 V")
edge = np.abs(np.diff(a, prepend=a[0])) > 5; near = np.convolve(edge.astype(float), np.ones(3), "same") > 0
low = m & (a < 3) & ~near & (t < -35)
a2.plot(t[low], s[low], ".", color=ORANGE, ms=3); a2.set(xlabel="time before the scope trigger (µs)", ylabel="phase A current from SOA (A)", ylim=(0, 27))
a2.axhline(22.5, color=CRIT, lw=1.2, ls=(0, (5, 3))); a2.text(-415, 23.0, "driver trips at ≈ 22–23 A  (0.06 V ÷ 2.7 mΩ)", color=CRIT, fontsize=9)
a2.annotate("last low-side plateau\nbefore the trip: 21.8 A", (-38, 21.5), xytext=(-18, 14), fontsize=9, va="center", arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
a1.annotate("driver trips: outputs off (nFAULT),\nnode floats", (-31, 16), xytext=(-18, 8), fontsize=9, va="center", arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
a2.text(-415, 2.0, "SOA is valid only while the low side conducts (points shown)", fontsize=8.5, color=MUTED)
fig.tight_layout(); save(fig, "fig5_vds_trip.png")

# 6 -- firmware over-current latency
z = Z("D1b", "20261122_210005", "trip0.npz"); t, a, bb = z["t"] * 1e6, z["a"], z["b"]; m = (t > -75) & (t < -12)
fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.6, 4.6), sharex=True)
a1.plot(t[m], a[m], color=BLUE); a1.set(ylabel="phase A (V)", title="Firmware over-current trip: ADC sample to outputs off = 9.5 µs (4 of 4 trips)")
a2.plot(t[m], bb[m], color=ORANGE); a2.set(ylabel="phase B (V)", xlabel="time before the scope trigger (µs)")
for ax in (a1, a2):
    ax.axvline(-40.9, color=MUTED, lw=1.2, ls=(0, (2, 2))); ax.axvline(-31.4, color=CRIT, lw=1.2, ls=(0, (5, 3))); ax.set_ylim(-4, 36)
a1.text(-41.4, 18, "ADC sample\n(centre of the low-side window)", ha="right", va="top", fontsize=9, color=MUTED); a1.text(-30.9, 33, "outputs off", ha="left", va="top", fontsize=9, color=CRIT)
a2.annotate("", (-31.4, 16), (-40.9, 16), arrowprops=dict(arrowstyle="<->", color=INK)); a2.text(-36.2, 18, "9.5 µs", ha="center", fontsize=9)
fig.tight_layout(); save(fig, "fig6_oc_latency.png")

# 7 -- regeneration
fig, ax = plt.subplots(figsize=(8.0, 4.0)); labs = ["1000 rpm\n1 A", "1000 rpm\n2 A", "1000 rpm\n3 A", "2000 rpm\n3 A", "2500 rpm\n3 A"]; pk = [12.07, 19.87, 23.0, 30.04, 30.06]
ax.bar(range(5), [p - 11.9 for p in pk], bottom=11.9, width=0.5, color=BLUE)
for i, p in enumerate(pk): ax.text(i, p + 0.4 if p < 29 else p - 1.5, f"{p:.1f} V" if p < 29 else f"{p:.2f} V", ha="center", fontsize=9, color=INK if p < 29 else "white")
ax.set_axisbelow(True); ax.axhline(11.9, color=MUTED, lw=1)
ax.axhline(29.97, color=CRIT, lw=1.2, ls=(0, (5, 3))); ax.text(-0.4, 30.5, "firmware clamp: braking withdrawn above 29.97 V (0.9 × OV limit)", color=CRIT, fontsize=9, ha="left")
ax.set_xticks(range(5)); ax.set_xticklabels(labs); ax.set(ylabel="peak bus voltage (V)", ylim=(10, 34), title="Regeneration: peak bus voltage for one stop to 300 rpm (bus 11.9 V before braking, bare rotor)"); ax.grid(axis="x", visible=False)
save(fig, "fig7_regeneration.png")

# 8 -- thermal
rows = list(csv.DictReader(open(os.path.join(H, "char", "E1", "20261122_182816", "tc_readings.csv"))))
def sec(c): h, m_, s_ = c.split(":"); return int(h) * 3600 + int(m_) * 60 + int(s_)
t0 = sec(rows[0]["clock"]); tt = np.array([(sec(r["clock"]) - t0) / 60 for r in rows]); tc = np.array([float(r["tc_c"]) for r in rows]); ok = ~((tc == 32) & (tt > 12))
fig, ax = plt.subplots(figsize=(8.0, 4.0)); ax.plot(tt[ok], tc[ok], "-o", color=BLUE, ms=6, mec=SURF, mew=1.5)
ax.axvline(10.2, color=MUTED, lw=1, ls=(0, (2, 2))); ax.text(5, 37.6, "3 A hold", ha="center", fontsize=9.5); ax.text(15.5, 37.6, "5 A hold", ha="center", fontsize=9.5)
ax.annotate("+7.5 °C", (10, 34.0), xytext=(-4, -16), textcoords="offset points", ha="right", fontsize=9); ax.annotate("+10.2 °C", (tt[ok][-1], tc[ok][-1]), xytext=(-4, -16), textcoords="offset points", ha="right", fontsize=9)
ax.set(xlabel="time (min)", ylabel="FET case, thermocouple (°C)", ylim=(25, 39), title="Phase A low-side FET temperature, rotor parked, 30 V (start 26.5 °C)"); save(fig, "fig8_thermal.png")

# 9 -- back-EMF
z = Z("BEMF", "20261122_205105", "coast0.npz"); t, a, bb = z["t"] * 1e3, z["a"], z["b"]
fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.6, 4.8), sharex=True)
a1.plot(t, a, color=BLUE, label="phase A"); a1.plot(t, bb, color=ORANGE, label="phase B"); a1.set(ylabel="to ground (V)", ylim=(26, 31.5), title="Coasting after the outputs are switched off: back-EMF (phases float up to the bus)")
a1.legend(frameon=False, ncol=2, loc="lower right"); a1.text(t[0] + 0.2, 31.0, "highest phase clamps at bus + diode drop", fontsize=8.5, color=MUTED)
a2.plot(t, a - bb, color=AQUA); a2.set(xlabel="time (ms)", ylabel="A − B, line-line (V)", ylim=(-4.2, 4.2))
a2.text(t[0] + 0.2, 3.5, "3.04 V peak at 200 Hz electrical (858 rpm)  →  flux constant 1.396 mV·s", fontsize=9)
fig.tight_layout(); save(fig, "fig9_back_emf.png")

# ============================================================== second set: more of the captured waveforms
import json
def J(*p): return json.load(open(os.path.join(H, "char", *p)))
def edge_overlay(ax, items, win=(-40, 160), ylim=None):
    for path, col, lab in items:
        z = Z(*path); t, v = z["t"] * 1e9, z["ch1"]; m = (t > win[0]) & (t < win[1]); ax.plot(t[m], v[m], color=col, label=lab)
    ax.set_xlabel("time from the edge (ns)"); ax.legend(frameon=False, loc="upper right")
    if ylim: ax.set_ylim(*ylim)

# 10 -- first look at the switch node (phase sourcing)
zp, zr, zf = Z("B1", "20261122_171957", "I3A_period.npz"), Z("B1", "20261122_171957", "I3A_rise.npz"), Z("B1", "20261122_171957", "I3A_fall.npz")
fig = plt.figure(figsize=(11, 4.2)); gs = fig.add_gridspec(1, 3, width_ratios=[1.5, 1, 1]); a0, a1, a2 = (fig.add_subplot(g) for g in gs)
a0.plot(zp["t"] * 1e6, zp["ch1"], color=BLUE, lw=1.4); a0.set(xlabel="time (µs)", ylabel="switch node, phase A (V)", title="One PWM period (40 µs)", ylim=(-4, 36))
a0.text(-30, 32.5, "high side on", fontsize=8.5, color=MUTED, ha="center"); a0.text(-10, 3, "low side on", fontsize=8.5, color=MUTED, ha="center")
t, v = zr["t"] * 1e9, zr["ch1"]; m = (t > -260) & (t < 120); a1.plot(t[m], v[m], color=BLUE); a1.set(xlabel="time from the edge (ns)", title="Rising edge (hard)", ylim=(-4, 36))
a1.annotate("dead-time: low-side body\ndiode conducts, ≈ −1 V", (-120, -1), xytext=(-250, 12), fontsize=8.5, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
a1.annotate("7.9 ns, +0.9 V overshoot", (5, float(v[m].max())), xytext=(-250, 33), fontsize=8.5, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
t, v = zf["t"] * 1e9, zf["ch1"]; m = (t > -120) & (t < 260); a2.plot(t[m], v[m], color=BLUE); a2.set(xlabel="time from the edge (ns)", title="Falling edge (soft)", ylim=(-4, 36))
a2.text(40, 18, "38 ns: the load current\ncharges ~5 nF of node\ncapacitance", fontsize=8.5, color=INK)
fig.suptitle("First look at the switch node: phase A sourcing 3 A, 30 V bus, driver-default gate current", x=0.01, ha="left", fontsize=11, fontweight="bold")
fig.tight_layout(); save(fig, "fig10_switch_node_sourcing.png")

# 11 -- three phases
fig, ax = plt.subplots(figsize=(8.2, 4.2))
edge_overlay(ax, ((("B11", "A_20261122_213858", "ID11_3A_sink_fall.npz"), BLUE, "phase A"), (("B7", "B_20261122_210217", "B_sink_fall.npz"), AQUA, "phase B"),
                  (("B11", "C_20261122_213623", "ID11_3A_sink_fall.npz"), ORANGE, "phase C")), ylim=(-9, 34))
limit(ax, -7, "SHx rating −7 V"); ax.set(ylabel="switch node (V)", title="Low-side turn-on on each phase (sinking 3 A, 30 V, 440 / 880 mA gate current)")
ax.annotate("C: −4.6 V", (8, -4.56), xytext=(40, -5.6), fontsize=9, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8)); ax.annotate("A: −2.8 V, B: −3.1 V", (8, -2.9), xytext=(40, -2.9), fontsize=9, va="center", arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
save(fig, "fig11_three_phases.png")

# 12 -- bus voltage and current overlays (zoomed on the region near ground)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.0), sharey=True)
edge_overlay(a1, ((("B8", "20261122_210544", "V12_sink_fall.npz"), AQUA, "12 V bus"), (("B8", "20261122_210736", "V24_sink_fall.npz"), BLUE, "24 V bus"),
                  (("B4neg", "20261122_202344", "ID11_fall.npz"), ORANGE, "30 V bus")), win=(-10, 120), ylim=(-8.5, 6))
a1.set(ylabel="switch node, near ground (V)", title="Bus voltage: phase A, 3 A, 440 / 880 mA"); limit(a1, -7, "SHx rating −7 V")
a1.text(20, 3.5, "minimum −2.7 V at all three", fontsize=9)
edge_overlay(a2, ((("B12", "C_20261122_215058", "ID7_5A_sink_fall.npz"), AQUA, "5 A"), (("B12", "C_20261122_215058", "ID7_7.5A_sink_fall.npz"), BLUE, "7.5 A"),
                  (("B12", "C_20261122_215058", "ID7_10A_sink_fall.npz"), ORANGE, "10 A")), win=(-10, 120), ylim=(-8.5, 6))
a2.set(title="Current: phase C, 30 V, 190 / 380 mA"); limit(a2, -7, "−7 V"); a2.text(20, 3.5, "minimum −0.8 / −0.9 / −1.1 V", fontsize=9)
fig.tight_layout(); save(fig, "fig12_voltage_and_current.png")

# 13 -- phase C sampling window (timing from the switch node; ADC instants from the firmware's sequence and clock)
fig, axs = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
for ax, (cm, win) in zip(axs, ((90, 4.0), (95, 2.0))):
    z = Z("C1b", "20261122_173922", f"C1b_cm{cm}.npz"); t, n = z["t"] * 1e6, z["ch1"]; m = (t > -1.0) & (t < win + 2.5)
    ax.plot(t[m], n[m], color=BLUE); ax.set(title=f"{cm} % duty: low-side window {win:g} µs", ylim=(-6, 40), xlabel="time from phase C's falling edge (µs)")
    ax.axvline(win / 2, color=MUTED, lw=1.2, ls=(0, (2, 2))); ax.axvspan(win / 2 + 0.87, win / 2 + 1.45, color=CRIT, alpha=0.18, lw=0)
    ax.text(win / 2 - 0.06, 37, "A and B\nsampled", ha="right", va="top", fontsize=8.5, color=MUTED); ax.text(win / 2 + 0.9, 37, "C sampled", ha="left", va="top", fontsize=8.5, color=CRIT)
    ax.text(win / 2, 8, "low side on:\nshunt carries the current", ha="center", fontsize=8.5, color=INK)
axs[0].set_ylabel("phase C switch node (V)"); axs[0].text(4.6, 14, "still inside\nthe window", fontsize=8.5, color=INK, ha="center"); axs[1].text(2.75, 14, "window already\nclosed: reads half", fontsize=8.5, color=INK, ha="left")
fig.suptitle("Why phase C reads wrong at high duty: it is converted 0.87–1.45 µs after A and B", x=0.01, ha="left", fontsize=11, fontweight="bold")
fig.tight_layout(); save(fig, "fig13_phase_c_sampling.png")

# 14 -- supply rails while spinning
z = Z("A3", "20261122_181829", "spin2000_OFF.npz"); t = z["t"] * 1e6
fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.6, 4.4), sharex=True)
a1.plot(t, z["ch1"] * 1e3, color=BLUE, lw=1.2); a1.set(ylabel="+3.3 V rail, AC (mV)", ylim=(-80, 80), title="Supply rails while the motor spins at 2000 rpm (AC-coupled)")
a2.plot(t, z["ch2"] * 1e3, color=ORANGE, lw=1.2); a2.set(ylabel="+5 V rail, AC (mV)", ylim=(-80, 80), xlabel="time (µs)")
a2.text(0.01, 0.06, "≈ 100 mV p-p at 120–160 kHz: the 5 V converter's own light-load ripple", transform=a2.transAxes, fontsize=8.5, color=MUTED)
fig.tight_layout(); save(fig, "fig14_rails.png")

# 15 -- bus ripple, static hold
z = Z("B5", "20261122_174829", "I3A_period.npz"); t = z["t"] * 1e6
fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.6, 4.4), sharex=True, gridspec_kw={"height_ratios": [1, 1.4]})
a1.plot(t, z["ch2"], color=BLUE, lw=1.2); a1.set(ylabel="phase A node (V)", title="Bus ripple over one PWM period (3 A hold, 30 V, bus AC-coupled)")
a2.plot(t, z["ch1"] * 1e3, color=ORANGE, lw=1.2); a2.set(ylabel="bus, AC (mV)", xlabel="time (µs)")
a2.text(0.01, 0.9, "≈ 20 mV between edges; spikes of up to ±0.4 V for ~20 ns at the hard edges", transform=a2.transAxes, fontsize=8.5, color=MUTED)
fig.tight_layout(); save(fig, "fig15_bus_ripple.png")

# 16 -- brown-out
bo = J("NP", "20261122_195422", "results.json")["brownout"]; dn, up = bo[:27], bo[27:]
fig, ax = plt.subplots(figsize=(8.0, 4.0))
ax.plot([r["psu_set"] for r in dn], [r["psu_ma"] for r in dn], "-o", color=BLUE, ms=5, mec=SURF, mew=1.2, label="supply falling")
ax.plot([r["psu_set"] for r in up], [r["psu_ma"] for r in up], "-o", color=ORANGE, ms=5, mec=SURF, mew=1.2, label="supply rising")
ax.axvspan(3.5, 5.5, color=CRIT, alpha=0.10, lw=0); ax.text(5.8, 3, "no answer at 4 V;\nrestarts between 5 and 6 V", fontsize=9, color=CRIT, va="bottom")
ax.annotate("64 mA at 5 V", (5, 64), xytext=(8, 66), fontsize=9, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8)); ax.annotate("13 mA at 30 V", (30, 13), xytext=(24, 22), fontsize=9, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
ax.set(xlabel="bus voltage (V)", ylabel="supply current, board idle (mA)", ylim=(0, 75), title="Brown-out sweep: constant-power input, clean shut-down and restart"); ax.legend(frameon=False, loc="upper right")
save(fig, "fig16_brownout.png")

# 17 -- regeneration against time (values polled over the serial link, ~45 ms apart)
fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.6, 4.8), sharex=True)
for path, col, lab in ((("REGEN", "12V_20261122_221408", "results.json"), AQUA, "from 1000 rpm"), (("REGEN", "12V_20261122_221703", "results.json"), BLUE, "from 2000 rpm"), (("REGEN", "12V_20261122_221751", "results.json"), ORANGE, "from 2500 rpm")):
    r = [x for x in J(*path) if x.get("brake_a") == 3.0][-1]; s = np.array(r["samples"]); s = s[s[:, 0] < 0.9]
    a1.plot(s[:, 0] * 1e3, s[:, 1], "-o", color=col, ms=4, mec=SURF, mew=1, label=lab); a2.plot(s[:, 0] * 1e3, s[:, 2], "-o", color=col, ms=4, mec=SURF, mew=1)
a1.set(ylabel="speed (rpm)", title="Braking at 3 A to 300 rpm on a 12 V bus"); a1.legend(frameon=False, loc="upper right")
a2.axhline(29.97, color=CRIT, lw=1.2, ls=(0, (5, 3))); a2.text(880, 30.5, "clamp level 29.97 V", color=CRIT, fontsize=9, ha="right"); a2.set(ylabel="bus voltage (V)", xlabel="time after the speed command dropped (ms)", ylim=(10, 33))
a2.text(880, 13.2, "the bus falls back as the board's own consumption drains it", fontsize=8.5, color=MUTED, ha="right")
fig.tight_layout(); save(fig, "fig17_regen_time.png")

# 18 -- why identification read 98 mOhm
fw = J("FW", "20261122_204048", "results.json")["hold"]; I = [h["ia"] for h in fw]; R = [1e3 * h["v_alpha"] / h["ia"] for h in fw]
fig, ax = plt.subplots(figsize=(7.6, 4.0)); ax.plot(I, R, "-o", color=BLUE, ms=7, mec=SURF, mew=1.5)
for x, y in zip(I, R): ax.annotate(f"{y:.0f}", (x, y), xytext=(0, 9), textcoords="offset points", ha="center", fontsize=9)
ax.axhline(18, color=AQUA, lw=1.5); ax.text(5.15, 19.5, "winding, 4-wire: 18 mΩ", fontsize=9, ha="right"); ax.axhline(30, color=MUTED, lw=1.2, ls=(0, (2, 2))); ax.text(5.15, 32, "winding + bridge path: ≈ 30 mΩ", fontsize=9, ha="right", color=MUTED)
ax.axhline(98, color=CRIT, lw=1.2, ls=(0, (5, 3))); ax.text(0.75, 86, "value identified in September\nat ≤ 1 A: 98 mΩ", fontsize=9, ha="left", color=CRIT)
ax.set(xlabel="hold current (A)", ylabel="apparent resistance, V ÷ I (mΩ)", ylim=(0, 160), xlim=(0.7, 5.2), title="The bridge's voltage error looks like resistance at low current")
save(fig, "fig18_apparent_resistance.png")
