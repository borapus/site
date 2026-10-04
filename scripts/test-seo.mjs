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
  assert.equal(locs.length, 36, 'Expected 8 main pages + 28 project pages');
  assert.ok(read('robots.txt').includes(`Sitemap: ${site}/sitemap.xml`));
}
const paths = [];
for (const lang of ['en', 'tr']) {
  for (const section of ['', 'projects/', 'studio/', 'contact/']) paths.push(`/${lang}/${section}`);
  for (const entry of readdirSync(join(dist, lang, 'projects'), {withFileTypes: true})) {
    if (entry.isDirectory() && entry.name !== 'detail') paths.push(`/${lang}/projects/${entry.name}/`);
  }
  assert.ok(read(`${lang}/projects/detail/index.html`).includes('noindex'), 'Legacy details must be noindex');
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
  const graph = [...html.matchAll(/<script[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/g)].map(m => JSON.parse(m[1]));
  assert.ok(graph.some(g => g['@graph'].some(n => n['@type'] === 'Organization')), `${path}: Organization`);
  if (/\/projects\/[^/]+\/$/.test(path)) {
    assert.ok(graph.some(g => g['@graph'].some(n => n['@type'] === 'CreativeWork')));
    assert.ok(graph.some(g => g['@graph'].some(n => n['@type'] === 'BreadcrumbList')));
    assert.ok((html.match(/class="detail__desc"[^>]*>([^<]+)/)?.[1] || '').length > 100, `${path}: static project description`);
    assert.ok(!html.includes('projects/detail/?id='), `${path}: legacy internal project link`);
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
assert.equal(paths.length, 36);
console.log(`PASS: ${paths.length} content pages, ${imageCount} image tags, metadata, schema, internal links, ${preview ? 'preview noindex' : 'production sitemap coverage'}.`);
