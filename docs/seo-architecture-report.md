# PUS&CO — SEO mimarisi denetimi, Aşama 1

Tarih: 5 Ekim 2026 (Europe/Istanbul). Dal: `seo-platform`.
İncelenen başlangıç commit'i: `0967898c2e5b3db739607b7da2905935d75e5921`.

Bu aşama yalnızca denetimdir. Uygulama kodu, üretim içeriği, ortam değişkenleri ve yayın yapılandırması değiştirilmedi. Kod incelemesine ek olarak 20 canlı URL salt okunur HTTP istekleriyle kontrol edildi. Lighthouse, tam bağlantı taraması, Search Console veya tarayıcı tabanlı performans testi bu aşamada çalıştırılmadı; bunlara ait skor veya başarı iddiası yoktur.

## 1. Gerçek teknoloji ve sürümler

- Proje **Next.js değil, Astro** kullanıyor. App Router / Pages Router, Next Metadata API, `generateMetadata`, `next/image`, `app/robots.ts` ve `app/sitemap.ts` mevcut değil.
- `package.json`: Astro `^7.0.6`; depodaki `package-lock.json` çözümü **7.0.6**. Önceki yerel önizleme kurulumunun farklı sürüm çözebilmesi nedeniyle bundan sonraki doğrulama depodaki kilit dosyasını esas almalıdır. Üretimde kullanılan kesin paket sürümü yayın loglarına erişmeden doğrulanamaz.
- Astro yapılandırmasında SSR adaptörü veya `output: 'server'` yok; varsayılan statik çıktı kullanılıyor. Son yerel derleme 11 HTML rotası üretmişti.
- Tailwind CSS, GSAP, ScrollTrigger ve Lenis; Sanity istemcisi ve ayrı Sanity Studio; Vercel Speed Insights; yerel Fontsource fontları mevcut.
- Canlı yayın Vercel/GitHub üzerinden yapılıyor. README ve `.htaccess` eski cPanel/LiteSpeed yayınını da anlatıyor. `.htaccess` kuralları Vercel üzerinde işleyen kurallar olarak kabul edilemez.
- Özel SEO kütüphanesi veya sitemap entegrasyonu yok.

Sonraki aşamalardaki Next.js örnekleri **Astro'nun mevcut statik mimarisine uyarlanmalı**; bu denetim framework geçişini önermiyor.

## 2. Rotalar ve render biçimi

| Rota | Render / içerik durumu |
| --- | --- |
| `/` | Statik boş gövde; JavaScript ve meta refresh ile dil yönlendirmesi |
| `/en/`, `/tr/` | Statik ana metin, H1, seçili proje kartları; tarayıcıda canlı proje listesi yenilemesi |
| `/en/projects/`, `/tr/projects/` | Statik 14 kart; tarayıcıda Sanity + yerel verilerle yenileme |
| `/en/studio/`, `/tr/studio/` | Statik stüdyo metni, H1 ve görsel |
| `/en/contact/`, `/tr/contact/` | Statik metin ve form; gönderim tarayıcıdan Web3Forms'a |
| `/en/projects/detail/?id=<slug>`, `/tr/projects/detail/?id=<slug>` | Statik ortak kabuk; proje H1, açıklama, künye ve galeri yalnızca tarayıcı JavaScript'iyle |

14 mantıksal proje, iki dilde 28 detay URL'si oluşturuyor; bunların her biri için ayrı HTML dosyası yok. Yerel başlangıç verisi ve uzaktaki CMS içeriği birlikte değerlendirilirse 8 ana içerik sayfası + 28 proje detayı = 36 mantıksal içerik URL'si vardır. Kök yönlendirme ve kimliksiz detay kabukları bunlara eklenmemelidir.

`ProjectDetailPage.astro` boş H1 (`&nbsp;`), boş açıklama ve boş görsel alanları oluşturuyor. `projectDetail.ts` sorgu parametresindeki `id` ile içeriği çekiyor ve yalnızca `document.title` değiştiriyor. İlk HTML'deki description, OG ve hreflang proje bazında güncellenmiyor.

Canlı TK House örnekleri:

- İngilizce ilk HTML: `Project — PUS&CO`, boş H1, description yok.
- Türkçe ilk HTML: `Proje — PUS&CO`, boş H1, description yok.
- İki dilde de geçersiz `id=does-not-exist` **200** ve aynı kabuğu döndürüyor. Tarayıcıda gösterilen bulunamadı mesajı gerçek HTTP 404 yerine geçmez.

## 3. İçerik kaynakları ve backend

- `src/data/uploadedProjects.ts`: kullanıcı dosyalarından alınmış 12 çift dilli proje, 125 kapak/galeri görseli.
- `src/data/projects.ts`: güncellenmiş projelerle birleşen başlangıç verisi; GU House ve UÇ House dahil toplam 14 yerel proje. Slug üzerinden yinelenen kayıtlar eleniyor.
- `src/lib/projects.ts`: Sanity ve yerel kaynakları birleştiriyor; güncellenmiş yerel slug'lar CMS içeriğine göre öncelikli. Bağlantı hatasında yerel veriye dönüş var.
- `src/lib/sanity.ts`: public proje kimliğiyle Sanity `production` dataset'i, `published` perspektifi ve CDN. Proje detayları, liste ve gezinme için GROQ sorguları var.
- `sanity/`: ayrı Studio uygulaması, proje/stüdyo/ayar şemaları. Ana sitenin altında bir `/admin` rotası tanımlı değil. Studio'nun canlı hostu ve erişim izinleri bu depodan doğrulanamaz.
- Veritabanı, SQLite, SEO fırsat deposu veya içerik onay pipeline'ı yok. SEO botu / crawler / AI yayın işi yok.
- İletişim formu Web3Forms'a doğrudan gönderiyor; ana sitede sunucu API endpoint'i yok. Gösterilen adres `info@pusnco.com`. Form anahtarına bağlı gerçek alıcı bu incelemeyle doğrulanamaz.

## 4. İndeksleme ve noindex

**Bulunan kaynak:** `src/pages/index.astro` içindeki sabit `<meta name="robots" content="noindex" />`.

- Canlı `/` için HTTP 200 ve `noindex` doğrulandı. Bu sayfa yalnızca dil yönlendirmesi yapıyor; içerik sayfası değil.
- Kontrol edilen `/en/`, `/tr/`, proje, stüdyo ve iletişim sayfalarında meta noindex veya `X-Robots-Tag` görülmedi.
- Kaynakta global noindex, middleware, preview/staging ortam flag'i veya indekslemeyi kontrol eden bir yayın yapılandırması bulunmadı.
- Vercel hesap/preview platformu seviyesindeki indeksleme davranışı bu depodan doğrulanamaz. Üretim/preview ayrımının kesin testi sonraki aşamada gereklidir.

**Onay sorusu:** Kök `/` sayfasındaki mevcut noindex bilinçli mi? Öneri: yalnızca dil yönlendiren kökte noindex korunabilir; gerçek içerik taşıyan `/en/` ve `/tr/` indekslenebilir kalmalı. Onay gelmeden noindex değiştirilmemeli.

## 5. Metadata ve site kimliği

`src/layouts/BaseLayout.astro` ortak head kaynağıdır.

| Alan | Durum |
| --- | --- |
| Title | Ana içerik sayfalarında dil bazında farklı; proje detaylarında ortak başlangıç başlığı |
| Description | Ana içerik sayfalarında var; Projects için yalnızca “Selected Works / Seçili İşler”, Studio için “The Practice / Ofis”; detaylarda yok |
| Canonical | Kaynakta ve canlı örneklerin tamamında yok |
| Open Graph | `og:title`, isteğe bağlı `og:description`, `og:type=website`; `og:image`, `og:url`, site/locale bilgisi yok |
| Twitter/X | Yok |
| Favicon | `/favicon.svg` var |
| HTML lang | EN/TR doğru tanımlanıyor |
| JSON-LD | Yok |

Başlıklar ana sayfa tipleri için var, fakat proje detaylarının ilk HTML başlıkları tekrar ediyor. Projeye özgü açıklama, paylaşım görseli ve server-render edilmiş metadata gereklidir.

## 6. Dil, hreflang ve URL tutarlılığı

- Astro i18n: `en`, `tr`; varsayılan İngilizce; her iki dilde açık önek.
- BaseLayout: `en`, `tr`, `x-default` alternatifleri üretir; origin `https://pusnco.com`.
- Detay sayfasının hreflang URL'leri `id` içermiyor; gerçek proje yerine ortak detay kabuğuna işaret eder.
- Tarayıcıdaki dil düğmeleri `site.ts` ile sorgu ve hash koruyor. Bu kullanıcı gezinmesini düzeltir, head içindeki hreflang sorununu çözmez.
- Canlı `/en/projects` ve `/en/projects/` ayrı ayrı **200**, yönlendirme yok.
- Canlı `https://www.pusnco.com/en/` ve apex sürümü ayrı ayrı **200**. Canonical da olmadığından host ve slash alternatifleri için tercih açık değil.
- Büyük harfli `/EN/PROJECTS/` **404**; küçük harfe normalize edilmiyor. Bu tek başına 301 zorunluluğu değildir, tutarlı URL üretimi ve gerçek gelen bağlantı ihtiyacına göre değerlendirilmelidir.
- Genel kök yönlendirme HTTP 301/302 değil; HTML/JS ile yapılır. `.htaccess` HTTPS kuralı canlı Vercel davranışının kanıtı değildir.

## 7. Sitemap, robots ve 404

Canlı kontroller:

| Adres | HTTP |
| --- | --- |
| `/robots.txt` | 404 |
| `/sitemap.xml` | 404 |
| `/sitemap-index.xml` | 404 |
| `/seo-audit-nonexistent-page/` | 404 |
| Geçersiz proje kimliğiyle detay URL'si | 200 |

Robots dosyasının olmaması kendi başına tüm siteyi engellemez; ancak sitemap keşfi ve açık crawler kuralları yoktur. Özel 404 sayfası bulunmadı. Proje bazlı gerçek 404 ve mantıksal detay URL'lerinin sitemap'te temsil edilmesi önceliklidir. Küçük site için sitemap index'i veya karmaşık altyapı gerekmez.

## 8. Görseller, mobil yapı ve performans riskleri

- Plain `<img>` ve CSS arka planı kullanılıyor; Astro optimize edilmiş Image/Picture bileşeni veya responsive `srcset` yok.
- Liste görsellerinde alt metni proje adı; lazy loading var, width/height yok. Canlı proje listesinde 14 kapak için boyut attribute'ları eksik. CSS media oranları kısmen yer ayırıyor; ölçüm yapılmadan CLS var/yok iddiası kurulamaz.
- Dinamik detay kapak/galerileri width/height olmadan oluşturuluyor; galeri alt metni proje adı + sıra numarası. Görsele özgü açıklamalar yok.
- Hero CSS background; dekoratif olarak aria-hidden. HTML image boyutlandırması/fetchpriority veya preload yok. LCP etkisi ölçülmeli.
- Footer logo ve stüdyo görseli boyutlandırılmış; stüdyo görseli 1122×1402, lazy ve async decode kullanıyor.
- Güncel 125 proje varlığının toplamı yaklaşık **320,7 MiB**; bu tek sayfa transfer boyutu değildir. Büyük PNG/JPEG'ler responsive/WebP/AVIF türevleriyle azaltılmalı. Aynı projelerin artık kullanılmayan eski JPG'leri de public dizininde kalmış; yalnızca doğrulanmış kullanım analiziyle temizlenmeli.
- Fontsource ile yerel fontlar var; BaseLayout iki font ailesinden toplam altı weight stylesheet'i import ediyor. Gerçek indirilen altküme/weight sayısı ve font-display davranışı performans testinde ölçülmeli.
- GSAP/ScrollTrigger ve Lenis tüm içerik sayfalarında yükleniyor. Kartlar tarayıcıda yeniden oluşturuluyor; statik içerik korunmuş olsa da bu işin gerekliliği ve JS maliyeti incelenmeli.
- `.js [data-reveal]` gizleme davranışı animasyon script'i çalışmazsa bazı metinleri görünmez bırakabilir. Kullanıcı erişilebilirliği için hata durumunda görünürlük garantisi gerekir.
- Responsive kırılımlar mevcut. Lighthouse/CWV skorları bu aşamada ölçülmedi; “95+”, CLS=0 veya tüm cihazlarda başarı sözü verilmez.

## 9. İç bağlantılar, sayfalama ve semantik

- Her sayfada ana menü: ana sayfa, projeler, stüdyo ve iletişim; logo ana sayfaya dönüyor.
- Ana sayfada seçili işler, tüm projeler ve iletişim CTA'ları; projeler sayfasında 14 statik detay bağlantısı var.
- Detaylarda listeye geri dönüş ve istemciyle eklenen “sonraki proje” zinciri var. JavaScript olmadan ileri proje zinciri oluşturulmuyor.
- Ana içerik sayfaları H1 içeriyor; ana sayfa H2 bölüm başlıkları kullanıyor. Detaylarda H1 başlangıçta boş.
- Pagination yok; 14 proje için pagination eklemek şu an gerekli değil.
- Tam inbound-link/orphan analizi ve tüm linklerin HTTP denetimi henüz yapılmadı; bunlar Aşama 3 kapsamındadır. Menüdeki bağlantıları veya önceki yayın kontrollerini tam tarama sonucu olarak göstermiyoruz.
- Journal, services, guides, locations veya FAQ sayfaları yok. Bunlara ilişkin schema/content gerçek içerik olmadan üretilemez.

## 10. İndekse girmemesi gereken alanlar

- Ayrı Sanity Studio hostu: kimlik doğrulama ve noindex ayrı ortamda doğrulanmalı.
- Preview/staging hostları, taslaklar, gelecekteki SEO dashboard/admin ve API rotaları: üretimden açıkça ayrılmalı; noindex erişim kontrolünün yerine geçmez.
- Mevcut kod yalnızca Sanity published perspektifini okuyor; taslak sayfa rotaları yok.
- Web3Forms dış endpoint'i kendi alanımızın sitemap'ine dahil edilmemeli.
- `.env` değerleri veya gizli erişim bilgileri okunmadı/değiştirilmedi; bu rapor gizli değer içermez.

## 11. Sonraki aşama için uygulama yönü (henüz uygulanmadı)

1. Astro static `getStaticPaths` ile `/en/projects/<slug>/` ve `/tr/projects/<slug>/` sayfalarını gerçek içerikten üretmek; eski query URL'lerinin uyumluluğunu ve canonical geçişini planlamak.
2. Head alanlarını mevcut BaseLayout üzerinden sayfa/proje verisinden üretmek; Next.js'e geçmemek.
3. Gerçek indekslenebilir URL'lerden küçük bir sitemap ve robots üretmek; host/slash tercihini açıklaştırmak. Yayın yapılandırması dosyanın global kuralıyla korunduğundan, platform seviyesinde 301 gerekiyorsa uygulamadan önce ayrıca kapsam/onay alınmalıdır.
4. Gerçek Organization/WebSite/WebPage/Breadcrumb/CreativeWork verisi; halka açık tam adres doğrulanmadan LocalBusiness veya hayali puan/yorum eklememek.
5. Görsel türevleri, boyutlar ve performans ölçümü; yalnızca gereken küçük araçları seçmek.
6. Küçük ölçekli otomatik metadata, sitemap, gerçek 404 ve preview-indexing testleri.

## 12. Aşama kapanış raporu

- Oluşturulan dosya: `docs/seo-architecture-report.md`.
- Değiştirilen uygulama dosyası: yok.
- Veritabanı değişikliği: yok.
- Yeni bağımlılık/servis/zamanlanmış iş: yok.
- SEO iyileştirmesi uygulaması: yok; bu aşama kanıta dayalı denetimdir.
- Dal: `seo-platform`; aşama raporu bu dalda commit edilecek. Üretim dalına merge/push veya yayın yapılmayacak.
- Mevcut build komutu: kilit dosyasıyla kurulum sonrası `npm run build`.
- SEO botu / crawler / onaylı içerik yayın komutu: henüz mevcut değil; ileriki aşamalarda gerekiyorsa eklenecek.
- Kalan iş: aşağıdaki öncelikler; Aşama 2 ve noindex kararı için kullanıcı onayı beklenir.

## 13. Öncelikli sorunlar

| Öncelik | Sorun | Etki / sonraki adım |
| --- | --- | --- |
| HIGH | Proje detaylarının gerçek metni ve metadata'sı ilk HTML'de yok | 28 gerçek proje/dil sayfasını içerikli statik HTML olarak üretmek |
| HIGH | Canonical yok; www/apex ve slash alternatifleri 200 | Tek tercih ve sayfa bazlı canonical; platform 301 kapsamını ayrıca onaylamak |
| HIGH | Sitemap yok; robots adresi 404 | Gerçek indekslenebilir, 200 URL'lerden sitemap/robots üretmek |
| HIGH | Geçersiz proje kimliği 200 dönüyor | Gerçek 404 ve geçerli slug rotaları |
| HIGH | Proje title/description/hreflang verileri ortak kabuğa ait | Benzersiz proje metadata'sı ve doğru dil eşleştirmeleri |
| MEDIUM | OG görseli ve Twitter kartı yok | Gerçek kapaklarla paylaşım metadata'sı |
| MEDIUM | Yapılandırılmış veri yok | Yalnızca doğrulanmış stüdyo/proje bilgisiyle JSON-LD |
| MEDIUM | Büyük görseller, responsive türevler ve detay boyutları yok | Optimize görseller + ölçülmüş CWV/LCP/CLS kontrolü |
| MEDIUM | Preview/staging için uygulamada açık indeksleme ayrımı yok | Platform davranışını doğrulayıp uygun ortam flag'i tasarlamak |
| MEDIUM | Projects/Studio açıklamaları çok kısa | Gerçek içerikten anlamlı ve dil bazında özgün descriptions |
| MEDIUM | JS animasyonu hata halinde metni gizleyebilir | Görünürlük için güvenli başlangıç ve hata davranışı |
| LOW | Kaynakta eski hosting belgeleri ve kullanılmayan görseller var | Belge güncellemesi ve kullanım analizi sonrası temizlik |
| LOW | Üstcase URL ve slash üretimi tutarlı politika taşımıyor | Gerçek URL tercihleriyle normalize link üretimi |

**Aşama 1 burada tamamlandı. Aşama 2 onay alınmadan başlatılmayacak.**
