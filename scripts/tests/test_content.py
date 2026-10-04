"""Editorial lifecycle tests. Synthetic approval occurs only in temporary test DBs."""
import copy
from contextlib import closing
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).parents[2]
spec=importlib.util.spec_from_file_location('content',ROOT/'scripts/content-pipeline.py')
pipeline=importlib.util.module_from_spec(spec); spec.loader.exec_module(pipeline)
DRAFTS=json.loads((ROOT/'seo/drafts/example-guides.json').read_text(encoding='utf8'))
POLICY=pipeline.load_policy(ROOT/'seo/content-policy.json')


def snapshot():
    # Source fixtures come from the checked-in draft evidence, without external requests.
    pages={}
    for draft in DRAFTS:
        for fact in draft['facts']:
            url=fact['source_url']
            pages.setdefault(url,{'url':url,'status':200,'indexable':True,'page_type':'project','h1':['Source project'],
                'title':'Source '+url,'description':'Source description '+url,'main_text':''})
            if fact['quote'] not in pages[url]['main_text']: pages[url]['main_text']+=' '+fact['quote']
    return {'canonical_origin':'https://pusnco.com','pages':list(pages.values())}


class ContentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.con=pipeline.connect(Path(self.temp.name)/'test.sqlite')
        self.sources=snapshot(); self.manifest=Path(self.temp.name)/'manifest.json'
        pipeline.import_drafts(self.con,DRAFTS,self.sources,POLICY)
    def tearDown(self): self.con.close(); self.temp.cleanup()

    def approve_pair(self):
        pair=[d for d in DRAFTS if d['slug']=='privacy-shared-living']
        for draft in pair:
            pipeline.transition(self.con,draft['id'],'submit',self.sources,POLICY)
            pipeline.transition(self.con,draft['id'],'approve',self.sources,POLICY,'TEST FIXTURE ONLY',True)
        return [d['id'] for d in pair]

    def test_source_thin_duplicate_and_metadata_gates(self):
        self.assertTrue(all(pipeline.quality(d,self.sources,POLICY,DRAFTS)['passed'] for d in DRAFTS))
        wrong=copy.deepcopy(DRAFTS[0]); wrong['facts'][0]['quote']='An invented claim which is not supported by any actual source.'
        self.assertFalse(pipeline.quality(wrong,self.sources,POLICY)['passed'])
        thin=copy.deepcopy(DRAFTS[0]); thin['introduction']='Short'; thin['sections']=[{'heading':'Short','paragraphs':['Short'],'source_urls':thin['source_urls']}]
        self.assertFalse(pipeline.quality(thin,self.sources,POLICY)['passed'])
        duplicate=copy.deepcopy(DRAFTS[0]); duplicate.update(id='guides:tr:duplicate',slug='duplicate')
        self.assertFalse(pipeline.quality(duplicate,self.sources,POLICY,DRAFTS)['passed'])
        location=copy.deepcopy(DRAFTS[0]); location['kind']='locations'
        self.assertFalse(pipeline.quality(location,self.sources,POLICY)['passed'])

    def test_unapproved_pair_and_hard_limit(self):
        with self.assertRaises(ValueError): pipeline.stage_publication(self.con,[DRAFTS[0]['id']],self.sources,POLICY,self.manifest)
        self.assertFalse(self.manifest.exists())
        ids=self.approve_pair()
        with self.assertRaises(ValueError): pipeline.stage_publication(self.con,ids[:1],self.sources,POLICY,self.manifest)
        with self.assertRaises(ValueError): pipeline.stage_publication(self.con,[d['id'] for d in DRAFTS],self.sources,POLICY,self.manifest)
        self.assertFalse(self.manifest.exists())
        pipeline.stage_publication(self.con,ids,self.sources,POLICY,self.manifest)
        self.assertEqual(len(json.loads(self.manifest.read_text(encoding='utf8'))),2)
        self.assertEqual(pipeline.get_item(self.con,ids[0])[0]['status'],'APPROVED')
        original=self.manifest.read_text(encoding='utf8')
        pipeline.stage_publication(self.con,ids,self.sources,POLICY,self.manifest)
        self.assertEqual(original,self.manifest.read_text(encoding='utf8'))

    def test_approval_invalidated_on_content_change(self):
        ids=self.approve_pair(); revised=copy.deepcopy(DRAFTS[0]); revised['introduction']+=' A new sentence needing review.'
        pipeline.import_drafts(self.con,[revised],self.sources,POLICY)
        row,_=pipeline.get_item(self.con,revised['id'])
        self.assertEqual(row['status'],'DRAFT'); self.assertIsNone(row['approval_json'])
        with self.assertRaises(ValueError): pipeline.stage_publication(self.con,ids,self.sources,POLICY,self.manifest)

    def test_explicit_human_and_service_confirmation(self):
        draft=DRAFTS[0]
        with self.assertRaises(ValueError): pipeline.transition(self.con,draft['id'],'approve',self.sources,POLICY,'TEST',True)
        pipeline.transition(self.con,draft['id'],'submit',self.sources,POLICY)
        with self.assertRaises(ValueError): pipeline.transition(self.con,draft['id'],'approve',self.sources,POLICY)
        service=copy.deepcopy(DRAFTS[0]); service.update(kind='services',id='services:tr:privacy-shared-living')
        pipeline.import_drafts(self.con,[service],self.sources,POLICY)
        # Exclude the matching guide from this scope-only fixture to avoid expected duplicate checks.
        self.con.execute('DELETE FROM content_items WHERE id=?',(draft['id'],))
        pipeline.transition(self.con,service['id'],'submit',self.sources,POLICY)
        with self.assertRaises(ValueError): pipeline.transition(self.con,service['id'],'approve',self.sources,POLICY,'TEST',True,False)

    def test_idempotent_import_and_archive(self):
        count=self.con.execute('SELECT count(*) FROM content_events').fetchone()[0]
        pipeline.import_drafts(self.con,DRAFTS,self.sources,POLICY)
        self.assertEqual(self.con.execute('SELECT count(*) FROM content_items').fetchone()[0],4)
        self.assertEqual(self.con.execute('SELECT count(*) FROM content_events').fetchone()[0],count)
        pipeline.archive(self.con,DRAFTS[0]['id'],'https://pusnco.com')
        self.assertEqual(pipeline.get_item(self.con,DRAFTS[0]['id'])[0]['status'],'ARCHIVED')

    def test_live_verification_rejects_wrong_content(self):
        ids=self.approve_pair(); item_id=ids[0]
        class Response:
            status=200
            url='https://pusnco.com/tr/guides/privacy-shared-living/'
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self,*args): return b'<html>Unrelated content</html>'
        with patch.object(pipeline,'urlopen',return_value=Response()):
            with self.assertRaises(ValueError): pipeline.confirm_publication(self.con,item_id,'https://pusnco.com')
        self.assertEqual(pipeline.get_item(self.con,item_id)[0]['status'],'APPROVED')


if __name__=='__main__': unittest.main()
