"""Read-only scheduled SEO analysis. Never approve, publish, commit or deploy."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(script, *args):
    subprocess.run([sys.executable, str(ROOT/'scripts'/script), *args], cwd=ROOT, check=True)


def changes(snapshot, previous):
    old = {p['url']: p for p in previous.get('pages', [])}
    result = []
    fields = ['status','title','description','canonical','robots','content_hash','schema_types','indexable']
    for page in snapshot['pages']:
        prior = old.get(page['url'])
        if not prior:
            result.append({'url':page['url'],'kind':'added','fields':[]})
        else:
            changed = [key for key in fields if page.get(key) != prior.get(key)]
            if changed: result.append({'url':page['url'],'kind':'changed','fields':changed})
    for url in old.keys()-{p['url'] for p in snapshot['pages']}:
        result.append({'url':url,'kind':'removed','fields':[]})
    return sorted(result,key=lambda p:p['url'])


def refresh_recommendations(snapshot, proposals):
    pages = {p['url']:p for p in snapshot['pages']}
    recommendations = []
    for item in proposals.get('content_opportunities',[]):
        recommendations.append({'url':item['proposed_url'],'priority':item['priority'],
            'reason':'supporting_content_candidate','source_urls':item['source_urls'],
            'action':'Review real source projects and reader intent; draft only after editorial selection.'})
    for page in pages.values():
        if page['indexable'] and page['content_completeness']=='review':
            recommendations.append({'url':page['url'],'priority':'MEDIUM','reason':'content_depth_review',
                'action':'Review usefulness; word count alone does not show obsolete content.'})
    return recommendations


def record(con, snapshot, report):
    con.executescript('''CREATE TABLE IF NOT EXISTS monitoring_runs (
        id TEXT PRIMARY KEY, mode TEXT, checked_at TEXT, data_json TEXT);
        CREATE TABLE IF NOT EXISTS monitoring_changes (
        id TEXT PRIMARY KEY, run_id TEXT, url TEXT, kind TEXT, fields_json TEXT);''')
    con.execute('INSERT OR REPLACE INTO monitoring_runs VALUES (?,?,?,?)',
        (report['id'],report['mode'],report['checked_at'],json.dumps(report,ensure_ascii=False)))
    for item in report['changes']:
        key=hashlib.sha256((report['id']+item['url']).encode()).hexdigest()
        con.execute('INSERT OR REPLACE INTO monitoring_changes VALUES (?,?,?,?,?)',
            (key,report['id'],item['url'],item['kind'],json.dumps(item['fields'])))


def monitor(mode, base, directory, baseline, snapshot_only=False):
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    crawl=directory/'crawl.json'; db=directory/'opportunities.sqlite'
    previous=json.loads(crawl.read_text(encoding='utf8')) if crawl.exists() else json.loads(Path(baseline).read_text(encoding='utf8')) if Path(baseline).exists() else {}
    if not snapshot_only:
        run('crawl-seo.py','--base',base,'--db',str(db),'--output',str(crawl))
    snapshot=json.loads(crawl.read_text(encoding='utf8'))
    proposals={}
    if mode in ['weekly','monthly'] and not snapshot_only:
        links=directory/'link-proposals.json'
        run('suggest-links.py','--crawl',str(crawl),'--db',str(db),'--output',str(links),'--review',str(directory/'link-review.md'),'--base',base)
        run('content-pipeline.py','discover','--crawl',str(crawl),'--db',str(db),'--proposals',str(links),'--briefs-dir',str(directory/'briefs'))
        proposals=json.loads(links.read_text(encoding='utf8'))
        run('competitor-gap.py','--crawl',str(crawl),'--output',str(directory/'competitor-gap.json'))
    elif (directory/'link-proposals.json').exists():
        proposals=json.loads((directory/'link-proposals.json').read_text(encoding='utf8'))
    fingerprint=hashlib.sha256(json.dumps([mode, [{k:p.get(k) for k in ['url','status','title','description','canonical','robots','content_hash','schema_types','indexable']} for p in snapshot['pages']],snapshot['tasks']],sort_keys=True).encode()).hexdigest()
    report={'id':fingerprint,'mode':mode,'checked_at':snapshot['updated_at'],'summary':snapshot['summary'],
        'baseline_available':bool(previous),'changes':changes(snapshot,previous) if previous else [],
        'tasks':snapshot['tasks'],'topic_clusters':len(proposals.get('clusters',[])),
        'refresh_recommendations':refresh_recommendations(snapshot,proposals) if mode=='monthly' else [],
        'automation_scope':'read-only: crawl, analyze, propose; no content approval or publishing',
        'performance_note':'Lighthouse is a separate measured audit; these scheduled checks do not measure Core Web Vitals.',
        'freshness_note':'Audit time is not the editorial update date; obsolete content requires human assessment.'}
    with sqlite3.connect(db) as con: record(con,snapshot,report)
    (directory/'monitor.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    text=['# SEO kontrol raporu','',f"Mod: {mode}; kontrol: {report['checked_at']}",
        f"İndekslenebilir sayfa: {snapshot['summary']['indexable']}",
        f"Öncelikler: {snapshot['summary']['priorities']}",
        f"Önceki ölçüme göre değişiklik: {len(report['changes'])}" if previous else 'Önceki ölçüm yok; değişiklik karşılaştırması yapılamadı.',
        '', 'Kontroller otomatik yayın yapmaz. İçerik eskiliği editör değerlendirmesi gerektirir.','']
    text += [f"- {t['priority']} — {t['url']} — {t['message']}" for t in snapshot['tasks']]
    (directory/'monitor.md').write_text('\n'.join(text)+'\n',encoding='utf8')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['daily','weekly','monthly'])
    parser.add_argument('--base',default='http://127.0.0.1:4322')
    parser.add_argument('--directory',default='.seo')
    parser.add_argument('--baseline',default='seo/monitor-baseline.json')
    parser.add_argument('--snapshot-only',action='store_true',help='Analyze existing crawl without requests; test/offline mode.')
    args=parser.parse_args()
    report=monitor(args.mode,args.base,args.directory,args.baseline,args.snapshot_only)
    print(json.dumps({'mode':args.mode,'summary':report['summary'],'changes':len(report['changes'])}))
    if any(t['priority']=='HIGH' for t in report['tasks']): raise SystemExit(1)
