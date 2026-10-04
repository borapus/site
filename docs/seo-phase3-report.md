# Faz 3 — Tarayıcı ve SEO fırsat veritabanı

## Sonuç

Yerel Astro üretim çıktısı önce tarandı, ölçümlerde bulunan sorunlar düzeltildi, ardından yeniden taranıp ölçüldü. `seo-platform` dalında çalışıldı; canlı veri, ortam sırları, yayın ayarları ve npm bağımlılık kilidi değiştirilmedi. GitHub'a gönderim veya canlı yayın yapılmadı; Faz 4 başlatılmadı.

Son tarama: **37 sayfa, 36 indekslenebilir içerik sayfası, 36 sitemap adresi, 370 görsel varyantı**. Kırık iç bağlantı, eksik canonical, yinelenen başlık/açıklama, önemli bağlantısız sayfa veya geçersiz sitemap girdisi bulunmadı. HIGH görev yok; Türkçe ana sayfanın mobil performansı için bir MEDIUM görev var.

## Tarayıcı ve veritabanı

`scripts/crawl-seo.py`, Python'un standart kütüphanesini kullanır; ilave Python paketi veya servis gerektirmez. Sitemap ve dil ana sayfalarından başlayıp aynı siteye ait bağlantıları izler. Üretim canonical adreslerini yerel sunucuya eşler; harici alan adlarını ziyaret etmez, formları göndermez, arama/tıklama üretmez ve sayfa JavaScript'ini çalıştırmaz. Render/performance ölçümü ayrı Lighthouse adımıdır.

Kontroller: HTTP durumu, yönlendirme zinciri/döngüsü, title/description, H1/H2 ve başlık sırası, canonical, meta/X-Robots-Tag ve robots.txt, iç bağlantılar, görsel src/srcset dosyaları ve alt/boyutlar, yinelenen başlık/açıklama/ana metin, sitemap kapsamı, indekslenebilirlik, JSON-LD, gelen/giden bağlantılar ve sayfa derinliği. Derinlik EN/TR ana sayfalarından hesaplanır. JavaScript içindeki veya erişilemeyen özel yollar otomatik keşfedilmez; dış bağlantıların erişilebilirliği bu taramanın kapsamı değildir.

Veritabanı: `.seo/opportunities.sqlite`.

- `pages`: URL, sayfa türü, ana konu, tahmini arama niyeti, başlık/meta/içerik kalitesi, gelen/giden bağlantı sayısı, indekslenebilirlik, schema, performans ölçümleri, denetim tarihi, sağlık puanı ve ayrıntılı JSON.
- `tasks`: sabit URL+kontrol kimliğiyle HIGH/MEDIUM/LOW görevler.
- `audit_state`: siteye ait son denetim özeti.

URL ve görev kimlikleri benzersizdir. Her çalıştırma yalnızca ilgili sitenin yerel denetim görüntüsünü atomik olarak yeniler; geçmiş çalıştırmalar aynı sayfaları çoğaltmaz. Son iki taramada **37 sayfa, 1 görev, 1 denetim özeti** kaldığı ayrıca kontrol edildi. Canlı/CMS veritabanına bağlantı veya yazma yoktur. Veritabanı ve ham raporlar `.gitignore` ile sürüm kontrolü dışında tutulur; paylaşılabilir sonuç özeti `docs/seo-phase3-evidence.json` içindedir.

Konu/niyet ve içerik yeterliliği gerçek sayfa metninden basit kurallarla çıkarılan denetim önerileridir; anahtar kelime araştırması değildir. Kelime sayısı sıralama faktörü olarak sunulmaz. Sağlık puanı yerel kontrol puanıdır: 100 üzerinden HIGH başına 20, MEDIUM başına 8, LOW başına 2 çıkarılır; Google sıralaması veya Lighthouse puanı değildir. Tarih, denetim tarihidir; içerik güncelleme tarihi uydurulmaz.

## Bulunan ve düzeltilen sorunlar

- Alt bilgi logosu 436.229 baytlık 12.750 piksel genişliğinde kaynaktan gösteriliyordu. Şeffaflığı korunarak 340/680 piksel WebP sürümleri üretildi; 680 piksel dosya 9.720 bayt. Orijinal korunuyor.
- İlk görünür metne uygulanan giriş animasyonu LCP'yi geciktiriyordu. İlk ekranda zaten görünen içerik gizlenmiyor; ekran altındaki animasyonlar korunuyor.
- Projeler listesindeki ilk fotoğraf lazy yükleniyordu. İlk karta eager/high öncelik verildi; diğerleri lazy kaldı.
- Kapaklar için 960 piksel varyant ve mobil kartlara uygun `sizes` eklendi. Büyük galeri görselleri korunuyor.
- Lighthouse yerleşim kaymalarında web fontlarını işaret etti. Kullanılan üç temel Latin fontu için preload eklendi.
- Tarayıcı testlerinde Windows'ta SQLite dosyasının açık kalması bulundu. Bağlantıların işlem sonrasında kapanması düzeltildi.

## Mobil Lighthouse sonuçları

Lighthouse **13.5.0**, kurulu Chrome, yerel üretim çıktısı ve varsayılan mobil/simüle ağ ayarları kullanıldı. Yedi sayfa iki dil ve beş sayfa şablonunu örnekler; 36 sayfanın tamamına Lighthouse uygulanmış olduğu iddia edilmez. Bunlar birer laboratuvar çalıştırmasıdır; canlı Core Web Vitals, gerçek cihaz garantisi veya tekrarlı ölçüm ortalaması değildir.

| Sayfa | Performans | SEO | LCP | CLS |
| --- | ---: | ---: | ---: | ---: |
| `/en/` | 93 | 100 | 3,17 sn | 0 |
| `/tr/` | 88 | 100 | 3,62 sn | 0 |
| `/en/projects/` | 95 | 100 | 2,97 sn | 0 |
| `/en/projects/hisaronu-house/` | 94 | 100 | 3,10 sn | 0 |
| `/tr/projects/hisaronu-house/` | 94 | 100 | 2,95 sn | 0 |
| `/en/studio/` | 99 | 100 | 1,83 sn | 0 |
| `/en/contact/` | 99 | 100 | 1,97 sn | 0 |

İlk EN ana sayfa ölçümü 80 performans / 4,99 sn LCP idi; son ölçüm 93 / 3,17 sn. Öncelik düzeltmesinden önce projeler listesi 75 / 7,68 sn idi; son ölçüm 95 / 2,97 sn. Son yedi çalıştırmada CLS sıfır ölçüldü; her ortamda sıfır kayma garantisi verilmez.

Ham JSON dosyaları `.seo/lighthouse/` içindedir; ilk karşılaştırma raporları `.seo/lighthouse-before/` altında saklanır. Ölçümler crawler tarafından SQLite'a alınır. Araç kurulumu ve headless CLI kullanımında [Lighthouse'un resmi belgeleri](https://github.com/GoogleChrome/lighthouse) esas alındı.

## Kalan işler

- **MEDIUM:** Türkçe ana sayfa performansı 88; LCP hâlâ 3,62 sn. Yeni ağır dosya/animasyon eklemeden, gerçek cihaz ve canlı yayın ölçümleriyle takip edilmeli. Bu görev veritabanında açık kaldı.
- Yerel Astro sunucusunda Vercel Speed Insights'ın `/_vercel/speed-insights/script.js` yolu 404 verir. Lighthouse bunu Best Practices altında bildirir; analitik entegrasyonu kaldırılmadı. Canlı Vercel davranışı ayrıca doğrulanmalıdır.
- www/apex, büyük harf, eğik çizgi ve eski sorgulu adreslerin gerçek HTTP 301 kuralları Faz 2 raporundaki yayın yapılandırması sınırı nedeniyle uygulanmış değildir.
- Crawler ham HTML denetler. İstemci etkileşimlerinin tamamı, özel/auth sayfaları, dış bağlantılar ve tüm 28 detayın ayrı Lighthouse ölçümleri kapsam dışıdır.
- AI üretimi, bağlantı öneri motoru, yayın botu, dashboard veya zamanlanmış işler henüz yoktur; sonraki aşamalara ait işler başlatılmadı.

## Testler

- Astro 7.0.6 üretim ve `VERCEL_ENV=preview` derlemeleri başarılı.
- 36 sayfanın üretim ve önizleme SEO testleri başarılı; ilk kart yükleme önceliği ve font preload dosyaları da doğrulanıyor.
- Üç crawler regresyon testi başarılı: bozuk bağlantı/görsel, orphan, duplicate, robots/noindex, yönlendirme, schema, idempotent SQLite ve Lighthouse ölçüm içe aktarma.
- İkinci görsel üretiminde manifest aynı kaldı: 130 kaynak / 370 aktif varyant.
- Son tarama iki kez çalıştı; veri kayıtları çoğalmadı ve HIGH görev kontrolü geçti.

## Dosyalar ve bağımlılıklar

Oluşturulanlar: `scripts/crawl-seo.py`, `scripts/audit-lighthouse.mjs`, `scripts/tests/test_crawler.py`, bu rapor, `docs/seo-phase3-evidence.json` ve 20 yeni WebP dosyası.

Değişenler: `.gitignore`, `package.json`, `scripts/prepare-seo-images.py`, `scripts/test-seo.mjs`, `src/data/imageManifest.json`, `src/layouts/BaseLayout.astro`, `src/scripts/site.ts`, `src/components/Footer.astro`, `src/components/ui/SeoImage.astro`, `src/components/gallery/ProjectGrid.astro`, `src/components/pages/ProjectsPage.astro`.

Yeni bağımlılık: **Lighthouse 13.5.0**, yalnızca isteğe bağlı yerel mobil performans/SEO denetimi için `../seo-tools` dizinine kuruldu; sitenin npm bağımlılıkları değiştirilmedi. Python crawler ve SQLite standart kütüphanededir. Yeni servis ve zamanlanmış iş yoktur. Pillow önceki aşamanın görsel üreticisinde kullanılır.

## Çalıştırma komutları

Site deposunda, Node/npm ve Python kuruluyken:

```text
npm run build
npm run test:seo
npm run test:crawler
npm run preview -- --host 127.0.0.1 --port 4322
```

Ayrı terminalde yerel tarama:

```text
npm run seo:crawl -- --base http://127.0.0.1:4322 --fail-on-high
```

İsteğe bağlı Lighthouse kurulumu ve ölçümü (kurulu Chrome gerekir):

```text
npm install --prefix ../seo-tools --no-save lighthouse@13.5.0
npm run seo:lighthouse -- --base=http://127.0.0.1:4322
npm run seo:crawl -- --base http://127.0.0.1:4322 --performance-dir .seo/lighthouse --fail-on-high
```

Chrome otomatik bulunmazsa runner'a `--chrome="C:\Program Files\Google\Chrome\Application\chrome.exe"` verilebilir. `--paths=/en/,/tr/` ile ölçüm kapsamı, `--output=...` ile Lighthouse klasörü seçilebilir. Crawler'da `--db`, `--output`, `--max-pages`, `--timeout` ve `--probe` seçenekleri vardır. Varsayılan çıktılar `.seo/crawl.json` ve `.seo/opportunities.sqlite` dosyalarıdır.

Bu komutlar sadece denetim yapar. Onaylı AI içerik yayın komutu henüz yoktur; GitHub/main/Vercel yayın işlemi bu aşamada yapılmadı. Belgedeki “After each phase ... STOP for my approval” kuralına göre Faz 4 için onay beklenir.
