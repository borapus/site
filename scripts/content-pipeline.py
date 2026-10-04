"""Source-grounded briefs and offline AI draft review. No automatic approval/deployment.

publish stages only approved content in the website manifest. PUBLISHED is recorded
only after confirm-publication verifies the exact approved hash on the live page.
"""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import urlsplit
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
HARD_PUBLISH_LIMIT = 2
STATUSES = ['DRAFT','REVIEW','APPROVED','PUBLISHED','ARCHIVED']


def now(): return datetime.now(timezone.utc).isoformat()
def canonical_json(value): return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def fingerprint(value): return hashlib.sha256(canonical_json(value).encode()).hexdigest()
def compact(text): return re.sub(r'\s+',' ',text).strip()
def words(text): return re.findall(r'\w+',text.lower())
def text_of(content): return ' '.join([content.get('introduction',''), *[p for s in content.get('sections',[]) for p in s.get('paragraphs',[])]])


def load_policy(path):
    policy = json.loads(Path(path).read_text(encoding='utf8'))
    if policy['auto_approve'] or not policy['require_human_factual_review'] or not policy['require_bilingual_pair'] or not policy['require_service_scope_confirmation']:
        raise ValueError('Human factual review and bilingual approval cannot be disabled.')
    if not 1<=policy['max_publish_per_run']<=HARD_PUBLISH_LIMIT: raise ValueError('Publication limit must be 1–2 items per run.')
    if policy['minimum_words']<200 or policy['minimum_sources']<2 or policy['minimum_sections']<3: raise ValueError('Quality thresholds cannot allow thin or unsourced pages.')
    if not policy['allowed_kinds'] or not set(policy['allowed_kinds']).issubset({'guides','services'}): raise ValueError('Only guides and services may be configured.')
    return policy


def connect(path):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    con = sqlite3.connect(path); con.row_factory=sqlite3.Row
    con.executescript('''CREATE TABLE IF NOT EXISTS seo_keywords (
        id TEXT PRIMARY KEY, keyword TEXT, intent TEXT, topic_cluster TEXT, priority TEXT,
        existing_url TEXT, recommended_url TEXT, content_status TEXT, last_updated TEXT, source TEXT);
        CREATE TABLE IF NOT EXISTS content_briefs (id TEXT PRIMARY KEY, data_json TEXT);
        CREATE TABLE IF NOT EXISTS content_items (id TEXT PRIMARY KEY, url TEXT UNIQUE, status TEXT,
        content_hash TEXT, data_json TEXT, approval_json TEXT, updated_at TEXT);
        CREATE TABLE IF NOT EXISTS content_events (id INTEGER PRIMARY KEY, item_id TEXT, action TEXT,
        actor TEXT, content_hash TEXT, created_at TEXT, detail TEXT);''')
    return con


def event(con,item,action,actor='',detail=''):
    con.execute('INSERT INTO content_events(item_id,action,actor,content_hash,created_at,detail) VALUES (?,?,?,?,?,?)',
        (item['id'],action,actor,fingerprint(item),now(),detail))


def discover(con, proposals, snapshot, directory):
    pages = {p['url']:p for p in snapshot['pages'] if p['indexable']}
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    count=0
    for opportunity in proposals['content_opportunities']:
        source_urls=[url for url in opportunity['source_urls'] if url in pages and pages[url]['page_type']=='project']
        if len(source_urls)<2: continue
        brief={**opportunity,'source':'existing studio website','source_snapshots':[{'url':url,'title':pages[url]['h1'][0],'text':pages[url]['main_text']} for url in source_urls],
            'writer_instructions':['Answer this intent with a meaningful comparison of actual project examples.',
                'Use only supplied source facts; preserve concept-design and implementation credits.',
                'Return original paragraphs, source-linked factual claims, unique metadata and contextual links.',
                'Do not add prices, certifications, ratings, performance claims, security details or unverified service promises.',
                'Do not create location pages, repeated project text or boilerplate. This is a draft for human review.'],
            'required_output':'id, kind (guides/services), lang, slug, topic, title, description, h1, intent, introduction, sections[{heading,paragraphs,source_urls}], source_urls, facts[{claim,source_url,quote}], related_links[{url,anchor}], image, generator'}
        keyword=opportunity['title']; kind='guides' if opportunity['kind']=='guide' else 'services'
        path=urlsplit(opportunity['proposed_url']).path
        item_id=f"{kind}:{opportunity['language']}:{path.strip('/').split('/')[-1]}"
        existing=con.execute('SELECT status FROM content_items WHERE id=?',(item_id,)).fetchone()
        status=existing['status'] if existing else 'DRAFT'
        row=con.execute('SELECT data_json FROM content_briefs WHERE id=?',(opportunity['id'],)).fetchone()
        encoded=canonical_json(brief)
        if not row or row['data_json']!=encoded:
            con.execute('INSERT OR REPLACE INTO content_briefs VALUES (?,?)',(opportunity['id'],encoded))
        previous=con.execute('SELECT * FROM seo_keywords WHERE id=?',(opportunity['id'],)).fetchone()
        updated=previous['last_updated'] if previous and previous['keyword']==keyword and previous['content_status']==status else now()
        con.execute('INSERT OR REPLACE INTO seo_keywords VALUES (?,?,?,?,?,?,?,?,?,?)',
            (opportunity['id'],keyword,opportunity['search_intent'],opportunity['topic'],opportunity['priority'],
                opportunity['proposed_url'] if opportunity['proposed_url'] in pages else None,opportunity['proposed_url'],status,updated,'existing studio website; inferred intent, no search-volume data'))
        (directory/(opportunity['id']+'.json')).write_text(json.dumps(brief,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        count+=1
    return count


def shingles(text):
    terms=words(text)
    return {tuple(terms[i:i+5]) for i in range(max(0,len(terms)-4))}


def similarity(a,b):
    left,right=shingles(a),shingles(b)
    return len(left&right)/len(left|right) if left|right else 0


def quality(content,snapshot,policy,peers=()):
    errors=[]; warnings=[]
    pages={p['url']:p for p in snapshot['pages'] if p['indexable'] and p['status']==200}
    origin=snapshot['canonical_origin'].rstrip('/')
    if content.get('kind') not in policy['allowed_kinds']: errors.append('Unsupported page kind; location/use-case pages are not allowed.')
    if content.get('lang') not in ['tr','en'] or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',content.get('slug','')): errors.append('Invalid language or canonical slug.')
    expected=f"{content.get('kind')}:{content.get('lang')}:{content.get('slug')}"
    if content.get('id')!=expected: errors.append('Content id must match kind, language and slug.')
    source_urls=list(dict.fromkeys(content.get('source_urls',[])))
    if len(source_urls)<policy['minimum_sources']: errors.append('Insufficient distinct project sources.')
    for url in source_urls:
        if url not in pages or pages[url]['page_type']!='project' or not urlsplit(url).path.startswith('/'+content.get('lang','')+'/'):
            errors.append('Unknown, non-project or different-language source: '+url)
    for key,min_length,max_length in [('title',10,90),('description',70,180),('h1',5,130),('intent',10,250)]:
        value=content.get(key,'')
        if not isinstance(value,str) or not min_length<=len(value)<=max_length: errors.append('Invalid '+key+' length.')
    text=text_of(content)
    word_count=len(words(text))
    if word_count<policy['minimum_words']: errors.append('Thin draft; insufficient meaningful body text.')
    if '<' in text or '>' in text: errors.append('Raw HTML is not allowed in draft paragraphs.')
    sections=content.get('sections',[])
    if len(sections)<policy['minimum_sections']: errors.append('Insufficient sections.')
    for section in sections:
        if not section.get('heading') or not section.get('paragraphs'): errors.append('Empty section.')
        if not section.get('source_urls') or any(url not in source_urls for url in section['source_urls']): errors.append('Every section needs valid source references.')
    facts=content.get('facts',[])
    if len({fact.get('source_url') for fact in facts})<policy['minimum_sources']: errors.append('Factual claims must cite at least two real sources.')
    for fact in facts:
        source=pages.get(fact.get('source_url'))
        quote=compact(fact.get('quote',''))
        if fact.get('source_url') not in source_urls or not source or len(quote)<35 or quote not in compact(source.get('main_text','')):
            errors.append('A factual evidence quote does not match its source.')
        if not fact.get('claim'): errors.append('Empty factual claim.')
    links=content.get('related_links',[])
    if len({link.get('url') for link in links})<policy['minimum_sources']: errors.append('At least two relevant real project links are required.')
    if any(link.get('url') not in source_urls or not link.get('anchor') for link in links): errors.append('Related links must reference cited source projects with meaningful anchors.')
    image=content.get('image','')
    if image not in json.loads((ROOT/'src/data/imageManifest.json').read_text(encoding='utf8')): errors.append('Use a real, prepared website image.')
    duplicates=[]
    for peer in peers:
        if peer.get('id')==content.get('id') or peer.get('lang')!=content.get('lang'): continue
        for key in ['title','description','h1','intent']:
            if compact(peer.get(key,''))==compact(content.get(key,'')): errors.append('Duplicate '+key+' against '+peer['id'])
        score=similarity(text,text_of(peer))
        if score>=policy['duplicate_threshold']: duplicates.append({'id':peer['id'],'similarity':round(score,4)})
    for url,page in pages.items():
        if url==origin+f"/{content.get('lang')}/{content.get('kind')}/{content.get('slug')}/": continue
        if not urlsplit(url).path.startswith('/'+content.get('lang','')+'/'): continue
        if content.get('title')==page['title'] or content.get('description')==page['description']: errors.append('Duplicate metadata against an existing page.')
        score=similarity(text,page.get('main_text',''))
        if score>=policy['duplicate_threshold']: duplicates.append({'url':url,'similarity':round(score,4)})
    if duplicates: errors.append('Near-duplicate content; rewrite before review.')
    warnings.append('Quote and structure checks do not prove semantic truth; the reviewer must check every claim and interpretation.')
    if content.get('kind')=='services': warnings.append('Actual service scope must be explicitly confirmed by the human reviewer.')
    return {'passed':not errors,'errors':list(dict.fromkeys(errors)),'warnings':warnings,'word_count':word_count,'source_count':len(source_urls),'duplicates':duplicates,'content_hash':fingerprint(content)}


def all_items(con): return [json.loads(row['data_json']) for row in con.execute("SELECT data_json FROM content_items WHERE status!='ARCHIVED' ORDER BY id")]


def import_drafts(con,drafts,snapshot,policy):
    if len(drafts)>policy['max_drafts_per_run']: raise ValueError('Draft import limit exceeded.')
    result=[]
    for draft in drafts:
        required=['id','kind','lang','slug','topic','title','description','h1','intent','introduction','sections','source_urls','facts','related_links','image','generator']
        if not isinstance(draft,dict) or any(key not in draft for key in required): raise ValueError('Draft schema is incomplete.')
        expected=f"{draft.get('kind')}:{draft.get('lang')}:{draft.get('slug')}"
        if draft.get('id')!=expected: raise ValueError('Invalid content id.')
        url=snapshot['canonical_origin'].rstrip('/')+f"/{draft['lang']}/{draft['kind']}/{draft['slug']}/"
        existing=con.execute('SELECT * FROM content_items WHERE id=?',(draft['id'],)).fetchone()
        digest=fingerprint(draft)
        if existing and existing['content_hash']==digest: result.append({'id':draft['id'],'status':existing['status'],'changed':False}); continue
        if existing and existing['status'] in ['PUBLISHED','ARCHIVED']: raise ValueError('Published/archived items need a separately reviewed revision, not in-place draft replacement.')
        con.execute('INSERT OR REPLACE INTO content_items VALUES (?,?,?,?,?,?,?)',(draft['id'],url,'DRAFT',digest,canonical_json(draft),None,now()))
        event(con,draft,'DRAFT_IMPORTED',detail='Offline AI-assisted input; not auto-approved.')
        result.append({'id':draft['id'],'status':'DRAFT','changed':True})
    return result


def get_item(con,item_id):
    row=con.execute('SELECT * FROM content_items WHERE id=?',(item_id,)).fetchone()
    if not row: raise ValueError('Unknown item: '+item_id)
    return row,json.loads(row['data_json'])


def sync_keywords(con):
    for row in con.execute('SELECT id,recommended_url,content_status FROM seo_keywords').fetchall():
        content=con.execute('SELECT status FROM content_items WHERE url=?',(row['recommended_url'],)).fetchone()
        if content and content['status']!=row['content_status']:
            con.execute('UPDATE seo_keywords SET content_status=?,last_updated=? WHERE id=?',(content['status'],now(),row['id']))


def transition(con,item_id,action,snapshot,policy,actor='',facts=False,service_scope=False):
    row,content=get_item(con,item_id)
    report=quality(content,snapshot,policy,all_items(con))
    if not report['passed']: raise ValueError('Quality gate failed: '+ '; '.join(report['errors']))
    if action=='submit':
        if row['status']=='REVIEW': return
        if row['status']!='DRAFT': raise ValueError('Only DRAFT can move to REVIEW.')
        con.execute("UPDATE content_items SET status='REVIEW',updated_at=? WHERE id=?",(now(),item_id)); event(con,content,'SUBMITTED')
    elif action=='approve':
        if row['status']!='REVIEW': raise ValueError('Only REVIEW can be approved.')
        if not actor.strip() or not facts: raise ValueError('A named human reviewer and explicit factual confirmation are required.')
        if content['kind']=='services' and policy['require_service_scope_confirmation'] and not service_scope: raise ValueError('Human service-scope confirmation is required.')
        approval={'reviewer':actor,'at':now(),'content_hash':report['content_hash'],'facts_confirmed':True,'service_scope_confirmed':service_scope}
        con.execute("UPDATE content_items SET status='APPROVED',approval_json=?,updated_at=? WHERE id=?",(canonical_json(approval),now(),item_id))
        event(con,content,'APPROVED',actor)


def stage_publication(con,ids,snapshot,policy,manifest):
    if not ids or len(ids)!=len(set(ids)) or len(ids)>min(policy['max_publish_per_run'],HARD_PUBLISH_LIMIT): raise ValueError('Select 1–2 unique approved items; hard publication limit exceeded.')
    path=Path(manifest); entries=json.loads(path.read_text(encoding='utf8')) if path.exists() else []
    prepared=[]
    for item_id in ids:
        row,content=get_item(con,item_id)
        approval=json.loads(row['approval_json']) if row['approval_json'] else None
        if row['status']!='APPROVED' or not approval or approval['content_hash']!=fingerprint(content) or not approval['facts_confirmed']:
            raise ValueError('Only the exact human-approved content can be staged.')
        report=quality(content,snapshot,policy,all_items(con))
        if not report['passed']: raise ValueError('Quality gate failed before publication.')
        prepared.append({'content':content,'content_hash':fingerprint(content),'approval':approval,'publication':{'status':'READY'}})
    merged={e['content']['id']:e for e in entries}
    merged.update({e['content']['id']:e for e in prepared})
    for entry in prepared:
        c=entry['content']
        if policy['require_bilingual_pair'] and not any(e['content']['kind']==c['kind'] and e['content']['slug']==c['slug'] and e['content']['lang']!=c['lang'] for e in merged.values()):
            raise ValueError('Approve and stage both language versions together.')
    encoded=json.dumps(sorted(merged.values(),key=lambda e:e['content']['id']),ensure_ascii=False,indent=2)+'\n'
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists() or path.read_text(encoding='utf8')!=encoded:
        temporary=path.with_suffix(path.suffix+'.tmp'); temporary.write_text(encoded,encoding='utf8'); temporary.replace(path)
        for entry in prepared: event(con,entry['content'],'PUBLICATION_STAGED',entry['approval']['reviewer'],'No deployment performed; status remains APPROVED.')
    return len(prepared)


def confirm_publication(con,item_id,live_origin):
    row,content=get_item(con,item_id)
    if row['status']!='APPROVED' or not row['approval_json']: raise ValueError('Only approved staged content can become PUBLISHED.')
    approval=json.loads(row['approval_json'])
    if approval['content_hash']!=fingerprint(content): raise ValueError('Approval does not match current content.')
    url=live_origin.rstrip('/')+urlsplit(row['url']).path
    with urlopen(url,timeout=20) as response:
        html=response.read(2_000_000).decode('utf8','replace')
        if response.status!=200 or response.url!=url: raise ValueError('Live page must return 200 without a redirect.')
    if f'data-content-id="{item_id}"' not in html or f'data-content-hash="{row["content_hash"]}"' not in html or 'noindex' in html:
        raise ValueError('Live page does not contain the exact approved, indexable content.')
    con.execute("UPDATE content_items SET status='PUBLISHED',updated_at=? WHERE id=?",(now(),item_id))
    event(con,content,'PUBLICATION_VERIFIED',approval['reviewer'],url)


def withdraw(ids,manifest):
    path=Path(manifest)
    entries=json.loads(path.read_text(encoding='utf8')) if path.exists() else []
    remaining=[e for e in entries if e['content']['id'] not in ids]
    for entry in remaining:
        c=entry['content']
        if not any(e['content']['slug']==c['slug'] and e['content']['kind']==c['kind'] and e['content']['lang']!=c['lang'] for e in remaining):
            raise ValueError('Withdraw both language versions together.')
    if entries!=remaining:
        temporary=path.with_suffix(path.suffix+'.tmp'); temporary.write_text(json.dumps(remaining,ensure_ascii=False,indent=2)+'\n',encoding='utf8'); temporary.replace(path)
    return len(entries)-len(remaining)


def archive(con,item_id,live_origin):
    row,content=get_item(con,item_id)
    if row['status'] not in ['DRAFT','REVIEW','APPROVED','PUBLISHED']: raise ValueError('Item is already archived.')
    if row['status']=='PUBLISHED':
        from urllib.error import HTTPError
        try:
            with urlopen(live_origin.rstrip('/')+urlsplit(row['url']).path,timeout=20): pass
        except HTTPError as error:
            if error.code not in [404,410]: raise ValueError('Unpublication must be verified before archiving.')
        else: raise ValueError('Remove the live page before marking it ARCHIVED.')
    con.execute("UPDATE content_items SET status='ARCHIVED',approval_json=NULL,updated_at=? WHERE id=?",(now(),item_id)); event(con,content,'ARCHIVED')


def export_review(con,snapshot,policy,output):
    items=all_items(con); lines=['# İçerik taslakları — insan incelemesi','',
        'Bu dosyadaki metinler taslaktır; yayın onayı verilmedi ve siteye eklenmedi. Her iddia ve kaynak ilişkisi editör tarafından doğrulanmalıdır.','']
    reports=[]
    for c in items:
        row,_=get_item(con,c['id']); report=quality(c,snapshot,policy,items); reports.append({'id':c['id'],'status':row['status'],**report})
        lines += [f"## {c['h1']}",'',f"- Kimlik: `{c['id']}`",f"- Durum: `{row['status']}`",f"- Başlık: {c['title']}",f"- Açıklama: {c['description']}",f"- Okuyucu amacı: {c['intent']}",f"- Kalite kapısı: {'geçti' if report['passed'] else 'geçmedi'}; {report['word_count']} kelime / {report['source_count']} kaynak",'',c['introduction'],'']
        for section in c['sections']:
            lines += ['### '+section['heading'],'',*sum(([p,''] for p in section['paragraphs']),[])]
        lines += ['### Kaynak ve iddia eşleştirmesi','']
        for fact in c['facts']: lines += ['- '+fact['claim'],'  - Kaynak: '+fact['source_url'],'  - Kaynak metin: '+fact['quote']]
        lines += ['', '### Önerilen proje bağlantıları','']+[f"- {link['anchor']}: {link['url']}" for link in c['related_links']]+['']
        if report['errors']: lines += ['Kalite sorunları: '+ '; '.join(report['errors']),'']
    dest=Path(output); dest.parent.mkdir(parents=True,exist_ok=True); dest.write_text('\n'.join(lines)+'\n',encoding='utf8')
    return reports


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['discover','generate','quality','submit','approve','publish','confirm-publication','withdraw','archive','review'])
    parser.add_argument('--db',default='.seo/opportunities.sqlite'); parser.add_argument('--crawl',default='.seo/crawl.json')
    parser.add_argument('--policy',default='seo/content-policy.json'); parser.add_argument('--proposals',default='docs/seo-phase4-proposals.json')
    parser.add_argument('--input'); parser.add_argument('--id',action='append',default=[]); parser.add_argument('--reviewer',default='')
    parser.add_argument('--confirm-facts',action='store_true'); parser.add_argument('--confirm-service-scope',action='store_true')
    parser.add_argument('--manifest',default='src/data/editorialContent.json'); parser.add_argument('--live-origin',default='https://pusnco.com')
    parser.add_argument('--briefs-dir',default='.seo/briefs'); parser.add_argument('--output',default='.seo/content-review.md')
    args=parser.parse_args(); policy=load_policy(args.policy); snapshot=json.loads(Path(args.crawl).read_text(encoding='utf8'))
    with closing(connect(args.db)) as con,con:
        if args.command=='discover': result={'briefs':discover(con,json.loads(Path(args.proposals).read_text(encoding='utf8')),snapshot,args.briefs_dir)}
        elif args.command=='generate':
            if not args.input: raise ValueError('Offline AI draft JSON is required; no LLM provider is configured.')
            result=import_drafts(con,json.loads(Path(args.input).read_text(encoding='utf8')),snapshot,policy)
        elif args.command in ['submit','approve']:
            if not args.id: raise ValueError('Select explicit content ids.')
            for item_id in args.id: transition(con,item_id,args.command,snapshot,policy,args.reviewer,args.confirm_facts,args.confirm_service_scope)
            result={'status':'REVIEW' if args.command=='submit' else 'APPROVED','ids':args.id}
        elif args.command=='publish': result={'staged':stage_publication(con,args.id,snapshot,policy,args.manifest),'deployed':False,'status':'APPROVED; awaiting live verification'}
        elif args.command=='withdraw':
            if not args.id: raise ValueError('Select explicit content ids.')
            result={'withdrawn_from_manifest':withdraw(args.id,args.manifest),'deployed':False}
        elif args.command in ['confirm-publication','archive']:
            if not args.id: raise ValueError('Select explicit content ids.')
            if args.command=='archive':
                staged=json.loads(Path(args.manifest).read_text(encoding='utf8')) if Path(args.manifest).exists() else []
                if any(e['content']['id'] in args.id for e in staged): raise ValueError('Withdraw the staged item before archiving it.')
            for item_id in args.id: (confirm_publication if args.command=='confirm-publication' else archive)(con,item_id,args.live_origin)
            result={'ids':args.id,'status':'PUBLISHED' if args.command=='confirm-publication' else 'ARCHIVED'}
        else:
            result=export_review(con,snapshot,policy,args.output)
            if args.command=='quality' and any(not r['passed'] for r in result):
                print(json.dumps(result,ensure_ascii=True)); raise SystemExit(1)
        sync_keywords(con)
    print(json.dumps(result,ensure_ascii=True))
