#!/usr/bin/env python3
"""extract_details icin kucuk oz-kontrol (stdlib, framework yok).
Calistir: python3 scripts/test_psi_audit.py  -> hata yoksa 'OK' basar."""
from psi_audit import extract_details, _detail_value


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


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("OK")
