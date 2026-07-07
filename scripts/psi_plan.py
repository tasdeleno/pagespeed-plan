#!/usr/bin/env python3
"""psi_audit JSON'unu LLM'siz, DETERMINISTIK bir Markdown iyilestirme planina cevirir.

Kullanim:
  python3 psi_plan.py psi_veri.json --out plan.md

SKILL.md "Plan formati" bolumleriyle ayni iskeleti uretir (ozet skorlar, CWV, oncelikli
aksiyonlar, kategori bulgulari + `details` kaniti, sonraki adimlar). Claude'un yazdigi zengin
plana bir alternatif/baseline; ag yok, yalnizca yerel JSON okunur.
"""
import argparse
import json
import sys

CAT_ORDER = ["performance", "accessibility", "best-practices", "seo"]
CAT_TR = {"performance": "Performans", "accessibility": "Erişilebilirlik",
          "best-practices": "En İyi Uygulamalar", "seo": "SEO"}

# Efor tahmini (SKILL.md "Onceliklendirme kurallari"): dusuk = mekanik, yuksek = mimari.
EFFORT = {
    "uses-optimized-images": "Düşük", "modern-image-formats": "Düşük", "uses-webp-images": "Düşük",
    "uses-responsive-images": "Düşük", "offscreen-images": "Düşük", "efficient-animated-content": "Düşük",
    "image-alt": "Düşük", "meta-description": "Düşük", "document-title": "Düşük",
    "color-contrast": "Düşük", "uses-long-cache-ttl": "Düşük", "unsized-images": "Düşük",
    "link-text": "Düşük", "target-size": "Düşük", "canonical": "Düşük", "hreflang": "Düşük",
    "server-response-time": "Yüksek", "critical-request-chains": "Yüksek",
    "render-blocking-resources": "Yüksek", "mainthread-work-breakdown": "Yüksek",
    "bootup-time": "Yüksek", "font-display": "Yüksek", "dom-size": "Yüksek",
}


def _effort(audit_id):
    return EFFORT.get(audit_id, "Orta")  # kullanilmayan JS/CSS, lazy-load, 3P = orta


def _impact(ms):
    if not ms:
        return "Düşük"
    return "Yüksek" if ms >= 500 else ("Orta" if ms >= 150 else "Düşük")


def _rep(results):
    """Temsili strateji: mobil oncelikli (SKILL.md), yoksa ilk mevcut."""
    return results.get("mobile") or next(iter(results.values()), {}) or {}


def _score_table(results):
    strats = list(results.keys())
    head = "| Kategori | " + " | ".join(strats) + " |"
    sep = "|---" * (len(strats) + 1) + "|"
    lines = [head, sep]
    for cid in CAT_ORDER:
        cells = []
        for s in strats:
            sc = ((results[s].get("categories") or {}).get(cid) or {}).get("score")
            cells.append(str(sc) if sc is not None else "—")
        lines.append(f"| {CAT_TR[cid]} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _cwv_section(res):
    lab, fld = res.get("labMetrics") or {}, res.get("fieldData") or {}
    rows = []
    for label in ("LCP", "INP", "TBT", "CLS", "FCP"):
        lv = (lab.get(label) or {}).get("display")
        fv = fld.get(label)
        fv = f'{fv.get("percentile")} ({fv.get("category")})' if isinstance(fv, dict) else "—"
        if lv is None and fv == "—":
            continue
        rows.append(f"| {label} | {lv or '—'} | {fv} |")
    if not rows:
        return ""
    out = ["## 2. Core Web Vitals", "", "| Metrik | Lab | Saha (CrUX) |", "|---|---|---|"] + rows
    for g in res.get("labVsFieldGaps") or []:
        out.append(f"\n> **{g.get('metric')}:** {g.get('note')}")
    return "\n".join(out)


def _priorities(res):
    opps = res.get("opportunities") or []
    if not opps:
        return ""
    out = ["## 3. Öncelikli aksiyonlar (etki × efor)", "",
           "| # | Aksiyon | Etki | Efor | Tahmini kazanç | Denetim |", "|---|---|---|---|---|---|"]
    for i, o in enumerate(opps[:10], 1):
        ms = o.get("savingsMs")
        gain = f"~{ms} ms" if ms else "—"
        out.append(f"| {i} | {o.get('title')} | {_impact(ms)} | {_effort(o.get('id'))} | {gain} | {o.get('id')} |")
    return "\n".join(out)


def _details_md(details):
    items = (details or {}).get("items") or []
    if not items:
        return ""
    lines = []
    for it in items[:6]:
        parts = [f"{k}: {v}" for k, v in it.items()]
        lines.append("  - " + " · ".join(parts))
    extra = details.get("truncated")
    if extra:
        lines.append(f"  - … +{extra} kalem")
    return "\n" + "\n".join(lines)


def _findings(results):
    res = _rep(results)
    abc = res.get("auditsByCategory") or {}
    counts = res.get("counts") or {}
    out = ["## 4. Kategori bazlı bulgular (öneri + kanıt)"]
    for cid in CAT_ORDER:
        rows = [r for r in (abc.get(cid) or []) if not r.get("passed")]
        n = (counts.get(cid) or {}).get("duzeltilecek", len(rows))
        out.append(f"\n### {CAT_TR[cid]} — {n} düzeltilecek")
        if not rows:
            out.append("- (bu kategoride açık bulgu yok)")
            continue
        for r in rows:
            disp = f" — {r['display']}" if r.get("display") else ""
            ms = f" · ~{r['savingsMs']} ms" if r.get("savingsMs") else ""
            desc = (r.get("description") or "").strip()
            out.append(f"- **{r.get('title')}** ({r.get('id')}){disp}{ms}"
                       + (f"\n  {desc}" if desc else "") + _details_md(r.get("details")))
    return "\n".join(out)


def plan_for(url, page):
    results = page.get("results") or {}
    if not results:
        errs = page.get("errors") or {}
        return f"# PageSpeed İyileştirme Planı — {url}\n\n> Sonuç alınamadı: {errs or 'bilinmeyen hata'}"
    rep = _rep(results)
    counts = rep.get("counts") or {}
    total = sum((c or {}).get("duzeltilecek", 0) for c in counts.values())
    lhv = rep.get("lighthouseVersion") or "?"
    head = [f"# PageSpeed İyileştirme Planı — {url}", "",
            f"**Strateji:** {', '.join(results.keys())}  ·  **Motor:** Lighthouse {lhv}  ·  "
            f"**Düzeltilecek toplam:** {total}", "",
            "## 1. Özet skorlar", "", _score_table(results)]
    parts = ["\n".join(head), _cwv_section(rep), _priorities(rep), _findings(results),
             "## 5. Sonraki adımlar\n- Değişiklikler **canlıya çıktıktan sonra** aynı URL'yi yeniden "
             "test et; mobil skoru önceliklendir. Bir düzeltme metriği oynatmadıysa kök-neden "
             "hipotezini gözden geçir (başka darboğaz ara)."]
    return "\n\n".join(p for p in parts if p)


def render_plan(obj):
    if isinstance(obj, dict) and "pages" in obj:
        return "\n\n---\n\n".join(plan_for(u, p) for u, p in obj["pages"].items())
    return plan_for(obj.get("url", ""), obj)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="psi_audit JSON -> deterministik Markdown plan")
    ap.add_argument("json", help="psi_audit JSON dosyasi")
    ap.add_argument("--out", help="Markdown ciktisini bu dosyaya da yaz")
    args = ap.parse_args()
    with open(args.json, encoding="utf-8") as f:
        obj = json.load(f)
    md = render_plan(obj)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(md)
    print(md)


if __name__ == "__main__":
    main()
