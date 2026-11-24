"""annotate_scope.py -- annotated copies of the DHO804 screenshots used in the top-level README.

The screenshot is left as captured. Callout positions come from the matching .npz record (the scope's own
1000-point screen data), mapped onto the 1024 x 600 screenshot: 10 horizontal divisions of 100 px from x = 12,
8 vertical divisions of 51.75 px about y = 300. Values written in the callouts are the ones in CHAR_LOG.md
(taken from the full-resolution records), not the 1000-point screen data.

    python3 annotate_scope.py <Testing/Bench/char> <output dir>
"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

S = 2                                   # output scale
X0, DIVX, YC, DIVY = 12, 100, 300, 51.75
BG, FG, MUTED = (17, 17, 17), (240, 240, 240), (170, 170, 170)
ORANGE, RED, GREEN = (255, 159, 28), (255, 77, 77), (61, 220, 132)
YEL, CYAN = (230, 220, 40), (40, 215, 230)


def font(weight, size):
    for p in (f'/usr/share/fonts/opentype/inter/Inter-{weight}.otf', '/Library/Fonts/Inter-{weight}.otf'):
        if os.path.exists(p):
            return ImageFont.truetype(p, size * S)
    return ImageFont.load_default()


F_TITLE, F_SUB, F_CALL, F_LEG = font('SemiBold', 19), font('Regular', 14), font('Medium', 14), font('Regular', 13)


class Fig:
    def __init__(self, png, npz):
        self.d = np.load(npz)
        t = self.d['t']
        self.t0, self.span = t[0], (t[1] - t[0]) * 1000
        self.img = Image.open(png).convert('RGB').resize((1024 * S, 600 * S), Image.LANCZOS)
        self.ov = Image.new('RGBA', self.img.size, (0, 0, 0, 0))
        self.dr = ImageDraw.Draw(self.ov)
        self.ch = {}

    def channel(self, key, scale, center):
        self.ch[key] = (scale, center)

    def px(self, t, v=None, key=None):
        x = (X0 + (t - self.t0) / self.span * 1000) * S
        if v is None:
            return x
        scale, center = self.ch[key]
        return x, (YC - (v - center) / scale * DIVY) * S

    # primitives -------------------------------------------------------------------------------
    def hline(self, v, key, text, col=RED, side='left'):
        _, y = self.px(self.t0, v, key)
        x0, x1 = X0 * S, (X0 + 1000) * S
        for x in range(int(x0), int(x1), 14 * S):
            self.dr.line([(x, y), (min(x + 8 * S, x1), y)], fill=col + (255,), width=2 * S)
        w = self.dr.textlength(text, font=F_LEG)
        tx = x0 + 70 * S if side == 'left' else x1 - w - 70 * S
        self.dr.rectangle([tx - 4 * S, y - 20 * S, tx + w + 4 * S, y - 3 * S], fill=BG + (220,))
        self.dr.text((tx, y - 19 * S), text, font=F_LEG, fill=col)

    def vline(self, t, text, col=ORANGE, ytext=110, left=False):
        x = self.px(t)
        for y in range(95 * S, 505 * S, 12 * S):
            self.dr.line([(x, y), (x, y + 6 * S)], fill=col + (255,), width=2 * S)
        w = max(self.dr.textlength(l, font=F_CALL) for l in text.split('\n'))
        self._box(x - w - 18 * S if left else x + 6 * S, ytext * S, text, col)

    def bracket(self, t1, t2, y, text, col=ORANGE, below=False):
        x1, x2, y = self.px(t1), self.px(t2), y * S
        self.dr.line([(x1, y), (x2, y)], fill=col, width=2 * S)
        for x in (x1, x2):
            self.dr.line([(x, y - 7 * S), (x, y + 7 * S)], fill=col, width=2 * S)
        w = self.dr.textlength(text, font=F_CALL)
        bx = (x1 + x2) / 2 - w / 2
        self._box(bx, y + (10 * S if below else -32 * S), text, col)

    def call(self, t, v, key, text, dx, dy, col=ORANGE):
        """Callout box offset (dx, dy) px from the data point, with a leader line and a ring on the point."""
        x, y = self.px(t, v, key)
        lines = text.split('\n')
        w = max(self.dr.textlength(l, font=F_CALL) for l in lines)
        h = len(lines) * 19 * S
        bx = min(max(x + dx * S, 16 * S), (1006 - 12) * S - w)
        by = min(max(y + dy * S, 128 * S), 478 * S - h - 8 * S)
        cx = min(max(x, bx), bx + w + 12 * S)
        cy = by if y < by else by + h + 8 * S
        self.dr.line([(x, y), (cx, cy)], fill=col, width=2 * S)
        r = 5 * S
        self.dr.ellipse([x - r, y - r, x + r, y + r], outline=col, width=2 * S)
        self._box(bx, by, text, col)

    def _box(self, x, y, text, col):
        lines = text.split('\n')
        w = max(self.dr.textlength(l, font=F_CALL) for l in lines)
        h = len(lines) * 19 * S
        self.dr.rounded_rectangle([x, y, x + w + 12 * S, y + h + 8 * S], radius=4 * S,
                                  fill=BG + (230,), outline=col, width=2 * S)
        for i, l in enumerate(lines):
            self.dr.text((x + 6 * S, y + 4 * S + i * 19 * S), l, font=F_CALL, fill=FG)

    # output -------------------------------------------------------------------------------------
    def save(self, path, title, sub, legend):
        body = Image.alpha_composite(self.img.convert('RGBA'), self.ov).convert('RGB')
        head, foot = 66 * S, (12 + 19 * len(legend)) * S
        out = Image.new('RGB', (body.width, body.height + head + foot), BG)
        out.paste(body, (0, head))
        d = ImageDraw.Draw(out)
        d.text((14 * S, 10 * S), title, font=F_TITLE, fill=FG)
        d.text((14 * S, 38 * S), sub, font=F_SUB, fill=MUTED)
        y = head + body.height + 6 * S
        for col, txt in legend:
            if col:
                d.rectangle([14 * S, y + 5 * S, 30 * S, y + 9 * S], fill=col)
            d.text((38 * S if col else 14 * S, y), txt, font=F_LEG, fill=MUTED if not col else FG)
            y += 19 * S
        out = out.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        out.save(path, optimize=True)
        print(path, out.size, os.path.getsize(path) // 1024, 'KB')


NS, US = 1e-9, 1e-6
LEG_RIGHT2 = (None, 'Right-hand scale belongs to CH2. Hand-held 10x probes, spring ground at the shunt ground end; '
                    '70 MHz scope, so fast peaks read low.')


def figs(char, out):
    c = lambda p: (os.path.join(char, p + '.png'), os.path.join(char, p + '.npz'))

    # 1. sourcing: the healthy edge ---------------------------------------------------------------
    f = Fig(*c('B1/20261122_171957/I3A_rise')); f.channel('ch1', 5, 15)
    f.bracket(-205 * NS, -9 * NS, 395, 'dead time 203 ns: low-side body diode, −1.0 V', below=True)
    f.call(4 * NS, 15, 'ch1', 'hard edge 7.9 ns (3.1 V/ns)', 30, 20)
    v = f.d['ch1']; i = int(np.argmax(v))
    f.call(f.d['t'][i], v[i], 'ch1', '30.5 V peak: +0.9 V overshoot', 40, -10)
    f.save(os.path.join(out, 'scope_01_sourcing_edge.png'),
           'Phase A sourcing 3 A: high-side turn-on looks clean',
           '30 V bus, rotor parked by a current vector, gate drive at the DRV8323 power-on default (1000 / 2000 mA)',
           [(YEL, 'CH1  phase A switch node, 5 V/div'), (CYAN, 'CH2  phase A current-sense output (SOA)'), LEG_RIGHT2])

    # 2-3. sinking: the hard edge moves to the low side ----------------------------------------------
    for name, out_name, ttl, low, txt in (
            ('ID15_fall', 'scope_02_lowside_default.png', 'Phase A sinking 3 A: -10 V at the gate driver default',
             'DRV8323 power-on default gate drive, 1000 / 2000 mA', '−10.0 V: beyond the −7 V rating\nrings ~90 MHz for ~80 ns'),
            ('ID7_fall', 'scope_03_lowside_slow.png', 'Same edge at 190 / 380 mA gate drive: −0.8 V',
             'gate drive 190 / 380 mA, now the firmware power-up value', '−0.76 V: body diode only, no ringing\nedge 18.4 ns (was 7.1 ns)')):
        f = Fig(*c('B4neg/20261122_202344/' + name)); f.channel('ch1', 10, 10)
        f.hline(-7, 'ch1', 'DRV8323 SHx absolute max −7 V', side='right')
        v = f.d['ch1']; w = np.abs(f.d['t']) < 60 * NS; i = int(np.argmin(np.where(w, v, 99)))
        bad = 'beyond' in txt
        f.call(f.d['t'][i], v[i], 'ch1', txt, 45 if bad else -330, 20, col=RED if bad else GREEN)
        f.call(-120 * NS, 30.3, 'ch1', 'bus + 0.65 V: high-side body diode\nconducts during the dead time', -40, 45)
        f.save(os.path.join(out, out_name), ttl, '30 V bus, phase A current reversed (rotor parked 180 electrical degrees on), ' + low,
               [(YEL, 'CH1  phase A switch node, 10 V/div'), (CYAN, 'CH2  phase A current-sense output (SOA)'), LEG_RIGHT2])

    # 4. shunt pins ---------------------------------------------------------------------------------
    f = Fig(*c('B6/20261122_202903/ID15_sink_fall')); f.channel('ch1', 2, 0)
    f.hline(-3, 'ch1', 'SPx / SNx / SLx absolute max −3 V', side='right')
    f.hline(3, 'ch1', '+3 V', side='right')
    v = f.d['ch1']; i = int(np.argmin(v))
    f.call(f.d['t'][i], v[i], 'ch1', '−4.6 V across the 3 mΩ shunt\n(beyond −3 V for 4.5 ns)', 60, 25, col=RED)
    f.save(os.path.join(out, 'scope_04_shunt_pins.png'),
           'The same edge across the phase A shunt: −4.6 V on pins rated −3 V',
           '30 V bus, phase A sinking 3 A, default gate drive 1000 / 2000 mA. At 440 / 880 mA it is −2.4 V',
           [(YEL, 'CH1  shunt A, sense end to ground end, 2 V/div'),
            (CYAN, 'CH2  phase A switch node, trigger only: long ground lead, amplitude not valid'), LEG_RIGHT2])

    # 5. phase C at 10 A ---------------------------------------------------------------------------
    f = Fig(*c('B12/C_20261122_215058/ID7_10A_sink_fall')); f.channel('ch1', 10, 10)
    f.hline(-7, 'ch1', 'DRV8323 SHx absolute max −7 V', side='right')
    v = f.d['ch1']; i = int(np.argmin(v))
    f.call(f.d['t'][i], v[i], 'ch1', '−1.1 V at 10 A, edge 18.4 ns\n(−0.06 V per amp from 5 A)', 45, 32, col=GREEN)
    f.save(os.path.join(out, 'scope_05_phaseC_10A.png'),
           'Phase C sinking 10 A at 190 / 380 mA gate drive',
           '30 V bus, 5.8 W into the whole board. Other probe placements on phase C read up to ~2.5 V more negative',
           [(YEL, 'CH1  phase C switch node, 10 V/div'), (CYAN, 'CH2  not used'), LEG_RIGHT2])

    # 6. firmware over-current latency -----------------------------------------------------------------
    f = Fig(*c('D1b/20261122_210005/trip0')); f.channel('a', 10, 10); f.channel('b', 10, 10)
    f.vline(-40.9 * US, 'ADC sample: centre of\nphase B low-side window', ytext=410, left=True)
    f.vline(-31.4 * US, 'outputs off', col=RED, ytext=410)
    f.bracket(-40.9 * US, -31.4 * US, 140, '9.5 µs')
    f.call(10 * US, 30, 'a', 'A floats at the bus after the trip', 60, 40)
    f.save(os.path.join(out, 'scope_06_firmware_trip.png'),
           'Firmware over-current trip: outputs off 9.5 µs after the sample that sees it',
           '30 V bus, phase A duty stepped 50 → 53 % so its current ramps through a 2.5 A limit. Same in 4 of 4 trips',
           [(YEL, 'CH1  phase A switch node, 10 V/div'), (CYAN, 'CH2  phase B switch node, 10 V/div'),
            (None, 'One sample per 40 µs PWM period, so the worst case from the limit being crossed is about 50 µs.'), LEG_RIGHT2])

    # 7. gate-driver VDS trip --------------------------------------------------------------------------
    f = Fig(*c('F2/20261122_214445/ceil22_3')); f.channel('a', 10, 10); f.channel('soa', 0.5, 1.65)
    t, a = f.d['t'], f.d['a']; last = t[np.where(a[t < 0] < 5)[0][-1]]
    f.vline(last, 'DRV8323 VDS trip\n0.06 V = 22 A', col=RED, ytext=415)
    f.call(-300 * US, 1.85, 'soa', 'duty step: phase A current\nramps ~1.8 A per period', -170, 45)
    f.call(-60 * US, 2.95, 'soa', 'last plateau 21.8 A\n(firmware ceiling 22 A)', -260, -75)
    f.save(os.path.join(out, 'scope_07_vds_trip.png'),
           'Short-circuit protection: the gate driver trips at 22 A',
           '30 V bus, DRV8323 VDS threshold at its lowest (0.06 V). Tripped before the firmware in 3 of 3 runs',
           [(YEL, 'CH1  phase A switch node, 10 V/div'), (CYAN, 'CH2  phase A current-sense output, 60 mV/A'),
            (None, 'Threshold = 0.06 V / 2.7 mΩ (FET on-resistance). The power-on 0.75 V setting is therefore about 280 A.'),
            LEG_RIGHT2])

    # 8. back-EMF --------------------------------------------------------------------------------------
    f = Fig(*c('BEMF/20261122_205105/coast0')); f.channel('a', 5, 15); f.channel('b', 5, 15)
    f.call(-7.6 * US * 1000, 27.0, 'a', 'outputs off, rotor coasting ~860 rpm:\nphases float just under the 30 V bus', 40, 60)
    i = int(np.argmax(f.d['a'] - f.d['b']))
    f.call(f.d['t'][i], f.d['a'][i], 'a', 'line-line A−B 3.04 V peak\n→ flux 1.396 mV·s (firmware value 1.389)', 60, 70)
    f.save(os.path.join(out, 'scope_08_back_emf.png'),
           'Back-EMF while coasting: motor flux constant measured directly',
           'Sensorless spin to 1000 rpm, then outputs off. Three runs agree within 0.5 %',
           [(YEL, 'CH1  phase A, 5 V/div'), (CYAN, 'CH2  phase B, 5 V/div'), LEG_RIGHT2])

    # 9. bus ripple ------------------------------------------------------------------------------------
    f = Fig(*c('B5b/20261122_180422/steady_3000')); f.channel('ch1', 0.156, 0)
    f.call(-20 * US, 0.03, 'ch1', '79 mV p-p between edges', -60, -95)
    v = f.d['ch1']; i = int(np.argmin(v))
    f.call(f.d['t'][i], v[i], 'ch1', '281 mV p-p spikes at the edges', 30, 90)
    f.save(os.path.join(out, 'scope_09_bus_ripple.png'),
           'DC bus at the input terminals, motor spinning at 3000 rpm',
           'Sensorless closed loop, 30 V, 21 W from the supply. 58 mV p-p at 1000 rpm',
           [(YEL, 'CH1  bus (+VPROT to GND at the input pads), AC coupled, 156 mV/div'),
            (CYAN, 'CH2  phase A switch node, 10 V/div'),
            (None, 'Right-hand scale belongs to CH1. Hand-held 10x probe, spring ground.')])


if __name__ == '__main__':
    os.makedirs(sys.argv[2], exist_ok=True)
    figs(sys.argv[1], sys.argv[2])
