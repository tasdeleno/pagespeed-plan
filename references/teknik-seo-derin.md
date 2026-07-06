# Teknik SEO — Derin Referans

PSI'nin **SEO** ve **En İyi Uygulamalar** kategorilerindeki bulguları derinleştirmek ve planın
"SEO / Projeye Özel Aksiyonlar" bölümünü `claude-seo` olmadan da doldurmak için yerleşik referans.
9 kategoride teknik denetim + her maddede ilgili PSI denetim kimliği (`audit id`).

> Kaynak/atıf: `claude-seo` v2.2.0 (AgriciDaniel, MIT) `seo-technical` materyalinden türetilip
> PSI-odaklı Türkçeye uyarlanmıştır. Bkz. `../NOTICE.md`.

## 1. Taranabilirlik (Crawlability)
- **robots.txt**: var mı, geçerli mi, önemli kaynakları engelliyor mu?
- **XML sitemap**: var mı, robots.txt'te referanslı mı, biçim geçerli mi?
- **noindex**: kasıtlı mı kazara mı? (audit: `is-crawlable` — sayfa engelli mi?)
- **Tarama derinliği**: önemli sayfalar ana sayfadan ≤ 3 tık.
- **JS render**: kritik içerik JS gerektiriyor mu (aşağıya bak).

### AI tarayıcı yönetimi (2025-2026)
AI şirketleri modelleri eğitmek ve AI aramayı beslemek için siteyi tarar. robots.txt ile yönetim
artık teknik SEO kararıdır.

| Tarayıcı | Şirket | robots.txt token | Amaç |
|---|---|---|---|
| GPTBot | OpenAI | `GPTBot` | Model eğitimi |
| ChatGPT-User | OpenAI | `ChatGPT-User` | Gerçek zamanlı gezinme |
| ClaudeBot | Anthropic | `ClaudeBot` | Model eğitimi |
| PerplexityBot | Perplexity | `PerplexityBot` | Arama indeksi + eğitim |
| Google-Extended | Google | `Google-Extended` | Gemini eğitimi (arama DEĞİL) |
| CCBot | Common Crawl | `CCBot` | Açık veri kümesi |

Ayrım: `Google-Extended`'i engellemek Gemini eğitimini durdurur ama Google Arama indekslemesini/
AI Overviews'u etkilemez (onlar `Googlebot` kullanır). AI'da alıntılanmak marka bilinirliği ve
yönlendirme trafiği getirir → engellemeden önce AI görünürlük stratejini düşün.

## 2. İndekslenebilirlik (Indexability)
- **Canonical**: kendine referanslı, noindex ile çakışmıyor.
- **Yinelenen içerik**: near-duplicate, parametreli URL, www vs non-www.
- **İnce içerik**: sayfa türüne göre minimum altında.
- **Sayfalama**: rel=next/prev veya load-more.
- **hreflang**: çok dilli/bölgeli sitede doğru.
- **Index bloat**: gereksiz sayfalar tarama bütçesini yiyor.
- PSI SEO audit'leri: `document-title`, `meta-description`, `http-status-code`, `is-crawlable`,
  `canonical`, `hreflang`, `robots-txt`.

## 3. Güvenlik (Best Practices ile örtüşür)
- **HTTPS**: zorunlu, geçerli SSL, karışık içerik yok (audit: `is-on-https`, `redirects-http`).
- **Güvenlik başlıkları**: Content-Security-Policy (CSP), Strict-Transport-Security (HSTS),
  X-Frame-Options, X-Content-Type-Options, Referrer-Policy (audit: `csp-xss`,
  `has-hsts`, `origin-isolation`).
- Yüksek güvenlik siteleri için HSTS preload listesi.

## 4. URL Yapısı
- Temiz URL: açıklayıcı, tireli, içerik için sorgu parametresi yok.
- Mantıklı hiyerarşi; yönlendirme zinciri yok (max 1 hop), kalıcı taşımada 301.
- URL uzunluğu > 100 karakter işaretle; sondaki eğik çizgi tutarlı.

## 5. Mobil Optimizasyon
- Responsive tasarım + `<meta name=viewport>` (audit: `viewport`).
- **Dokunma hedefleri: min 48×48 px, aralarında 8 px boşluk** (audit: `target-size` /
  eski `tap-targets`). PSI `details`'i **hangi butonun** küçük olduğunu ve boyutunu verir → planda
  somut yaz (ör. "`a.nav` 24×24 → en az 48×48").
- Taban font ≥ 16 px; yatay kaydırma yok.
- **Mobile-first indeksleme 5 Temmuz 2024'te %100 tamamlandı**: Google TÜM siteleri yalnızca
  mobil Googlebot ile tarar/indeksler → mobil skoru önceliklendir.

## 6. Core Web Vitals
Özet: LCP < 2,5 sn, INP < 200 ms, CLS < 0,1; p75 gerçek kullanıcı. **Detaylı düzeltme oyun kitabı
için `core-web-vitals-derin.md`.**

## 7. Yapılandırılmış Veri (Structured Data)
- Tespit: JSON-LD (tercih), Microdata, RDFa. Google'ın desteklediği tiplere karşı doğrula.
- Detaylı tip durumu + şablonlar için `schema-ve-erisilebilirlik.md`.
- PSI audit: `structured-data` (manuel), `structured-data` bulunmasa bile ilgili sayfa tipine
  göre şema öner.

## 8. JavaScript Render
- İçerik ilk HTML'de mi yoksa JS mi gerektiriyor? CSR vs SSR ayır; SPA (React/Vue/Angular)
  indeksleme sorunlarını işaretle.
- **JS SEO (Aralık 2025 Google rehberi):**
  1. **Canonical çakışması:** ham HTML ile JS'in enjekte ettiği canonical farklıysa Google
     HERHANGİ birini kullanabilir → ikisi aynı olsun.
  2. **JS ile noindex:** ham HTML'de `noindex` varsa JS silse bile Google onu onurlandırabilir →
     doğru robots direktifini ilk HTML yanıtında ver.
  3. **200 olmayan durum kodları:** Google, 200 olmayan sayfalarda JS render etmez → hata
     sayfalarında JS ile enjekte edilen içerik görünmez.
  4. **JS'teki yapılandırılmış veri:** Product/Article gecikmeli işlenebilir → zaman-duyarlı
     markup'ı (özellikle e-ticaret Product) sunucu-render HTML'e koy.
- **En iyi uygulama:** canonical, meta robots, structured data, title, meta description gibi
  kritik SEO öğelerini ilk sunucu-render HTML'de sun.

## 9. IndexNow Protokolü
- Bing/Yandex/Naver için IndexNow desteği (Google harici). Hızlı indeksleme için öner.

## Önceliklendirme (teknik bulgular)
- **Kritik (hemen):** HTTPS yok, karışık içerik, kazara noindex, canonical çakışması, mobil
  viewport eksik.
- **Yüksek (1 hafta):** eksik meta description/title, kırık dokunma hedefleri, robots/sitemap sorunları.
- **Orta (1 ay):** güvenlik başlıkları, URL yapısı, hreflang.
- **Düşük (backlog):** IndexNow, ince içerik iyileştirmeleri.
