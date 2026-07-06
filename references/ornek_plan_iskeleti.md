# PageSpeed Iyilestirme Plani — <URL>

**Test tarihi:** <tarih>  ·  **Strateji:** Mobil + Masaustu  ·  **Motor:** Lighthouse <surum>

## 1. Ozet skorlar
| Kategori | Mobil | Masaustu |
|---|---|---|
| Performans | 62 | 88 |
| Erisilebilirlik | 88 | 90 |
| En Iyi Uygulamalar | 92 | 100 |
| SEO | 83 | 83 |

## 2. Core Web Vitals
| Metrik | Lab | Saha (CrUX) | Durum |
|---|---|---|---|
| LCP | 3,2 sn | 2,8 sn | Gelistirilmeli |
| INP / TBT | 620 ms (TBT) | 240 ms (INP) | Gelistirilmeli |
| CLS | 0,02 | 0,05 | Iyi |

## 3. Oncelikli aksiyonlar (etki x efor)
| # | Aksiyon | Etki | Efor | Tahmini kazanc | Denetim |
|---|---|---|---|---|---|
| 1 | Isleme engelleyen CSS/JS'i ertele/inline kritik CSS | Yuksek | Orta | ~1,1 sn | render-blocking-resources |
| 2 | Kullanilmayan JavaScript'i bol/kaldir | Yuksek | Orta | ~0,75 sn | unused-javascript |
| 3 | Resimleri WebP/AVIF olarak sun + boyutlandir | Orta | Dusuk | ~0,4 sn | uses-optimized-images |

## 4. Kategori bazli bulgular
### Performans
- ...
### SEO
- Meta aciklamasi ekle (meta-description)
### Erisilebilirlik
- Resimlere alt metni ekle (image-alt); renk kontrastini WCAG AA'ya cikar
### En Iyi Uygulamalar
- ...

## 5. Sonraki adimlar
- Degisiklikler sonrasi ayni URL'yi yeniden test et; mobil skoru onceliklendir.
