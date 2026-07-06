# Yapılandırılmış Veri (Schema) + Erişilebilirlik — Derin Referans

PSI'nin **erişilebilirlik** denetimlerini derinleştirmek ve şema (JSON-LD) önerileri üretmek için
yerleşik referans. `claude-seo` olmadan da planın erişilebilirlik + schema bölümü bu dosyayla dolar.

> Kaynak/atıf: `claude-seo` v2.2.0 (AgriciDaniel, MIT) `seo-schema` + `seo-technical` (agent-friendly
> pages) materyalinden türetilmiştir. Bkz. `../NOTICE.md`.

---

## Bölüm A — Yapılandırılmış Veri (Schema.org / JSON-LD)

### Tespit ve doğrulama
1. Sayfa kaynağında `<script type="application/ld+json">` (JSON-LD — Google'ın tercihi), Microdata
   (`itemscope`/`itemprop`), RDFa (`typeof`/`property`) ara.
2. Tip başına zorunlu alanları ve Google'ın desteklediği rich result tiplerini doğrula.
3. Yaygın hatalar: eksik `@context`, geçersiz `@type`, yanlış veri tipi, placeholder metin, göreli
   URL (mutlak olmalı), geçersiz tarih biçimi.
4. **JS ile enjekte edilen JSON-LD gecikmeli işlenir** (Aralık 2025 rehberi) → zaman-duyarlı markup'ı
   (özellikle Product/Offer) sunucu-render HTML'e koy.

### Tip durumu (Mayıs 2026 itibarıyla)
**AKTİF (serbestçe öner):** Organization, LocalBusiness, SoftwareApplication, WebApplication,
Product (Nisan 2025'ten Certification markup), ProductGroup, Offer, Service, Article, BlogPosting,
NewsArticle, Review, AggregateRating, BreadcrumbList, WebSite, WebPage, Person, ProfilePage,
ContactPage, VideoObject, ImageObject, Event, JobPosting, Course, DiscussionForumPosting.

**RICH RESULT YOK ama AI için tut:** FAQPage — Google 7 Mayıs 2026'da FAQ rich result'ı TÜM siteler
için kaldırdı; SERP özelliği yok ama AI Mode/AI Overviews varlık çözümlemesine yardım eder → Info
düzeyinde işaretle. Gerçek soru-cevap sayfaları için **QAPage**.

**KULLANIMDAN KALKMIŞ (asla önerme):** HowTo (Eyl 2023), SpecialAnnouncement (Tem 2025),
CourseInfo/EstimatedSalary/LearningVideo (Haz 2025), ClaimReview (Haz 2025), VehicleListing (Haz 2025),
Practice Problem (2025 sonu), Dataset (2025 sonu).

### Hazır JSON-LD şablonları
**Organization:**
```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "[Şirket]", "url": "[URL]", "logo": "[Logo URL]",
  "contactPoint": {"@type": "ContactPoint", "telephone": "[Telefon]", "contactType": "customer service"},
  "sameAs": ["[Facebook]", "[LinkedIn]", "[Twitter]"]
}
```
**Article/BlogPosting:**
```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "[Başlık]",
  "author": {"@type": "Person", "name": "[Yazar]"},
  "datePublished": "[YYYY-MM-DD]", "dateModified": "[YYYY-MM-DD]",
  "image": "[Görsel URL]",
  "publisher": {"@type": "Organization", "name": "[Yayıncı]",
    "logo": {"@type": "ImageObject", "url": "[Logo URL]"}}
}
```
LocalBusiness için ad/adres/telefon/openingHours/geo alanlarını doldur. Yalnızca doğrulanabilir
gerçek veri kullan; kullanıcı doldursun diye placeholder'ları açıkça işaretle.

---

## Bölüm B — Erişilebilirlik (WCAG / Lighthouse a11y)

PSI erişilebilirlik denetimleri gruplu gelir; her grubun PSI `details`'i **hangi elementin** başarısız
olduğunu verir — planda o elementi ve değeri **somut** yaz.

| PSI grubu / denetim | Ne kontrol eder | Plana somut yazım |
|---|---|---|
| `color-contrast` (Kontrast) | Metin/arka plan kontrast oranı (WCAG AA: normal 4.5:1, büyük 3:1) | "`selector` kontrastı X:1 → hedef 4.5:1" |
| `target-size` / `tap-targets` (Dokunma) | Dokunma hedefi ≥ 48×48 px, 8 px boşluk | "`selector` 24×24 → en az 48×48" |
| `image-alt` (Adlar/etiketler) | `<img>` `alt` metni | "`selector` görseline anlamlı alt ekle" |
| `link-name` | Bağlantının ayırt edilebilir adı | "`selector` bağlantısına metin/aria-label ver" |
| `button-name` | Butonun erişilebilir adı | "`selector` butonuna aria-label ver" |
| `heading-order` (Gezinme) | Başlıklar sırayla (h1→h2→…) | "`selector` başlık düzeyini düzelt" |
| `label` / `form-field-multiple-labels` | Form girdisi `<label for>` ilişkisi | "`selector` girdisine label bağla" |
| `aria-*` | ARIA rol/özellik geçerliliği | ilgili elementte ARIA'yı düzelt |
| `document-title`, `html-has-lang` | Sayfa başlığı, `<html lang>` | ekle/düzelt |

### Kontrast düzeltirken (kritik)
PSI/Lighthouse **hangi renk** olduğunu `details` node'uyla verir ama **opaklık/rgba harmanını**
hesaba katmadan körlemesine tema değiştirme. Yarı saydam renkler (ör. `red-600/40`) zemine
harmanlanır → gerçek kontrastı hesapla (chrome-devtools `evaluate_script` ile DOM'u gez veya axe).
Düzeltme sonrası aynı taramayı tekrarla → 0 ihlal teyidi.

### Agent-friendly (ileriye dönük, fırsat olarak)
AI ajanları siteyi erişilebilirlik ağacından okur (en temiz sinyal). Semantik HTML (gerçek
`<button>`/`<a>`, `<div onclick>` değil), `<label for>` ilişkileri, yeterli hedef boyutu, şablonlar
arası layout kararlılığı, doğru `cursor: pointer` → bunları **fırsat** olarak sun, sub-100 skoru
kapı olarak kullanma.
