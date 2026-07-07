#!/usr/bin/env python3
"""Kod-tarafi WCAG kontrast kontrolu (stdlib, chrome-devtools GEREKMEZ).

PSI `details` "hangi element" + rengi verir; kaynaga erisimin varsa bu betikle o renk
ciftinin WCAG kontrast oranini hesapla. rgba/yari-saydam renkleri zemine harmanlar.

Kullanim:
  python3 contrast.py "#111" "#fff"                 -> oran + AA/AAA
  python3 contrast.py "rgba(220,38,38,0.4)" "#fff"  -> yari-saydam, beyaza harmanlanir
  python3 contrast.py "#777" "#fff" --large         -> buyuk metin esikleri
  python3 contrast.py "#fff" "rgba(0,0,0,.4)" --behind "#0b1020"  -> saydam zemin arkasi
"""
import argparse
import re
import sys


def parse_color(s):
    """'#rgb' / '#rrggbb(aa)' / 'rgb(a)(...)' -> (r, g, b, a[0-1])."""
    s = s.strip()
    if s.startswith("#"):
        h = s[1:]
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        if len(h) not in (6, 8):
            raise ValueError(f"gecersiz hex renk: {s}")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return (r, g, b, a)
    m = re.match(r"rgba?\(([^)]+)\)", s, re.I)
    if m:
        parts = [p for p in re.split(r"[,/\s]+", m.group(1).strip()) if p]
        r, g, b = (int(round(float(x.rstrip("%")))) for x in parts[:3])
        a = float(parts[3]) if len(parts) > 3 else 1.0
        return (r, g, b, a)
    raise ValueError(f"anlasilmayan renk: {s} (hex veya rgb/rgba kullan)")


def _blend(fg, over):
    """Yari-saydam fg'yi opak over uzerine harmanla -> (r, g, b)."""
    r, g, b, a = fg
    R, G, B = over[:3]
    return (round(r * a + R * (1 - a)), round(g * a + G * (1 - a)), round(b * a + B * (1 - a)))


def _lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _luminance(rgb):
    r, g, b = rgb
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast_ratio(fg, bg, behind="#ffffff"):
    """WCAG kontrast orani. fg/bg saydamsa harmanlanir (bg once `behind`'e)."""
    beh = _blend(parse_color(behind), (255, 255, 255)) if False else parse_color(behind)[:3]
    bgc = parse_color(bg)
    bg_solid = _blend(bgc, beh) if bgc[3] < 1 else bgc[:3]
    fgc = parse_color(fg)
    fg_solid = _blend(fgc, bg_solid) if fgc[3] < 1 else fgc[:3]
    l1, l2 = _luminance(fg_solid), _luminance(bg_solid)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def wcag_pass(ratio, large=False):
    """WCAG 2.x esikleri: normal 4.5/7, buyuk metin 3/4.5."""
    return {"AA": ratio >= (3.0 if large else 4.5),
            "AAA": ratio >= (4.5 if large else 7.0)}


def main():
    ap = argparse.ArgumentParser(description="WCAG kontrast orani hesaplayici (stdlib)")
    ap.add_argument("fg", help="On plan (metin) rengi: hex veya rgb/rgba")
    ap.add_argument("bg", help="Arka plan rengi: hex veya rgb/rgba")
    ap.add_argument("--large", action="store_true", help="Buyuk metin esikleri (>=18.66px bold / >=24px)")
    ap.add_argument("--behind", default="#ffffff", help="Saydam arka planin arkasindaki zemin (varsayilan beyaz)")
    args = ap.parse_args()
    try:
        ratio = contrast_ratio(args.fg, args.bg, args.behind)
    except ValueError as e:
        print(f"HATA: {e}", file=sys.stderr)
        sys.exit(2)
    res = wcag_pass(ratio, args.large)
    tick = lambda ok: "GECTI" if ok else "KALDI"
    print(f"Kontrast: {ratio:.2f}:1  ({'buyuk' if args.large else 'normal'} metin)")
    print(f"  WCAG AA : {tick(res['AA'])}  (hedef {'3.0' if args.large else '4.5'}:1)")
    print(f"  WCAG AAA: {tick(res['AAA'])}  (hedef {'4.5' if args.large else '7.0'}:1)")
    if not res["AA"]:
        sys.exit(1)  # CI/kapi icin: AA gecmezse hata kodu


if __name__ == "__main__":
    main()
