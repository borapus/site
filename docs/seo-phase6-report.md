# Faz 6 — Rakip karşılaştırması, yönetim paneli ve düzenli kontroller

Bu aşama `seo-platform` dalında yerel olarak uygulanmıştır. GitHub'a gönderim, dal birleştirme, Vercel dağıtımı veya içerik yayını yapılmamıştır.

## Rakip incelemesi

Kullanıcının sağladığı [Emre Arolat Architecture](https://emrearolat.com/) yapılandırmaya eklendi. `competitor-gap.py` yalnızca public HTTPS adreslerini, robots kurallarını ve bekleme süresini dikkate alır. Her site için en fazla 20 adres denenir; dış adresler, özel IP'ler ve yönlendirmeler takip edilmez. JavaScript çalıştırılmaz. Rakip metinleri saklanmaz: kelime sayısı, sayfa türü, konu terimi eşleşmesi, metadata bulunurluğu, schema türleri ve bağlantı sayıları raporlanır. Başlık/açıklama tekrarlarını karşılaştırmak için yalnızca özet değerler saklanır.

İlk gerçek incelemede 16 sayfa ölçüldü; dört adres 512 KB yanıt sınırını aştığı için atlandı. Örneklemde 11 haber/yayın benzeri sayfa, bir proje sayfası, ana sayfa, iletişim ve iki diğer sayfa bulundu. Haber/yayın sınıflandırması URL ve Article schema üzerinden yapılan bir sezgiseldir. Tahmini kapsam, sitenin tamamına dair bir tespit veya kalite sıralaması değildir. Bilinen konu sözlüğünde PUS&CO'nun mevcut içeriklerinde bulunmayan yeni bir konu saptanmadı; buna rağmen kaynaklı süreç rehberleriyle destekleyici içerik yapısını geliştirmek incelemeye değer bir fırsattır. Hazır dört taslak bunu değerlendirmek için kullanılabilir; ayrı içerik onayı gerekir.

14 örnek sayfada meta açıklaması gözlenmedi, iki sayfada schema görülmedi; bu kayıtlar rakibin bütününe genellenemez. Site haritasının varsayılan `/sitemap.xml` adresinde bulunmaması, başka adreste olmadığı anlamına gelmez. PUS&CO ölçümleri anlamlı ana içerik üzerinden, rakip ölçümleri görünür HTML metni üzerinden hesaplandığı için kelime sayıları doğrudan kalite karşılaştırması değildir.

İlk ölçüm kanıtı: [seo-competitor-evidence.json](seo-competitor-evidence.json). Güncel çıktı `.seo/competitor-gap.json` dosyasındadır.

## Yönetim paneli

Mevcut site statik Astro çıktısıdır; uzaktan kimlik doğrulaması ve sunucu çalıştırma altyapısı yoktur. Üretim/dağıtım ayarlarına dokunmama kuralına uygun olarak panel ayrı bir Python standart kütüphane sunucusunda, yalnızca `127.0.0.1` üzerinde çalışır. Public siteye yönetim HTML'i veya özel raporlar eklenmez.

- Adres: `http://127.0.0.1:4330/admin/seo/`; kullanıcı `pusnco`.
- İlk çalıştırmada üretilen parola `.seo/dashboard-password.txt` içindedir. Parola ve raporlar Git'e alınmaz. Panel bu bilgisayar dışında erişilebilir değildir; uzak sunucuya açılmak için tasarlanmamıştır.
- HTTP Basic giriş kontrolü her veri/sayfa isteğinde yapılır. Host doğrulaması, sabit süreli parola karşılaştırması, `noindex/nofollow/noarchive`, `no-store`, içerik güvenlik politikası ve çerçeve engeli uygulanır. Parola veya kimlik doğrulama başlıkları loglanmaz.
- Panel yalnızca okur. İçerik onayı/yayını veya dosya değişikliği için web uç noktası yoktur. Filtreler arama, öncelik ve içerik durumunu destekler.
- İndekslenebilir sayfa, yerel sağlık puanı, bağlantısız sayfalar, kırık bağlantılar, metadata tekrarları, metin tekrarları, schema, sitemap, bağlantı incelemeleri, içerik fırsatları, bekleyen/yayındaki içerikler ve son değişiklikler gösterilir.

Gerçek verilerle doğrulandı: 36 indekslenebilir sayfa, 20 fırsat, 19 bağlantı önerisi, 22 bağlamsal bağlantı inceleme kaydı, dört REVIEW taslağı, sıfır PUBLISHED içerik. Son teknik taramada kırık bağlantı, bağlantısız sayfa, eksik metadata/schema veya sitemap hatası yoktur. Yerel sağlık puanı Lighthouse puanı değildir.

## Düzenli işler

`.github/workflows/seo-monitor.yml` yalnızca okuma yetkili GitHub Actions işidir. Günlük 06:17, pazartesi haftalık 06:37, ayın ilk günü aylık 06:47 Türkiye saatine karşılık gelen UTC programları hazırlanmıştır. Günlük iş bu küçük sitenin tamamını tarar; haftalık iş buna konu/bağlantı analizi, briefler ve rakip örneklemini ekler. Aylık iş kaynaklı içerik yenileme ve konu kapsamı önerileri de üretir. Bir içeriğin eski olması yalnızca son tarama tarihinden çıkarılmaz; eski içerik tespiti editör incelemesi gerektirir.

Kod henüz varsayılan GitHub dalına gönderilmediği için programlar aktif değildir; GitHub üzerinde bir çalışma yapıldığı iddia edilmez. Zamanlanmış işler varsayılan dal üzerinden çalışır ve GitHub yoğunluğunda gecikebilir. [GitHub schedule belgeleri](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).

İşler yeni içerik üretip onaylamaz veya dağıtmaz. HIGH teknik sorunlarda başarısız durum döndürür. Sadece isimleri açıkça belirtilen public analiz raporları 30 gün saklanır; yerel parola, taslak veritabanı ve çevre dosyaları yüklenmez. Checkout ve rapor yükleme için resmi v7 Actions kullanılır; kimlik bilgileri checkout içinde kalıcı tutulmaz. [Checkout](https://github.com/actions/checkout), [Upload artifact](https://github.com/actions/upload-artifact).

GitHub çalıştırmaları mevcut yerel veritabanından bağımsızdır. Çalışmaların karşılaştırma referansı checked-in `seo/monitor-baseline.json` dosyasıdır. Yerel çalışmada önceki crawl kullanılır. GitHub'ın farklı çalışmalarına ait SQLite geçmişi otomatik birleştirilmez; artifact raporları incelenebilir. Baseline yeni yayınlar doğrulandıktan sonra bilerek güncellenmelidir.

## Dosyalar ve veritabanı

Yeni: `scripts/seo-monitor.py`, `scripts/seo-dashboard.py`, `scripts/competitor-gap.py`, `scripts/tests/test_phase6.py`, `seo/competitors.json`, `seo/monitor-baseline.json`, `.github/workflows/seo-monitor.yml`, bu rapor, `docs/seo-phase6-evidence.json` ve `docs/seo-competitor-evidence.json`.

Değişen: `package.json` (komutlar), `scripts/crawl-seo.py` (rehber/hizmet sayfa türü sınıflandırması).

Yerel SQLite: `monitoring_runs`, `monitoring_changes`. Karşılaştırma sonuçları JSON dosyasındadır. İzleme kayıtları deterministik kimlikle tekrarlandığında çoğalmaz. Yeni npm/Python bağımlılığı, ücretli hizmet veya üretim veritabanı yoktur. Ayrı yerel panel süreci vardır. Dağıtım ayarları, gerçek proje verileri ve içerik yayın manifesti değiştirilmedi.

## Doğrulama

- 20 birim testi geçti. Yeni testler girişsiz erişim, yanlış Host, yazma isteği reddi, noindex/no-store, filtreler, HTML kaçışları, özel adres engeli, rakip metninin saklanmaması ve izleme kayıtlarının tekrar çalışmada çoğalmamasını kapsar.
- Yerel önizlemede haftalık tam zincir çalıştı: 37 taranan adres, 36 indekslenebilir sayfa, 370 resim varyantı, 409 istek, sıfır HIGH sorun; 20 brief.
- Aylık zincir de gerçek yerel tarama/rakip örneklemiyle çalıştırıldı. Yenileme önerileri yayınlanmış içerik değişiklikleri değildir.
- Gerçek veritabanıyla panelin kimlik doğrulanmış API isteği başarılı: 36 sayfa ve dört bekleyen taslak.
- Astro derlemesi ve 36 sayfanın metadata, schema, bağlantı ve sitemap testleri geçti.
- GitHub workflow uzaktan çalıştırılmadı. Yeni Lighthouse ölçümü yoktur. Faz 3'teki Türkçe ana sayfa performans 88 konusu devam eder; bu hafif zamanlanmış iş Lighthouse ölçümü yerine geçmez.

## Çalıştırma

Proje klasöründe önizleme 4322 portunda çalışırken:

```text
npm run seo:monitor -- daily
npm run seo:monitor -- weekly
npm run seo:monitor -- monthly
npm run seo:competitors
npm run seo:dashboard
npm run test:monitor
npm run seo:crawl -- --base http://127.0.0.1:4322
```

Tam süreç: crawl → analiz → fırsatlar → briefler → çevrimdışı kaynaklı taslak JSON'u → kalite kontrolü → bağlantı/schema → derleme doğrulaması → insan içerik onayı → yayın manifesti → ayrıca yetkilendirilmiş dağıtım → canlı doğrulama → izleme. Mevcut LLM sağlayıcısı olmadığı için otomatik model çağrısı yoktur; bu adım insan seçimi ve çevrimdışı taslak üretimi olarak kalır.

Onaylı içeriği hazırlama ve canlı durumu doğrulama komutları [Faz 5 raporunda](seo-phase5-report.md) bulunur. `publish` dağıtım komutu değildir; inceleme ve içerik özeti onayı zorunludur. Bu aşamanın devam onayı, taslakların içerik onayı olarak kullanılmadı.

## Kalanlar

GitHub aktarımı/dağıtım yapılmadı; dolayısıyla düzenli işler aktif değil ve uzaktan korumalı panel yayınlanmadı. Uzaktan panel üretim altyapısı/kimlik doğrulaması tasarımı ve dağıtım ayarı gerektirir; verilen kurala uygun olarak eklenmedi. Faz 2'deki gerçek 301 normalizasyonları aynı dağıtım kısıtı nedeniyle bekler. Taslaklar ve bağlantı önerileri ayrı editör onayını bekler. Arama hacmi, Search Console, gerçek kullanıcı Core Web Vitals verisi ve otomatik LLM hizmeti yoktur.
