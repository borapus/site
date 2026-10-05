import base64
import importlib.util
import json
from pathlib import Path
import socket
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[2]
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
monitor=load('monitor','seo-monitor.py'); dashboard=load('dashboard','seo-dashboard.py'); competitor=load('competitor','competitor-gap.py')


class MonitoringTests(unittest.TestCase):
    def test_changes_and_idempotent_records(self):
        old={'pages':[{'url':'https://pusnco.com/tr/','title':'Old','indexable':True},{'url':'https://pusnco.com/removed/'}]}
        new={'pages':[{'url':'https://pusnco.com/tr/','title':'New','indexable':True},{'url':'https://pusnco.com/en/','title':'Added'}]}
        changes=monitor.changes(new,old)
        self.assertEqual([x['kind'] for x in changes],['added','removed','changed'])
        self.assertEqual(changes[-1]['fields'],['title'])
        self.assertEqual(monitor.changes(new,new),[])
        report={'id':'same-run','mode':'daily','checked_at':'now','changes':changes}
        with sqlite3.connect(':memory:') as con:
            monitor.record(con,new,report); monitor.record(con,new,report)
            self.assertEqual(con.execute('SELECT count(*) FROM monitoring_runs').fetchone()[0],1)
            self.assertEqual(con.execute('SELECT count(*) FROM monitoring_changes').fetchone()[0],3)

    def test_no_fabricated_obsolete_content(self):
        snapshot={'pages':[{'url':'https://pusnco.com/tr/','indexable':True,'content_completeness':'present'}]}
        self.assertEqual(monitor.refresh_recommendations(snapshot,{}),[])


class CompetitorTests(unittest.TestCase):
    def test_private_hosts_and_cross_host_blocked(self):
        with patch.object(socket,'getaddrinfo',return_value=[(2,1,6,'',('127.0.0.1',443))]):
            with self.assertRaises(ValueError): competitor.public_url('https://example.com/')
        with self.assertRaises(ValueError): competitor.public_url('http://example.com/')
        with self.assertRaises(ValueError): competitor.public_url('https://other.com/','example.com')
        with self.assertRaises(ValueError): competitor.public_url('https://user:pass@example.com/')

    def test_metrics_do_not_copy_competitor_text(self):
        taxonomy={'clusters':[{'id':'residential','terms':['housing']}],'themes':[]}
        prose='Unique competitor housing prose should never be retained.'
        data,links=competitor.measure('https://example.com/projects/test/',200,
            '<html><title>Example</title><main><h1>House</h1><p>'+prose+'</p><a href="/about/">About</a></main></html>',taxonomy)
        encoded=json.dumps(data)
        self.assertNotIn(prose,encoded); self.assertNotIn('Example',encoded)
        self.assertEqual(data['topics'],['residential']); self.assertEqual(data['page_type'],'project')
        comparison=competitor.compare({'pages':[{'url':'https://pusnco.com/tr/','indexable':True,'main_text':'Housing'}]}, {'pages':[data]},taxonomy)
        self.assertEqual(comparison['candidate_gaps'],[])


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.directory=Path(self.temp.name)
        self.server=dashboard.ThreadingHTTPServer(('127.0.0.1',0),dashboard.handler(self.directory,'test-password'))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True); self.thread.start()
        self.origin='http://127.0.0.1:'+str(self.server.server_port)
        self.auth='Basic '+base64.b64encode(b'pusnco:test-password').decode()
    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(); self.temp.cleanup()
    def test_auth_noindex_read_only_and_host_validation(self):
        for route in ['/admin/seo/','/api/seo/']:
            with self.assertRaises(HTTPError) as error: urlopen(self.origin+route)
            self.assertEqual(error.exception.code,401)
            self.assertIn('noindex',error.exception.headers['X-Robots-Tag'])
        with urlopen(Request(self.origin+'/admin/seo/',headers={'Authorization':self.auth})) as response:
            self.assertEqual(response.status,200)
            self.assertEqual(response.headers['Cache-Control'],'no-store')
            self.assertIn('noindex',response.read().decode())
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(self.origin+'/api/seo/',headers={'Authorization':self.auth,'Host':'evil.example'}))
        self.assertEqual(error.exception.code,403)
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(self.origin+'/api/seo/',data=b'publish',headers={'Authorization':self.auth}))
        self.assertEqual(error.exception.code,405)
        with urlopen(Request(self.origin+'/api/seo/',headers={'Authorization':self.auth})) as response:
            self.assertEqual(json.load(response)['summary']['indexable'],0)
    def test_filters_and_html_escaping(self):
        data=dashboard.dashboard_data(self.directory)
        data['tasks']=[{'priority':'HIGH','url':'https://pusnco.com/<script>','message':'<script>alert(1)</script>'},
            {'priority':'LOW','url':'https://pusnco.com/tr/','message':'Fine'}]
        result=dashboard.filtered(data,{'priority':['HIGH']})
        self.assertEqual(len(result['tasks']),1)
        html=dashboard.render(result,{'q':['" onfocus="evil']})
        self.assertNotIn('<script>',html); self.assertIn('&lt;script&gt;',html)
        self.assertNotIn('value="" onfocus=',html)


if __name__=='__main__': unittest.main()
