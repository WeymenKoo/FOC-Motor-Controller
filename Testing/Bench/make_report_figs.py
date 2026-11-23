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
