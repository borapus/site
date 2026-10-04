# Faz 5 — İçerik hazırlama ve insan onayı

Bu aşama yerel `seo-platform` dalında tamamlandı. GitHub'a gönderim ve canlı yayın yapılmadı. Gerçek yayın manifesti boş; dört taslak REVIEW durumunda, APPROVED/PUBLISHED içerik yok.

## Sonuç

- Mevcut proje verilerine dayalı 20 içerik fırsatı için kaynaklı brief üretildi. Anahtar kelime, amaç, konu kümesi, öncelik, mevcut/önerilen adres, durum ve güncelleme tarihi SQLite içinde tutulur. Bunlar site içeriğinden çıkarılan fikirlerdir; arama hacmi veya Search Console verisi değildir.
- Ortak yaşamda mahremiyet ve uygulama çizimleri/şantiye koordinasyonu konularında iki dilde dört özgün rehber taslağı hazırlandı. Her taslak üç gerçek projeye dayanır. Kalite kontrolü geçti: 303–372 kelime, kaynak alıntıları, özgün metadata ve proje bağlantıları.
- İnceleme metni: [seo-content-review.md](seo-content-review.md). Kaynak alıntısının bulunması, iddianın anlam bakımından doğru olduğunu kanıtlamaz; editörün tüm iddiaları doğrulaması gerekir.
- Rehber ve hizmet detay/liste şablonları, Article/Service ve Breadcrumb verileri, sitemap ve koşullu alt menü bağlantıları hazırlandı. Onaylı içerik yokken yeni boş sayfa veya menü üretilmez.
- Durumlar DRAFT → REVIEW → APPROVED → PUBLISHED → ARCHIVED. Değişen metin eski onayı geçersiz kılar. Onay metnin SHA-256 özetiyle eşleşir. Hizmet kapsamı ayrıca doğrulanmalıdır; Türkçe/İngilizce çift birlikte hazırlanır. Bir çalıştırmada en fazla iki içerik hazırlanabilir. İnsan onayı kapatılamaz.
- `publish` yalnızca onaylı manifesti hazırlar; GitHub/Vercel dağıtımı yapmaz. PUBLISHED durumuna geçiş için canlı HTTPS sayfasında doğru içerik kimliği/özeti, 200 yanıtı ve indekslenebilirlik doğrulanır. Yayındaki içerik ancak kaldırıldığı doğrulandıktan sonra arşivlenebilir.

## Dosyalar ve veritabanı

Yeni: `scripts/content-pipeline.py`, `scripts/tests/test_content.py`, `seo/content-policy.json`, `seo/drafts/example-guides.json`, `src/data/editorialContent.json`, `src/lib/editorial.ts`, `src/components/pages/EditorialPage.astro`, `EditorialIndex.astro`, `src/pages/[lang]/[kind]/index.astro`, `[slug].astro`, bu rapor ve inceleme belgesi.

Değişen: `package.json` (komutlar), `scripts/test-seo.mjs`, `src/components/Footer.astro`, `src/pages/sitemap.xml.ts`.

Yerel SQLite'a `seo_keywords`, `content_briefs`, `content_items`, `content_events` eklendi. Üretim veritabanı değişmedi. Yeni servis, bağımlılık veya zamanlanmış görev yok. Dağıtım yapılandırması, proje kaynak verileri ve kilit dosyası değişmedi.

## Doğrulama

- 14 birim testi geçti: tarama, bağlantı önerileri, eksik onay, yayın sınırı, dil çifti, değişiklik sonrası onay iptali, yinelenen içerik, hizmet onayı, tekrarlanabilirlik ve yanlış canlı içerik reddi.
- Gerçek site derlemesi geçti; 36 indekslenebilir sayfada metadata, schema, iç bağlantılar ve sitemap kontrolü geçti (328 resim etiketi).
- `.seo/site-fixture` içindeki ayrı test kopyasında yalnızca otomatik test amacıyla dört örnek onay oluşturuldu. Rehber ve hizmet şablonları derlendi: 44 indekslenebilir sayfa, 340 resim etiketi; metadata, schema, bağlantı ve sitemap kontrolü geçti. Bu onaylar gerçek içerik veritabanına veya yayın manifestine taşınmadı.
- Yeni şablonlar için Lighthouse ölçümü yapılmadı. Faz 3'ün yedi mevcut sayfadaki SEO 100 sonuçları korunur; Türkçe ana sayfanın performans 88 konusu devam eder.

## Komutlar

Proje klasöründe, mevcut önizleme ve tarama çıktısı hazırken:

```text
npm run seo:crawl -- --base http://127.0.0.1:4322
npm run seo:content -- discover
npm run seo:content -- generate --input seo/drafts/example-guides.json
npm run seo:content -- quality
npm run seo:content -- review --output docs/seo-content-review.md
npm run test:content
npm run build
npm run test:seo
```

İnsan incelemesinden SONRA belirli taslakları onaylamak ve yayın manifestine almak için (örnek kimlikler; bu komutlar gerçek içerik üzerinde çalıştırılmadı):

```text
npm run seo:content -- approve --id guides:tr:privacy-shared-living --id guides:en:privacy-shared-living --reviewer "İnceleyen kişinin adı" --confirm-facts
npm run seo:content -- publish --id guides:tr:privacy-shared-living --id guides:en:privacy-shared-living
npm run build
npm run test:seo
```

Hizmet onayında ayrıca `--confirm-service-scope` gerekir. Dağıtım tamamlandıktan sonra `confirm-publication --id ...` canlı doğrulamayı yapar. Kaldırmak için önce iki dilde `withdraw --id ...`, dağıtım ve ardından `archive --id ...` gerekir.

## Sınırlar ve sonraki aşama

Projede mevcut LLM sağlayıcısı bulunmadı. Dört taslak Codex yardımıyla çevrimdışı hazırlandı; `generate` kaynaklı JSON taslağını içeri alır. Kendi başına model çağıran sürekli bir üretici henüz yapılandırılmadı. Yeni ücretli hizmet veya anahtar eklenmedi. Onaylayan kişinin adı yerel operatör beyanıdır; kimliği doğrulanan uzak yönetim ekranı Faz 6 kapsamındadır. Yayınlanmış metnin yerinde revizyon akışı henüz yoktur; onaylı bir yeni revizyon mekanizması ayrıca gerekir.

Gönderilen görev belgesindeki “After each phase ... STOP for my approval” kuralı nedeniyle Faz 6 başlatılmadı. Faz 6'ya devam izni, bu dört taslağın içerik onayı yerine geçmez.
