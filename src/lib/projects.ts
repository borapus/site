// Birleşik proje veri katmanı.
// Sanity yapılandırılmışsa Sanity'den (canlı) çeker; değilse yerel seed'i kullanır.
import {
  isSanityConfigured,
  fetchProjects,
  fetchProject,
  img,
  type ProjectCard,
  type ProjectDetail,
} from './sanity';
import { localProjects } from '../data/projects';
import { uploadedProjects } from '../data/uploadedProjects';

type Loc = { en: string; tr: string };
const pick = (o: Loc, lang: string) => (lang === 'tr' ? o.tr : o.en) || o.en || '';
// Tarihi olmayan projeler sonda; aynı yıldaki projeler mevcut sırasını korur.
const projectYear = (year: string) => {
  const value = Number(year.trim());
  return Number.isFinite(value) && value > 0 ? value : 0;
};
const byYearDesc = (a: { year: string }, b: { year: string }) =>
  projectYear(b.year) - projectYear(a.year);

export async function getProjects(
  lang: string,
  opts: { limit?: number; featured?: boolean } = {},
): Promise<ProjectCard[]> {
  if (isSanityConfigured) {
    const remote = await fetchProjects(lang, { featured: opts.featured });
    const additions = uploadedProjects
      .filter((p) => (!opts.featured || p.featured) && !remote.some((r) => r.slug === p.slug))
      .map((p) => ({ _id: p.slug, title: pick(p.title, lang), slug: p.slug,
        location: pick(p.location, lang), year: p.year, cover: p.cover, orientation: p.orientation }));
    const merged = [...remote, ...additions].sort(byYearDesc);
    return typeof opts.limit === 'number' ? merged.slice(0, opts.limit) : merged;
  }

  let list = localProjects.filter((p) => (opts.featured ? p.featured : true)).sort(byYearDesc);
  if (typeof opts.limit === 'number') list = list.slice(0, opts.limit);
  return list.map((p) => ({
    _id: p.slug,
    title: pick(p.title, lang),
    slug: p.slug,
    location: pick(p.location, lang),
    year: p.year,
    cover: p.cover,
    orientation: p.orientation,
  }));
}

export async function getProject(slug: string, lang: string): Promise<ProjectDetail | null> {
  if (isSanityConfigured) {
    const remote = await fetchProject(slug, lang);
    if (remote) return remote;
    if (!uploadedProjects.some((p) => p.slug === slug)) return null;
  }

  const p = localProjects.find((x) => x.slug === slug);
  if (!p) return null;
  return {
    _id: p.slug,
    title: pick(p.title, lang),
    slug: p.slug,
    year: p.year,
    location: pick(p.location, lang),
    typology: pick(p.typology, lang),
    area: p.area,
    client: p.client,
    photographer: p.photographer,
    description: pick(p.description, lang),
    cover: p.cover,
    gallery: p.gallery,
  };
}

export async function getProjectNav(lang: string): Promise<{ slug: string; title: string }[]> {
  if (isSanityConfigured) {
    return (await getProjects(lang)).map(({ slug, title }) => ({ slug, title }));
  }
  return localProjects
    .slice()
    .sort(byYearDesc)
    .map((p) => ({ slug: p.slug, title: pick(p.title, lang) }));
}

export { img };
