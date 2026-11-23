#!/usr/bin/env python3
"""motor_r.py <pair-label> -- 4-wire winding resistance: PSU in constant current (3 V compliance) through two motor pins,
user's DMM (mV DC) directly on the same pins. The motor is UNPLUGGED from the board; the board is unpowered.
Holds 2.000 A then 3.000 A; logs the PSU's own terminal voltage (includes its leads) -> char/MOTOR_R/motor_r.csv."""
import csv, os, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); label = sys.argv[1]; sys.argv = sys.argv[:1]; sys.path.insert(0, HERE)
import char_b1 as b
from instruments import Psu

psu = Psu(); rows = []
try:
    psu.output(False); psu.set_v(3.0); psu.set_i(2.0); time.sleep(0.3)
    vs = psu.vset()
    if not (2.9 <= vs <= 3.1): raise SystemExit(f"PSU voltage setting is {vs} V, expected 3 V -- not enabling the output")
    for k in range(5, 0, -1): b.say(str(k))
    psu.output(True)
    for amps, word in ((2.0, "two"), (3.0, "three")):
        psu.set_i(amps); time.sleep(2.5); b.say(f"read now, {word} amps")
        s = []; t0 = time.time()
        while time.time() - t0 < 7: s.append((psu.vout(), psu.iout(), psu.status()["cv"])); time.sleep(0.3)
        v, i = statistics.mean(x[0] for x in s), statistics.mean(x[1] for x in s); cv = any(x[2] for x in s)
        rows.append((label, amps, v, i, cv))
        print(f"  {label} @ {amps:g} A: PSU terminals {v:.3f} V, {i:.3f} A -> {1e3*v/i:.1f} mOhm incl. leads"
              + ("   WARNING: supply in CV (voltage-limited): current not reached" if cv else ""), flush=True)
finally:
    psu.output(False); time.sleep(0.5); psu.set_i(2.0); psu.set_v(30.0); b.say("done, output off")
os.makedirs(os.path.join(HERE, "char", "MOTOR_R"), exist_ok=True)
p = os.path.join(HERE, "char", "MOTOR_R", "motor_r.csv"); new = not os.path.exists(p)
with open(p, "a", newline="") as f:
    w = csv.writer(f)
    if new: w.writerow(["time", "pair", "amps_set", "psu_v", "psu_a", "psu_in_cv", "dmm_mV"])
    for r in rows: w.writerow([time.strftime("%H:%M:%S")] + [r[0], r[1], f"{r[2]:.4f}", f"{r[3]:.4f}", r[4], ""])
