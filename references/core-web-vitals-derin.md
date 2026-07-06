# Core Web Vitals — Derin Referans

Bu dosya, PSI/Lighthouse çıktısındaki Core Web Vitals (CWV) bulgularını **derinlemesine**
yorumlamak için yerleşik referanstır. `claude-seo` kurulu olmasa da plan bu derinlikle yazılır.

> Kaynak/atıf: içerik `claude-seo` v2.2.0 (AgriciDaniel, MIT) `seo-google` + `seo-performance`
> materyalinden türetilip PSI-odaklı Türkçeye uyarlanmıştır. Bkz. `../NOTICE.md`.

## Eşikler (Mart 2026 itibarıyla güncel)

| Metrik | İyi | Geliştirilmeli | Zayıf | Birim |
|---|---|---|---|---|
| **LCP** (Largest Contentful Paint) | ≤ 2.500 ms | 2.500–4.000 ms | > 4.000 ms | ms |
| **INP** (Interaction to Next Paint) | ≤ 200 ms | 200–500 ms | > 500 ms | ms |
| **CLS** (Cumulative Layout Shift) | ≤ 0,1 | 0,1–0,25 | > 0,25 | birimsiz |
| **FCP** (First Contentful Paint) | ≤ 1.800 ms | 1.800–3.000 ms | > 3.000 ms | ms |
| **TTFB** (Time to First Byte) | ≤ 800 ms | 800–1.800 ms | > 1.800 ms | ms |

**Önemli:** INP, 12 Mart 2024'te FID'nin yerini aldı; FID 9 Eylül 2024'te tüm Chrome
araçlarından (CrUX, PSI, Lighthouse) tamamen kaldırıldı. **Çıktıda asla FID'den söz etme.**

## Değerlendirme yöntemi (kritik ayrım)
- Google, gerçek kullanıcıların **75. persentilini (p75)** değerlendirir: ziyaretlerin %75'i
  "iyi" eşiğini geçmeli.
- **Saha (field/CrUX)** verisi = 28 günlük gerçek Chrome kullanıcı ortalaması → asıl karne budur.
- **Lab (Lighthouse)** verisi = tek bir denetleyici koşusu → teşhis içindir; saha ile doğrula.
- PSI JSON'da: saha `loadingExperience` (URL) + `originLoadingExperience` (kaynak) altında;
  lab ise `lighthouseResult.audits` altında. `psi_audit.py` ikisini de çıkarır (`fieldData`,
  `labMetrics`, `labVsFieldGaps`).
- **Kural:** Saha "GOOD" değilse ama lab iyiyse (`labVsFieldGaps`), **saha metriğini** önceliklendir.

## LCP alt-parçaları (Şubat 2025'ten beri CrUX'ta)
LCP tek bir sayı değildir; dört parçaya ayrılır. Hangi parçanın büyük olduğu düzeltmeyi belirler:

1. **TTFB** — sunucu ilk baytı ne kadar sürede gönderdi. Büyükse: edge/CDN, sunucu önbelleği,
   TTFB > 800 ms → sunucu tarafı (PSI audit: `server-response-time`).
2. **Resource load delay** — LCP kaynağı keşfedilene kadar geçen boşluk. Büyükse: kaynak geç
   keşfediliyor → `<link rel=preload as=image>`, `fetchpriority=high`, HTML'e erken koy
   (audit: `prioritize-lcp-image`, `lcp-lazy-loaded` — LCP görseli lazy olmamalı).
3. **Resource load duration** — LCP kaynağının indirilme süresi. Büyükse: görseli sıkıştır,
   WebP/AVIF, boyutlandır, CDN (audit: `uses-optimized-images`, `uses-responsive-images`,
   `modern-image-formats`, `unsized-images`).
4. **Element render delay** — indirildikten sonra ekrana boyanana kadar. Büyükse: render'ı
   engelleyen CSS/JS, kritik CSS eksik (audit: `render-blocking-resources`,
   `render-blocking-insight`, `unused-css-rules`).

### SPA'da geç-LCP tuzağı
LCP görseli JS render + API çağrısı sonrası indiriliyorsa (React/Vue) `fetchpriority=high` bile
geç devreye girer. Çözüm: sunucu-taraflı `<link rel=preload as=image>` veya HTML'e inline.
**Preload URL'si `<img>`'in gerçekte indirdiğiyle BİREBİR eşleşmeli** (CDN transform + `srcset`/`sizes`
dahil), yoksa çift indirme olur ve preload boşa gider.

## INP (etkileşim) kırılımı
INP üç bileşenin toplamıdır: **input delay** + **processing time** + **presentation delay**.
Yaygın nedenler ve düzeltmeler:
- Ana iş parçacığındaki uzun JS görevleri → görevleri < 50 ms parçalara böl, `scheduler.yield()`,
  `requestIdleCallback` (audit: `long-tasks`, `bootup-time`, `mainthread-work-breakdown`).
- Ağır olay işleyicileri → debounce/throttle, `requestAnimationFrame`.
- Aşırı DOM (> ~1.500 öğe) → sanallaştırma, DOM'u küçült (audit: `dom-size`).
- Üçüncü taraf scriptleri ana iş parçacığını ele geçiriyor → ertele/parçala (audit:
  `third-party-summary`, `third-party-facades`).
- Senkron işlemler → asenkron yap.
- Lab karşılığı **TBT** (Total Blocking Time); TBT ≤ 200 ms iyi. TBT yüksekse INP de risklidir.

## CLS (kayma) kaynakları
- Boyutu belirtilmeyen görseller/iframe → `width`/`height` veya `aspect-ratio` ver
  (audit: `unsized-images`).
- Dinamik enjekte içerik (banner, cookie notice) → yer ayır (min-height rezerve et).
- Web fontları (FOIT/FOUT) → `font-display: optional/swap`, boyut-eşleştirme
  (audit: `font-display`).
- Reklam/embed'ler için ayrılmamış alan → sabit kap boyutu.
- Geç yüklenen öğeler layout'u itiyor → `layout-shift-elements` / `layout-shifts` audit'i hangi
  elementin kaydığını (`details`) verir; o elemente yer ayır.

## CrUX veri notları (parsing tuzakları)
- **CLS p75 bir STRING'dir** (ör. `"0.05"`), sayı değil — float'a çevir.
- Histogramın son kovasında `end` yoktur (sonsuza uzanır); yoğunluklar ~1,0'a toplanır.
- **404 = veri yok** (yetersiz trafik), yetki hatası değil. Düşük trafikli sayfalarda saha
  verisi bulunmaz → lab'ı vekil kullan, "trafik artınca yeniden test" notu bırak.
- CrUX History API 25 haftalık trend verir; `"NaN"`/`null` uygunsuz dönemleri işaret eder,
  sayısal işlemden önce kontrol et.

## Plana yansıtma
Her CWV metriği için planda: **lab değeri + (varsa) saha p75 + eşiğe göre etiket** yaz. LCP zayıfsa
alt-parçalara göre kök nedeni belirt; INP zayıfsa TBT ve `long-tasks`'a bak; CLS zayıfsa
`layout-shift-elements` `details`'inden **hangi elementin** kaydığını somut yaz.
