# Editorial Luxury Mimarlık Sitesi — Proje Planı

> **Felsefe:** "Sessiz Lüks" (Quiet Luxury). Bir web sitesinden çok, dijital bir mimari
> portfolyo kitabı. Sanat galerisi / yüksek moda dergisi (Vogue, Kinfolk) estetiği.
> Negatif alan, tipografik hiyerarşi, mikro-interaksiyonlar ve asimetrik denge.
>
> **Yayın hedefi:** Basit statik hosting (cPanel / FTP). Sunucu (Node.js) gerektirmez —
> yerelde `build` alınıp `dist/` klasörü upload edilir.

---

## 1. Vizyon & Tasarım Prensipleri

| # | Prensip | Uygulama Karşılığı |
|---|---------|--------------------|
| 1 | **Negatif alan hâkim** | İçerik ekranın en fazla %55'ini doldurur; kalan boşluk "nefes alır". Section'lar arası dikey boşluk cömert (min. 160px masaüstü). |
| 2 | **Asimetrik denge** | Geleneksel 12'li grid kırılır; içerik bazen 2. sütundan başlar, görseller kaçık (offset) yerleşir. |
| 3 | **Tipografi = kimlik** | İnce, yüksek kontrastlı serif başlıklar + geometrik sans-serif gövde. Boyut farkları dramatik. |
| 4 | **Sessiz etkileşim** | Hiçbir animasyon "gösteriş" yapmaz. 300-600ms yumuşak geçişler, `cubic-bezier(0.4, 0, 0.2, 1)`. |
| 5 | **Görsel öncelikli** | Fotoğraflar kenarsız, geniş formatlı, yüksek çözünürlüklü. Metin görseli desteklerken görsel sahnenin yıldızı. |
| 6 | **İçerik yavaş açılır** | Scroll ile içerik aşağıdan süzülerek belirir (staggered reveal). Aceleye getirilmez. |

---

## 2. Teknoloji Yığını (Kararlaştırıldı)

Hepsi **ücretsiz**; tek gerçek masraf mevcut hosting + (opsiyonel) alan adı.

| Katman | Seçim | Gerekçe |
|--------|-------|---------|
| Framework | **Astro** (statik çıktı) | `npm run build` → saf HTML/CSS/JS. Basit hostinge upload edilir, sunucu gerektirmez. Bileşen tekrarı + yerleşik i18n. |
| Stil | **Tailwind CSS** (`@astrojs/tailwind`) + CSS token'ları | Boşluk/tipografi ölçeğini token yönetmek; asimetrik grid'i utility ile hızlı kurmak. |
| Animasyon | **GSAP + ScrollTrigger** + **Lenis** | Vanilla JS — React'e bağımlı değil, Astro ile birebir uyumlu. Reveal, parallax, pin, Ken Burns, akıcı scroll. |
| İçerik (CMS) | **Sanity** (Headless, ücretsiz katman) | Editör panelinden proje/künye/görsel yönetimi. Görseller Sanity CDN. Localized (TR/EN) alanlar. |
| Projelerin çekilişi | **Client-side canlı fetch** (`@sanity/client`, tarayıcıda GROQ) | ✅ *Karar.* Admin'e proje eklenince **yeniden build/upload gerekmeden** projeler sayfasında görünür. |
| Çok dil (i18n) | **Astro yerleşik i18n** (`en` varsayılan + `tr`) | `/en` ve `/tr` yolları. Ücretsiz, ekstra kütüphane yok. |
| Dil algılama | **`.htaccess`** (LiteSpeed, `Accept-Language`) + JS fallback | Host LiteSpeed (Apache uyumlu) → kökte (`/`) sunucu tarafı yönlendirme yapılabilir; eşleşme yoksa **`en`**, seçim `localStorage`'da hatırlanır. |
| Font | `@fontsource` ile self-host (Cormorant Garamond, Montserrat) | CLS'siz, hızlı, CDN bağımsız. |
| Deploy | **turkticaret.net** — cPanel/File Manager veya FTP → `dist/` upload | LiteSpeed + Linux + ücretsiz SSL/alan adı. Web Mini paketi yeter (tek site, klasör-bazlı i18n subdomain gerektirmez). |

> **Sanity canlı fetch notları:** Dataset **public (okuma)** olmalı (yayınlanan içerik için
> standart). Sitenin origin'i Sanity **CORS** listesine eklenir. Token gerekmez (public read).

---

## 3. Tasarım Sistemi (Design Tokens)

### 3.1 Renk Paleti

```css
:root {
  --color-bg:        #FFFFFF;  /* Saf beyaz arka plan */
  --color-text:      #1A1A1A;  /* Antrasit ana metin (tam siyah DEĞİL) */
  --color-muted:     #757575;  /* Hover / ikincil / accent metin */
  --color-line:      #E0E0E0;  /* Çok ince ayraç çizgileri */
  --color-bg-soft:   #FAFAF8;  /* Opsiyonel sıcak beyaz (section ayrımı) */
}
```

- Tek renk vurgusu opsiyonel (§11 açık). Şimdilik salt monokrom palet.

### 3.2 Tipografi

| Rol | Font | Ağırlık | Notlar |
|-----|------|---------|--------|
| Display / Başlık | **Cormorant Garamond** ✅ | 300–400 | İnce, zarif, yüksek kontrastlı serif. `letter-spacing` hafif artırılmış. |
| Gövde | **Montserrat Light** ✅ | 300 | Geometrik, okunabilir sans-serif. Renk `#1A1A1A`. |
| Etiket / Alt başlık | Montserrat | 400–500 | `text-transform: uppercase`, `letter-spacing: 0.15em`, küçük punto. |

**Tip ölçeği (fluid, `clamp`):**

```css
--fs-display:  clamp(3.5rem, 8vw, 9rem);   /* Hero başlık — devasa ama ince */
--fs-h1:       clamp(2.5rem, 5vw, 5rem);
--fs-h2:       clamp(1.75rem, 3vw, 3rem);
--fs-h3:       clamp(1.25rem, 2vw, 1.75rem);
--fs-body:     clamp(1rem, 1.1vw, 1.125rem);
--fs-label:    0.75rem;  /* uppercase etiketler */

--tracking-tight:  -0.02em;  /* büyük serif başlıklar */
--tracking-wide:   0.15em;   /* uppercase etiketler */
--leading-display: 1.05;
--leading-body:    1.7;      /* gövde — ferah satır aralığı */
```

### 3.3 Boşluk & Grid

```css
--space-scale: 8px temel;  /* 8, 16, 24, 40, 64, 96, 160, 240 */
--section-gap-desktop: clamp(120px, 15vh, 240px);
--container-max: 1600px;
--gutter: clamp(24px, 5vw, 120px);  /* geniş dış boşluk */
```

- **Grid:** 12 sütun ama asimetrik kullanılır. Örn. başlık `col 2–7`, görsel `col 8–12`.
- **Breakpoint'ler:** `sm 640 / md 768 / lg 1024 / xl 1280 / 2xl 1600`.

### 3.4 Animasyon Token'ları

```css
--ease-editorial: cubic-bezier(0.4, 0, 0.2, 1);
--dur-fast:   0.3s;
--dur-base:   0.4s;
--dur-slow:   0.6s;
--dur-reveal: 0.8s;
```

- Reveal: `opacity 0→1` + `translateY 24px→0`, `--dur-reveal`, stagger 80–120ms.
- Hover: renk `#1A1A1A → #757575`, `--dur-base`.

---

## 4. Bileşen Kütüphanesi

Astro bileşenleri (`.astro`); etkileşimliler `<script>` içinde GSAP/Lenis ile hidratlanır.

| Bileşen | Davranış |
|---------|----------|
| **Navigation** | Minimal üst bar: solda logo/ofis adı (ince serif), sağda `MENU` + `TR/EN` switch. `MENU` tıklanınca tam ekran tipografik overlay (aşağıdan/soldan yumuşak geçiş), büyük serif link listesi + GSAP stagger reveal. Kapanış `Close`. |
| **Ghost Button** | Çerçevesiz, yalnızca metin. Altında 1px çizgi soldan sağa açılır (`scaleX 0→1`, `transform-origin: left`) **veya** metin 2–3px yukarı kayar. Renk `#1A1A1A → #757575`. Saf CSS `:hover` yeterli. |
| **Hero** | Ortada devasa ince başlık; yanında/altında dikey konumlu küçük açıklama (uppercase etiket). Arka planda tek ikonik yapı fotoğrafı, yavaş Ken Burns zoom (CSS `@keyframes` scale 1→1.08, 12–20s ease). |
| **Proje Galerisi** | Asimetrik masonry. **Sanity'den client-side canlı çekilir** ve JS ile render edilir. Bazı görseller dikey, bazı yatay, kaçık offset. Hover'da proje adı + yıl zarifçe belirir, görsel hafif koyulaşır/scale. |
| **Proje Kartı** | Görsel (Sanity CDN, boyut parametreli) + altında ince serif proje adı, uppercase konum/yıl etiketi. |
| **Split Section** | Bir yanda büyük görsel, diğer yanda dikey ortalanmış metin — asimetrik oran (örn. 60/40). |
| **LocaleSwitch** | `TR / EN`; aktif dil vurgulu. Tıklama `localStorage`'a yazar ve karşı dildeki eş sayfaya gider. |
| **Footer** | En altta çok küçük fontlarla geniş boşluklu iletişim bilgisi. İnce üst ayraç çizgisi (`--color-line`). Sayfa "nefes alarak" biter. |
| **Cursor (ops.)** | Özel ince daire imleç; görsel üzerinde `View` etiketi. Zarif, abartısız. |

---

## 5. Site Haritası & Sayfalar

Astro i18n ile locale önekli. Varsayılan `en`, ikinci dil `tr`.

```
/                     Kök — dil algılama + redirect (en/tr)
/en                   Ana sayfa   — Hero + seçili projeler + felsefe + CTA
/en/projects          Projeler    — asimetrik galeri (Sanity canlı), minimal filtre (ops.)
/en/projects/[slug]   Proje detay — büyük görseller, künye, metin, sonraki proje
/en/studio            Stüdyo/Hakkında — ekip, felsefe, süreç, ödüller
/en/contact           İletişim    — minimal form + adres/sosyal
/tr, /tr/projects ...  (TR karşılıkları)
```

- **Ana sayfadaki "seçili projeler"** ve **projeler sayfası** Sanity'den canlı çekilir.
- **Journal/Blog:** Bu fazda kapsam dışı; gelecekte Sanity `post` şeması ile eklenebilir.

**Proje detay akışı:** Tam genişlik kapak → sol sütunda künye (konum, yıl, alan, tip) →
tam genişlik ve asimetrik görsel dizisi → kısa editorial metin → "Sonraki Proje" geçişi.

---

## 6. Etkileşim & Animasyon Kataloğu (GSAP + Lenis)

1. **Sayfa yükleme:** İçerik aşağıdan süzülerek gelir (GSAP stagger). Minimal, hızlı.
2. **Scroll reveal:** ScrollTrigger ile her section görünür alana girince `translateY + opacity`.
3. **Ken Burns:** Hero görselinde sürekli yavaş zoom (CSS keyframes).
4. **Parallax:** Görseller scroll'da farklı hızda hafif kayar (Lenis + ScrollTrigger).
5. **Menu overlay:** Full-screen açılış, linkler GSAP stagger ile belirir.
6. **Buton underline:** Hover'da soldan sağa 1px çizgi (CSS).
7. **Görsel hover:** Proje adı fade-in + görsel scale/koyulaşma.
8. **Sayfa geçişi:** Astro **View Transitions** ile yumuşak fade/mask.
9. **Smooth scroll:** Lenis ile tüm sitede ağırlıklı, akıcı kaydırma.

> **Erişilebilirlik:** Tüm hareket `prefers-reduced-motion: reduce` ile devre dışı
> bırakılabilir olmalı — animasyonlar kapalıyken içerik tam işlevsel kalır.

---

## 7. Klasör Yapısı (Astro)

```
architechture/
├── src/
│   ├── pages/
│   │   ├── index.astro            # kök: dil algılama + redirect
│   │   ├── en/
│   │   │   ├── index.astro
│   │   │   ├── projects/index.astro
│   │   │   ├── projects/[slug].astro
│   │   │   ├── studio.astro
│   │   │   └── contact.astro
│   │   └── tr/ …                  # TR karşılıkları
│   ├── layouts/BaseLayout.astro   # font, Lenis, nav, footer, <head>/SEO
│   ├── components/
│   │   ├── nav/Navbar.astro, MenuOverlay.astro, LocaleSwitch.astro
│   │   ├── hero/Hero.astro
│   │   ├── gallery/ProjectGrid.astro     # + client script (Sanity fetch)
│   │   ├── gallery/ProjectCard.astro
│   │   └── ui/GhostButton.astro, Reveal.astro, Divider.astro
│   ├── scripts/
│   │   ├── lenis.ts               # smooth scroll init
│   │   ├── animations.ts          # GSAP + ScrollTrigger reveal/parallax
│   │   ├── sanity.ts              # @sanity/client + GROQ (client-side)
│   │   └── i18n.ts                # dil algılama/redirect, çeviri sözlüğü
│   ├── i18n/en.json, tr.json      # statik UI metinleri
│   └── styles/tokens.css, global.css
├── sanity/                        # Sanity Studio (ayrı deploy / sanity.io)
│   ├── schemas/project.ts, studio.ts, settings.ts   # localized fields (TR/EN)
│   └── sanity.config.ts
├── public/                        # olduğu gibi dist'e kopyalanır:
│   ├── favicon, statik ikonlar
│   ├── contact.php                # PHP mail handler (host'ta çalışır)
│   └── .htaccess                  # dil yönlendirme + SSL zorlama + cache
├── astro.config.mjs               # i18n + tailwind + view transitions
├── .env                           # PUBLIC_SANITY_PROJECT_ID, DATASET
└── PLAN.md
```

> Build çıktısı `dist/` → FTP/cPanel ile hostinge upload. Sanity Studio ayrı çalışır
> (sanity.io'da ücretsiz barındırma veya yerel).

---

## 8. Yol Haritası (Fazlar)

### Faz 0 — Temel & Altyapı ✅ TAMAMLANDI
- ✅ Astro 7 + Tailwind 4 kurulumu (`npm run build` doğrulandı, 9 sayfa üretiliyor).
- ✅ Cormorant Garamond + Montserrat self-host (`@fontsource`), design token'ları (`global.css`).
- ✅ Astro **i18n** (`en` default, `tr`), kök redirect + dil algılama scripti (yerelde doğrulandı).
- ✅ **Sanity** şema iskeleti (`project`, `studio`, `settings`) + `@sanity/client` client-side
  canlı fetch + GROQ. (Studio kurulumu ve `.env` kullanıcıya kalıyor — bkz. README.)
- ✅ Lenis + GSAP entegrasyonu (`site.ts`: reveal, parallax, menü, proje yükleme).
- ✅ Bonus: Navbar + full-screen menü, Hero (Ken Burns), Footer, iletişim formu + `contact.php`,
  `.htaccess`, ana sayfa/projeler/stüdyo/iletişim sayfaları (EN+TR) — hepsi çalışır durumda.

### Faz 1 — Tasarım Sistemi & İskelet (1–2 gün)
- Renk/tipografi/boşluk token'ları, `Reveal`, `GhostButton`, `Divider`.
- Responsive asimetrik grid yardımcıları.

### Faz 2 — Navigasyon & Layout (1 gün)
- Navbar + full-screen menü overlay (GSAP stagger) + **LocaleSwitch (TR/EN)**.
- `BaseLayout`, footer, `<head>`/SEO.

### Faz 3 — Ana Sayfa (1–2 gün)
- Hero + Ken Burns, seçili projeler (Sanity canlı) asimetrik galeri, felsefe section, CTA.

### Faz 4 — Projeler & Detay (2 gün)
- Projeler galerisi (Sanity **client-side canlı** render), proje detay şablonu,
  "sonraki proje" geçişi. Localized (TR/EN) alanların çekilmesi.

### Faz 5 — Stüdyo & İletişim (1 gün)
- Hakkında/ekip/felsefe (Sanity), minimal iletişim formu + **`contact.php`** mail handler.

### Faz 6 — Cila, Performans & Yayın (1–2 gün)
- View Transitions ince ayar, parallax, `prefers-reduced-motion`.
- Her iki dil için Lighthouse (perf/erişilebilirlik/SEO), görsel optimizasyonu,
  locale-aware `<meta>` + `hreflang` + `sitemap.xml`.
- `.htaccess`: dil yönlendirme + HTTPS zorlama + statik varlık cache başlıkları.
- **Yayın:** `npm run build` → `dist/` → **turkticaret.net** cPanel/File Manager (veya FTP)
  ile `public_html`'e upload. Sanity Studio ayrı deploy (sanity.io) + CORS'a site origin'i ekle.

**Tahmini toplam:** ~8–11 gün (içerik hazırsa).

---

## 9. Kalite: Performans, SEO, Erişilebilirlik

- **Performans:** Astro varsayılan sıfır-JS (yalnız gereken adacıklar hidratlanır).
  Sanity görselleri boyut/format parametreli (`w`, `auto=format`), lazy-load.
  Animasyon yalnız `transform`/`opacity`. Hedef LCP < 2.5s.
- **SEO:** Statik HTML → güçlü. Semantik başlık hiyerarşisi, locale-aware `<meta>`,
  `hreflang` (TR/EN), OG görseli, `sitemap.xml`, structured data (Organization/CreativeWork).
  ⚠️ **Not:** Projeler client-side çekildiği için proje listesi/detayı ilk HTML'de olmaz —
  o içeriğin SEO'su daha zayıftır ve kısa bir yükleme anı olur. Ana sayfalar tam statik
  ve güçlü kalır. (İleride gerekirse projeler build-time'a alınabilir.)
- **Erişilebilirlik:** WCAG AA kontrast, klavye ile menü gezinimi, focus göstergeleri,
  `alt` metinleri, `prefers-reduced-motion`.

---

## 10. İçerik & Görsel Gereksinimleri

- **Görseller:** Yüksek çözünürlüklü (min. 2400px), tutarlı ton, kenarsız. Yatay + dikey
  karışımı (asimetri). Ken Burns için tek güçlü hero fotoğrafı. Sanity'ye yüklenir, CDN'den servis.
- **Metin:** Kısa, editoryal, "boşluğu seven" dil. TR + EN.
- **Künye verisi (Sanity `project` şeması):** başlık, slug, konum, yıl, alan (m²), tip,
  müşteri, fotoğrafçı, kapak görseli, galeri görselleri, açıklama — hepsi TR/EN.

---

## 11. Kararlar & Açık Sorular

**Verilen kararlar:**
- ✅ **Yayın:** **turkticaret.net** (LiteSpeed + cPanel, Linux). `dist/` → File Manager/FTP upload. Ücretsiz SSL + alan adı dahil. Web Mini paketi yeterli.
- ✅ **Framework:** **Astro** (statik çıktı), animasyon **GSAP + Lenis**.
- ✅ **İçerik:** **Sanity** (ücretsiz), projeler **client-side canlı** — admin'e ekle, upload'sız görünür. MySQL kullanılmıyor (boşta kalır).
- ✅ **Çok dil:** Astro i18n, **otomatik dil algılama** (`.htaccess` + JS fallback), eşleşme yoksa **varsayılan `en`**.
- ✅ **İletişim formu:** Host'ta PHP (5.x–8.x) mevcut → basit **`contact.php`** mail scripti (3. parti gerekmez). Spam için honeypot + basit doğrulama.
- ✅ **Display font:** Cormorant Garamond · **Gövde font:** Montserrat Light (300).
- ✅ **Journal/Blog:** Kapsam dışı (sonradan eklenebilir).

**Hâlâ açık:**
- [ ] İmza vurgu rengi olacak mı (varsa hangi ton)? — Şimdilik salt monokrom palet varsayılıyor.

---

*Bu plan "Editorial Luxury / Sessiz Lüks" briefine ve şu kararlara göre günceldir:
Astro + Sanity (canlı) + GSAP/Lenis, basit statik hostinge yayın. Onay sonrası Faz 0'dan
başlanabilir.*
