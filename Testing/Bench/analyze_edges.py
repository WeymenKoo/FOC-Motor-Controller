#!/usr/bin/env python3
"""analyze_edges.py <dir> -- switch-node edge metrics from char_b1 / char_b4 captures (*.npz)."""
import glob, json, os, sys
import numpy as np


def metrics(t, v, vb, rising):
    hi = np.median(v[v > vb * 0.8]); lo = np.median(v[v < vb * 0.2]); sw = hi - lo
    def cross(level, r):
        idx = np.where((v[:-1] < level) & (v[1:] >= level))[0] if r else np.where((v[:-1] > level) & (v[1:] <= level))[0]
        if not len(idx): return None
        i = idx[np.argmin(abs(t[idx]))]; dt = t[1] - t[0]
        return t[i] + (level - v[i]) / (v[i + 1] - v[i]) * dt
    o = {"high": hi, "low": lo, "peak": v.max(), "min": v.min(), "overshoot": v.max() - hi, "undershoot": lo - v.min()}
    a, b = cross(lo + 0.1 * sw, rising), cross(lo + 0.9 * sw, rising)
    if a is not None and b is not None:
        o["t10_90_ns"] = abs(b - a) * 1e9; o["dvdt_V_ns"] = 0.8 * sw / abs(b - a) / 1e9
    t0 = cross(lo + 0.5 * sw, rising)
    if t0 is not None:
        fin = hi if rising else lo; m = (t > t0 + 5e-9) & (t < t0 + 300e-9); e = v[m] - fin; tt = t[m]
        zc = np.where(np.diff(np.sign(e)) != 0)[0]
        if len(zc) >= 3: o["ring_MHz"] = 1e-6 / (2 * np.mean(np.diff(tt[zc])))
        if rising:   # diode plateau before the hard edge = dead time
            j = np.searchsorted(t, t0)
            while j > 0 and v[j] > -0.5: j -= 1
            k = j
            while k > 0 and v[k] < -0.5: k -= 1
            o["deadtime_ns"] = (t[j] - t[k]) * 1e9
    return o


if __name__ == "__main__":
    d = sys.argv[1]
    for f in sorted(glob.glob(os.path.join(d, "*_rise.npz")) + glob.glob(os.path.join(d, "*_fall.npz"))):
        z = np.load(f); meta = json.loads(str(z["meta"])); vb = float(meta["vbat_voltage"])
        o = metrics(z["t"], z["ch1"], vb, f.endswith("_rise.npz"))
        print(f"{os.path.basename(f)[:-4]:10s} " + "  ".join(f"{k}={v:.2f}" for k, v in o.items()))
