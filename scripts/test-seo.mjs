import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { join, resolve } from 'node:path';
import assert from 'node:assert/strict';

const dist = resolve(process.argv[2] || 'dist');
const preview = process.argv.includes('--preview');
const read = path => readFileSync(join(dist, path), 'utf8');
const site = 'https://pusnco.com';
const sitemap = read('sitemap.xml');
const locs = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m => m[1]);
assert.equal(locs.length, new Set(locs).size, 'Duplicate sitemap URLs');
assert.ok(!locs.some(url => /detail|404|admin|api|draft|preview|\?/.test(url)), 'Private/legacy URL in sitemap');
assert.ok(read('index.html').includes('content="noindex"'), 'Root noindex must remain');
assert.ok(read('404.html').includes('noindex'), '404 must be noindex');
if (preview) {
  assert.equal(locs.length, 0, 'Preview sitemap must be empty');
  assert.ok(read('robots.txt').includes('Disallow: /'), 'Preview robots must block crawling');
} else {
  assert.ok(read('robots.txt').includes(`Sitemap: ${site}/sitemap.xml`));
}
const paths = [];
for (const lang of ['en', 'tr']) {
  for (const section of ['', 'projects/', 'studio/', 'contact/']) paths.push(`/${lang}/${section}`);
  for (const entry of readdirSync(join(dist, lang, 'projects'), {withFileTypes: true})) {
    if (entry.isDirectory() && entry.name !== 'detail') paths.push(`/${lang}/projects/${entry.name}/`);
  }
  assert.ok(read(`${lang}/projects/detail/index.html`).includes('noindex'), 'Legacy details must be noindex');
  for (const section of ['guides', 'services']) {
    const root = join(dist, lang, section);
    if (!existsSync(root)) continue;
    if (existsSync(join(root, 'index.html'))) paths.push(`/${lang}/${section}/`);
    for (const entry of readdirSync(root, {withFileTypes:true})) {
      if (entry.isDirectory() && existsSync(join(root, entry.name, 'index.html'))) paths.push(`/${lang}/${section}/${entry.name}/`);
    }
  }
}
const titles = [], descriptions = [];
let imageCount = 0;
for (const path of paths) {
  const html = read(`${path.slice(1)}index.html`);
  const title = html.match(/<title>([^<]+)<\/title>/)?.[1];
  const description = html.match(/name="description" content="([^"]+)"/)?.[1];
  assert.ok(title && description, `${path}: missing title/description`);
  titles.push(title); descriptions.push(description);
  assert.equal((html.match(/<h1\b/g) || []).length, 1, `${path}: H1 count`);
  assert.ok(!/<h1[^>]*>\s*(?:&nbsp;)?\s*<\/h1>/.test(html), `${path}: empty H1`);
  assert.ok(html.includes(`rel="canonical" href="${site}${path}"`), `${path}: canonical`);
  assert.ok(html.includes(preview ? 'content="noindex, nofollow"' : 'content="index, follow"'), `${path}: robots`);
  for (const lang of ['en', 'tr']) assert.ok(html.includes(`hreflang="${lang}" href="${site}${path.replace(/^\/(en|tr)\//, `/${lang}/`)}"`), `${path}: hreflang`);
  assert.ok(html.includes('property="og:image"') && html.includes('name="twitter:card"'));
  const fonts = [...html.matchAll(/<link\b[^>]*rel="preload"[^>]*href="([^"]+)"[^>]*as="font"/g)];
  assert.equal(fonts.length, 3, `${path}: critical font preload coverage`);
  for (const font of fonts) assert.ok(existsSync(join(dist, font[1].slice(1))), `${path}: missing preloaded font`);
  if (/^\/(en|tr)\/projects\/$/.test(path)) {
    const firstImage = html.match(/<img\b[^>]+>/)?.[0] || '';
    assert.ok(firstImage.includes('loading="eager"') && firstImage.includes('fetchpriority="high"'), `${path}: first project image must load promptly`);
  }
  const graph = [...html.matchAll(/<script[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/g)].map(m => JSON.parse(m[1]));
  assert.ok(graph.some(g => g['@graph'].some(n => n['@type'] === 'Organization')), `${path}: Organization`);
  if (/\/projects\/[^/]+\/$/.test(path)) {
    assert.ok(graph.some(g => g['@graph'].some(n => n['@type'] === 'CreativeWork')));
    assert.ok(graph.some(g => g['@graph'].some(n => n['@type'] === 'BreadcrumbList')));
    assert.ok((html.match(/class="detail__desc"[^>]*>([^<]+)/)?.[1] || '').length > 100, `${path}: static project description`);
    assert.ok(!html.includes('projects/detail/?id='), `${path}: legacy internal project link`);
  }
  if (/\/(guides|services)\/[^/]+\/$/.test(path)) {
    assert.ok(graph.some(g => g['@graph'].some(n => ['Article','Service'].includes(n['@type']))), `${path}: editorial schema`);
    assert.ok(graph.some(g => g['@graph'].some(n => n['@type'] === 'BreadcrumbList')), `${path}: editorial breadcrumb`);
    assert.ok(/data-content-hash="[a-f0-9]{64}"/.test(html), `${path}: approved content identity`);
  }
  for (const match of html.matchAll(/<img\b([^>]+)>/g)) {
    const attrs = match[1]; imageCount++;
    assert.ok(/\balt(?:="[^"]*"|(?=\s|$))/.test(attrs), `${path}: missing alt`);
    assert.ok(/\bwidth="\d+"/.test(attrs) && /\bheight="\d+"/.test(attrs), `${path}: missing image dimensions`);
    const src = attrs.match(/\bsrc="([^"]+)"/)?.[1];
    if (src?.startsWith('/')) assert.ok(existsSync(join(dist, src.slice(1))), `${path}: missing image ${src}`);
  }
  for (const match of html.matchAll(/<a\b[^>]*href="(\/[^"?#]*)[^\"]*"/g)) {
    const target = match[1];
    if (target === '/') continue;
    assert.ok(existsSync(join(dist, target.slice(1), 'index.html')) || existsSync(join(dist, target.slice(1))), `${path}: broken internal link ${target}`);
  }
}
assert.equal(titles.length, new Set(titles).size, 'Duplicate public titles');
assert.equal(descriptions.length, new Set(descriptions).size, 'Duplicate public descriptions');
assert.ok(paths.length >= 8);
if (!preview) assert.deepEqual([...locs].sort(), paths.map(path => `${site}${path}`).sort(), 'Sitemap must cover every public content route exactly');
console.log(`PASS: ${paths.length} content pages, ${imageCount} image tags, metadata, schema, internal links, ${preview ? 'preview noindex' : 'production sitemap coverage'}.`);
