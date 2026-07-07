#!/usr/bin/env python3
"""psi_audit / psi_diff / contrast oz-kontrolu (stdlib, framework yok).
Calistir: python3 scripts/test_psi_audit.py  -> hata yoksa 'OK' basar."""
from psi_audit import (extract_details, _detail_value, parse_sitemap,
                       parse_budget, check_budget, parse_robots_ai)
from psi_diff import diff_results
from contrast import contrast_ratio, wcag_pass


def test_node_flatten():
    v = {"type": "node", "selector": "button.cta", "snippet": "<button class='cta'>Al</button>"}
    assert _detail_value(v) == "button.cta — <button class='cta'>Al</button>"


def test_bool_skipped():
    assert _detail_value(True) is None
    assert _detail_value(1) == 1  # bool atlanir ama gercek int kalir


def test_tap_target_evidence():
    a = {"details": {"items": [
        {"tapTarget": {"type": "node", "selector": "a.nav", "snippet": "<a>X</a>"},
         "size": "24x24", "shouldBeMobileFriendly": True},
    ]}}
    out = extract_details(a)
    assert out is not None
    item = out["items"][0]
    assert item["size"] == "24x24"
    assert item["tapTarget"].startswith("a.nav")
    assert "shouldBeMobileFriendly" not in item  # bool gurultu atlandi


def test_empty_details():
    assert extract_details({"title": "x"}) is None
    assert extract_details({"details": {"items": []}}) is None


def test_cap_and_truncated():
    items = [{"url": f"https://x/{i}.js"} for i in range(20)]
    out = extract_details({"details": {"items": items}}, cap=12)
    assert len(out["items"]) == 12
    assert out["truncated"] == 8


def test_parse_sitemap():
    xml = ('<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
           '<url><loc>https://a.com/</loc></url><url><loc>https://a.com/x</loc></url></urlset>')
    assert parse_sitemap(xml) == ["https://a.com/", "https://a.com/x"]
    assert parse_sitemap("<bozuk") == []


def test_parse_budget():
    assert parse_budget("perf=90, lcp=2500 , cls=0.1,bozuk") == {"perf": 90.0, "lcp": 2500.0, "cls": 0.1}


def test_check_budget():
    results = {"mobile": {"categories": {"performance": {"score": 80}, "seo": {"score": 95}},
                          "labMetrics": {"LCP": {"numericValue": 3000}, "CLS": {"numericValue": 0.05}}}}
    keys = {v["key"] for v in check_budget(results, "perf=90,seo=90,lcp=2500,cls=0.1")}
    assert keys == {"perf", "lcp"}  # perf 80<90, lcp 3000>2500 ihlal; seo/cls gecti
    assert check_budget(results, "perf=70") == []


def test_parse_robots_ai():
    r = parse_robots_ai("User-agent: GPTBot\nDisallow: /\n\nUser-agent: *\nAllow: /\n")
    assert r["GPTBot"] == "blocked"
    assert r["ClaudeBot"] == "not-mentioned"


def test_diff_results():
    old = {"mobile": {"categories": {"performance": {"score": 90}},
                      "labMetrics": {"LCP": {"numericValue": 2000}},
                      "auditsByCategory": {"performance": [{"id": "x", "passed": True},
                                                           {"id": "y", "passed": False}]}}}
    new = {"mobile": {"categories": {"performance": {"score": 80}},
                      "labMetrics": {"LCP": {"numericValue": 2500}},
                      "auditsByCategory": {"performance": [{"id": "x", "passed": False},
                                                           {"id": "y", "passed": True}]}}}
    d = diff_results(old, new)
    assert d["regressed"] is True
    audits = d["strategies"]["mobile"]["audits"]
    assert "x" in audits["regressed"] and "y" in audits["fixed"]


def test_contrast():
    assert round(contrast_ratio("#000000", "#ffffff")) == 21
    assert wcag_pass(21)["AAA"] is True
    assert wcag_pass(contrast_ratio("#999999", "#ffffff"))["AA"] is False  # ~2.85 < 4.5
    assert contrast_ratio("rgba(0,0,0,1)", "#fff") > contrast_ratio("rgba(0,0,0,0.4)", "#fff")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("OK")
