// Birleşik proje veri katmanı.
// Sanity yapılandırılmışsa Sanity'den (canlı) çeker; değilse yerel seed'i kullanır.
import {
  isSanityConfigured,
  fetchProjects,
  fetchProject,
  fetchProjectNav,
  img,
  type ProjectCard,
  type ProjectDetail,
} from './sanity';
import { localProjects } from '../data/projects';

type Loc = { en: string; tr: string };
const pick = (o: Loc, lang: string) => (lang === 'tr' ? o.tr : o.en) || o.en || '';
const byYearDesc = (a: { year: string }, b: { year: string }) =>
  a.year < b.year ? 1 : a.year > b.year ? -1 : 0;

export async function getProjects(
  lang: string,
  opts: { limit?: number; featured?: boolean } = {},
): Promise<ProjectCard[]> {
  if (isSanityConfigured) return fetchProjects(lang, opts);

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
  if (isSanityConfigured) return fetchProject(slug, lang);

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
  if (isSanityConfigured) return fetchProjectNav(lang);
  return localProjects
    .slice()
    .sort(byYearDesc)
    .map((p) => ({ slug: p.slug, title: pick(p.title, lang) }));
}

export { img };
