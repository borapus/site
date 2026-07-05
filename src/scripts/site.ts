import Lenis from 'lenis';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* -------------------------------------------------
   Akıcı scroll (Lenis) — ScrollTrigger ile senkron
--------------------------------------------------- */
let lenis: Lenis | null = null;
if (!reduce) {
  lenis = new Lenis({
    duration: 1.1,
    easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
  });
  lenis.on('scroll', ScrollTrigger.update);
  gsap.ticker.add((time) => lenis!.raf(time * 1000));
  gsap.ticker.lagSmoothing(0);
}

/* -------------------------------------------------
   Scroll reveal — aşağıdan süzülerek belirir
--------------------------------------------------- */
function initReveals(scope: ParentNode = document) {
  const els = gsap.utils.toArray<HTMLElement>(scope.querySelectorAll('[data-reveal]'));
  els.forEach((el) => {
    if (reduce) {
      gsap.set(el, { autoAlpha: 1 });
      return;
    }
    const delay = Number(el.dataset.revealDelay ?? 0);
    gsap.fromTo(
      el,
      { autoAlpha: 0, y: 26 },
      {
        autoAlpha: 1,
        y: 0,
        duration: 0.8,
        ease: 'power2.out',
        delay,
        scrollTrigger: { trigger: el, start: 'top 88%', once: true },
      },
    );
  });
}

/* -------------------------------------------------
   Hafif parallax  ( [data-parallax="0.15"] )
--------------------------------------------------- */
function initParallax() {
  if (reduce) return;
  gsap.utils.toArray<HTMLElement>('[data-parallax]').forEach((el) => {
    const amount = Number(el.dataset.parallax || 0.15);
    gsap.to(el, {
      yPercent: amount * 100,
      ease: 'none',
      scrollTrigger: { trigger: el, start: 'top bottom', end: 'bottom top', scrub: true },
    });
  });
}

/* -------------------------------------------------
   Full-screen menü overlay
--------------------------------------------------- */
function initMenu() {
  const toggle = document.querySelector<HTMLButtonElement>('[data-menu-toggle]');
  const overlay = document.querySelector<HTMLElement>('[data-menu]');
  const closeBtn = document.querySelector<HTMLButtonElement>('[data-menu-close]');
  if (!toggle || !overlay) return;

  const links = gsap.utils.toArray<HTMLElement>(overlay.querySelectorAll('[data-menu-item]'));

  const open = () => {
    document.documentElement.classList.add('menu-open');
    overlay.setAttribute('aria-hidden', 'false');
    lenis?.stop();
    if (!reduce) {
      gsap.fromTo(
        links,
        { autoAlpha: 0, y: 28 },
        { autoAlpha: 1, y: 0, duration: 0.6, ease: 'power3.out', stagger: 0.07, delay: 0.15 },
      );
    }
  };
  const close = () => {
    document.documentElement.classList.remove('menu-open');
    overlay.setAttribute('aria-hidden', 'true');
    lenis?.start();
  };

  toggle.addEventListener('click', open);
  closeBtn?.addEventListener('click', close);
  overlay.querySelectorAll('a').forEach((a) => a.addEventListener('click', close));
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && document.documentElement.classList.contains('menu-open')) close();
  });
}

/* -------------------------------------------------
   Dil seçimi hatırlama (kök yönlendirme için)
--------------------------------------------------- */
function initLocaleMemory() {
  document.querySelectorAll<HTMLAnchorElement>('[data-locale]').forEach((a) => {
    a.addEventListener('click', () => {
      try {
        localStorage.setItem('lang', a.dataset.locale || 'en');
      } catch {
        /* yok say */
      }
    });
  });
}

/* -------------------------------------------------
   Projeleri Sanity'den canlı yükle
--------------------------------------------------- */
function initProjects() {
  const grid = document.querySelector<HTMLElement>('[data-projects]');
  if (!grid) return;
  const lang = document.documentElement.lang || 'en';
  const featured = grid.hasAttribute('data-featured');
  const limitAttr = grid.getAttribute('data-limit');
  const limit = limitAttr ? Number(limitAttr) : undefined;

  import('../lib/projects').then(async ({ getProjects, img }) => {
    let projects;
    try {
      projects = await getProjects(lang, { featured, limit });
    } catch (err) {
      console.error('[projects] yüklenemedi:', err);
      return;
    }
    if (!projects.length) return; // seed/Sanity boşsa "boş durum"u koru

    grid.querySelector('[data-projects-empty]')?.remove();
    const frag = document.createDocumentFragment();

    for (const p of projects) {
      const a = document.createElement('a');
      a.className = 'project-card ' + (p.orientation === 'portrait' ? 'is-portrait' : 'is-landscape');
      a.href = `/${lang}/projects/detail/?id=${p.slug}`;
      a.setAttribute('data-reveal', '');
      a.innerHTML = `
        <span class="project-card__media">${
          p.cover
            ? `<img src="${img(p.cover, 1400)}" alt="${p.title}" loading="lazy" onerror="this.remove()" />`
            : ''
        }</span>
        <span class="project-card__meta">
          <span class="project-card__title">${p.title}</span>
          <span class="u-label">${[p.location, p.year].filter(Boolean).join(' — ')}</span>
        </span>`;
      frag.appendChild(a);
    }
    grid.appendChild(frag);
    initReveals(grid);
    ScrollTrigger.refresh();
  });
}

/* ------------------------------------------------- */
initReveals();
initParallax();
initMenu();
initLocaleMemory();
initProjects();
