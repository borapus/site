# ATELIER — Editorial Luxury Mimarlık Sitesi

Astro + Sanity + GSAP/Lenis ile "Sessiz Lüks" estetiğinde, çok dilli (TR/EN) statik
mimarlık portföyü. Basit statik hostinge (turkticaret.net — LiteSpeed/cPanel) yayınlanır.

Tasarım ve karar dokümanı: [PLAN.md](PLAN.md)

---

## Komutlar

```bash
npm install       # bağımlılıklar
npm run dev       # yerel geliştirme (http://localhost:4321)
npm run build     # statik çıktı → dist/
npm run preview   # build çıktısını yerelde önizle
```

## Proje yapısı

```
src/
├── pages/              # rotalar: / (dil yönlendirme), /en/*, /tr/*
├── layouts/            # BaseLayout (font, SEO, nav, footer, script)
├── components/         # nav, hero, gallery, ui, pages/
├── scripts/site.ts     # Lenis + GSAP reveal/parallax + menü + Sanity fetch
├── lib/sanity.ts       # client-side canlı proje çekişi
├── i18n/ui.ts          # TR/EN sözlük + yardımcılar
└── styles/global.css   # design token'lar + base + galeri stilleri
public/                 # .htaccess, contact.php, favicon (olduğu gibi dist'e kopyalanır)
sanity/                 # AYRI Sanity Studio projesi (şemalar + config)
```

---

## Sanity'yi bağlama (projeleri "canlı" yapmak için)

Sanity bağlanana kadar proje galerileri "boş durum" mesajı gösterir (tasarım bozulmaz).

1. **Studio oluştur:** `npm create sanity@latest` ile ayrı bir Studio projesi kur.
   `sanity/schemas/*` şemalarını ve `sanity.config.ts`'i oraya taşı, `projectId` gir.
2. **Dataset:** `production` datasetini **public (read)** yap.
3. **CORS:** Sanity proje ayarlarında sitenin origin'ini (ör. `https://alanadi.com`
   ve geliştirme için `http://localhost:4321`) CORS listesine ekle.
4. **.env:** Kök dizinde `.env` oluştur (`.env.example`'dan kopyala):
   ```
   PUBLIC_SANITY_PROJECT_ID=xxxx
   PUBLIC_SANITY_DATASET=production
   ```
5. Studio'dan proje ekle → sitede **yeniden build gerektirmeden** görünür.

---

## Yayınlama (turkticaret.net — cPanel)

1. `npm run build` → `dist/` klasörü oluşur.
2. Yayından önce:
   - `astro.config.mjs` içindeki `site`'ı gerçek alan adıyla değiştir (hreflang/sitemap için).
   - `public/contact.php` içindeki `$TO` adresini gerçek alıcı e-postasıyla değiştir.
3. `dist/` **içeriğini** cPanel File Manager veya FTP ile `public_html`'e yükle
   (Plesk kullanıyorsan `httpdocs`). `.htaccess` ve `contact.php` dahildir.
4. cPanel'den ücretsiz SSL'i etkinleştir.

---

## Proje detay sayfası

- URL: `/[locale]/projects/detail/?id=<slug>` (client-side, canlı — yeniden build gerekmez).
- Kapak, künye (konum/yıl/alan/tipoloji/müşteri/fotoğraf), açıklama, galeri, "sonraki proje".
- Sanity bağlı değilken zarif bir durum mesajı gösterir.
- Not: "temiz" URL (`/projects/<slug>`) istenirse `.htaccess` rewrite ile sonradan eklenebilir.

## Hero fotoğrafı

- `public/images/hero.jpg` ekle → otomatik görünür (Ken Burns). Dosya yoksa gradient fallback kalır.
- Farklı görsel: `<Hero image="/images/xxx.jpg" />`.

## Açık işler (sonraki fazlar)

- [ ] Sanity Studio'yu kurup gerçek içerik + görsellerle doldurmak (bkz. `sanity/README.md`).
- [ ] `sitemap.xml` (Astro `@astrojs/sitemap` entegrasyonu).
- [ ] Astro **View Transitions** ile yumuşak sayfa geçişleri (Faz 6 cila).
- [ ] İmza vurgu rengi kararı (şu an salt monokrom).
- [ ] (Ops.) Proje detay için "temiz URL" `.htaccess` rewrite.
