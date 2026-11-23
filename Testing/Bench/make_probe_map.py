#!/usr/bin/env python3
"""make_probe_map.py -- PROBE_MAP.png / .pdf: top view of the Rev A board with every test point, probe pad and usable
ground pad labelled, colour-coded by how safe it is to touch with a hand-held probe while powered.

Labels are placed collision-free with leader lines (no label may hide another or sit on another pad). Ground pads: only
top-side passives 0603 or larger with a pad on GND; the label names the part's OTHER net, and a red outline marks parts
whose other end is a power net (a clip bridging both pads would short it).

  QT_QPA_PLATFORM=offscreen ~/foc-venv/bin/python make_probe_map.py      (kicad-cli 10 + PySide6)
"""
import math, os, re, subprocess, sys, tempfile

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QColor, QFont, QFontMetricsF, QGuiApplication, QImage, QPageLayout, QPageSize, QPainter,
                           QPdfWriter, QPen)
from PySide6.QtSvg import QSvgRenderer

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "..", "..", "Hardware", "FoC Motor Controller.kicad_pcb")
KICAD = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
BIG = re.compile(r"(0603|0805|1206|1210|1812|2010|2512|1608Metric|2012Metric|3216Metric|3225Metric|6332Metric|CP_|C_Elec)")
POWER_NETS = re.compile(r"(VPROT|VBAT|VM\b|OUT_[ABC]|SOURCE_|SH[ABC]|VIN|\+12V|\+24V)", re.I)

CAT = {  # colour, legend text
    "power": ("#FF3CF2", "Power pad / switch node: BIG pad, OK to probe (power off while placing)"),
    "danger": ("#FF2D3B", "Gate / switch-node test pad: 30 V next to gates, 1.3 mm apart -- NEVER probe while powered"),
    "analog": ("#35F06A", "Low-voltage analog (0-3.3 V): safe to probe live"),
    "logic": ("#3FE0FF", "3.3 V logic: safe to probe live"),
    "rail": ("#FFD21F", "Supply rail test point: safe to probe live"),
    "gnd": ("#7FA8FF", "Ground clip point: header pin / mounting pad / shunt GND end"),
    "gndpad": ("#7FA8FF", "Ground pad of a 0603+ part (filled dot = the GND end); label = the part's OTHER net"),
    "gndwarn": ("#7FA8FF", "  ...red outline: the OTHER end is a power net -- touch only the dot, never bridge the part"),
    "nogo": ("#FF8A00", "Shunt SOURCE end: not a ground -- never clip a probe ground here"),
}


def blocks(s, head):
    for m in re.finditer(r"\(" + head + r"\b", s):
        j = m.start(); d = 0; k = j
        while True:
            c = s[k]
            if c == "(": d += 1
            elif c == ")":
                d -= 1
                if d == 0: break
            k += 1
        yield s[j:k + 1]


def pad_xy(fx, fy, rot, pad):
    px, py = [float(v) for v in re.search(r"\(at ([-\d.]+) ([-\d.]+)", pad).groups()]
    a = math.radians(rot)
    return fx + px * math.cos(a) + py * math.sin(a), fy - px * math.sin(a) + py * math.cos(a)


def pad_net(pad):
    m = re.search(r'\(net (?:\d+ )?"([^"]*)"\)', pad)
    return m.group(1).split("/")[-1] if m else None


def classify_tp(net):
    n = (net or "").upper()
    if re.search(r"\b(SH[ABC]|GH[ABC]|GL[ABC])\b", n): return "danger"
    if n in ("+3V3", "+5V") or "PG_5V" in n: return "rail"
    if re.search(r"SO[ABC]|SENSE|TEMP", n): return "analog"
    return "logic"


def collect():
    s = open(PCB).read()
    xs, ys = [], []
    for head in ("gr_line", "gr_arc", "gr_rect", "gr_circle", "gr_poly"):
        for b in blocks(s, head):
            if '"Edge.Cuts"' in b:
                for a, c in re.findall(r"\((?:start|end|mid|center|xy) ([-\d.]+) ([-\d.]+)\)", b):
                    xs.append(float(a)); ys.append(float(c))
    bbox = (min(xs), min(ys), max(xs), max(ys))
    pts = []
    for fp in blocks(s, "footprint"):
        lib = re.match(r'\(footprint "([^"]+)"', fp).group(1)
        ref = re.search(r'\(property "Reference" "([^"]+)"', fp); ref = ref.group(1) if ref else "?"
        layer = re.search(r'\(layer "([^"]+)"', fp).group(1)
        at = re.search(r"\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)", fp)
        fx, fy, rot = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
        pads = list(blocks(fp, "pad")); nets = [pad_net(p) for p in pads]
        if ref.startswith("TP"):
            pts.append(dict(ref=ref, label=ref, text=nets[0], x=fx, y=fy, cat=classify_tp(nets[0]), big=False))
        elif re.match(r"H[1-9]$", ref) and nets and nets[0] in ("GND", "OUT_A", "OUT_B", "OUT_C", "+VPROT"):
            text = {"OUT_A": "PHASE A (SW node)", "OUT_B": "PHASE B (SW node)", "OUT_C": "PHASE C (SW node)",
                    "+VPROT": "BUS + (VPROT)", "GND": "GND (power)"}[nets[0]]
            pts.append(dict(ref=ref, label=ref, text=text, x=fx, y=fy, cat="gnd" if nets[0] == "GND" else "power", big=True))
        elif ref in ("R22", "R27", "R32"):
            ph = {"R22": "A", "R27": "B", "R32": "C"}[ref]
            for p, n in zip(pads, nets):
                x, y = pad_xy(fx, fy, rot, p)
                if n == "GND": pts.append(dict(ref=f"{ref}-GND", label=f"{ref}-GND", text=f"shunt {ph} GND end", x=x, y=y, cat="gnd", big=True))
                else: pts.append(dict(ref=f"{ref}-S", label=f"{ref}-S", text=f"shunt {ph} SOURCE end", x=x, y=y, cat="nogo", big=True))
        elif ref in ("J2", "J7"):
            for p, n in zip(pads, nets):
                if n == "GND":
                    pn = re.match(r'\(pad "([^"]*)"', p).group(1); x, y = pad_xy(fx, fy, rot, p)
                    pts.append(dict(ref=f"{ref}-{pn}", label=f"{ref}-{pn}", text="GND header pin", x=x, y=y, cat="gnd", big=True))
        elif re.match(r"[CR]\d", ref) and layer == "F.Cu" and BIG.search(lib) and "GND" in nets:
            others = sorted(set(n for n in nets if n and n != "GND")); other = others[0] if others else "GND"
            for p, n in zip(pads, nets):
                if n == "GND":
                    x, y = pad_xy(fx, fy, rot, p)
                    pts.append(dict(ref=ref, label=ref, text=f"GND end, other end {other}", x=x, y=y, cat="gndpad",
                                    big=False, warn=bool(POWER_NETS.search(other)), other=other))
                    break
    return bbox, pts


class Placer:
    """Greedy collision-free label placement with leader lines."""
    def __init__(self, bounds): self.rects = []; self.bounds = bounds; self.blocks = []

    def block_circle(self, c, r): self.blocks.append(QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r))

    def place(self, anchor, w, h, r0):
        for dist in (r0 + 6, r0 + 30, r0 + 60, r0 + 100, r0 + 150, r0 + 220, r0 + 320):
            for deg in (90, 270, 0, 180, 60, 120, 240, 300, 30, 150, 210, 330, 75, 105, 255, 285):   # straight below/above first
                a = math.radians(deg)
                cx, cy = anchor.x() + math.cos(a) * dist, anchor.y() + math.sin(a) * dist
                dx = 0 if math.cos(a) > 0.3 else (w if math.cos(a) < -0.3 else w / 2)
                dy = 0 if math.sin(a) > 0.3 else (h if math.sin(a) < -0.3 else h / 2)
                rect = QRectF(cx - dx, cy - dy, w, h)
                if not self.bounds.contains(rect): continue
                if any(rect.intersects(o) for o in self.rects) or any(rect.intersects(b) for b in self.blocks): continue
                self.rects.append(rect); return rect
        rect = QRectF(anchor.x() + r0, anchor.y() - h / 2, w, h); self.rects.append(rect); return rect


ORDER = {"power": 0, "gnd": 1, "nogo": 2, "danger": 3, "analog": 4, "rail": 5, "logic": 6, "gndpad": 7}


def draw_points(p, pts, to_px, bounds, scale_mark, font_px, full_labels=False):
    pl = Placer(bounds); items = []
    for pt in pts:
        q = to_px(pt["x"], pt["y"])
        if not bounds.contains(q): continue
        r = (30 if pt["big"] else 12) * scale_mark
        items.append((pt, q, r)); pl.block_circle(q, r)
    for pt, q, r in sorted(items, key=lambda it: ORDER[it[0]["cat"]]):
        c = QColor(CAT[pt["cat"]][0])
        if pt["cat"] == "gndpad":
            p.setPen(QPen(QColor("#FF2D3B") if pt.get("warn") else c, 3)); p.setBrush(c); p.drawEllipse(q, r * 0.8, r * 0.8)
        else:
            p.setPen(QPen(c, max(3, r / 4))); p.setBrush(QColor(0, 0, 0, 110)); p.drawEllipse(q, r, r)
        fs = font_px * (1.2 if pt["big"] else 1.0)
        f = QFont("Helvetica"); f.setPixelSize(int(fs)); f.setBold(True); p.setFont(f)
        if not full_labels: txt = pt["label"]
        elif pt["cat"] == "gndpad": txt = f"{pt['ref']} GND (other end {pt['other']})"
        else: txt = f"{pt['label']} {pt['text']}"
        w = QFontMetricsF(f).horizontalAdvance(txt) + 14; h = fs * 1.35
        rect = pl.place(q, w, h, r)
        tgt = QPointF(min(max(q.x(), rect.left()), rect.right()), min(max(q.y(), rect.top()), rect.bottom()))
        p.setPen(QPen(c, 2)); p.drawLine(q, tgt)
        p.setPen(QPen(QColor("#FF2D3B"), 3) if pt.get("warn") else Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 230)); p.drawRoundedRect(rect, 4, 4)
        p.setPen(c); p.drawText(rect, Qt.AlignmentFlag.AlignCenter, txt)


def main():
    bbox, pts = collect()
    tmp = tempfile.mkdtemp(); svg = os.path.join(tmp, "top.svg")
    subprocess.run([KICAD, "pcb", "export", "svg", "--mode-single", "-o", svg, "-l", "F.Cu,F.Silkscreen,Edge.Cuts",
                    "--page-size-mode", "2", "--exclude-drawing-sheet", PCB], check=True, capture_output=True)
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    r = QSvgRenderer(svg); vb = r.viewBoxF()
    x0 = bbox[0] + ((bbox[2] - bbox[0]) - vb.width()) / 2; y0 = bbox[1] + ((bbox[3] - bbox[1]) - vb.height()) / 2
    PX = 44.0
    W, H = int(vb.width() * PX), int(vb.height() * PX)
    board = QImage(W, H, QImage.Format.Format_ARGB32); board.fill(QColor("#101010"))
    p = QPainter(board); p.setRenderHint(QPainter.RenderHint.Antialiasing); r.render(p, QRectF(0, 0, W, H))
    p.fillRect(QRectF(0, 0, W, H), QColor(0, 0, 0, 150)); p.end()

    insets = [("Current sense, left to right: TP18 SOC | TP19 SOB | TP20 SOA (1 mm apart) -- nearest ground: J7-5", 125.6, 87.2, 129.9, 89.3),
              ("Filtered current sense TP15 / 16 / 17", 149.5, 90.0, 156.5, 96.5),
              ("Gate-driver / switch-node cluster (RED = never while powered)", 131.0, 71.0, 148.0, 80.5),
              ("MCU / PWM / DRV-SPI cluster (3.3 V logic)", 134.0, 94.5, 148.0, 102.5)]
    LEG_W = 2400
    canvas = QImage(W + LEG_W, max(H, 4800), QImage.Format.Format_ARGB32); canvas.fill(QColor("#050505"))
    p = QPainter(canvas); p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.drawImage(0, 0, board)
    to_main = lambda x, y: QPointF((x - x0) * PX, (y - y0) * PX)
    for _, xa, ya, xb, yb in insets:
        p.setPen(QPen(QColor("#FFFFFF"), 3, Qt.PenStyle.DashLine)); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(QRectF(to_main(xa, ya), to_main(xb, yb)))
    in_inset = lambda pt: any(xa <= pt["x"] <= xb and ya <= pt["y"] <= yb for _, xa, ya, xb, yb in insets)
    draw_points(p, [q for q in pts if not in_inset(q)], to_main, QRectF(0, 0, W, H), 1.0, 28)
    for q in pts:                                    # inside the insets: markers only on the main view
        if in_inset(q):
            c = QColor(CAT[q["cat"]][0]); pos = to_main(q["x"], q["y"])
            p.setPen(QPen(c, 3)); p.setBrush(c if q["cat"] == "gndpad" else Qt.BrushStyle.NoBrush); p.drawEllipse(pos, 9, 9)

    lx = W + 40; ly = 30
    f = QFont("Helvetica"); f.setPixelSize(56); f.setBold(True); p.setFont(f); p.setPen(QColor("#FFFFFF"))
    p.drawText(QPointF(lx, ly + 50), "FOC Rev A -- probe map (top side)"); ly += 100
    f.setPixelSize(28); f.setBold(False); p.setFont(f)
    for cat, (col, txt) in CAT.items():
        c = QColor(col)
        if cat in ("gndpad", "gndwarn"):
            p.setPen(QPen(QColor("#FF2D3B") if cat == "gndwarn" else c, 3)); p.setBrush(c); p.drawEllipse(QPointF(lx + 18, ly), 11, 11)
        else:
            p.setPen(QPen(c, 5)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawEllipse(QPointF(lx + 18, ly), 14, 14)
        p.setPen(c); p.drawText(QRectF(lx + 50, ly - 20, LEG_W - 100, 42), Qt.AlignmentFlag.AlignVCenter, txt); ly += 48
    ly += 20
    col_x = [lx, lx + (LEG_W - 60) / 2]; col_y = [ly, ly]
    for i, (name, xa, ya, xb, yb) in enumerate(insets):
        col = i % 2
        iw = (LEG_W - 120) / 2; sc = iw / (xb - xa); ih = (yb - ya) * sc
        bx, by = col_x[col], col_y[col]
        f.setPixelSize(28); f.setBold(True); p.setFont(f); p.setPen(QColor("#FFFFFF"))
        p.drawText(QRectF(bx, by, iw, 80), Qt.TextFlag.TextWordWrap, name); by += 84
        src = QRectF((xa - x0) * PX, (ya - y0) * PX, (xb - xa) * PX, (yb - ya) * PX)
        p.drawImage(QRectF(bx, by, iw, ih), board, src)
        p.setPen(QPen(QColor("#FFFFFF"), 2)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawRect(QRectF(bx, by, iw, ih))
        to_in = lambda x, y, xa=xa, ya=ya, bx=bx, by=by, sc=sc: QPointF(bx + (x - xa) * sc, by + (y - ya) * sc)
        draw_points(p, [q for q in pts if xa <= q["x"] <= xb and ya <= q["y"] <= yb], to_in, QRectF(bx, by, iw, ih), 1.7, 30,
                    full_labels=True)
        col_y[col] = by + ih + 40
    ly = max(col_y) + 10
    f = QFont("Menlo"); f.setPixelSize(23); p.setFont(f)
    rows = sorted(pts, key=lambda t: (ORDER[t["cat"]], t["ref"]))
    ncol = 3; per = (len(rows) + ncol - 1) // ncol; cw = (LEG_W - 60) / ncol
    for i, t in enumerate(rows):
        cx = lx + cw * (i // per); cy = ly + 29 * (i % per)
        txt = f"{t['ref']:8s}{t['text']}" if t["cat"] != "gndpad" else f"{t['ref']:8s}GND | other: {t['other']}"
        p.setPen(QColor("#FF6060") if t.get("warn") else QColor(CAT[t["cat"]][0])); p.drawText(QPointF(cx, cy + 22), txt[:38])
    p.end()
    canvas = canvas.copy(0, 0, canvas.width(), int(max(H, ly + 29 * per + 40)))
    png = os.path.join(HERE, "PROBE_MAP.png"); canvas.save(png)
    pdf = QPdfWriter(os.path.join(HERE, "PROBE_MAP.pdf")); pdf.setPageSize(QPageSize(QPageSize.PageSizeId.A3))
    pdf.setPageOrientation(QPageLayout.Orientation.Landscape)
    q = QPainter(pdf); rect = q.viewport(); s = min(rect.width() / canvas.width(), rect.height() / canvas.height())
    q.drawImage(QRectF(0, 0, canvas.width() * s, canvas.height() * s), canvas); q.end()
    print("wrote", png, "and PROBE_MAP.pdf;", len(pts), "points,", sum(1 for t in pts if t["cat"] == "gndpad"), "ground pads,",
          sum(1 for t in pts if t.get("warn")), "with a power net on the other end")


if __name__ == "__main__":
    main()
