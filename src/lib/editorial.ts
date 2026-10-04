import { createHash } from 'node:crypto';
import manifest from '../data/editorialContent.json';
import type { Lang } from '../i18n/ui';

export interface EditorialContent {
  id: string; kind: 'guides' | 'services'; lang: Lang; slug: string; topic: string;
  title: string; description: string; h1: string; intent: string; introduction: string;
  sections: { heading: string; paragraphs: string[]; source_urls: string[] }[];
  related_links: { url: string; anchor: string }[];
  source_urls: string[]; facts: { claim: string; source_url: string; quote: string }[];
  image: string; generator: string;
}
export interface EditorialEntry {
  content: EditorialContent;
  content_hash: string;
  approval: { reviewer: string; at: string; content_hash: string; facts_confirmed: boolean; service_scope_confirmed: boolean };
  publication: { status: 'READY' };
}
function stable(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stable).join(',')}]`;
  if (value !== null && typeof value === 'object') return `{${Object.keys(value).sort().map(k => `${JSON.stringify(k)}:${stable((value as Record<string, unknown>)[k])}`).join(',')}}`;
  return JSON.stringify(value);
}
export function editorialEntries(): EditorialEntry[] {
  const entries = manifest as EditorialEntry[];
  const paths = new Set<string>();
  for (const entry of entries) {
    const c = entry.content;
    const hash = createHash('sha256').update(stable(c)).digest('hex');
    const path = `/${c.lang}/${c.kind}/${c.slug}/`;
    if (!['en','tr'].includes(c.lang) || !['guides','services'].includes(c.kind) || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(c.slug)
      || paths.has(path) || entry.publication.status !== 'READY' || !entry.approval.reviewer?.trim()
      || !entry.approval.facts_confirmed || (c.kind === 'services' && !entry.approval.service_scope_confirmed)
      || c.sections.length < 3 || new Set(c.source_urls).size < 2 || !c.h1.trim() || c.description.length < 70
      || [c.introduction,...c.sections.flatMap(s => s.paragraphs)].join(' ').split(/\s+/).length < 200
      || hash !== entry.content_hash || hash !== entry.approval.content_hash) throw new Error(`Unapproved or invalid editorial entry: ${c.id}`);
    paths.add(path);
  }
  for (const entry of entries) {
    const c = entry.content;
    if (!entries.some(other => other.content.slug === c.slug && other.content.kind === c.kind && other.content.lang !== c.lang)) throw new Error(`Missing approved language counterpart: ${c.id}`);
  }
  return entries;
}
export function editorialRoutes(kind: EditorialContent['kind'], lang: Lang) {
  return editorialEntries().filter(e => e.content.kind === kind && e.content.lang === lang).map(entry => ({ params: {slug: entry.content.slug}, props: {entry} }));
}
export function editorialPaths(): string[] {
  const entries = editorialEntries();
  return ['en','tr'].flatMap(lang => ['guides','services'].flatMap(kind => {
    const items = entries.filter(e => e.content.lang === lang && e.content.kind === kind);
    return items.length ? [`/${lang}/${kind}/`, ...items.map(e => `/${lang}/${kind}/${e.content.slug}/`)] : [];
  }));
}
