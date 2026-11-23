#!/usr/bin/env python3
"""instruments.py -- bench instruments for the characterization (CHARACTERIZATION_PLAN.md).

Psu   : Korad KA3005P over its USB virtual COM (9600 8N1, commands without terminator, ~50 ms between commands).
Scope : Rigol DHO804 over USB-TMC (pyvisa, '@py' backend: pyvisa-py + pyusb + libusb-package).

Run with:  uv run --no-project --python 3.12 --with pyserial --with pyvisa --with pyvisa-py --with pyusb --with libusb-package \
           --with numpy python instruments.py          (prints identities and the PSU state; changes nothing)
"""
import glob, time

PSU_PORT_GLOB = "/dev/cu.usbmodem*"
SCOPE_ID_HINT = "DHO8"


class Psu:
    def __init__(self, port=None):
        import serial
        port = port or sorted(glob.glob(PSU_PORT_GLOB))[0]
        self.s = serial.Serial(port, 9600, timeout=0.3)
        self.port = port

    def _q(self, cmd, n=64):
        self.s.reset_input_buffer()
        self.s.write(cmd.encode()); time.sleep(0.08)
        return self.s.read(n).decode(errors="replace").strip()

    def _w(self, cmd):
        self.s.write(cmd.encode()); time.sleep(0.08)

    def idn(self):        return self._q("*IDN?")
    def vset(self):       return float(self._q("VSET1?") or "nan")
    def iset(self):       return float(self._q("ISET1?") or "nan")
    def vout(self):       return float(self._q("VOUT1?") or "nan")
    def iout(self):       return float(self._q("IOUT1?") or "nan")

    def status(self):
        """STATUS? returns one byte: bit0 CH1 CC(0)/CV(1), bit6 output on/off."""
        self.s.reset_input_buffer(); self.s.write(b"STATUS?"); time.sleep(0.08)
        b = self.s.read(1)
        if not b: return None
        v = b[0]
        return {"raw": v, "cv": bool(v & 0x01), "output_on": bool(v & 0x40)}

    def set_v(self, v):   self._w(f"VSET1:{v:05.2f}")
    def set_i(self, a):   self._w(f"ISET1:{a:05.3f}")
    def output(self, on): self._w("OUT1" if on else "OUT0")

    def off_and_wait(self, below_v=1.0, timeout=5.0):
        """Output off, then wait until the terminal voltage reads below `below_v` (board caps drained by the board)."""
        self.output(False)
        t0 = time.time()
        while time.time() - t0 < timeout:
            if self.vout() < below_v: return True
            time.sleep(0.2)
        return False


class Scope:
    def __init__(self):
        import pyvisa
        self.rm = pyvisa.ResourceManager("@py")
        res = [r for r in self.rm.list_resources() if r.startswith("USB")]
        self.inst = None
        for r in res:
            try:
                i = self.rm.open_resource(r); i.timeout = 10000
                if SCOPE_ID_HINT in i.query("*IDN?"): self.inst = i; self.res = r; break
            except Exception:
                pass
        if self.inst is None: raise RuntimeError(f"no {SCOPE_ID_HINT} among {res}")

    def q(self, c):  return self.inst.query(c).strip()
    def w(self, c):  self.inst.write(c)
    def idn(self):   return self.q("*IDN?")

    # ---------------------------------------------------------------- setup
    def chan(self, n, on=True, scale=1.0, offset=0.0, probe=10, coupling="DC", bwl="OFF"):
        self.w(f":CHANnel{n}:DISPlay {'ON' if on else 'OFF'}")
        if not on: return
        self.w(f":CHANnel{n}:PROBe {probe}"); self.w(f":CHANnel{n}:COUPling {coupling}")
        self.w(f":CHANnel{n}:BWLimit {bwl}"); self.w(f":CHANnel{n}:SCALe {scale}"); self.w(f":CHANnel{n}:OFFSet {offset}")

    def timebase(self, scale, offset=0.0):
        self.w(f":TIMebase:MAIN:SCALe {scale}"); self.w(f":TIMebase:MAIN:OFFSet {offset}")

    def trig_edge(self, src=1, level=0.0, slope="POSitive", sweep="NORMal"):
        self.w(":TRIGger:MODE EDGE"); self.w(f":TRIGger:EDGE:SOURce CHANnel{src}")
        self.w(f":TRIGger:EDGE:SLOPe {slope}"); self.w(f":TRIGger:EDGE:LEVel {level}"); self.w(f":TRIGger:SWEep {sweep}")

    def single(self, timeout=3.0):
        """Arm one acquisition and wait for it; True if it triggered.
        Bench 2026-11-22: after a channel/timebase change the DHO804 reports a transient STOP (~0.5 s) and then goes back
        to WAIT while it re-arms; reading at that first STOP gave empty/stale records. STOP must now hold for 0.4 s."""
        self.w(":SINGle"); t0 = time.time()
        # first wait until the scope has actually re-armed (it may still show the previous STOP): otherwise the old
        # record is read back again (seen 2026-11-22: identical numbers from two "different" captures)
        while time.time() - t0 < 1.0 and self.q(":TRIGger:STATus?").upper().startswith("STOP"): time.sleep(0.02)
        t0 = time.time(); stop_since = None
        while time.time() - t0 < timeout:
            st = self.q(":TRIGger:STATus?").upper()
            if st.startswith("STOP"):
                stop_since = stop_since or time.time()
                if time.time() - stop_since >= 0.4: return True
            else:
                stop_since = None
            time.sleep(0.05)
        self.w(":STOP"); return False

    def single_forced(self, settle=0.3, wait=0.8):
        """One fresh acquisition at a random time (for noise / ripple): NORMal sweep, :SINGle, then force the trigger.
        Bench 2026-11-22: :SINGle with AUTO sweep returned the previous record again; this does not."""
        self.w(":TRIGger:SWEep NORMal"); self.w(":SINGle"); time.sleep(settle); self.w(":TFORce"); time.sleep(wait)
        return self.q(":TRIGger:STATus?").upper().startswith("STOP")

    def single_valid(self, ch=1, timeout=3.0, tries=2):
        """single() + a sanity check that channel `ch` holds real data (>= 20 distinct values); one retry."""
        import numpy as np
        for _ in range(tries):
            if self.single(timeout):
                _, v = self.read(ch)
                if len(np.unique(v)) >= 20: return True
        return False

    def read(self, n):
        """Displayed-record waveform of channel n: (t[s], v[V]) as numpy arrays (WORD, NORMal mode)."""
        import numpy as np
        self.w(f":WAVeform:SOURce CHANnel{n}"); self.w(":WAVeform:MODE NORMal"); self.w(":WAVeform:FORMat WORD")
        pre = [float(x) for x in self.q(":WAVeform:PREamble?").split(",")]
        raw = self.inst.query_binary_values(":WAVeform:DATA?", datatype="H", is_big_endian=False, container=np.array)
        xinc, xorg, xref, yinc, yorg, yref = pre[4], pre[5], pre[6], pre[7], pre[8], pre[9]
        t = (np.arange(len(raw)) - xref) * xinc + xorg
        v = (raw.astype(float) - yorg - yref) * yinc
        return t, v

    def screenshot(self, path):
        try:
            png = self.inst.query_binary_values(":DISPlay:DATA? PNG", datatype="B", container=bytes)
            open(path, "wb").write(png); return True
        except Exception as e:
            print("   screenshot failed:", e); return False


if __name__ == "__main__":
    p = Psu()
    print("PSU  ", p.port, "|", p.idn())
    print("      set", p.vset(), "V", p.iset(), "A | out", p.vout(), "V", p.iout(), "A |", p.status())
    s = Scope()
    print("SCOPE", s.res, "|", s.idn())
