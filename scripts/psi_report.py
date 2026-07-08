#!/usr/bin/env python3
"""psi_audit JSON'unu KENDINE-YETER (inline CSS, harici istek yok) bir HTML rapora cevirir.

Kullanim:
  python3 psi_report.py psi_veri.json --out rapor.html

Cok-URL (`pages`) JSON'u bolum bolum render eder. Varsa filmstrip/ekran goruntusu dosyalari
base64 olarak GOMULUR (rapor tasinabilir kalir). Ag yok. Tasarim: dashboard/denetim raporu
(dairesel skor gauge'leri, CWV durum kartlari, siddet-kodlu bulgular; WCAG AA kontrast).
"""
import argparse
import base64
import html
import json
import math
import os
import sys

CAT_ORDER = ["performance", "accessibility", "best-practices", "seo"]
CAT_TR = {"performance": "Performans", "accessibility": "Erişilebilirlik",
          "best-practices": "En İyi Uygulamalar", "seo": "SEO"}
STRAT_TR = {"mobile": "Mobil", "desktop": "Masaüstü"}

# CWV esikleri (numericValue birimi: zaman=ms, CLS=birimsiz); dusuk = iyi. (iyi_max, gelistirilmeli_max)
CWV_TH = {"LCP": (2500, 4000), "FCP": (1800, 3000), "TBT": (200, 600),
          "INP": (200, 500), "CLS": (0.1, 0.25), "SI": (3400, 5800), "TTI": (3800, 7300)}
STATUS_TR = {"good": "İyi", "ni": "Geliştirilmeli", "poor": "Zayıf"}


def _score_color(score):
    if score is None:
        return "#8a919e"
    return "#0cce6b" if score >= 90 else ("#ffa400" if score >= 50 else "#ff4e42")


def _cwv_status(label, num):
    th = CWV_TH.get(label)
    if th is None or not isinstance(num, (int, float)):
        return None
    return "good" if num <= th[0] else ("ni" if num <= th[1] else "poor")


def _esc(x):
    return html.escape(str(x)) if x is not None else ""


def _img_data_uri(path):
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(ext, "png")
    try:
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        return f"data:image/{mime};base64,{b64}"
    except OSError:
        return None


def _gauge(score, label):
    r, cx = 42, 48
    circ = 2 * math.pi * r
    dash = round(circ * (score or 0) / 100, 1)
    col = _score_color(score)
    num = score if score is not None else "—"
    aria = f"{label}: {num} / 100"
    return (f'<div class="gcard"><div class="gring" role="img" aria-label="{_esc(aria)}">'
            f'<svg viewBox="0 0 96 96" width="96" height="96">'
            f'<circle cx="{cx}" cy="{cx}" r="{r}" fill="none" stroke="var(--track)" stroke-width="9"/>'
            f'<circle cx="{cx}" cy="{cx}" r="{r}" fill="none" stroke="{col}" stroke-width="9" '
            f'stroke-linecap="round" stroke-dasharray="{dash} {round(circ,1)}" '
            f'transform="rotate(-90 {cx} {cx})"/></svg>'
            f'<span class="gnum" style="color:{col}">{num}</span></div>'
            f'<span class="glabel">{_esc(label)}</span></div>')


def _score_cards(results):
    cells = []
    for strat, res in results.items():
        cats = res.get("categories") or {}
        gauges = "".join(_gauge((cats.get(cid) or {}).get("score"), CAT_TR.get(cid, cid))
                         for cid in CAT_ORDER)
        cells.append(f'<div class="strat"><div class="sname">{_esc(STRAT_TR.get(strat, strat))}</div>'
                     f'<div class="gauges">{gauges}</div></div>')
    return f'<div class="strats">{"".join(cells)}</div>'


def _cwv_cards(res):
    lab = res.get("labMetrics") or {}
    fld = res.get("fieldData") or {}
    cards = []
    for label in ("LCP", "INP", "TBT", "CLS", "FCP", "SI"):
        lm = lab.get(label) or {}
        disp = lm.get("display")
        st = _cwv_status(label, lm.get("numericValue"))
        fv = fld.get(label)
        if disp is None and not isinstance(fv, dict):
            continue
        pill = f'<span class="pill {st}">{STATUS_TR[st]}</span>' if st else ""
        field = ""
        if isinstance(fv, dict) and fv.get("percentile") is not None:
            fs = _cwv_status(label, fv.get("percentile"))
            field = f'<div class="mfield">Saha: {_esc(fv.get("percentile"))}{" · " + STATUS_TR[fs] if fs else ""}</div>'
        cards.append(f'<div class="mcard"><div class="mlab">{label}</div>'
                     f'<div class="mval">{_esc(disp) or "—"}</div>{pill}{field}</div>')
    return f'<div class="cwv">{"".join(cards)}</div>' if cards else ""


def _priorities(res):
    opps = res.get("opportunities") or []
    if not opps:
        return ""
    rows = []
    for o in opps[:10]:
        ms = o.get("savingsMs")
        gain = f'<span class="save">~{ms} ms</span>' if ms else ""
        rows.append(f"<tr><td>{_esc(o.get('title'))}</td><td class=c>{_esc(o.get('category'))}</td>"
                    f"<td class=c>{_esc(o.get('display')) or ''}</td><td class=c>{gain}</td></tr>")
    return ('<h4>Öncelikli fırsatlar</h4><div class="tw"><table class="t"><thead><tr><th>Aksiyon</th>'
            '<th>Kategori</th><th>Değer</th><th>Kazanç</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def _details_html(details):
    items = (details or {}).get("items") or []
    if not items:
        return ""
    lis = []
    for it in items:
        chips = "".join(f'<span class="chip"><b>{_esc(k)}</b> {_esc(v)}</span>' for k, v in it.items())
        lis.append(f'<li>{chips}</li>')
    extra = details.get("truncated")
    tail = f'<li><span class="more">… +{extra} kalem</span></li>' if extra else ""
    return f'<ul class="ev">{"".join(lis)}{tail}</ul>'


def _sev(r):
    ms = r.get("savingsMs") or 0
    return "hi" if ms >= 1000 else ("md" if ms >= 300 else "lo")


def _findings(res):
    abc = res.get("auditsByCategory") or {}
    out = []
    for cid in CAT_ORDER:
        rows = [r for r in (abc.get(cid) or []) if not r.get("passed")]
        if not rows:
            continue
        out.append(f'<h4>{_esc(CAT_TR.get(cid, cid))} <span class="cnt">{len(rows)} bulgu</span></h4>')
        for r in rows:
            ms = f'<span class="save">~{r["savingsMs"]} ms</span>' if r.get("savingsMs") else ""
            disp = f'<span class="disp">{_esc(r.get("display"))}</span>' if r.get("display") else ""
            out.append(f'<div class="finding {_sev(r)}"><div class="ft">{_esc(r.get("title"))}'
                       f'<span class="tags">{disp}{ms}</span></div>'
                       f'<div class="fd">{_esc(r.get("description"))}</div>{_details_html(r.get("details"))}</div>')
    return "".join(out)


def _screenshots(results):
    imgs = []
    for strat, res in results.items():
        for p in (res.get("screenshots") or []):
            uri = _img_data_uri(p)
            if uri:
                imgs.append(f'<figure><img src="{uri}" alt="{_esc(os.path.basename(p))}" loading="lazy">'
                            f'<figcaption>{_esc(STRAT_TR.get(strat, strat))}</figcaption></figure>')
    return f'<div class="shots">{"".join(imgs)}</div>' if imgs else ""


def _meta_chips(results):
    rep = next(iter(results.values()), {}) or {}
    chips = []
    strats = " + ".join(STRAT_TR.get(s, s) for s in results.keys())
    if strats:
        chips.append(strats)
    if rep.get("lighthouseVersion"):
        chips.append(f'Lighthouse {rep["lighthouseVersion"]}')
    if rep.get("runs"):
        chips.append(f'{rep["runs"]} koşu · medyan')
    total = sum((c or {}).get("duzeltilecek", 0) for c in (rep.get("counts") or {}).values())
    if total:
        chips.append(f'{total} düzeltilecek bulgu')
    return "".join(f'<span class="chip">{_esc(c)}</span>' for c in chips)


def _page_body(results):
    body = [_score_cards(results), _screenshots(results)]
    for strat, res in results.items():
        body.append(f'<h3>{_esc(STRAT_TR.get(strat, strat))}</h3>')
        body.append(_cwv_cards(res))
        body.append(_priorities(res))
        body.append(_findings(res))
    return "".join(p for p in body if p)


def _page_section(url, page):
    results = page.get("results") or {}
    if not results:
        return f'<section><h2>{_esc(url)}</h2><p class="err">Sonuç alınamadı.</p></section>'
    return (f'<section><div class="shead"><h2>{_esc(url)}</h2>'
            f'<div class="meta">{_meta_chips(results)}</div></div>{_page_body(results)}</section>')


CSS = """
:root{--bg:#160b10;--card:#20121a;--card2:#291621;--ink:#f6ebef;--mut:#c7a9b2;
--line:rgba(255,235,242,.10);--track:rgba(255,255,255,.09);--brand:#ff5c7a;--brand2:#7d1636}
*{box-sizing:border-box}
body{margin:0;font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
color:var(--ink);-webkit-font-smoothing:antialiased;
background:
 radial-gradient(900px 520px at 92% -6%, rgba(255,92,122,.10), transparent 60%),
 radial-gradient(760px 520px at 0% 104%, rgba(160,21,64,.14), transparent 55%),
 var(--bg)}
.wrap{max-width:1040px;margin:0 auto;padding:26px 20px 40px}
.hero{background:linear-gradient(135deg,#1c0d13 0%,var(--brand2) 60%,#a11540 100%);
color:#fff;padding:26px 28px;border-radius:18px;margin-bottom:22px;
border:1px solid rgba(255,92,122,.22);box-shadow:0 16px 40px -16px rgba(255,60,107,.4)}
.hero .k{font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:#f6b9c8;font-weight:700}
.hero h1{font-size:24px;margin:6px 0 0;color:#fff;font-weight:800;letter-spacing:-.01em}
.hero .u{font-size:13.5px;color:#f4cdd8;margin-top:4px;word-break:break-all}
section{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:22px 24px;margin:0 0 22px;
box-shadow:0 1px 2px rgba(0,0,0,.3)}
.shead{border-bottom:1px solid var(--line);padding-bottom:14px;margin-bottom:18px}
h2{font-size:19px;margin:0;word-break:break-all;color:var(--ink)}
h3{font-size:15px;margin:24px 0 10px;color:var(--ink);text-transform:capitalize}
h4{font-size:13px;margin:20px 0 8px;color:var(--mut);font-weight:700;letter-spacing:.02em;
display:flex;align-items:center;gap:8px}
.cnt,.meta .chip{font-size:11px}
.meta{margin-top:12px;display:flex;gap:8px;flex-wrap:wrap}
.chip{background:rgba(255,92,122,.14);color:#ff9db0;font-weight:600;padding:4px 11px;border-radius:999px;font-size:12px}
.strats{display:flex;gap:16px;flex-wrap:wrap}
.strat{flex:1;min-width:280px;border:1px solid var(--line);border-radius:14px;padding:16px 14px 18px;background:var(--card2)}
.sname{font-size:13px;font-weight:700;color:var(--mut);text-align:center;margin-bottom:10px}
.gauges{display:flex;gap:8px;justify-content:space-around}
.gcard{display:flex;flex-direction:column;align-items:center;gap:8px;flex:1}
.gring{position:relative;width:96px;height:96px}
.gnum{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
font-size:27px;font-weight:800;font-variant-numeric:tabular-nums}
.glabel{font-size:11px;color:var(--mut);font-weight:600;text-align:center;line-height:1.25}
.cwv{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:6px 0}
.mcard{border:1px solid var(--line);border-radius:12px;padding:12px 14px;background:var(--card2)}
.mlab{font-size:12px;color:var(--mut);font-weight:700;letter-spacing:.03em}
.mval{font-size:23px;font-weight:800;margin:3px 0 2px;font-variant-numeric:tabular-nums}
.mfield{font-size:12px;color:var(--mut);margin-top:4px}
.pill{display:inline-block;font-size:11px;font-weight:700;padding:2px 9px;border-radius:999px}
.pill.good{background:rgba(52,211,153,.16);color:#4ade80}.pill.ni{background:rgba(255,164,0,.16);color:#fbbf24}
.pill.poor{background:rgba(255,78,66,.18);color:#fb7185}
.tw{overflow-x:auto}
.t{width:100%;border-collapse:collapse;margin:4px 0;font-size:13.5px}
.t th,.t td{border-bottom:1px solid var(--line);padding:8px 10px;text-align:left}
.t th{background:rgba(255,92,122,.07);color:var(--mut);font-size:12px;font-weight:700;letter-spacing:.02em;
border-bottom:2px solid var(--line)}
.t td.c{white-space:nowrap;color:var(--mut)}.t tbody tr:hover{background:rgba(255,255,255,.03)}
.finding{border-left:4px solid #6b3a46;padding:9px 14px;margin:8px 0;background:rgba(255,255,255,.03);border-radius:0 10px 10px 0}
.finding.hi{border-left-color:#ff4e42;background:rgba(255,78,66,.08)}
.finding.md{border-left-color:#ffa400;background:rgba(255,164,0,.07)}
.finding.lo{border-left-color:var(--brand)}
.ft{font-weight:700;display:flex;justify-content:space-between;gap:10px;align-items:baseline;flex-wrap:wrap;color:var(--ink)}
.tags{display:inline-flex;gap:6px;flex-wrap:wrap}
.fd{color:var(--mut);font-size:13px;margin:3px 0 0}
.disp{font-size:12px;font-weight:700;color:#fbbf24;background:rgba(255,164,0,.14);padding:1px 8px;border-radius:6px}
.save{font-size:12px;font-weight:700;color:#4ade80;background:rgba(52,211,153,.14);padding:1px 8px;border-radius:6px;white-space:nowrap}
.ev{margin:8px 0 0;padding:0;list-style:none}
.ev li{margin:5px 0}
.chip.b,.ev .chip{display:inline-flex;gap:5px;align-items:baseline;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;
font-size:12px;background:rgba(255,255,255,.05);color:#ecd7de;border:1px solid var(--line);border-radius:7px;padding:3px 9px;margin:2px 6px 2px 0;
word-break:break-word}
.ev .chip b{color:var(--brand);font-weight:700}
.more{font-size:12px;color:var(--mut);font-style:italic}
.shots{display:flex;gap:10px;overflow-x:auto;padding:8px 0 4px}
.shots figure{margin:0;flex:0 0 auto}
.shots img{height:168px;border:1px solid var(--line);border-radius:10px;display:block}
.shots figcaption{font-size:11px;color:var(--mut);text-align:center;margin-top:4px}
.err{color:#fb7185}
@media (max-width:560px){.wrap{padding:16px 12px 32px}section{padding:16px 14px}.gauges{flex-wrap:wrap}}
"""


def render_report(obj):
    if isinstance(obj, dict) and "pages" in obj:
        title = f'{len(obj["pages"])} sayfa denetlendi'
        sections = "".join(_page_section(u, p) for u, p in obj["pages"].items())
    else:
        title = _esc(obj.get("url", ""))
        sections = _page_section(obj.get("url", ""), obj)
    hero = (f'<div class="hero"><div class="k">PageSpeed → Plan · denetim raporu</div>'
            f'<h1>{title}</h1></div>')
    return (f'<!doctype html><html lang="tr"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>PageSpeed raporu — {title}</title><style>{CSS}</style></head>'
            f'<body><div class="wrap">{hero}{sections}</div></body></html>')


def main():
    ap = argparse.ArgumentParser(description="psi_audit JSON -> kendine-yeter HTML rapor")
    ap.add_argument("json", help="psi_audit JSON dosyasi")
    ap.add_argument("--out", required=True, help="HTML cikti dosyasi")
    args = ap.parse_args()
    with open(args.json, encoding="utf-8") as f:
        obj = json.load(f)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(render_report(obj))
    print(f"HTML rapor yazildi: {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
