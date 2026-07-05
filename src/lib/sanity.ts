import { createClient, type SanityClient } from '@sanity/client';

const projectId = import.meta.env.PUBLIC_SANITY_PROJECT_ID as string | undefined;
const dataset = (import.meta.env.PUBLIC_SANITY_DATASET as string) || 'production';

export const isSanityConfigured = Boolean(projectId);

export const sanity: SanityClient | null = projectId
  ? createClient({
      projectId,
      dataset,
      apiVersion: '2024-01-01',
      useCdn: true,
      perspective: 'published',
    })
  : null;

export type ProjectCard = {
  _id: string;
  title: string;
  slug: string;
  location: string;
  year: string;
  cover: string | null;
  orientation: 'portrait' | 'landscape';
};

/**
 * Projeleri Sanity'den client-side (canlı) çeker.
 * Sanity yapılandırılmadıysa boş dizi döner (grid "boş durum"unu korur).
 */
export async function fetchProjects(
  lang: string,
  opts: { limit?: number; featured?: boolean } = {},
): Promise<ProjectCard[]> {
  if (!sanity) return [];
  const { limit, featured } = opts;
  const filter = featured ? ' && featured == true' : '';
  const slice = typeof limit === 'number' ? `[0...${limit}]` : '';
  const query = `*[_type == "project"${filter}] | order(year desc) ${slice}{
    _id,
    "title": coalesce(title[$lang], title.en, "Untitled"),
    "slug": slug.current,
    "location": coalesce(location[$lang], location.en, ""),
    "year": string(coalesce(year, "")),
    "cover": coverImage.asset->url,
    "orientation": coalesce(orientation, "landscape")
  }`;
  return sanity.fetch<ProjectCard[]>(query, { lang });
}

export type ProjectDetail = {
  _id: string;
  title: string;
  slug: string;
  year: string;
  location: string;
  typology: string;
  area: string;
  client: string;
  photographer: string;
  description: string;
  cover: string | null;
  gallery: string[];
};

/** Tek bir projeyi slug ile çeker (detay sayfası). */
export async function fetchProject(slug: string, lang: string): Promise<ProjectDetail | null> {
  if (!sanity) return null;
  const query = `*[_type == "project" && slug.current == $slug][0]{
    _id,
    "title": coalesce(title[$lang], title.en, "Untitled"),
    "slug": slug.current,
    "year": string(coalesce(year, "")),
    "location": coalesce(location[$lang], location.en, ""),
    "typology": coalesce(typology[$lang], typology.en, ""),
    "area": coalesce(area, ""),
    "client": coalesce(client, ""),
    "photographer": coalesce(photographer, ""),
    "description": coalesce(description[$lang], description.en, ""),
    "cover": coverImage.asset->url,
    "gallery": coalesce(gallery[].asset->url, [])
  }`;
  return sanity.fetch<ProjectDetail | null>(query, { slug, lang });
}

/** Sıralı proje listesi (title + slug) — "sonraki proje" navigasyonu için. */
export async function fetchProjectNav(lang: string): Promise<{ slug: string; title: string }[]> {
  if (!sanity) return [];
  const query = `*[_type == "project"] | order(year desc){
    "slug": slug.current,
    "title": coalesce(title[$lang], title.en, "Untitled")
  }`;
  return sanity.fetch(query, { lang });
}

/** Sanity CDN görsel URL'sine boyut/format parametreleri ekler. Yerel yollar aynen döner. */
export function img(url: string | null, w = 1200): string {
  if (!url) return '';
  if (url.startsWith('/')) return url; // yerel görsel (public/) — dokunma
  const sep = url.includes('?') ? '&' : '?';
  return `${url}${sep}w=${w}&auto=format&fit=max`;
}
