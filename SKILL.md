---
name: pagespeed-plan
description: >-
  pagespeed.web.dev / Google PageSpeed Insights (Lighthouse) ile bir web sitesini
  otomatik test eder ve PSI'nin gosterdigi TUM bulgulara (firsatlar, tanilar, insights,
  teknolojiye ozel oneriler) gore onceliklendirilmis, uygulanabilir bir iyilestirme
  plani (Markdown) uretir. Su durumlarda kullan: "sayfa hizi testi", "PageSpeed testi",
  "site hiz denetimi", "performans/SEO/erisilebilirlik denetimi", "Core Web Vitals",
  "Lighthouse skoru", "hiz optimizasyonu plani", "pagespeed skorlarina gore plan hazirla".
  Hem Cowork'te hem Claude Code CLI'da calisir. Ciktiyi bir .md dosyasina yazar ve
  sohbette ozetini gosterir. SEO/projeye ozel derinlik icin claude-seo skill'ine devreder.
---

# PageSpeed Insights Denetim + Plan

Bir URL'yi Google PageSpeed Insights API'siyle (Lighthouse motoru) test eder ve
**PSI sayfasinda gorunen her seyi** (firsatlar + tanilar + yeni "Insights" denetimleri +
teknolojiye ozel oneriler) onceliklendirilmis bir eylem planina cevirir.
SEO ve projeye ozel aksiyon derinligi icin `claude-seo` skill'ine devreder.

## Ne zaman kullanilir
Kullanici bir sitenin/URL'nin hizini, Core Web Vitals'ini, SEO/erisilebilirlik/best-practices
durumunu olcmek ve **ne yapilmasi gerektigine dair plan** istediginde.

## Gereksinimler
- Python 3 (yalnizca standart kutuphane; `pip install` gerekmez).
- Internet erisimi (googleapis.com'a).
- Opsiyonel `PSI_API_KEY` ortam degiskeni. Anahtarsiz da calisir ama Google dusuk
  hiz limiti uygular; medyan-of-3 birden fazla istek attigi icin anahtar onerilir.
  Ucretsiz anahtar: Google Cloud Console > "PageSpeed Insights API"'yi etkinlestir > Credentials > API key.

## Adimlar
1. Kullanicidan URL'yi al. Strateji belirtmediyse `--strategy both` (mobil + masaustu);
   mobil skor genelde onceliklidir.
2. Bu SKILL.md ile ayni dizindeki betigi calistir (varsayilan 3 kosu, medyan alinir):
   ```bash
   python3 scripts/psi_audit.py <URL> --strategy both --runs 3 --locale tr --out psi_veri.json
   ```
   Anahtar varsa: `PSI_API_KEY=... python3 scripts/psi_audit.py <URL> ...`
   Hiz limiti/kota (429) olursa: `--runs 1`, `PSI_API_KEY` ekle, ya da PSI'siz teshise gec
   (bkz. "Derin teshis" #5). `both`+`--runs 3` = 6 istek; anahtarsiz gunluk limit dusuktur.
3. Betik STDOUT'a (ve `--out` ile dosyaya) **tam kapsamli** bir ozet JSON basar:
   - `results.<strateji>.categories`: kategori skorlari (0-100) + `runs` (kosu basina ham skor).
   - `labMetrics`: FCP, LCP, TBT, CLS, SpeedIndex, TTI (medyan).
   - `fieldData` + `fieldOverall`: gercek kullanici (CrUX) verisi (varsa).
   - `labVsFieldGaps`: lab ile saha celiskileri.
   - `counts`: kategori basina toplam / duzeltilecek / gecti sayilari.
   - **`auditsByCategory`**: her kategoride PSI'de gorunen **TUM** denetimler — firsatlar,
     tanilar (cache politikasi, byte agirligi, DOM vb.) ve yeni **insights** (or. resim teslimi).
     Her denetimde: `passed`, `score`, `group`/`groupTitle`, `display`, `savingsMs`,
     `savingsBytes`, `weight`, `description` (duzeltme rehberi).
   - `opportunities`: kazanci (`savingsMs`) olan denetimler, kazanca gore sirali (oncelik icin).
   - `thirdParties`: en cok engelleyen ucuncu taraf servisler.
   - `resourceSummary`: kaynak turune gore istek + boyut.
   - `largestResources`: en agir **tekil** kaynaklar (transferSize'a gore). Tur-toplaminin
     gizledigi sisman tek dosyayi (cogu zaman logo/header ikonu) yuzeye cikarir — bunu daima gozden gecir.
   - `stackPacks`: **teknolojiye ozel oneriler** (WordPress, WooCommerce, React vb.).
   - `warnings` / `errors`: kismi/tam basarisizlik nedeni.
4. **SEO ve projeye ozel derinlik icin `claude-seo` skill'ini cagir** (asagidaki bolum).
5. Iki kaynagi birlestirip asagidaki formatta **tek bir plan** yaz. `.md` dosyasina kaydet
   (or. `<alanadi>-pagespeed-plani.md`) ve sohbette kisa ozet goster.

## TAMLIK KURALI (onemli)
Plan, PSI'de gorunen hicbir bulguyu atlamamali:
- `auditsByCategory`'deki **passed=false olan HER denetim** plana girsin — grup grup
  (or. "Firsatlar", "Tanilar", "Insights") baslikla; `counts.duzeltilecek` ile sayisi tutmali.
- Her maddede denetimin adi + `display` degeri + varsa `savingsMs` + `description`'dan
  cikan somut duzeltme yer alsin.
- `stackPacks`'teki teknolojiye ozel onerileri ilgili denetimin altina entegre et
  (or. cache icin "WordPress'te su onbellek eklentisi").
- Gecmis (passed=true) denetimler istege bagli "Gecen denetimler" altinda kisaca ozetlenebilir.
- Kullanici "ozet" isterse ilk 5-10 onceligi one cikar ama tam listeyi de plana ekle.

## claude-seo devri (derinlestirme)
Bu skill olcum + performans/teknik tarafina odaklanir. SEO icerigi ve **projeye ozel
aksiyon** derinligi `claude-seo` skill'inden gelir:
1. PSI'deki `auditsByCategory.seo` (ve varsa erisilebilirlik) bulgularini topla.
2. `claude-seo` skill'ini calistir; girdi olarak URL'yi ve bu bulgulari baglam ver.
3. Ciktisini planin **"SEO / Projeye Ozel Aksiyonlar"** bolumune entegre et (cakisanlari tekille).
4. `claude-seo` yok/erisilemezse bolumu PSI'nin ham SEO denetimleriyle doldur ve
   "derin SEO analizi icin claude-seo kurulmali" notu birak.

## Plan formati (Markdown)
1. **Ozet** – URL (gerekirse `finalUrl`/redirect notu), test tarihi, strateji(ler),
   kosu sayisi, kategori skor tablosu (mobil vs masaustu) ve `counts` ("PSI'de N bulgu, M duzeltilecek").
2. **Core Web Vitals** – LCP / INP (veya TBT) / CLS icin lab + varsa saha + etiket;
   `labVsFieldGaps` varsa vurgula.
3. **Oncelikli aksiyonlar** – Etki x Efor matrisine gore sirali tablo (ilk 5-10):
   | # | Aksiyon | Etki | Efor | Tahmini kazanc | Ilgili denetim |
4. **Tum performans bulgulari** – `auditsByCategory.performance`'in tamami, grup grup
   (Firsatlar / Tanilar / Insights). `thirdParties`, `resourceSummary` ve `largestResources`
   (en agir tekil dosyalar — gizli logo/ikon darbogazini yakalar) ile destekle.
5. **SEO / Projeye Ozel Aksiyonlar** – `claude-seo` devrinden gelen bolum.
6. **Erisilebilirlik & En Iyi Uygulamalar** – ilgili `auditsByCategory` denetimlerinin tamami.
7. **Teknolojiye ozel notlar** – `stackPacks` ozeti.
8. **Sonraki adimlar / tekrar test** – degisiklik **CANLIYA ciktiktan SONRA** (bkz. "Derin
   teshis" #4 — deploy/cache dogrulamasi) ayni URL'yi yeniden calistir.

Plani teknik ekibin dogrudan uygulayabilecegi somutlukta yaz: her maddede *ne*, *nerede*, *neden*.

## Onceliklendirme kurallari
- **Etki**: `savingsMs` (firsatlar/insights); ucuncu tarafta `blockingMs`; digerlerinde
  denetim `weight`i + skor dusuklugu. `labVsFieldGaps`'te saha kotuyse o metrigi yukari tasi.
- **Efor** (tahmini): resim sikistirma/format, alt metin, meta aciklama, kontrast, cache
  baslik ayari = **dusuk**; kullanilmayan JS/CSS, lazy-load, 3P script erteleme = **orta**;
  sunucu yaniti/TTFB, kritik CSS, mimari/render, font stratejisi = **yuksek**.
- Ilk 3-5 aksiyon "yuksek etki + dusuk/orta efor".

## Core Web Vitals esikleri (referans)
- **LCP**: <=2.5 sn iyi, <=4.0 sn gelistirilmeli, >4.0 sn zayif
- **INP**: <=200 ms iyi, <=500 ms gelistirilmeli, >500 ms zayif
- **CLS**: <=0.1 iyi, <=0.25 gelistirilmeli, >0.25 zayif
- **FCP (lab)**: <=1.8 sn iyi; **TBT (lab)**: <=200 ms iyi
- Kategori skoru: 90-100 iyi, 50-89 gelistirilmeli, 0-49 zayif

## Derin teshis ve yaygin tuzaklar (saha dersleri)
Ozet metrikler kok nedeni GIZLEYEBILIR. Skor iyilesmiyorsa veya bir metrik inatciysa:

1. **"Gorsel agir ama LCP gorseli optimize" celiskisi → tekil buyuk kaynaklara bak.**
   `resourceSummary` sadece TUR TOPLAMI verir (or. "image: 371 KB") ve tek bir sisman dosyayi
   gizler — cogu zaman **logo / header ikonu**. Once `largestResources`'a bak; supheliyse dosyayi
   `curl -s -o /dev/null -w '%{size_download}' <url>` ile OLC. Header'da eager yuklenen global
   gorseller (logo) LCP gorseliyle bant genisligi yarisir → LCP'yi tikar. Cok siklikla bir gorsel,
   optimizasyon pipeline'i (CDN `f_auto/q_auto`, `<img>` wrapper) DISINDA kalmistir.

2. **SPA'da gec-LCP.** LCP gorseli JS render + API cagrisi sonrasi indirilmeye baslarsa
   (React/Vue/SPA) `fetchpriority=high` bile gec devreye girer. Cozum: HTML'e sunucu-taraflı
   `<link rel=preload as=image>` enjekte et ya da URL'yi HTML'e inline ver. **Preload URL'si
   `<img>`'in gercekte indirdigiyle BIREBIR eslesmeli** (CDN transform + `srcset`/`sizes` dahil),
   yoksa cift indirme olur ve preload bosa gider.

3. **`color-contrast` / cogu a11y denetiminde PSI HANGI element oldugunu SOYLEMEZ.** Kesin node
   icin canliya karsi tarayici calistir: chrome-devtools `evaluate_script` ile DOM'u gezip WCAG
   kontrast hesabi yap (**opaklik/rgba blend dahil** — `red-600/40` gibi yari-saydam renkler zemine
   harmanlanir) veya axe kullan. Boylece hangi `class`/renk duzeltilecek netlesir; korlemesine
   tema degistirme. Duzeltme sonrasi ayni taramayi tekrarla → 0 ihlal teyidi.

4. **Retest'ten ONCE degisikligin CANLIDA oldugunu DOGRULA.** `autoDeploy` kapali olabilir,
   manuel deploy gerekebilir, CDN/HTML cache bayat olabilir → yoksa eski surumu olcup "degismedi"
   sanirsin. Once `curl -s <url> | grep '<beklenen-asset-veya-markup>'` ile yeni surumu teyit et,
   sonra PSI'yi tekrar calistir.

5. **PSI kota (429) yonetimi ve PSI'siz teshis.** Anahtarsiz gunluk limit dusuktur; ayni gun
   birkac tam testte dolar. Doldugunda: `PSI_API_KEY` kullan (yarin sifirlanir), `--runs 1`'e dus,
   ya da PSI'yi tamamen atla — **chrome-devtools** (network istekleri + lighthouse) ve **`curl` byte
   olcumu** lab tarafini + kaynak agirligini PSI olmadan da verir. Once/sonra dogrulamasi icin de
   PSI sart degil: ayni `curl` byte olcumunu iki surumde karsilastir.

## Notlar
- Betik yalnizca okuma yapar; siteyi degistirmez.
- `auditsByCategory` PSI'nin metrik disindaki tum gorunur denetimlerini icerir; gizli
  (grupsuz) ve "uygulanamaz/manuel" denetimler PSI'de de gosterilmedigi icin haric tutulur.
- Lab verisi her zaman doner; saha (CrUX) verisi yalnizca yeterli trafigi olan sayfalarda bulunur.
- Medyan-of-3 lab varyansini azaltir; kucuk oynamalar normaldir.
- Iki `--out` dosyasini elle karsilastirarak "onceki/sonraki" (baseline/diff) bakisi elde edebilirsin.
