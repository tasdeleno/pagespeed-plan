<p align="center">
  <img src="assets/banner.png" alt="pagespeed-plan" width="100%">
</p>

<h1 align="center">pagespeed-plan</h1>

<p align="center">
  PageSpeed Insights denetimlerini önceliklendirilmiş, kanıtlı ve uygulanabilir bir
  iyileştirme planına çeviren, bağımlılıksız bir Claude skill'i.
</p>

<p align="center">
  <img alt="Python 3" src="https://img.shields.io/badge/Python-3-blue">
  <img alt="stdlib only" src="https://img.shields.io/badge/deps-stdlib%20only-brightgreen">
  <img alt="CI ready" src="https://img.shields.io/badge/CI-ready-success">
  <img alt="MIT" src="https://img.shields.io/badge/license-MIT-black">
</p>

<p align="center"><b>Türkçe</b> · <a href="README.en.md">English</a></p>

PageSpeed Insights sana skoru ve önerileri verir. `pagespeed-plan` bunları CI'de kırılabilen bir
bütçe kapısına, dağıtım öncesi/sonrası bir diff'e, sitemap taramasına, paylaşılabilir bir rapora ve
bir ajanın okuyup uygulayabileceği önceliklendirilmiş bir plana çevirir — Node/Chrome ya da
`pip install` olmadan, saf Python ile.

## İçindekiler

- [Ne yapar](#ne-yapar)
- [Kurulum](#kurulum)
- [Kullanım](#kullanım)
- [Modlar ve betikler](#modlar-ve-betikler)
- [Nasıl çalışır](#nasıl-çalışır)
- [PSI ve diğer araçlara göre konum](#psi-ve-diğer-araçlara-göre-konum)
- [Plan çıktısı](#plan-çıktısı)
- [Yerleşik derinlik](#yerleşik-derinlik)
- [Roadmap](#roadmap)
- [Lisans ve atıf](#lisans-ve-atıf)

## Ne yapar

Bir URL'yi PageSpeed Insights v5 (Lighthouse) ile test eder ve görünen her denetimi — fırsatlar,
tanılar, Insights, teknolojiye özel öneriler, Core Web Vitals (lab + CrUX) — çıkarır. Her bulguya
düzeltme önerisini (`description`) ve somut kanıtını (`details`: hangi element, hangi değer → hedef)
ekler. Örneğin *"kontrast kötü"* demez; *"`button.cta` 2,1:1 → hedef 4,5:1"* der. Çıktı, etki × efor
sırasına dizilmiş tek bir Markdown planıdır.

Ölçüm yalnızca Python standart kütüphanesiyle yapılır; siteyi değiştirmez, yalnızca okur.

## Kurulum

```bash
git clone https://github.com/tasdeleno/pagespeed-plan.git ~/.claude/skills/pagespeed-plan
```

Hepsi bu — bağımlılık yok. (Opsiyonel: kota için `PSI_API_KEY` ortam değişkeni.)

## Kullanım

En kolayı: Claude'a **"şu sitenin PageSpeed testini yap"** de. Komut satırından:

```bash
python3 scripts/psi_audit.py https://ornek.com --out psi.json         # tek URL
python3 scripts/psi_audit.py --sitemap https://ornek.com/sitemap.xml  # tüm site
python3 scripts/psi_audit.py https://ornek.com --budget "perf=90"     # CI kapısı (exit 1)
python3 scripts/psi_report.py psi.json --out rapor.html               # HTML rapor
```

Tüm bayraklar ve `psi_diff`/`contrast` için [Modlar ve betikler](#modlar-ve-betikler).

## Modlar ve betikler

| Betik | İş |
|---|---|
| `scripts/psi_audit.py` | Denetim + JSON. Tek/çoklu URL, `--sitemap`, `--screenshots`, `--geo`, `--budget` |
| `scripts/psi_diff.py` | İki denetimi karşılaştırır; `--fail-on-regression` ile CI kapısı |
| `scripts/psi_report.py` | JSON'u kendine-yeter tek-dosya HTML rapora çevirir |
| `scripts/contrast.py` | Kod-tarafı WCAG kontrast oranı; AA geçmezse exit 1 (tarayıcı gerekmez) |

## Nasıl çalışır

```mermaid
flowchart LR
    U([URL · URL'ler]) --> S["psi_audit.py<br/>stdlib · medyan-of-N · mobil+masaüstü"]
    SM([sitemap.xml]) -.->|parse_sitemap| S
    S -->|PSI v5 runPagespeed| G[("Google PSI<br/>Lighthouse + CrUX")]
    S -.->|--geo| W[("hedef site<br/>robots.txt · llms.txt")]
    G --> J[("psi JSON<br/>skorlar · CWV · auditsByCategory + details<br/>opportunities · screenshots · geo · pages")]
    W -.-> J
    J -->|--budget ihlali| X{{"exit 1 · CI kapısı"}}
    J --> M["Claude + references/<br/>önceliklendirilmiş plan .md"]
    O[["claude-seo · opsiyonel"]] -.-> M
    J --> R["psi_report.py<br/>kendine-yeter HTML"]
    P([önceki JSON]) --> D["psi_diff.py<br/>öncesi → sonrası · regresyonda exit 1"]
    J --> D
```

`psi_audit.py` ölçümü PSI'den, saha verisini CrUX'tan alır; `--geo`/`--sitemap` doğrudan hedef siteden
çeker. Aynı JSON'u `--budget` (CI kapısı), `psi_report.py` (HTML) ve `psi_diff.py` (iki çalışmayı
karşılaştırma) tüketir; plan ise Claude + yerleşik `references/` ile yazılır (`claude-seo` kuruluysa ek derinlik).

## PSI ve diğer araçlara göre konum

Sadece skoruna bakacaksan pagespeed.web.dev yeterli. Fark, PSI sayfasının yapmadığı işlerde:

| | pagespeed.web.dev | Lighthouse CI | Unlighthouse | pagespeed-plan |
|---|:---:|:---:|:---:|:---:|
| Önceliklendirilmiş plan | ham liste | — | — | ✓ |
| Somut kanıt (element/değer) | UI'da | — | kısmi | metin (ajan okur) |
| CI bütçe kapısı | — | ✓ | ✓ | ✓ |
| Öncesi/sonrası diff | — | ✓ | kısmi | ✓ |
| Çoklu sayfa / sitemap | — | ✓ | ✓ | ✓ |
| Tek-dosya HTML rapor | kendi UI | sunucu | ✓ | ✓ |
| GEO / llms.txt | — | — | — | ✓ |
| Kurulum yükü | — | Node | Node+Chrome | sıfır-pip |

## Plan çıktısı

Üretilen Markdown; özet skorlar, Core Web Vitals, etki×efor öncelikleri, tüm performans bulguları,
SEO/erişilebilirlik aksiyonları (her biri somut kanıtla), teknolojiye özel notlar ve dağıtım sonrası
tekrar-test adımını içerir. Örnek: [`references/ornek_plan_iskeleti.md`](references/ornek_plan_iskeleti.md).

## Yerleşik derinlik

SEO/teknik/erişilebilirlik derinliği `references/` altında yereldir; `claude-seo` gerekmez
(kuruluysa opsiyonel ek derinlik için kullanılır).

| Dosya | İçerik |
|---|---|
| [`core-web-vitals-derin.md`](references/core-web-vitals-derin.md) | LCP alt-parçaları, INP/CLS kırılımı, eşikler, CrUX tuzakları |
| [`teknik-seo-derin.md`](references/teknik-seo-derin.md) | Crawlability, indexability, güvenlik, mobil, JS render, AI-crawler |
| [`seo-performans-ajan.md`](references/seo-performans-ajan.md) | Performans teşhis yöntemi ve darboğaz kataloğu |
| [`schema-ve-erisilebilirlik.md`](references/schema-ve-erisilebilirlik.md) | JSON-LD şablonları, WCAG/a11y eşlemesi |

## Roadmap

Karbon/CO₂ tahmini · CrUX 25-hafta saha trendi · opsiyonel yerel Lighthouse (kota-bağımsız).

## Lisans ve atıf

MIT — [`LICENSE`](LICENSE). `references/` içeriği `claude-seo` v2.2.0 (AgriciDaniel, MIT)
materyalinden türetilmiştir; atıf: [`NOTICE.md`](NOTICE.md). Katkı için betiklerde stdlib-only
ilkesini koru ve `python3 scripts/test_psi_audit.py` öz-kontrolünü geçir.
