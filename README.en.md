<p align="center">
  <img src="assets/banner.png" alt="pagespeed-plan" width="100%">
</p>

<h1 align="center">pagespeed-plan</h1>

<p align="center">
  A zero-dependency Claude skill that turns PageSpeed Insights audits into a prioritized,
  evidence-backed, actionable improvement plan.
</p>

<p align="center">
  <img alt="Python 3" src="https://img.shields.io/badge/Python-3-blue">
  <img alt="stdlib only" src="https://img.shields.io/badge/deps-stdlib%20only-brightgreen">
  <img alt="CI ready" src="https://img.shields.io/badge/CI-ready-success">
  <img alt="MIT" src="https://img.shields.io/badge/license-MIT-black">
</p>

<p align="center"><a href="README.md">Türkçe</a> · <b>English</b></p>

PageSpeed Insights gives you the score and the recommendations. `pagespeed-plan` turns them into a
CI budget gate that can fail a build, a before/after diff, a sitemap-wide crawl, a shareable report,
and a prioritized plan an agent can read and act on — all in plain Python, with no Node/Chrome and no
`pip install`.

## Contents

- [What it does](#what-it-does)
- [Install](#install)
- [Usage](#usage)
- [Modes and scripts](#modes-and-scripts)
- [CI (GitHub Actions)](#ci-github-actions)
- [How it works](#how-it-works)
- [Where it fits vs other tools](#where-it-fits-vs-other-tools)
- [Example output](#example-output)
- [Configuration](#configuration)
- [Built-in depth](#built-in-depth)
- [FAQ](#faq)
- [Roadmap](#roadmap)
- [License and attribution](#license-and-attribution)

## What it does

It tests a URL with PageSpeed Insights v5 (Lighthouse) and extracts every visible audit —
opportunities, diagnostics, Insights, stack-specific advice, and Core Web Vitals (lab + CrUX). Each
finding carries its fix recommendation (`description`) and concrete evidence (`details`: which element,
what value → target). It won't just say *"low contrast"*; it says *"`button.cta` 2.1:1 → target 4.5:1"*.
The output is a single Markdown plan ordered by impact × effort.

Measurement uses only the Python standard library; it never modifies the site — read-only.

## Install

```bash
git clone https://github.com/tasdeleno/pagespeed-plan.git ~/.claude/skills/pagespeed-plan
```

That's it — no dependencies. (Optional: `PSI_API_KEY` env var to avoid quota limits.)

## Usage

Easiest: tell Claude **"run a PageSpeed test on this site"**. From the command line:

```bash
python3 scripts/psi_audit.py https://example.com --out psi.json          # single URL
python3 scripts/psi_audit.py --from-robots https://example.com           # robots.txt → whole site
python3 scripts/psi_audit.py https://example.com --budget "perf=90"      # CI gate (exit 1)
python3 scripts/psi_plan.py psi.json --out plan.md                       # deterministic plan (no LLM)
python3 scripts/psi_report.py psi.json --out report.html                 # HTML report
```

For every flag plus `psi_diff`/`contrast`, see [Modes and scripts](#modes-and-scripts).

## Modes and scripts

| Script | Job |
|---|---|
| `scripts/psi_audit.py` | Audit + JSON. Single/multi URL, `--sitemap`, `--from-robots`, `--screenshots`, `--geo`, `--budget`, `--history` |
| `scripts/psi_plan.py` | Renders the JSON into a deterministic Markdown plan, no LLM (summary/CWV/priorities/evidence) |
| `scripts/psi_diff.py` | Compares two audits (`--fail-on-regression`); `--trend history.jsonl` for a score trend over time |
| `scripts/psi_report.py` | Renders the JSON into a self-contained single-file HTML report |
| `scripts/contrast.py` | Code-side WCAG contrast ratio; exits 1 if AA fails (no browser needed) |

## CI (GitHub Actions)

If a `--budget` threshold is exceeded, `psi_audit.py` returns **exit 1** and fails the build:

```yaml
- name: PageSpeed budget gate
  run: |
    python3 scripts/psi_audit.py https://example.com \
      --strategy mobile --runs 1 --budget "perf=90,lcp=2500,cls=0.1"
```

For a post-deploy regression gate, compare two runs:
`python3 scripts/psi_diff.py old.json new.json --fail-on-regression`.

## How it works

<p align="center"><img src="assets/schema.png" alt="pagespeed-plan flow diagram" width="100%"></p>

<details>
<summary>Text-based diagram (Mermaid)</summary>

```mermaid
flowchart LR
    U([URL · URLs]) --> S["psi_audit.py<br/>stdlib · median-of-N · mobile+desktop"]
    SM([sitemap.xml · robots.txt]) -.->|parse_sitemap · --from-robots| S
    S -->|PSI v5 runPagespeed| G[("Google PSI<br/>Lighthouse + CrUX")]
    S -.->|--geo| W[("target site<br/>robots.txt · llms.txt")]
    G --> J[("psi JSON<br/>scores · CWV · auditsByCategory + details<br/>opportunities · screenshots · geo · pages")]
    W -.-> J
    J -->|--budget exceeded| X{{"exit 1 · CI gate"}}
    J --> M["Claude + references/<br/>prioritized plan .md"]
    O[["claude-seo · optional"]] -.-> M
    J --> PL["psi_plan.py<br/>deterministic plan .md"]
    J --> R["psi_report.py<br/>self-contained HTML"]
    J -.->|--history| H[("history.jsonl")]
    H --> T["psi_diff.py --trend<br/>score/CWV trend"]
    P([previous JSON]) --> D["psi_diff.py<br/>before → after · exit 1 on regression"]
    J --> D
```

</details>

`psi_audit.py` gets lab data from PSI and field data from CrUX; `--geo`/`--sitemap`/`--from-robots` are
fetched directly from the target site. The same JSON feeds `--budget` (CI gate), `psi_plan.py` (deterministic
plan), `psi_report.py` (HTML) and `psi_diff.py` (comparing two runs; `--history` for a trend over time); the
rich plan is written by Claude + the built-in `references/` (with `claude-seo` adding depth if installed).

## Where it fits vs other tools

If you just want to look at your score, pagespeed.web.dev is enough. The difference is in what the PSI
page doesn't do:

| | pagespeed.web.dev | Lighthouse CI | Unlighthouse | pagespeed-plan |
|---|:---:|:---:|:---:|:---:|
| Prioritized plan | raw list | — | — | ✓ |
| Concrete evidence (element/value) | in UI | — | partial | text (agent-readable) |
| CI budget gate | — | ✓ | ✓ | ✓ |
| Before/after diff | — | ✓ | partial | ✓ |
| Multi-page / sitemap | — | ✓ | ✓ | ✓ |
| Single-file HTML report | own UI | server | ✓ | ✓ |
| GEO / llms.txt | — | — | — | ✓ |
| Setup cost | — | Node | Node+Chrome | zero-pip |

## Example output

The self-contained HTML report from `psi_report.py` (score cards, CWV, priorities, evidence-backed findings):

<p align="center"><img src="assets/report-ornek.png" alt="Example HTML report" width="82%"></p>

The Markdown plan covers summary scores, Core Web Vitals, impact×effort priorities, all performance
findings, SEO/accessibility actions (each with concrete evidence), and a post-deploy retest step.
A short excerpt:

```markdown
## 3. Priority actions (impact × effort)
| # | Action | Impact | Effort | Est. gain | Audit |
|---|---|---|---|---|---|
| 1 | Defer render-blocking resources | High | High | ~1100 ms | render-blocking-resources |

### Accessibility — 1 to fix
- **Low contrast** (color-contrast) — Darken the colors.
  - element: button.cta — <button class='cta'>Buy</button> · contrast: 2.1
```

`psi_plan.py` produces the same skeleton deterministically (no LLM). Full example:
[`references/ornek_plan_iskeleti.md`](references/ornek_plan_iskeleti.md).

## Configuration

`psi_audit.py` flags:

| Flag | Default | Description |
|---|---|---|
| `--strategy` | `both` | `mobile` · `desktop` · `both` |
| `--runs` | 3 (multi: 1) | Runs per strategy; median is taken |
| `--sitemap URL` | — | Crawl a sitemap.xml |
| `--from-robots URL` | — | Discover sitemaps from robots.txt |
| `--max-pages` | 10 | Page cap in multi mode |
| `--budget` | — | Exit 1 on threshold breach (CI) |
| `--screenshots DIR` | — | Write screenshot + filmstrip |
| `--geo` | — | robots.txt AI-crawler + llms.txt check |
| `--history FILE` | — | Append the run to a JSONL (trend) |
| `--locale` | `tr` | Report language |
| `--api-key` | `PSI_API_KEY` | PSI API key (for quota) |
| `--out FILE` | — | Also write the JSON to a file |

## Built-in depth

SEO/technical/accessibility depth lives locally under `references/`; `claude-seo` is not required
(if installed, it's used for optional extra depth).

| File | Content |
|---|---|
| [`core-web-vitals-derin.md`](references/core-web-vitals-derin.md) | LCP subparts, INP/CLS breakdown, thresholds, CrUX pitfalls |
| [`teknik-seo-derin.md`](references/teknik-seo-derin.md) | Crawlability, indexability, security, mobile, JS rendering, AI crawlers |
| [`seo-performans-ajan.md`](references/seo-performans-ajan.md) | Performance diagnosis method and bottleneck catalog |
| [`schema-ve-erisilebilirlik.md`](references/schema-ve-erisilebilirlik.md) | JSON-LD templates, WCAG/a11y mapping |

> Reference files are written in Turkish; the code and this README are English/Turkish.

## FAQ

**Do I need an API key?** No — it works without one, but Google applies a low rate limit.
Since median-of-3 makes several requests, `PSI_API_KEY` is recommended (free: Google Cloud Console).

**Hit the quota (429)?** Drop to `--runs 1`, add `PSI_API_KEY`, or use `--strategy mobile` to halve the requests.

**Why this over PSI?** PSI gives you the score and recommendations; here you get a CI budget gate, diff,
sitemap crawl, a shareable report, and an agent-actionable prioritized plan. See the
[comparison table](#where-it-fits-vs-other-tools).

**Does it modify the site?** No — read-only (PSI + robots.txt/llms.txt).

**Node/Chrome required?** No. Every script is Python stdlib; no `pip install`.

## Roadmap

Carbon/CO₂ estimate · CrUX 25-week field trend · optional local Lighthouse (quota-free).

## License and attribution

MIT — [`LICENSE`](LICENSE). The `references/` content is derived from `claude-seo` v2.2.0
(AgriciDaniel, MIT); attribution in [`NOTICE.md`](NOTICE.md). To contribute, keep the stdlib-only
principle in the scripts and make sure `python3 scripts/test_psi_audit.py` passes.
