#!/usr/bin/env python3
"""psi_audit iki JSON ciktisini karsilastirir (oncesi -> sonrasi) ve regresyonlari gosterir.

Kullanim:
  python3 psi_diff.py eski.json yeni.json
  python3 psi_diff.py eski.json yeni.json --fail-on-regression   # CI: regresyonda exit 1
  python3 psi_diff.py --trend history.jsonl                      # zaman icinde skor trendi

Ag yok; yalnizca yerel JSON/JSONL okunur. Cok-URL (`pages`) JSON'da ilk sayfa alinir.
"""
import argparse
import json
import sys


def _results(obj):
    if isinstance(obj, dict) and "pages" in obj:
        first = next(iter(obj["pages"].values()), {}) or {}
        return first.get("results") or {}
    return (obj or {}).get("results") or {}


def _flat_audits(res):
    """auditsByCategory -> {audit_id: passed(bool)}"""
    out = {}
    for rows in (res.get("auditsByCategory") or {}).values():
        for r in rows or []:
            out[r["id"]] = r.get("passed")
    return out


def diff_results(old_results, new_results):
    """Strateji basina kategori/metrik/denetim deltalari + genel regresyon bayragi. [saf]"""
    out = {"strategies": {}, "regressed": False}
    for s in sorted(set(old_results) | set(new_results)):
        o, n = old_results.get(s) or {}, new_results.get(s) or {}
        cat_rows, met_rows = [], []

        oc, nc = o.get("categories") or {}, n.get("categories") or {}
        for cid in sorted(set(oc) | set(nc)):
            ov, nv = (oc.get(cid) or {}).get("score"), (nc.get(cid) or {}).get("score")
            d = (nv - ov) if (ov is not None and nv is not None) else None
            cat_rows.append({"id": cid, "old": ov, "new": nv, "delta": d})
            if d is not None and d < 0:
                out["regressed"] = True

        ol, nl = o.get("labMetrics") or {}, n.get("labMetrics") or {}
        for lbl in sorted(set(ol) | set(nl)):
            ov, nv = (ol.get(lbl) or {}).get("numericValue"), (nl.get(lbl) or {}).get("numericValue")
            d = (nv - ov) if (ov is not None and nv is not None) else None
            met_rows.append({"id": lbl, "old": ov, "new": nv, "delta": d})
            if d is not None and d > 0:  # tum lab metrikleri "dusuk = iyi"
                out["regressed"] = True

        oa, na = _flat_audits(o), _flat_audits(n)
        buckets = {"regressed": [], "fixed": [], "new_failed": [], "resolved": []}
        for aid in sorted(set(oa) | set(na)):
            op, npass = oa.get(aid), na.get(aid)
            if op is None and npass is False:
                buckets["new_failed"].append(aid)
            elif npass is None and op is not None:
                buckets["resolved"].append(aid)
            elif op and npass is False:
                buckets["regressed"].append(aid)
                out["regressed"] = True
            elif op is False and npass:
                buckets["fixed"].append(aid)
        out["strategies"][s] = {"categories": cat_rows, "metrics": met_rows, "audits": buckets}
    return out


def _arrow(d, worse_positive=False):
    if d is None:
        return "—"
    if d == 0:
        return "0"
    worse = (d > 0) if worse_positive else (d < 0)
    sign = "+" if d > 0 else ""
    return f"{sign}{round(d, 3)} {'🔴' if worse else '🟢'}"


def to_markdown(diff, old_name, new_name):
    L = [f"# PageSpeed diff — {old_name} → {new_name}", ""]
    L.append("**Regresyon:** " + ("🔴 VAR" if diff["regressed"] else "🟢 yok"))
    for s, d in diff["strategies"].items():
        L += ["", f"## {s}", "", "| Kategori | Öncesi | Sonrası | Δ |", "|---|---|---|---|"]
        for r in d["categories"]:
            L.append(f"| {r['id']} | {r['old']} | {r['new']} | {_arrow(r['delta'])} |")
        L += ["", "| Metrik (lab) | Öncesi | Sonrası | Δ |", "|---|---|---|---|"]
        for r in d["metrics"]:
            ov = round(r["old"]) if isinstance(r["old"], (int, float)) else r["old"]
            nv = round(r["new"]) if isinstance(r["new"], (int, float)) else r["new"]
            L.append(f"| {r['id']} | {ov} | {nv} | {_arrow(r['delta'], worse_positive=True)} |")
        a = d["audits"]
        if a["regressed"]:
            L += ["", f"**🔴 Kötüleşen denetimler ({len(a['regressed'])}):** " + ", ".join(a["regressed"])]
        if a["fixed"]:
            L += ["", f"**🟢 Düzelen denetimler ({len(a['fixed'])}):** " + ", ".join(a["fixed"])]
        if a["new_failed"]:
            L += ["", f"**Yeni başarısız ({len(a['new_failed'])}):** " + ", ".join(a["new_failed"])]
    return "\n".join(L)


def load_history(path):
    """history.jsonl -> [record, ...] (bozuk satirlari atlar). [saf-yakin: sadece dosya okur]"""
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def _ms(v):
    return round(v) if isinstance(v, (int, float)) else "—"


def trend_table(records):
    """history kayitlarini zaman-sirali Markdown trend tablosuna cevirir. [saf]"""
    L = [f"# PageSpeed trend — {len(records)} kayit", ""]
    L += ["| Zaman | URL | Strateji | Perf | A11y | BP | SEO | LCP | CLS |",
          "|---|---|---|---|---|---|---|---|---|"]
    for rec in records:
        ts = rec.get("ts", "—")
        url = rec.get("url", "—")
        for s, sd in (rec.get("strategies") or {}).items():
            sc = sd.get("scores") or {}
            cwv = sd.get("cwv") or {}
            L.append(f"| {ts} | {url} | {s} | {sc.get('performance')} | {sc.get('accessibility')} | "
                     f"{sc.get('best-practices')} | {sc.get('seo')} | {_ms(cwv.get('LCP'))} | {cwv.get('CLS')} |")
    return "\n".join(L)


def main():
    try:  # Windows konsolu (cp1254 vb.) UTF-8 disi karakterlerde cokmesin
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="psi_audit JSON'larini karsilastir (oncesi -> sonrasi)")
    ap.add_argument("old", nargs="?", help="Onceki psi_audit JSON")
    ap.add_argument("new", nargs="?", help="Sonraki psi_audit JSON")
    ap.add_argument("--trend", metavar="FILE", help="history.jsonl'i zaman-sirali trend tablosuna cevir")
    ap.add_argument("--fail-on-regression", action="store_true", help="Regresyonda exit 1 (CI)")
    ap.add_argument("--out", help="Markdown ciktisini bu dosyaya da yaz")
    args = ap.parse_args()

    if args.trend:
        md = trend_table(load_history(args.trend))
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(md)
        print(md)
        return

    if not (args.old and args.new):
        ap.error("iki JSON (old new) veya --trend FILE gerekli")

    with open(args.old, encoding="utf-8") as f:
        old = json.load(f)
    with open(args.new, encoding="utf-8") as f:
        new = json.load(f)

    diff = diff_results(_results(old), _results(new))
    md = to_markdown(diff, args.old, args.new)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(md)
    print(md)

    if args.fail_on_regression and diff["regressed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
