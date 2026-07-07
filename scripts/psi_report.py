#!/usr/bin/env python3
"""psi_audit JSON'unu KENDINE-YETER (inline CSS, harici istek yok) bir HTML rapora cevirir.

Kullanim:
  python3 psi_report.py psi_veri.json --out rapor.html

Cok-URL (`pages`) JSON'u bolum bolum render eder. Varsa filmstrip/ekran goruntusu dosyalari
base64 olarak GOMULUR (rapor tasinabilir kalir). Ag yok.
"""
import argparse
import base64
import html
import json
import os
import sys

CAT_ORDER = ["performance", "accessibility", "best-practices", "seo"]
CAT_TR = {"performance": "Performans", "accessibility": "Erişilebilirlik",
          "best-practices": "En İyi Uygulamalar", "seo": "SEO"}


def _color(score):
    if score is None:
        return "#9aa0a6"
    return "#0cce6b" if score >= 90 else ("#ffa400" if score >= 50 else "#ff4e42")


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


def _score_cards(results):
    cells = []
    for strat, res in results.items():
        cats = res.get("categories") or {}
        chips = []
        for cid in CAT_ORDER:
            sc = (cats.get(cid) or {}).get("score")
            chips.append(f'<div class="gauge"><span style="color:{_color(sc)}">{sc if sc is not None else "—"}</span>'
                         f'<small>{_esc(CAT_TR.get(cid, cid))}</small></div>')
        cells.append(f'<div class="strat"><h3>{_esc(strat)}</h3><div class="gauges">{"".join(chips)}</div></div>')
    return f'<div class="strats">{"".join(cells)}</div>'


def _cwv_table(res):
    lab = res.get("labMetrics") or {}
    fld = res.get("fieldData") or {}
    rows = []
    for label in ("LCP", "INP", "TBT", "CLS", "FCP"):
        lv = (lab.get(label) or {}).get("display")
        fv = fld.get(label)
        fv = f'{fv.get("percentile")} ({fv.get("category")})' if isinstance(fv, dict) else "—"
        if lv is None and fv == "—":
            continue
        rows.append(f"<tr><td>{label}</td><td>{_esc(lv) or '—'}</td><td>{_esc(fv)}</td></tr>")
    if not rows:
        return ""
    return ('<table class="t"><thead><tr><th>Metrik</th><th>Lab</th><th>Saha (CrUX)</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>')


def _priorities(res):
    opps = res.get("opportunities") or []
    if not opps:
        return ""
    rows = []
    for o in opps[:10]:
        ms = o.get("savingsMs")
        rows.append(f"<tr><td>{_esc(o.get('title'))}</td><td>{_esc(o.get('category'))}</td>"
                    f"<td>{_esc(o.get('display')) or ''}</td><td>{('~' + str(ms) + ' ms') if ms else ''}</td></tr>")
    return ('<h4>Öncelikli fırsatlar</h4><table class="t"><thead><tr><th>Aksiyon</th><th>Kategori</th>'
            f'<th>Değer</th><th>Kazanç</th></tr></thead><tbody>{"".join(rows)}</tbody></table>')


def _details_html(details):
    items = (details or {}).get("items") or []
    if not items:
        return ""
    lis = []
    for it in items:
        parts = [f"<b>{_esc(k)}</b>: {_esc(v)}" for k, v in it.items()]
        lis.append("<li>" + " · ".join(parts) + "</li>")
    extra = details.get("truncated")
    tail = f"<li><i>… +{extra} kalem</i></li>" if extra else ""
    return f'<ul class="ev">{"".join(lis)}{tail}</ul>'


def _findings(res):
    abc = res.get("auditsByCategory") or {}
    out = []
    for cid in CAT_ORDER:
        rows = [r for r in (abc.get(cid) or []) if not r.get("passed")]
        if not rows:
            continue
        out.append(f"<h4>{_esc(CAT_TR.get(cid, cid))} — {len(rows)} bulgu</h4>")
        for r in rows:
            ms = f' · <span class="save">~{r["savingsMs"]} ms</span>' if r.get("savingsMs") else ""
            disp = f' <span class="disp">{_esc(r.get("display"))}</span>' if r.get("display") else ""
            out.append(f'<div class="finding"><div class="ft">{_esc(r.get("title"))}{disp}{ms}</div>'
                       f'<div class="fd">{_esc(r.get("description"))}</div>{_details_html(r.get("details"))}</div>')
    return "".join(out)


def _screenshots(results):
    imgs = []
    for strat, res in results.items():
        for p in (res.get("screenshots") or []):
            uri = _img_data_uri(p)
            if uri:
                imgs.append(f'<figure><img src="{uri}" alt="{_esc(os.path.basename(p))}"><figcaption>'
                            f'{_esc(strat)} · {_esc(os.path.basename(p))}</figcaption></figure>')
    return f'<div class="shots">{"".join(imgs)}</div>' if imgs else ""


def _page_section(url, page):
    results = page.get("results") or {}
    if not results:
        return f'<section><h2>{_esc(url)}</h2><p class="err">Sonuç yok.</p></section>'
    body = [_score_cards(results)]
    body.append(_screenshots(results))
    for strat, res in results.items():
        body.append(f"<h3>{_esc(strat)}</h3>")
        body.append(_cwv_table(res))
        body.append(_priorities(res))
        body.append(_findings(res))
    return f'<section><h2>{_esc(url)}</h2>{"".join(body)}</section>'


CSS = """
:root{--bg:#f6f8fc;--card:#fff;--ink:#1a1c22;--mut:#5f6673;--line:#e6e9f0}
*{box-sizing:border-box}body{margin:0;font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--ink)}
.wrap{max-width:1000px;margin:0 auto;padding:28px 20px}
h1{font-size:28px;margin:0 0 4px}.sub{color:var(--mut);margin:0 0 24px}
section{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 22px;margin:0 0 22px}
h2{font-size:20px;margin:0 0 14px;word-break:break-all}h3{font-size:16px;margin:20px 0 8px}h4{font-size:14px;margin:18px 0 6px;color:var(--mut)}
.strats{display:flex;gap:16px;flex-wrap:wrap}.strat{flex:1;min-width:240px}
.gauges{display:flex;gap:14px}.gauge{text-align:center}.gauge span{font-size:34px;font-weight:800;display:block}.gauge small{color:var(--mut);font-size:11px}
.t{width:100%;border-collapse:collapse;margin:6px 0 4px;font-size:13.5px}.t th,.t td{border:1px solid var(--line);padding:6px 9px;text-align:left}.t th{background:#f0f3f9}
.finding{border-left:3px solid #ffa400;padding:6px 12px;margin:8px 0;background:#fbfcfe;border-radius:0 8px 8px 0}
.ft{font-weight:600}.fd{color:var(--mut);font-size:13px;margin:2px 0}.disp{color:#b26b00;font-weight:600}.save{color:#0a7d46;font-weight:600}
.ev{margin:4px 0 0;padding-left:18px;font-size:12.5px;color:#3a3f4a}.ev li{margin:2px 0;word-break:break-word}
.shots{display:flex;gap:8px;overflow-x:auto;padding:6px 0}.shots figure{margin:0;flex:0 0 auto}.shots img{height:150px;border:1px solid var(--line);border-radius:8px}
.shots figcaption{font-size:10px;color:var(--mut);text-align:center}
.err{color:#ff4e42}
"""


def render_report(obj):
    if isinstance(obj, dict) and "pages" in obj:
        sections = "".join(_page_section(u, p) for u, p in obj["pages"].items())
        sub = f'{len(obj["pages"])} sayfa'
    else:
        sections = _page_section(obj.get("url", ""), obj)
        sub = _esc(obj.get("url", ""))
    return (f'<!doctype html><html lang="tr"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>PageSpeed raporu — {sub}</title><style>{CSS}</style></head>'
            f'<body><div class="wrap"><h1>PageSpeed raporu</h1><p class="sub">{sub}</p>'
            f'{sections}</div></body></html>')


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
