import { getProject, getProjectNav, img } from '../lib/projects';
import { useTranslations, type Lang } from '../i18n/ui';

const root = document.querySelector<HTMLElement>('[data-detail]');

if (root) {
  const lang = (document.documentElement.lang || 'en') as Lang;
  const t = useTranslations(lang);
  const id = new URLSearchParams(location.search).get('id');

  const stateEl = root.querySelector<HTMLElement>('[data-detail-state]');
  const setState = (msg: string) => {
    if (stateEl) {
      stateEl.textContent = msg;
      stateEl.hidden = false;
    }
  };

  const run = async () => {
    if (!id) return setState(t('detail.notFound'));

    let project;
    try {
      project = await getProject(id, lang);
    } catch (err) {
      console.error('[projects] proje yüklenemedi:', err);
      return setState(t('detail.notFound'));
    }
    if (!project) return setState(t('detail.notFound'));

    // Başlık
    const titleEl = root.querySelector('[data-detail-title]');
    if (titleEl) titleEl.textContent = project.title;
    document.title = `${project.title} — ${t('site.name')}`;

    // Kapak
    const coverEl = root.querySelector('[data-detail-cover]');
    if (coverEl && project.cover) {
      const im = document.createElement('img');
      im.src = img(project.cover, 2000);
      im.alt = project.title;
      im.onerror = () => im.remove();
      coverEl.appendChild(im);
    }

    // Künye
    const metaEl = root.querySelector('[data-detail-meta]');
    if (metaEl) {
      const rows: [string, string][] = (
        [
          [t('meta.location'), project.location],
          [t('meta.year'), project.year],
          [t('meta.area'), project.area],
          [t('meta.typology'), project.typology],
          [t('meta.client'), project.client],
          [t('meta.photographer'), project.photographer],
        ] as [string, string][]
      ).filter(([, v]) => Boolean(v));
      metaEl.innerHTML = rows
        .map(
          ([k, v]) =>
            `<div class="detail__meta-row"><span class="u-label">${k}</span><span class="detail__meta-val">${v}</span></div>`,
        )
        .join('');
    }

    // Açıklama
    const descEl = root.querySelector('[data-detail-desc]');
    if (descEl && project.description) descEl.textContent = project.description;

    // Galeri
    const galEl = root.querySelector('[data-detail-gallery]');
    if (galEl && project.gallery.length) {
      galEl.innerHTML = project.gallery
        .map(
          (u, i) =>
            `<figure class="detail__shot ${i % 3 === 1 ? 'is-narrow' : ''}"><img src="${img(
              u,
              1600,
            )}" alt="${project!.title} — ${i + 1}" loading="lazy" onerror="this.remove()" /></figure>`,
        )
        .join('');
    }

    // Sonraki proje
    try {
      const nav = await getProjectNav(lang);
      if (nav.length > 1) {
        const idx = nav.findIndex((p) => p.slug === project!.slug);
        const next = nav[(idx + 1) % nav.length];
        const nextEl = root.querySelector<HTMLElement>('[data-detail-next]');
        const nextLink = root.querySelector<HTMLAnchorElement>('[data-detail-next-link]');
        const nextTitle = root.querySelector('[data-detail-next-title]');
        if (nextEl && nextLink && nextTitle && next) {
          nextLink.href = `/${lang}/projects/detail/?id=${next.slug}`;
          nextTitle.textContent = next.title;
          nextEl.hidden = false;
        }
      }
    } catch {
      /* navigasyon opsiyonel — yok say */
    }
  };

  run();
}
