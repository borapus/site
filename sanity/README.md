# ATELIER — Sanity Studio

İçerik yönetim paneli (projeler, stüdyo, ayarlar). Site'den **ayrı** çalışır.

## Kurulum

1. **Proje oluştur:** [sanity.io/manage](https://www.sanity.io/manage) → yeni proje →
   `projectId`'yi kopyala. `production` dataset'ini oluştur ve **public (read)** yap.

2. **Env:** `sanity/.env` dosyası oluştur (`.env.example`'dan):
   ```
   SANITY_STUDIO_PROJECT_ID=xxxxxxxx
   SANITY_STUDIO_DATASET=production
   ```

3. **Çalıştır:**
   ```bash
   cd sanity
   npm install
   npx sanity login      # tarayıcıdan Sanity hesabına giriş
   npm run dev           # http://localhost:3333
   ```

4. **CORS:** sanity.io/manage → API → CORS origins →
   `http://localhost:4321` ve yayın alan adını ekle (credentials gerekmez).

5. **Ana siteyle bağla:** Kök dizindeki `.env` içine aynı projectId'yi yaz:
   ```
   PUBLIC_SANITY_PROJECT_ID=xxxxxxxx
   PUBLIC_SANITY_DATASET=production
   ```

## Yayınlama (ücretsiz)

```bash
npm run deploy          # https://<isim>.sanity.studio adresinde barınır
```

## Şemalar

- **project** — başlık, slug, yıl, konum, tipoloji, alan, müşteri, fotoğrafçı,
  kapak, galeri, açıklama (TR/EN), `featured`, `orientation`.
- **studio** — hakkında metni (TR/EN), portre, ekip.
- **settings** — stüdyo adı, iletişim, lokasyonlar, sosyal.

> `title`, `location`, `typology`, `description` alanları `{ en, tr }` nesnesidir.
> Site, aktif dile göre `coalesce(alan[$lang], alan.en)` ile çeker.
