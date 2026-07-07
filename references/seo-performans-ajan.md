# Performans Teşhis Yöntemi (Yerleşik "Ajan")

`claude-seo`'nun performans ajanının teşhis yöntemi — plan yazarken izlenecek düşünce akışı.
Metrik eşikleri için `core-web-vitals-derin.md`; bu dosya **yöntem + yaygın darboğaz kataloğu**.

> Kaynak/atıf: `claude-seo` v2.2.0 (AgriciDaniel, MIT) `seo-performance` materyalinden türetilmiştir.
> Bkz. `../NOTICE.md`.

## Analiz sırası
1. PSI/CrUX saha verisi varsa **onu** esas al; yoksa lab'ı vekil kullan (404 = yetersiz trafik).
2. Performans skoru (0-100) + metrik-başına geç/kal durumunu çıkar.
3. `opportunities` (kazançlı denetimler) + `auditsByCategory.performance` (tüm tanılar/insights) +
   `thirdParties` + `largestResources`'ı birlikte oku.
4. **Kök nedene in** — özet metrikler kök nedeni gizler (bkz. SKILL.md "Derin teşhis").
5. Somut, uygulanabilir öneriler ver; **beklenen etkiye göre** önceliklendir.

## Yaygın LCP nedenleri → düzeltme
- Optimize edilmemiş hero görseli → sıkıştır, WebP/AVIF, preload.
- Render engelleyen CSS/JS → defer, async, kritik CSS.
- Yavaş TTFB (> 200 ms lab / > 800 ms saha) → edge CDN, önbellek.
- Render engelleyen üçüncü taraf scriptleri.
- Web font yükleme gecikmesi.

## Yaygın INP nedenleri → düzeltme
- Ana iş parçacığında uzun JS görevleri → < 50 ms parçalara böl.
- Ağır olay işleyicileri → debounce, `requestAnimationFrame`.
- Aşırı DOM (> 1.500 öğe).
- Üçüncü taraf scriptleri ana iş parçacığını ele geçiriyor.
- Senkron işlemler bloke ediyor.

## Yaygın CLS nedenleri → düzeltme
- `width`/`height` olmayan görseller.
- Dinamik enjekte içerik.
- Web fontları (FOIT/FOUT).
- Yer ayrılmamış reklam/embed.
- Geç yüklenen öğeler.

## Araç notları (2025-2026)
- **Lighthouse 13.0** (Ekim 2025): denetimler yeniden yapılandırıldı, skor ağırlıkları güncellendi.
  Lab teşhis aracıdır; **daima CrUX saha verisiyle doğrula.**
- **LCP alt-parçaları** (TTFB, load delay, load duration, render delay) CrUX'ta mevcut → hangi
  parçanın büyük olduğunu bul, düzeltmeyi ona göre seç (`core-web-vitals-derin.md`).
- Kota/PSI'siz teşhis (chrome GEREKMEZ): **`curl` byte/format ölçümü** kaynak ağırlığını, opsiyonel
  **`npx lighthouse`** (kuruluysa) lab tarafını PSI olmadan da verir. chrome-devtools yalnızca
  kuruluysa opsiyonel alternatiftir (SKILL.md "Derin teşhis #5").

## Çıktı (plana ne yazılır)
- Performans skoru (0-100).
- Core Web Vitals durumu (metrik-başına geç/kal).
- Tespit edilen somut darboğazlar (`largestResources`/`thirdParties`/`details` kanıtıyla).
- Beklenen etkiye göre önceliklendirilmiş öneriler.
