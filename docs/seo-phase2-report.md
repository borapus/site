# Faz 2 — Teknik SEO

## Sonuç ve kapsam

Onaylanan Faz 2, projenin mevcut Astro 7.0.6 yapısıyla uygulandı. `seo-platform` dalındadır; GitHub'a gönderilmedi, main ile birleştirilmedi ve canlı siteye yayınlanmadı. Faz 3 başlatılmadı.

14 projenin iki dilde toplam 28 detay sayfası artık derleme sırasında gerçek açıklama ve görsellerle oluşturuluyor. Örnek yeni adres: `/tr/projects/hisaronu-house/`. Ana sayfa, projeler, stüdyo ve iletişimle birlikte sitemap'te 36 indekslenebilir içerik sayfası var.

## Uygulananlar

- Her içerik sayfasında benzersiz title ve description, dolu tek H1, küçük harfli ve sonu eğik çizgili canonical bulunuyor. Parametreler canonical'a taşınmıyor.
- EN/TR/x-default hreflang, Open Graph ve Twitter kartları gerçek proje/stüdyo görselleriyle oluşturuluyor. Mevcut favicon ve site kimliği korundu.
- `robots.txt` ve `sitemap.xml` gerçek yayınlanmış proje verilerinden derleniyor. Eski detay, 404, admin, API, taslak ve önizleme adresleri sitemap'e alınmıyor.
- Organization, WebSite ve WebPage; proje sayfalarında BreadcrumbList, CreativeWork ve ImageObject verileri eklendi. Adres, puan veya yorum uydurulmadı.
- Yeni proje detayları JavaScript olmadan okunabilir. Proje kartlarının gereksiz istemci veri yüklemesi kaldırıldı; animasyon kodu yüklenmediğinde metinler görünür kalıyor.
- 129 kaynak görsel için 353 WebP varyantı ve otomatik manifest oluşturuldu. `srcset`, `sizes`, width/height, alt, ekran altı lazy loading ve ana görselde yüksek öncelik uygulanıyor. Orijinal dosyalar korunuyor.
- WebP varyantlarının tamamı yaklaşık 51,7 MiB; kaynak görsel seti yaklaşık 320,7 MiB. Bu toplam dosya karşılaştırmasıdır; tek sayfanın indirme miktarı veya Lighthouse ölçümü değildir.
- Eski `projects/detail/?id=...` adresleri noindex uyumluluk sayfasında yeni adrese JavaScript ile geçiyor. Geçersiz kimlikler bulunmayan adrese giderek 404 alıyor. JavaScript kapalıysa proje listesine bağlantı gösteriliyor.
- Özel 404 çıktısı eklendi. Kök dil seçimi sayfasının mevcut `noindex` değeri değiştirilmedi; esas EN/TR ana sayfalar indekslenebilir.
- `VERCEL_ENV=preview/development` veya `SEO_NOINDEX=true/1` ile oluşturulan çıktıda noindex/nofollow, engelleyici robots ve boş sitemap var. Admin/API/draft/preview yollarında ortak layout noindex uyguluyor. Bu kurallar erişim kontrolü yerine geçmez; mevcut projede bu özel sayfalar yoktur.

## Değişen dosyalar

- `package.json`: bağımlılıksız `test:seo` komutu.
- `src/layouts/BaseLayout.astro`: ortak metadata, canonical, hreflang, sosyal kartlar, JSON-LD ve noindex kuralları.
- `src/components/Hero.astro`, `src/components/pages/StudioPage.astro`, `src/components/gallery/ProjectGrid.astro`: duyarlı görseller ve yeni proje bağlantıları.
- `src/components/nav/LocaleSwitch.astro`, `src/i18n/ui.ts`: tutarlı dil bağlantıları.
- `src/components/pages/ProjectDetailPage.astro`: eski bağlantılar için uyumluluk sayfası.
- `src/scripts/site.ts`, `src/styles/global.css`: istemci yükünü ve görünmez içerik riskini azaltma.

## Oluşturulan dosyalar

- `src/lib/seo.ts`, `src/lib/projectRoutes.ts`
- `src/components/pages/StaticProjectPage.astro`, `src/components/ui/SeoImage.astro`
- `src/pages/en/projects/[slug].astro`, `src/pages/tr/projects/[slug].astro`
- `src/pages/robots.txt.ts`, `src/pages/sitemap.xml.ts`, `src/pages/404.astro`
- `src/data/imageManifest.json`, `public/images/optimized/*.webp` (353 dosya)
- `scripts/prepare-seo-images.py`, `scripts/test-seo.mjs`
- Bu rapor.

## Doğrulama

- Depodaki npm kilidinin Astro 7.0.6 sürümüyle üretim derlemesi başarılı: 40 HTML sayfası (36 içerik, 2 eski detay, kök ve 404).
- Otomatik SEO testi başarılı: 36 içerik sayfası, 328 görsel etiketi; benzersiz başlık/açıklama, canonical, hreflang, JSON-LD, görsel boyutları/alt/dosyalar ve iç bağlantılar doğrulandı.
- `SEO_NOINDEX=true` önizleme çıktısının testi başarılı.
- Son değişikliklerden sonra ayrıca `VERCEL_ENV=preview` derlemesi ve aynı önizleme testi başarılı.
- Yerel Astro sunucusunda 36 sitemap adresinin tamamı HTTP 200; bulunmayan proje ve `/not-found/` HTTP 404.
- Görsel üreticisinin ikinci çalıştırmasında manifest değişmedi; 129 kayıt/353 varyant aynı kaldı.
- Lighthouse, gerçek mobil tarayıcı görünümü ve canlı Vercel yönlendirmeleri bu aşamada doğrulanmadı. Lighthouse ve tam tarama Faz 3 kapsamındadır; 95+ puan veya ölçülmüş sıfır CLS iddiası yoktur.

## Sınırlar ve kalan işler

Belgedeki “Never touch production data, environment secrets, or deployment config.” kuralı nedeniyle `astro.config.mjs`, Vercel/domain yönlendirme ayarları ve ortam sırları değiştirilmedi. Dolayısıyla www/apex, büyük harf, son eğik çizgi ve eski sorgulu adresler için sunucu düzeyinde **301 uygulanmadı**. Canonical ve iç bağlantılar tutarlı; uyumluluk sayfasındaki geçiş HTTP 301 değildir. Bu işler ayrıca yayın yapılandırması değişikliğine izin verilmesini gerektirir.

Astro önizlemesinde `/404/` doğrudan açıldığında özel 404 belgesi 200 ile sunulabilir; belgenin kendisi noindex'tir. Bulunmayan normal yollar 404 verir. Canlı barındırıcı davranışı yayın sonrasında ayrıca kontrol edilmelidir.

Sanity ve yerel kaynaklar derleme sırasında okunur. CMS'de veya proje dosyalarında değişiklik yapıldığında yeni detay adreslerinin ve sitemap'in güncellenmesi için yeniden derleme/yayın gerekir. Testteki mevcut 36 sayfalık kapsam beklentisi proje sayısı değişirse güncellenmelidir.

Önizleme koruması derleme zamanında uygulanır. Üretim çıktısını sonradan başka bir önizleme alan adına taşımak bu etiketleri değiştirmez; o ortamın önizleme bayrağıyla yeniden derlenmesi gerekir.

## Veri, servis ve bağımlılıklar

Veritabanı, canlı içerik, yeni servis, zamanlanmış görev veya AI yayın sistemi değişikliği yok. Yeni npm bağımlılığı yok; npm kilidi değiştirilmedi. Pillow yalnızca orijinal görseller değiştiğinde WebP varlıklarını yeniden üretmek için kullanılır; hazır varlıklar depoda olduğundan normal site derlemesinde Python/Pillow gerekmez.

## Çalıştırma

Depo dizininde mevcut Node/npm kurulumu ile:

```text
npm ci
npm run build
npm run test:seo
```

Orijinal görseller değişince (Python ve Pillow gerekir):

```text
python scripts/prepare-seo-images.py
```

PowerShell'de önizleme kontrolü:

```powershell
$env:SEO_NOINDEX = 'true'
npm run build -- --outDir ../seo-preview-dist
node scripts/test-seo.mjs ../seo-preview-dist --preview
Remove-Item Env:SEO_NOINDEX
```

SEO botu ve crawler henüz oluşturulmadı; bunların komutları Faz 3 ve sonrasında verilecek. Onaylı içerik yayınlama komutu henüz yok; bu aşama canlı yayına çıkmadı.

Belgedeki aşama kuralına göre sonraki çalışma için kullanıcı onayı beklenir.
