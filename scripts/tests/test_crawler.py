"""Regression tests against a small local HTTP fixture; no external network."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sqlite3
import tempfile
import threading
from types import SimpleNamespace
import unittest

spec = importlib.util.spec_from_file_location('crawler', Path(__file__).parents[1]/'crawl-seo.py')
crawler = importlib.util.module_from_spec(spec); spec.loader.exec_module(crawler)
ORIGIN = 'https://pusnco.com'


def page(path, links='', extra='', noindex=False, title='Architecture fixture'):
    return f'''<html><head><title>{title}</title><meta name="description" content="A sufficiently detailed description of this architecture fixture for the crawler regression tests and quality heuristics.">
    <link rel="canonical" href="{ORIGIN}{path}"><meta name="robots" content="{'noindex' if noindex else 'index, follow'}"></head>
    <body><nav>{links}</nav><main><h1>Fixture</h1><h2>Overview</h2><p>{'Meaningful fixture content. '*40}</p>{extra}</main>
    <script type="application/ld+json">{{"@type":"WebPage"}}</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def do_GET(self):
        status = 200; kind = 'text/html'; location = None
        if self.path == '/robots.txt': kind = 'text/plain'; body = 'User-agent: *\nDisallow: /admin/\n'
        elif self.path == '/sitemap.xml':
            kind = 'application/xml'; body = '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{ORIGIN}{p}</loc></url>' for p in ['/en/','/tr/','/en/orphan/','/admin/','/en/noindex/'])+'</urlset>'
        elif self.path == '/': body = page('/', noindex=True)
        elif self.path == '/en/': body = page('/en/', '<a href="/tr/">TR</a><a href="/missing/">Broken</a><a href="/old/">Old</a>', '<img src="/missing.webp"><script type="application/ld+json">invalid</script>')
        elif self.path == '/tr/': body = page('/tr/', '<a href="/en/">EN</a>', title='Turkish architecture fixture')
        elif self.path == '/en/orphan/': body = page('/en/orphan/')
        elif self.path == '/admin/': body = page('/admin/', title='Admin fixture')
        elif self.path == '/en/noindex/': body = page('/en/noindex/', noindex=True, title='Noindex fixture')
        elif self.path == '/old/': status = 301; location = '/tr/'; body = ''
        else: status = 404; body = page(self.path, noindex=True)
        self.send_response(status); self.send_header('Content-Type', kind)
        if location: self.send_header('Location', location)
        self.end_headers()
        if self.command != 'HEAD': self.wfile.write(body.encode())
    do_HEAD = do_GET


class CrawlerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True); cls.thread.start()
    @classmethod
    def tearDownClass(cls): cls.server.shutdown(); cls.server.server_close(); cls.thread.join()

    def test_findings_and_idempotent_database(self):
        with tempfile.TemporaryDirectory() as directory:
            args = SimpleNamespace(base=f'http://127.0.0.1:{self.server.server_port}', canonical_origin=ORIGIN,
                timeout=2, max_pages=30, probe=[], db=str(Path(directory)/'seo.sqlite'), output=str(Path(directory)/'crawl.json'), performance_dir=None)
            with contextlib.redirect_stdout(io.StringIO()): first = crawler.crawl(args)
            codes = {t['code'] for t in first['tasks']}
            for expected in ['orphan','duplicate_title','schema','image_alt:/missing.webp','image_dimensions:/missing.webp','broken_image:/missing.webp','broken_link:'+ORIGIN+'/missing/','invalid_sitemap_entry']:
                self.assertIn(expected, codes)
            pages = {p['url']:p for p in first['pages']}
            self.assertFalse(pages[ORIGIN+'/admin/']['indexable'])
            self.assertFalse(pages[ORIGIN+'/en/noindex/']['indexable'])
            self.assertEqual(pages[ORIGIN+'/old/']['redirect_chain'][0]['status'], 301)
            self.assertEqual(pages[ORIGIN+'/old/']['final_url'], ORIGIN+'/tr/')
            self.assertEqual(pages[ORIGIN+'/en/orphan/']['depth'], None)
            with contextlib.redirect_stdout(io.StringIO()): second = crawler.crawl(args)
            self.assertEqual(first['summary'], second['summary'])
            with contextlib.closing(sqlite3.connect(args.db)) as con:
                self.assertEqual(con.execute('SELECT count(*) FROM pages').fetchone()[0], len(second['pages']))
                self.assertEqual(con.execute('SELECT count(*) FROM tasks').fetchone()[0], len(second['tasks']))
                self.assertEqual(con.execute('SELECT count(*) FROM audit_state').fetchone()[0], 1)
            self.assertEqual(json.loads(Path(args.output).read_text())['summary'], second['summary'])

    def test_empty_decorative_alt_and_nested_schema(self):
        parser = crawler.PageParser()
        parser.feed('<main><h1>Real <em>heading</em></h1><p>Visible</p><img src="/x.webp" alt="" width="20" height="20"></main><script type="application/ld+json">{"@graph":[{"@type":"CreativeWork","image":{"@type":"ImageObject"}}]}</script>')
        self.assertEqual(parser.headings[0]['text'], 'Real heading')
        self.assertIn('alt', parser.images[0])
        self.assertEqual(crawler.schema_types(parser.schema), {'CreativeWork','ImageObject'})
        self.assertNotIn('@graph', ' '.join(parser.text))
        self.assertEqual(crawler.schema_types({'@type':None}), set())

    def test_link_context_and_main_text(self):
        parser = crawler.PageParser()
        parser.feed('<header><nav><a href="/en/">Home</a></nav></header><main><p>Real topic text</p><a href="/en/project/">Useful <em>example</em></a><a class="detail__next-link" href="/en/next/">Next project</a><a class="detail__back" href="/en/projects/">All projects</a></main><footer><a href="/contact/">Contact</a></footer>')
        self.assertEqual([link['context'] for link in parser.link_details],['navigation','content','sequence','hierarchy','footer'])
        self.assertEqual(parser.link_details[1]['anchor'],'Useful example')
        self.assertNotIn('Home',' '.join(parser.text))
        self.assertNotIn('Contact',' '.join(parser.text))

    def test_lighthouse_metrics_import(self):
        with tempfile.TemporaryDirectory() as directory:
            report = {'requestedUrl':f'http://127.0.0.1:{self.server.server_port}/tr/', 'lighthouseVersion':'fixture',
                'categories':{'performance':{'score':.6},'seo':{'score':.94}},
                'audits':{'cumulative-layout-shift':{'numericValue':.2},'largest-contentful-paint':{'numericValue':5000}}}
            Path(directory,'lighthouse.json').write_text(json.dumps(report))
            args = SimpleNamespace(base=f'http://127.0.0.1:{self.server.server_port}', canonical_origin=ORIGIN,
                timeout=2, max_pages=30, probe=[], db=str(Path(directory)/'seo.sqlite'), output=str(Path(directory)/'crawl.json'), performance_dir=directory)
            with contextlib.redirect_stdout(io.StringIO()): result = crawler.crawl(args)
            page = next(p for p in result['pages'] if p['url'] == ORIGIN+'/tr/')
            self.assertEqual(page['performance']['lighthouse']['largest-contentful-paint'], 5000)
            codes = {t['code'] for t in result['tasks'] if t['url'] == page['url']}
            self.assertTrue({'lighthouse_seo','performance','layout_shift'}.issubset(codes))


if __name__ == '__main__': unittest.main()
