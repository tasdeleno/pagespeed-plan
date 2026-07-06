#!/usr/bin/env python3
"""
PageSpeed Insights denetim araci (v3 - tam kapsam).

Bir URL'yi Google PageSpeed Insights (Lighthouse) API'siyle test eder ve
PSI sayfasinda gorunen HER SEYI cikarir:
  - Kategori skorlari + Core Web Vitals (lab) + gercek kullanici (CrUX) verisi
  - Firsatlar (opportunities), Tanilar (diagnostics) VE yeni "Insights" denetimleri
  - Teknolojiye ozel oneriler (stackPacks)
  - Ucuncu taraf servisler ve kaynak dagilimi
Boylece hicbir PSI bulgusu/onerisi duesmez.

Sadece Python 3 standart kutuphanesini kullanir (pip install gerekmez).

Kullanim:
  python3 psi_audit.py https://ornek.com
  python3 psi_audit.py ornek.com --strategy both --runs 3 --locale tr --out veri.json
  PSI_API_KEY=xxxx python3 psi_audit.py https://ornek.com
"""
import argparse
import json
import os
import statistics
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

API = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
DEFAULT_CATS = ["performance", "accessibility", "best-practices", "seo"]
RETRY_CODES = {429, 500, 502, 503, 504}

METRIC_AUDITS = {
    "first-contentful-paint": "FCP",
    "largest-contentful-paint": "LCP",
    "total-blocking-time": "TBT",
    "cumulative-layout-shift": "CLS",
    "speed-index": "SpeedIndex",
    "interactive": "TTI",
}

CRUX_METRICS = {
    "FIRST_CONTENTFUL_PAINT_MS": "FCP",
    "LARGEST_CONTENTFUL_PAINT_MS": "LCP",
    "CUMULATIVE_LAYOUT_SHIFT_SCORE": "CLS",
    "INTERACTION_TO_NEXT_PAINT": "INP",
    "EXPERIMENTAL_TIME_TO_FIRST_BYTE": "TTFB",
}


def fetch(url, strategy, cats, locale, api_key, timeout, retries=3):
    params = [("url", url), ("strategy", strategy), ("locale", locale)]
    for c in cats:
        params.append(("category", c))
    if api_key:
        params.append(("key", api_key))
    q = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(q, headers={"User-Agent": "psi-audit/3.0"})
    last_err = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in RETRY_CODES and attempt < retries - 1:
                time.sleep(2 ** attempt)
                last_err = e
                continue
            raise
        except urllib.error.URLError as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                last_err = e
                continue
            raise
    if last_err:
        raise last_err


def pct(score):
    return None if score is None else round(score * 100)


def med(vals):
    v = [x for x in vals if x is not None]
    return None if not v else statistics.median(v)


def _entity_name(ent):
    if isinstance(ent, dict):
        return ent.get("text") or ent.get("url") or ent.get("name")
    return ent


def audit_savings(a):
    """Bir denetimin tahmini kazancini dondurur (ms, bytes).
    Hem klasik opportunity (overallSavingsMs) hem yeni insight (metricSavings) formatini destekler."""
    det = a.get("details") or {}
    ms = det.get("overallSavingsMs")
    by = det.get("overallSavingsBytes")
    if ms is None:
        msv = a.get("metricSavings") or {}
        vals = [v for v in msv.values() if isinstance(v, (int, float))]
        if vals:
            ms = max(vals)
    return (round(ms) if isinstance(ms, (int, float)) else None,
            by if isinstance(by, (int, float)) else None)


def _detail_value(v):
    """Bir details item degerini kisa, okunabilir bir sey'e indirger.
    Lighthouse'un node/url/kod sarmallarini 'selector - snippet' gibi acar."""
    if isinstance(v, bool):
        return None  # bool, int'in alt-turudur; gurultu, atla
    if isinstance(v, (int, float)):
        return v
    if isinstance(v, str):
        return v.strip()[:180] or None
    if isinstance(v, dict):
        if v.get("type") == "node":
            sel = (v.get("selector") or v.get("nodeLabel") or "").strip()
            snip = (v.get("snippet") or "").strip()
            s = f"{sel} — {snip}" if sel and snip else (sel or snip)
            return s[:180] or None
        for k in ("url", "value", "text", "name", "location"):
            if v.get(k) not in (None, ""):
                return str(v[k])[:180]
    return None


def extract_details(a, cap=12):
    """Bir denetimin details.items'indan SOMUT KANIT uretir (hangi element + deger).
    color-contrast / tap-targets / image-alt gibi denetimlerde PSI sayfasindaki
    'hangi element, ne kadar, hedef ne' bilgisini plana tasir. cap ile sinirlanir."""
    items = (a.get("details") or {}).get("items") or []
    if not items:
        return None
    rows = []
    for it in items[:cap]:
        if not isinstance(it, dict):
            continue
        row = {}
        for k, v in it.items():
            fv = _detail_value(v)
            if fv is not None:
                row[k] = fv
        if row:
            rows.append(row)
    if not rows:
        return None
    out = {"items": rows}
    if len(items) > cap:
        out["truncated"] = len(items) - cap
    return out


def audits_by_category(lh):
    """Her kategoride PSI'nin gosterdigi TUM gruplu denetimleri dondurur
    (firsatlar + tanilar + insights). 'metrics' grubu ve gizli (grupsuz) denetimler haric."""
    audits = lh.get("audits", {}) or {}
    groups = lh.get("categoryGroups", {}) or {}
    out = {}
    for cid, c in (lh.get("categories", {}) or {}).items():
        rows = []
        seen = set()
        for ref in c.get("auditRefs", []) or []:
            gid = ref.get("group")
            aid = ref.get("id")
            if not gid or gid == "metrics" or aid in seen:
                continue
            a = audits.get(aid)
            if not a:
                continue
            mode = a.get("scoreDisplayMode")
            if mode in ("manual", "notApplicable"):
                continue
            seen.add(aid)
            score = a.get("score")
            ms, by = audit_savings(a)
            passed = (score is not None and score >= 0.9)
            row = {
                "id": aid,
                "title": a.get("title"),
                "group": gid,
                "groupTitle": (groups.get(gid) or {}).get("title"),
                "score": pct(score),
                "scoreDisplayMode": mode,
                "passed": passed,
                "display": a.get("displayValue"),
                "savingsMs": ms,
                "savingsBytes": by,
                "metricSavings": a.get("metricSavings") or None,
                "weight": ref.get("weight", 0),
                "description": (a.get("description") or "").strip()[:1200],
            }
            if not passed:
                det = extract_details(a)
                if det:
                    row["details"] = det  # hangi element/deger (kontrast, tap-target, alt...)
            rows.append(row)
        rows.sort(key=lambda x: (
            0 if not x["passed"] else 1,
            -(x["savingsMs"] or 0),
            -(x["weight"] or 0),
            x["score"] if x["score"] is not None else 101,
        ))
        out[cid] = rows
    return out


def opportunities_from(abc):
    """Tahmini kazanci olan (henuz gecmemis) denetimleri kazanca gore siralar."""
    opps = []
    seen = set()
    for cid, rows in abc.items():
        for r in rows:
            if r["savingsMs"] and not r["passed"] and r["id"] not in seen:
                seen.add(r["id"])
                opps.append({
                    "id": r["id"], "title": r["title"], "category": cid,
                    "display": r["display"], "savingsMs": r["savingsMs"],
                    "savingsBytes": r["savingsBytes"], "score": r["score"],
                })
    opps.sort(key=lambda x: x["savingsMs"], reverse=True)
    return opps


def category_counts(abc):
    out = {}
    for cid, rows in abc.items():
        tofix = [r for r in rows if not r["passed"]]
        out[cid] = {"toplam": len(rows), "duzeltilecek": len(tofix), "gecti": len(rows) - len(tofix)}
    return out


def extract_third_parties(audits):
    a = audits.get("third-party-summary")
    if not a:
        return None
    items = (a.get("details") or {}).get("items") or []
    out = []
    for it in items:
        out.append({
            "entity": _entity_name(it.get("entity")),
            "blockingMs": round(it.get("blockingTime") or 0),
            "mainThreadMs": round(it.get("mainThreadTime") or 0),
            "transferBytes": it.get("transferSize"),
        })
    out.sort(key=lambda x: x["blockingMs"], reverse=True)
    return out[:8] or None


def extract_resource_summary(audits):
    a = audits.get("resource-summary")
    if not a:
        return None
    items = (a.get("details") or {}).get("items") or []
    out = {}
    for it in items:
        rt = it.get("resourceType") or it.get("label")
        if not rt:
            continue
        out[rt] = {"requests": it.get("requestCount"), "transferBytes": it.get("transferSize")}
    return out or None


def extract_largest_resources(audits, top=10):
    """En agir tekil kaynaklar (transferSize'a gore). resourceSummary'nin tur-toplami
    gizledigi tek sisman dosyayi (cogu zaman logo/header ikonu) yuzeye cikarir."""
    a = audits.get("network-requests")
    if not a:
        return None
    items = (a.get("details") or {}).get("items") or []
    out = []
    for it in items:
        ts = it.get("transferSize")
        if not isinstance(ts, (int, float)) or ts <= 0:
            continue
        out.append({
            "url": (it.get("url") or "")[:140],
            "type": it.get("resourceType"),
            "mime": it.get("mimeType"),
            "transferBytes": round(ts),
        })
    out.sort(key=lambda x: x["transferBytes"], reverse=True)
    return out[:top] or None


def extract_stackpacks(lh):
    """Lighthouse'un teknolojiye ozel onerileri (WordPress, React, WooCommerce vb.)."""
    sp = lh.get("stackPacks") or []
    out = []
    for p in sp:
        descs = p.get("descriptions") or {}
        out.append({
            "id": p.get("id"),
            "title": p.get("title"),
            "adviceCount": len(descs),
            "advice": {k: (v or "").strip()[:300] for k, v in list(descs.items())[:25]},
        })
    return out or None


def run_once(data, strategy):
    lh = data.get("lighthouseResult", {}) or {}
    audits = lh.get("audits", {}) or {}

    categories = {}
    for cid, c in (lh.get("categories", {}) or {}).items():
        categories[cid] = {"title": c.get("title"), "score": pct(c.get("score"))}

    lab_metrics = {}
    for aid, label in METRIC_AUDITS.items():
        a = audits.get(aid)
        if a:
            lab_metrics[label] = {
                "display": a.get("displayValue"),
                "numericValue": a.get("numericValue"),
                "score": pct(a.get("score")),
            }

    abc = audits_by_category(lh)

    field = {}
    le = data.get("loadingExperience", {}) or {}
    for key, label in CRUX_METRICS.items():
        m = (le.get("metrics") or {}).get(key)
        if m:
            field[label] = {"percentile": m.get("percentile"), "category": m.get("category")}

    return {
        "strategy": strategy,
        "finalUrl": lh.get("finalUrl"),
        "requestedUrl": lh.get("requestedUrl"),
        "lighthouseVersion": lh.get("lighthouseVersion"),
        "categories": categories,
        "labMetrics": lab_metrics,
        "fieldData": field or None,
        "fieldOverall": le.get("overall_category"),
        "auditsByCategory": abc,
        "counts": category_counts(abc),
        "opportunities": opportunities_from(abc),
        "thirdParties": extract_third_parties(audits),
        "resourceSummary": extract_resource_summary(audits),
        "largestResources": extract_largest_resources(audits),
        "stackPacks": extract_stackpacks(lh),
    }


def compute_gaps(lab, field):
    if not field:
        return []
    gaps = []
    for m in ("LCP", "CLS", "FCP"):
        lm = lab.get(m)
        fm = field.get(m)
        if not fm:
            continue
        fcat = fm.get("category")
        lscore = lm.get("score") if lm else None
        if fcat and fcat != "GOOD" and lscore is not None and lscore >= 90:
            gaps.append({"metric": m,
                         "note": f"Lab iyi (skor {lscore}) ama gercek kullanicida {fcat}. Saha verisini onceliklendir."})
        elif lscore is not None and lscore < 50 and fcat == "GOOD":
            gaps.append({"metric": m,
                         "note": f"Lab kotu (skor {lscore}) ama gercek kullanicida GOOD. Lab olcumu ortam kaynakli olabilir."})
    return gaps


def aggregate(runs, strategy):
    all_cids = set()
    for r in runs:
        all_cids |= set(r["categories"].keys())

    categories = {}
    for cid in all_cids:
        scores = [r["categories"].get(cid, {}).get("score") for r in runs]
        title = next((r["categories"][cid]["title"] for r in runs if cid in r["categories"]), cid)
        m = med(scores)
        categories[cid] = {"title": title,
                           "score": round(m) if m is not None else None,
                           "runs": [s for s in scores]}

    perf = [(i, r["categories"].get("performance", {}).get("score")) for i, r in enumerate(runs)]
    perf = [(i, s) for i, s in perf if s is not None]
    if perf:
        mp = med([s for _, s in perf])
        rep_idx = min(perf, key=lambda t: abs(t[1] - mp))[0]
    else:
        rep_idx = 0
    rep = runs[rep_idx]

    labels = set()
    for r in runs:
        labels |= set(r["labMetrics"].keys())
    lab = {}
    for lbl in labels:
        nums = [r["labMetrics"].get(lbl, {}).get("numericValue") for r in runs]
        scs = [r["labMetrics"].get(lbl, {}).get("score") for r in runs]
        ms = med(scs)
        lab[lbl] = {"display": rep["labMetrics"].get(lbl, {}).get("display"),
                    "numericValue": med(nums),
                    "score": round(ms) if ms is not None else None}

    return {
        "strategy": strategy,
        "runs": len(runs),
        "finalUrl": rep.get("finalUrl"),
        "requestedUrl": rep.get("requestedUrl"),
        "redirected": bool(rep.get("finalUrl") and rep.get("requestedUrl")
                           and rep["finalUrl"].rstrip("/") != rep["requestedUrl"].rstrip("/")),
        "lighthouseVersion": rep.get("lighthouseVersion"),
        "categories": categories,
        "labMetrics": lab,
        "fieldData": rep.get("fieldData"),
        "fieldOverall": rep.get("fieldOverall"),
        "labVsFieldGaps": compute_gaps(lab, rep.get("fieldData")),
        "counts": rep.get("counts"),
        "opportunities": rep.get("opportunities"),
        "auditsByCategory": rep.get("auditsByCategory"),
        "thirdParties": rep.get("thirdParties"),
        "resourceSummary": rep.get("resourceSummary"),
        "largestResources": rep.get("largestResources"),
        "stackPacks": rep.get("stackPacks"),
    }


def main():
    ap = argparse.ArgumentParser(description="PageSpeed Insights denetim araci (tam kapsam)")
    ap.add_argument("url", help="Test edilecek URL")
    ap.add_argument("--strategy", choices=["mobile", "desktop", "both"], default="both")
    ap.add_argument("--runs", type=int, default=3, help="Strateji basina kosu (medyan alinir)")
    ap.add_argument("--categories", default=",".join(DEFAULT_CATS))
    ap.add_argument("--locale", default="tr")
    ap.add_argument("--api-key", default=os.environ.get("PSI_API_KEY"))
    ap.add_argument("--timeout", type=int, default=90)
    ap.add_argument("--delay", type=float, default=1.0, help="Kosular arasi bekleme (sn)")
    ap.add_argument("--out", help="JSON ozeti ek olarak bu dosyaya yaz")
    args = ap.parse_args()

    url = args.url
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    cats = [c.strip() for c in args.categories.split(",") if c.strip()]
    strategies = ["mobile", "desktop"] if args.strategy == "both" else [args.strategy]
    runs_n = max(1, args.runs)

    out = {"url": url, "locale": args.locale, "runsRequested": runs_n,
           "results": {}, "errors": {}, "warnings": {}}

    for s in strategies:
        singles = []
        err = None
        for i in range(runs_n):
            try:
                data = fetch(url, s, cats, args.locale, args.api_key, args.timeout)
                if isinstance(data, dict) and "error" in data:
                    err = data["error"].get("message") if isinstance(data["error"], dict) else str(data["error"])
                    break
                singles.append(run_once(data, s))
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", "ignore")[:400]
                err = f"HTTP {e.code}: {body}"
                break
            except urllib.error.URLError as e:
                err = f"Aginda hata: {e.reason}"
                break
            except Exception as e:  # noqa: BLE001
                err = f"{type(e).__name__}: {e}"
                break
            if i < runs_n - 1:
                time.sleep(args.delay)
        if singles:
            out["results"][s] = aggregate(singles, s)
            if err:
                out["warnings"][s] = f"{len(singles)}/{runs_n} kosu basarili; son hata: {err}"
        else:
            out["errors"][s] = err or "bilinmeyen hata"

    text = json.dumps(out, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
    print(text)

    if not out["results"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
