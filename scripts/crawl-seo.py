"""Local/read-only SEO crawler. Python standard library only; SQLite upserts by URL.

Run: python scripts/crawl-seo.py --base http://127.0.0.1:4322
The crawler never submits forms, executes page JavaScript or follows external hosts.
"""
import argparse
from collections import Counter, deque
from contextlib import closing
from datetime import datetime, timezone
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ''; self.description = ''; self.canonical = ''; self.robots = []
        self.links = []; self.images = []; self.headings = []; self.schema = []
        self.ids = set(); self.text = []; self.main = False; self.ignore = 0
        self.capture = None; self.buffer = []; self.schema_errors = 0
        self.link_details = []; self.anchor = None; self.regions = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ('main', 'nav', 'header', 'footer'): self.regions.append(tag)
        if a.get('id'): self.ids.add(a['id'])
        if tag == 'main': self.main = True
        if tag in ('script', 'style', 'nav', 'footer', 'header'): self.ignore += 1
        if tag == 'title' or re.fullmatch(r'h[1-6]', tag):
            self.capture = tag; self.buffer = []
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.capture = 'jsonld'; self.buffer = []
        if tag == 'meta':
            name = a.get('name', '').lower()
            if name == 'description': self.description = a.get('content', '')
            if name in ('robots', 'googlebot'): self.robots.append(a.get('content', ''))
        if tag == 'link' and 'canonical' in a.get('rel', '').split(): self.canonical = a.get('href', '')
        if tag == 'a' and a.get('href'):
            self.links.append(a['href'])
            context = 'language' if 'data-locale' in a else 'navigation' if any(r in self.regions for r in ['nav','header']) else 'footer' if 'footer' in self.regions else 'content' if self.main else 'other'
            classes = a.get('class', '').split()
            if 'detail__next-link' in classes: context = 'sequence'
            elif 'detail__back' in classes: context = 'hierarchy'
            self.anchor = {'href': a['href'], 'context': context, 'parts': []}
        if tag == 'img': self.images.append(a)

    def handle_endtag(self, tag):
        if tag == 'a' and self.anchor is not None:
            self.link_details.append({'href': self.anchor['href'], 'anchor': re.sub(r'\s+', ' ', ''.join(self.anchor['parts'])).strip(), 'context': self.anchor['context']})
            self.anchor = None
        if tag in ('main', 'nav', 'header', 'footer') and tag in self.regions: self.regions.remove(tag)
        if self.capture == tag or (tag == 'script' and self.capture == 'jsonld'):
            value = ''.join(self.buffer).strip()
            if self.capture == 'title': self.title = value
            elif self.capture == 'jsonld':
                try: self.schema.append(json.loads(value))
                except (ValueError, TypeError): self.schema_errors += 1
            else: self.headings.append({'level': int(tag[1]), 'text': value})
            self.capture = None; self.buffer = []
        if tag in ('script', 'style', 'nav', 'footer', 'header'): self.ignore = max(0, self.ignore - 1)
        if tag == 'main': self.main = False

    def handle_data(self, data):
        if self.anchor is not None: self.anchor['parts'].append(data)
        if self.capture: self.buffer.append(data)
        if self.main and not self.ignore and data.strip(): self.text.append(data.strip())


def schema_types(value):
    result = set()
    if isinstance(value, dict):
        types = value.get('@type', [])
        result.update([types] if isinstance(types, str) else [t for t in types if isinstance(t, str)] if isinstance(types, list) else [])
        for child in value.values(): result.update(schema_types(child))
    elif isinstance(value, list):
        for child in value: result.update(schema_types(child))
    return result


def crawl(args):
    base = args.base.rstrip('/')
    origin = args.canonical_origin.rstrip('/')
    allowed = {urlsplit(base).netloc, urlsplit(origin).netloc}
    opener = build_opener(NoRedirect())
    now = datetime.now(timezone.utc).isoformat()
    requests = 0

    def local(url):
        u = urlsplit(urljoin(base + '/', url))
        if u.scheme not in ('http', 'https') or u.netloc not in allowed: return None
        return base + urlunsplit(('', '', u.path or '/', u.query, ''))

    def public(url):
        u = urlsplit(url)
        return origin + urlunsplit(('', '', u.path or '/', u.query, ''))

    def fetch(url, head=False):
        nonlocal requests
        current = url; chain = []; started = time.perf_counter(); seen = set()
        for _ in range(11):
            if current in seen: return 0, {}, b'', chain, current, 'redirect_loop', 0
            seen.add(current); requests += 1
            req = Request(current, headers={'User-Agent': 'PusCoSeoAudit/1.0'}, method='HEAD' if head else 'GET')
            try:
                response = opener.open(req, timeout=args.timeout)
            except HTTPError as error: response = error
            except (URLError, TimeoutError, OSError) as error:
                return 0, {}, b'', chain, current, type(error).__name__, round((time.perf_counter()-started)*1000)
            with response:
                status = response.code; headers = dict(response.headers.items())
                if status in (301, 302, 303, 307, 308):
                    destination = local(urljoin(current, response.headers.get('Location', '')))
                    chain.append({'url': public(current), 'status': status, 'location': response.headers.get('Location', '')})
                    if not destination: return status, headers, b'', chain, current, 'external_redirect', 0
                    current = destination; continue
                body = b'' if head else response.read(5_000_001)
                error = 'body_too_large' if len(body) > 5_000_000 else None
                return status, headers, body[:5_000_000], chain, current, error, round((time.perf_counter()-started)*1000)
        return 0, {}, b'', chain, current, 'redirect_limit', 0

    status, _, raw, _, _, error, _ = fetch(base + '/robots.txt')
    robot = RobotFileParser(); robot.parse(raw.decode('utf8', 'replace').splitlines() if status == 200 else [])
    robots_available = status == 200 and not error
    sitemap_urls = set(); sitemap_errors = []; sitemap_seen = set()

    def sitemap(url):
        if url in sitemap_seen: return
        if len(sitemap_seen) >= 10: sitemap_errors.append('Sitemap index limit exceeded'); return
        sitemap_seen.add(url)
        status, _, raw, chain, _, error, _ = fetch(url)
        if status != 200 or error or chain:
            sitemap_errors.append(f'{public(url)}: status={status}, error={error}, redirects={len(chain)}'); return
        try:
            tree = ET.fromstring(raw)
            index = tree.tag.endswith('sitemapindex')
            for loc in tree.findall('.//{*}loc'):
                target = local(loc.text or '')
                if not target: sitemap_errors.append(f'External sitemap URL: {loc.text}'); continue
                if index: sitemap(target)
                else: sitemap_urls.add(target)
        except ET.ParseError: sitemap_errors.append('Malformed sitemap XML')

    sitemap(base + '/sitemap.xml')
    seeds = [base + '/', base + '/en/', base + '/tr/']
    probes = {local(path) for path in args.probe}; probes.discard(None)
    queue = deque(seeds + sorted(sitemap_urls) + sorted(probes)); pages = {}; assets = {}
    while queue:
        url = queue.popleft()
        if url in pages: continue
        if len(pages) >= args.max_pages: raise RuntimeError('Page limit exceeded; audit is incomplete')
        status, headers, raw, chain, final, error, elapsed = fetch(url)
        parser = PageParser(); content_type = next((v for k, v in headers.items() if k.lower() == 'content-type'), '')
        if 'text/html' in content_type: parser.feed(raw.decode('utf8', 'replace'))
        links = sorted({target for href in parser.links if (target := local(urljoin(final, href)))})
        for target in links:
            if target not in pages: queue.append(target)
        directives = ','.join(parser.robots + [v for k, v in headers.items() if k.lower() == 'x-robots-tag']).lower()
        canonical = urljoin(public(final), parser.canonical) if parser.canonical else ''
        blocked = robots_available and not robot.can_fetch('Googlebot', public(url))
        indexable = status == 200 and not chain and not error and 'text/html' in content_type and not blocked and 'noindex' not in directives and 'none' not in re.split(r'[\s,]+', directives)
        main_text = ' '.join(parser.text)
        u = urlsplit(url); section = u.path.strip('/').split('/')
        page_type = 'project' if len(section) == 3 and section[1] == 'projects' and section[2] != 'detail' else section[-1] if len(section) > 1 else 'home'
        if '/projects/detail' in u.path: page_type = 'legacy'
        metrics = {'response_ms': elapsed, 'html_bytes': len(raw), 'lighthouse': None}
        pages[url] = {'url': public(url), 'status': status, 'final_url': public(final), 'error': error, 'redirect_chain': chain,
            'title': parser.title, 'description': parser.description, 'h1': [h['text'] for h in parser.headings if h['level'] == 1],
            'h2': [h['text'] for h in parser.headings if h['level'] == 2], 'headings': parser.headings,
            'canonical': canonical, 'robots': directives, 'robots_blocked': blocked, 'indexable': indexable,
            'sitemap': url in sitemap_urls, 'page_type': page_type, 'primary_topic': (parser.headings[0]['text'] if parser.headings else parser.title),
            'search_intent': 'project portfolio' if page_type == 'project' else 'contact/navigation' if page_type == 'contact' else 'studio/portfolio information',
            'main_text': main_text, 'word_count': len(main_text.split()), 'content_hash': hashlib.sha256(main_text.encode()).hexdigest(),
            'schema_types': sorted(schema_types(parser.schema)), 'schema_errors': parser.schema_errors,
            'images': parser.images, 'links': [public(link) for link in links],
            'link_details': [{'url': public(target), 'anchor': link['anchor'], 'context': link['context']} for link in parser.link_details if (target := local(urljoin(final, link['href'])))], 'depth': None,
            'internal_link_count': len(links), 'inbound_link_count': 0, 'performance': metrics, 'updated_at': now,
            'title_quality': 'missing' if not parser.title else 'review' if not 10 <= len(parser.title) <= 70 else 'present',
            'meta_quality': 'missing' if not parser.description else 'review' if not 70 <= len(parser.description) <= 170 else 'present',
            'content_completeness': 'review' if len(main_text.split()) < (70 if page_type == 'project' else 30) else 'present'}
        for image in parser.images:
            image['resolved_src'] = urljoin(public(final), image.get('src', ''))
            candidates = [image.get('src', '')] + [item.strip().split()[0] for item in image.get('srcset', '').split(',') if item.strip()]
            image['resolved_candidates'] = [urljoin(public(final), src) for src in candidates if src]
            for src in candidates:
                target = local(urljoin(final, src)) if src else None
                if target and target not in assets:
                    astatus, _, _, achain, _, aerror, _ = fetch(target, head=True)
                    assets[target] = {'url': public(target), 'status': astatus, 'redirect_chain': achain, 'error': aerror}

    by_url = {page['url']: page for page in pages.values()}
    inbound = {url: set() for url in by_url}
    for page in by_url.values():
        if not page['indexable']: continue
        for link in page['links']:
            if link in inbound and link != page['url']: inbound[link].add(page['url'])
    depth_queue = deque([(origin + '/en/', 0), (origin + '/tr/', 0)])
    while depth_queue:
        url, depth = depth_queue.popleft(); page = by_url.get(url)
        if not page or (page['depth'] is not None and page['depth'] <= depth): continue
        page['depth'] = depth
        depth_queue.extend((link, depth+1) for link in page['links'])
    for url, page in by_url.items(): page['inbound_link_count'] = len(inbound[url])
    indexable = [p for p in by_url.values() if p['indexable']]
    duplicates = {key: Counter(p[key] for p in indexable if p[key]) for key in ['title', 'description', 'content_hash']}
    tasks = []

    def task(page, priority, code, message):
        tasks.append({'id': hashlib.sha256((page['url']+'|'+code).encode()).hexdigest(), 'url': page['url'], 'priority': priority, 'code': code, 'message': message})

    for page in by_url.values():
        if page['sitemap'] and (not page['indexable'] or page['canonical'] != page['url']): task(page, 'HIGH', 'invalid_sitemap_entry', 'Sitemap URL must be canonical, indexable and return 200 without redirects.')
        if not page['indexable']: continue
        if not page['canonical']: task(page, 'HIGH', 'missing_canonical', 'Add a canonical URL.')
        elif page['canonical'] != page['url']: task(page, 'HIGH', 'canonical_mismatch', 'Normalize canonical and internal URLs.')
        if not page['sitemap']: task(page, 'HIGH', 'missing_sitemap', 'Include this indexable page in the sitemap.')
        if page['inbound_link_count'] == 0: task(page, 'HIGH', 'orphan', 'Add a relevant inbound internal link.')
        elif page['inbound_link_count'] < 2: task(page, 'MEDIUM', 'weak_inbound_links', 'Review contextual inbound links.')
        if not page['title']: task(page, 'HIGH', 'missing_title', 'Add a descriptive title.')
        elif duplicates['title'][page['title']] > 1: task(page, 'HIGH', 'duplicate_title', 'Use a unique page title.')
        if page['meta_quality'] != 'present' or duplicates['description'][page['description']] > 1: task(page, 'MEDIUM', 'meta_quality', 'Review missing, duplicate or unusually short/long meta description.')
        if len(page['h1']) != 1 or not page['h1'][0]: task(page, 'HIGH', 'h1', 'Use one meaningful H1.')
        if not page['schema_types'] or page['schema_errors']: task(page, 'MEDIUM', 'schema', 'Review missing or malformed JSON-LD.')
        if page['content_completeness'] == 'review': task(page, 'MEDIUM', 'content_review', 'Review actual content depth; word count is only a heuristic, not a ranking factor.')
        if duplicates['content_hash'][page['content_hash']] > 1: task(page, 'MEDIUM', 'duplicate_content', 'Review duplicate main text.')
        previous = 0
        for heading in page['headings']:
            if previous and heading['level'] > previous + 1:
                task(page, 'LOW', 'heading_order', 'Review a skipped heading level.'); break
            previous = heading['level']
        for link in page['links']:
            dest = by_url.get(link)
            if not dest or dest['status'] >= 400 or dest['error']:
                task(page, 'HIGH', 'broken_link:'+link, 'Broken internal link: '+link)
            elif dest['redirect_chain']: task(page, 'LOW', 'redirect_link:'+link, 'Link directly to the canonical destination: '+link)
        for image in page['images']:
            src = image.get('src', '')
            if 'alt' not in image: task(page, 'MEDIUM', 'image_alt:'+src, 'Image is missing alt; decorative empty alt is allowed.')
            if not str(image.get('width', '')).isdigit() or not str(image.get('height', '')).isdigit(): task(page, 'LOW', 'image_dimensions:'+src, 'Reserve image space using width and height.')
            for candidate in image['resolved_candidates']:
                asset = assets.get(local(candidate))
                if asset and (asset['status'] >= 400 or asset['error']): task(page, 'HIGH', 'broken_image:'+src, 'Image request failed: '+candidate)

    performance_paths = sorted(Path(args.performance_dir).glob('*.json')) if args.performance_dir else []
    for file in performance_paths:
        report = json.loads(file.read_text(encoding='utf8'))
        if 'audits' not in report: continue
        target = local(report.get('requestedUrl', report.get('finalUrl', '')))
        page = pages.get(target)
        if not page: continue
        metrics = {name: report.get('categories', {}).get(name, {}).get('score') for name in ['performance', 'accessibility', 'best-practices', 'seo']}
        metrics.update({name: report.get('audits', {}).get(name, {}).get('numericValue') for name in ['first-contentful-paint', 'largest-contentful-paint', 'cumulative-layout-shift', 'total-blocking-time', 'speed-index']})
        metrics['report'] = file.name; metrics['lighthouse_version'] = report.get('lighthouseVersion'); metrics['fetch_time'] = report.get('fetchTime')
        if report.get('runtimeError'):
            metrics['error'] = report['runtimeError']; task(page, 'MEDIUM', 'performance_unavailable', 'Lighthouse run failed; retry the measurement.')
        elif page['indexable']:
            if metrics['seo'] is not None and metrics['seo'] < .95: task(page, 'HIGH', 'lighthouse_seo', 'Lighthouse SEO is below 95; inspect failed audits.')
            if metrics['performance'] is not None and metrics['performance'] < .9: task(page, 'MEDIUM', 'performance', 'Review Lighthouse mobile performance. Local lab values are not field Core Web Vitals.')
            if (metrics['cumulative-layout-shift'] or 0) > .1: task(page, 'MEDIUM', 'layout_shift', 'Review measured layout shifts.')
        page['performance']['lighthouse'] = metrics
    tasks = list({t['id']: t for t in tasks}.values())
    for page in by_url.values():
        counts = Counter(t['priority'] for t in tasks if t['url'] == page['url'])
        page['seo_health_score'] = max(0, 100 - 20*counts['HIGH'] - 8*counts['MEDIUM'] - 2*counts['LOW']) if page['indexable'] else None
    result = {'base': base, 'canonical_origin': origin, 'updated_at': now, 'robots_available': robots_available,
        'sitemap_errors': sitemap_errors, 'summary': {'pages': len(pages), 'indexable': len(indexable), 'sitemap_urls': len(sitemap_urls), 'assets_checked': len(assets),
        'requests': requests, 'priorities': dict(Counter(t['priority'] for t in tasks)), 'orphan_pages': sum(p['inbound_link_count'] == 0 for p in indexable)},
        'pages': sorted(by_url.values(), key=lambda p: p['url']), 'assets': sorted(assets.values(), key=lambda a: a['url']), 'tasks': sorted(tasks, key=lambda t: (['HIGH','MEDIUM','LOW'].index(t['priority']), t['url'], t['code']))}
    if not robots_available or sitemap_errors: raise RuntimeError('robots/sitemap audit failed: '+json.dumps(sitemap_errors))
    db = Path(args.db); db.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db)) as con, con:
        con.executescript('''CREATE TABLE IF NOT EXISTS pages (
            url TEXT PRIMARY KEY, page_type TEXT, primary_topic TEXT, search_intent TEXT,
            title_quality TEXT, meta_quality TEXT, content_completeness TEXT,
            internal_link_count INTEGER, inbound_link_count INTEGER, indexable INTEGER,
            schema_available INTEGER, performance_json TEXT, updated_at TEXT, seo_health_score INTEGER, data_json TEXT);
            CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, url TEXT, priority TEXT, code TEXT, message TEXT);
            CREATE TABLE IF NOT EXISTS audit_state (origin TEXT PRIMARY KEY, updated_at TEXT, summary_json TEXT);''')
        # Replace only this site's current snapshot atomically; no duplicate historical rows.
        con.execute('DELETE FROM tasks WHERE url LIKE ?', (origin+'/%',))
        con.execute('DELETE FROM pages WHERE url LIKE ?', (origin+'/%',))
        for p in result['pages']:
            con.execute('INSERT INTO pages VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (p['url'],p['page_type'],p['primary_topic'],p['search_intent'],p['title_quality'],p['meta_quality'],p['content_completeness'],p['internal_link_count'],p['inbound_link_count'],p['indexable'],bool(p['schema_types']) and not p['schema_errors'],json.dumps(p['performance']),now,p['seo_health_score'],json.dumps(p,ensure_ascii=False)))
        for t in tasks: con.execute('INSERT INTO tasks VALUES (?,?,?,?,?)', (t['id'],t['url'],t['priority'],t['code'],t['message']))
        con.execute('INSERT OR REPLACE INTO audit_state VALUES (?,?,?)', (origin,now,json.dumps(result['summary'])))
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps(result['summary'], ensure_ascii=False))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='http://127.0.0.1:4322')
    parser.add_argument('--canonical-origin', default='https://pusnco.com')
    parser.add_argument('--db', default='.seo/opportunities.sqlite')
    parser.add_argument('--output', default='.seo/crawl.json')
    parser.add_argument('--performance-dir')
    parser.add_argument('--timeout', type=float, default=15)
    parser.add_argument('--max-pages', type=int, default=250)
    parser.add_argument('--probe', action='append', default=[])
    parser.add_argument('--fail-on-high', action='store_true')
    args = parser.parse_args()
    result = crawl(args)
    if args.fail_on_high and any(t['priority'] == 'HIGH' for t in result['tasks']): raise SystemExit(1)
