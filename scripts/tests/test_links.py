"""Tests for link relevance, language boundaries, cycles and review persistence."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

root = Path(__file__).parents[2]
spec = importlib.util.spec_from_file_location('links',root/'scripts/suggest-links.py')
links = importlib.util.module_from_spec(spec); spec.loader.exec_module(links)
TAXONOMY = json.loads((root/'seo/topic-taxonomy.json').read_text(encoding='utf8'))
ORIGIN = 'https://pusnco.com'


def fixture():
    pages = []
    for lang in ['en','tr']:
        slugs = ['gu-house','tk-house','uc-house']
        urls = [f'{ORIGIN}/{lang}/projects/{slug}/' for slug in slugs]
        hub = f'{ORIGIN}/{lang}/projects/'
        pages.append({'url':hub,'status':200,'indexable':True,'canonical':hub,'page_type':'projects','title':'Projects','h1':['Projects'],
            'main_text':'Residential housing portfolio','word_count':100,'links':urls,'link_details':[{'url':url,'anchor':'Project','context':'content'} for url in urls]})
        texts = ['A courtyard house with privacy and a landscape connection. Steel and natural material detail.',
            'An existing building with privacy, forest and landscape views. Steel material detail.',
            'A house balancing privacy and shared living, with landscape, steel material detail.']
        for i,url in enumerate(urls):
            # Real next-project navigation can form a ring; it must not suppress topical proposals.
            next_url = urls[(i+1)%len(urls)]
            pages.append({'url':url,'status':200,'indexable':True,'canonical':url,'page_type':'project','title':slugs[i],'h1':[slugs[i]],
                'main_text':texts[i],'word_count':100,'links':[hub,next_url],
                'link_details':[{'url':hub,'anchor':'All projects','context':'hierarchy'},{'url':next_url,'anchor':'Next project' if lang=='en' else 'Sonraki proje','context':'content'}]})
    return {'canonical_origin':ORIGIN,'updated_at':'fixture','pages':pages}


class LinkTests(unittest.TestCase):
    def test_relevance_language_existing_edges_and_cycles(self):
        snapshot = fixture(); result = links.analyze(snapshot,TAXONOMY)
        self.assertTrue(result['link_suggestions'])
        self.assertEqual({p['language'] for p in result['link_suggestions']},{'en','tr'})
        graph = {}
        existing = {p['url']:set(p['links']) for p in snapshot['pages']}
        counts = {}
        for proposal in result['link_suggestions']:
            source,target = proposal['source_url'],proposal['target_url']
            self.assertNotEqual(source,target)
            self.assertEqual(source.split('/')[3],target.split('/')[3])
            self.assertNotIn(target,existing[source])
            self.assertFalse(links.reachable(graph,target,source))
            graph.setdefault(source,set()).add(target)
            counts[source] = counts.get(source,0)+1
            self.assertLessEqual(counts[source],TAXONOMY['maximum_suggestions_per_page'])
            self.assertTrue(proposal['same_cluster'] or len(proposal['shared_themes'])>=2)
            self.assertTrue(proposal['evidence']['source'] and proposal['evidence']['target'])
            self.assertEqual(proposal['status'],'REVIEW')
        self.assertTrue(result['summary']['cycles_prevented'])

    def test_no_singleton_pillar_no_creation_and_idempotence(self):
        snapshot = fixture()
        singleton = copy.deepcopy(snapshot['pages'][1])
        singleton.update(url=ORIGIN+'/en/projects/hazar-cultural-centre/',canonical=ORIGIN+'/en/projects/hazar-cultural-centre/',main_text='A cultural centre with adaptive reuse.',links=[],link_details=[])
        snapshot['pages'].append(singleton)
        result = links.analyze(snapshot,TAXONOMY)
        culture = next(c for c in result['clusters'] if c['topic']=='culture')
        self.assertEqual(culture['pillar_status'],'SKIPPED_SINGLE_PROJECT')
        self.assertIsNone(culture['pillar_url'])
        self.assertFalse(any(o['topic']=='culture' for o in result['content_opportunities']))
        self.assertEqual(result,links.analyze(snapshot,TAXONOMY))
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory)/'test.sqlite'; output = Path(directory)/'out.json'
            with contextlib.redirect_stdout(io.StringIO()): links.save(result,db,output)
            with contextlib.closing(sqlite3.connect(db)) as con:
                proposal = result['link_suggestions'][0]['id']
                con.execute("UPDATE link_suggestions SET status='REJECTED' WHERE id=?",(proposal,)); con.commit()
            with contextlib.redirect_stdout(io.StringIO()): links.save(links.analyze(snapshot,TAXONOMY),db,output)
            with contextlib.closing(sqlite3.connect(db)) as con:
                self.assertEqual(con.execute('SELECT count(*) FROM link_suggestions').fetchone()[0],len(result['link_suggestions']))
                self.assertEqual(con.execute('SELECT status FROM link_suggestions WHERE id=?',(proposal,)).fetchone()[0],'REJECTED')
                self.assertEqual(con.execute('SELECT count(*) FROM content_opportunities').fetchone()[0],len(result['content_opportunities']))
            exported = json.loads(output.read_text(encoding='utf8'))
            self.assertEqual(next(p for p in exported['link_suggestions'] if p['id']==proposal)['status'],'REJECTED')

    def test_stale_crawl_is_rejected(self):
        snapshot = fixture(); del snapshot['pages'][0]['main_text']
        with self.assertRaises(ValueError): links.analyze(snapshot,TAXONOMY)

    def test_orphan_and_excessive_link_findings(self):
        snapshot = fixture()
        orphan = copy.deepcopy(snapshot['pages'][1])
        orphan.update(url=ORIGIN+'/en/projects/new-house/',canonical=ORIGIN+'/en/projects/new-house/',links=[],link_details=[])
        snapshot['pages'].append(orphan)
        home = copy.deepcopy(snapshot['pages'][0])
        home.update(url=ORIGIN+'/en/',canonical=ORIGIN+'/en/',page_type='home',links=[],link_details=[])
        snapshot['pages'].append(home)
        # Test the configurable editorial link-count heuristic with nine actual targets.
        for i in range(9):
            target = copy.deepcopy(home)
            target.update(url=f'{ORIGIN}/en/guide-{i}/',canonical=f'{ORIGIN}/en/guide-{i}/',page_type='guides')
            snapshot['pages'].append(target)
            orphan['links'].append(target['url'])
            orphan['link_details'].append({'url':target['url'],'anchor':f'Guide {i}','context':'content'})
        result = links.analyze(snapshot,TAXONOMY)
        codes = {issue['code'] for issue in result['issues'] if issue['url']==orphan['url']}
        self.assertIn('orphan',codes)
        self.assertIn('excessive_content_links',codes)


if __name__=='__main__': unittest.main()
