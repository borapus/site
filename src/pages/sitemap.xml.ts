import { getProjects } from '../lib/projects';
import { SITE, isPreview } from '../lib/seo';
export async function GET() {
  const slugs = (await getProjects('en')).map(p => p.slug);
  const paths = ['', 'projects/', 'studio/', 'contact/', ...slugs.map(s => `projects/${s}/`)];
  const urls = isPreview ? [] : ['en', 'tr'].flatMap(lang => paths.map(path => {
    const alternate = ['en', 'tr'].map(l => `<xhtml:link rel="alternate" hreflang="${l}" href="${SITE}/${l}/${path}"/>`).join('');
    return `<url><loc>${SITE}/${lang}/${path}</loc>${alternate}<xhtml:link rel="alternate" hreflang="x-default" href="${SITE}/en/${path}"/></url>`;
  }));
  return new Response(`<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">${urls.join('')}</urlset>`, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
}
