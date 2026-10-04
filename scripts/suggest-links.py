"""Evidence-based topic/link proposals. Never edits or publishes website pages.

Requires a fresh crawl with main_text/link_details. No model, API key or new package.
"""
import argparse
from collections import Counter, defaultdict
from contextlib import closing
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import unicodedata
from urllib.parse import urlsplit


STOP = set('the and with from that this into through within while for are was were its their has have been not as on in of to by a an is be it at or over between each during which also these those project projects architecture architectural design designed building buildings space spaces studio pus co bir ve ile icin olarak olan bu da de da ve yapinin proje projesi projeleri tasarim mimari mimarlik alan yapinin yapida alanlar the'.split())


def normalize(text):
    text = text.lower().replace('ı', 'i')
    return ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))


def tokens(text):
    return [word for word in re.findall(r'[a-z]{3,}', normalize(text)) if word not in STOP]


def matches(text, terms):
    text = normalize(text)
    return [term for term in terms if re.search(r'(?<!\w)'+re.escape(normalize(term))+(r'(?!\w)' if len(term) < 4 else ''), text)]


def evidence(text, terms):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return next((s[:450] for s in sentences if matches(s, terms)), text[:450])


def vectors(pages):
    frequencies = {p['url']: Counter(tokens(p['main_text'])) for p in pages}
    document_frequency = Counter(term for counts in frequencies.values() for term in counts)
    result = {}
    for url, counts in frequencies.items():
        vector = {word: (1+math.log(count))*(1+math.log((1+len(pages))/(1+document_frequency[word]))) for word, count in counts.items()}
        norm = math.sqrt(sum(v*v for v in vector.values())) or 1
        result[url] = {word: value/norm for word,value in vector.items()}
    return result


def reachable(graph, start, goal):
    pending = [start]; seen = set()
    while pending:
        node = pending.pop()
        if node == goal: return True
        if node in seen: continue
        seen.add(node); pending.extend(graph.get(node, set()))
    return False


def identifier(kind, *parts):
    return hashlib.sha256('|'.join([kind, *parts]).encode()).hexdigest()


def analyze(snapshot, taxonomy):
    eligible = [p for p in snapshot['pages'] if p['indexable'] and p['status'] == 200 and p['canonical'] == p['url']]
    if any('main_text' not in p or 'link_details' not in p for p in eligible): raise ValueError('Run the updated crawler first; main_text and link_details are required.')
    pages = {p['url']:p for p in eligible}
    topics = {}; clusters = []; opportunities = []; issues = []; proposals = []
    incoming = defaultdict(set); context_incoming = defaultdict(set); existing = {}; semantic_graph = defaultdict(set)
    languages = {url: urlsplit(url).path.strip('/').split('/')[0] for url in pages}
    for url,p in pages.items():
        existing[url] = set(p['links'])
        for link in p['link_details']:
            if link['url'] not in pages or link['url'] == url: continue
            incoming[link['url']].add(url)
            # Navigation/language/next-project/back links are useful, but are not topic evidence.
            anchor = normalize(link['anchor'])
            sequence = any(word in anchor for word in ['next project', 'sonraki proje', 'siradaki proje', 'back to projects', 'projelere don'])
            hierarchy = p['page_type'] == 'project' and pages[link['url']]['page_type'] == 'projects'
            if link['context'] == 'content' and not sequence and not hierarchy and languages[url] == languages[link['url']]:
                context_incoming[link['url']].add(url)
                semantic_graph[url].add(link['url'])
        slug = urlsplit(url).path.strip('/').split('/')[-1]
        category = None; basis = 'not a project'
        if p['page_type'] == 'project':
            category = next((c['id'] for c in taxonomy['clusters'] if slug in c['slugs']), None)
            basis = 'verified project mapping' if category else 'text heuristic; editorial review required'
            if not category:
                scores = [(len(matches(p['main_text'],c['terms'])),c['id']) for c in taxonomy['clusters']]
                score,category = max(scores)
                if score == 0: category = None
        themes = {theme['id']: {'matched_terms': matches(p['main_text'],theme['terms']), 'excerpt': evidence(p['main_text'],theme['terms'])} for theme in taxonomy['themes'] if matches(p['main_text'],theme['terms'])}
        topics[url] = {'url':url,'language':languages[url],'title':p['h1'][0] if p['h1'] else p['title'], 'cluster':category,'classification_basis':basis,'themes':themes}
    for url,p in pages.items():
        for code, priority, message, condition in [
            ('orphan','HIGH','No inbound link from an indexable page.',not incoming[url]),
            ('weak_contextual_links','MEDIUM','Review relevant contextual inbound links; navigation alone does not establish topic relationships.',p['page_type']=='project' and len(context_incoming[url])<2),
            ('excessive_content_links','LOW','Review content links; the limit is a local heuristic, not a search-engine rule.',p['page_type']=='project' and len(semantic_graph[url])>8),
            ('unclassified_project','MEDIUM','Review taxonomy before proposing links for this project.',p['page_type']=='project' and topics[url]['cluster'] is None)]:
            if condition: issues.append({'id':identifier('issue',url,code),'url':url,'code':code,'priority':priority,'message':message})
    origin = snapshot['canonical_origin'].rstrip('/')
    for lang in sorted(set(languages.values())):
        for cluster in taxonomy['clusters']:
            members = [url for url,t in topics.items() if t['language']==lang and t['cluster']==cluster['id']]
            if not members: continue
            proposed = f"{origin}/{lang}/services/{cluster['pillar_slug']}/"
            minimum = taxonomy['minimum_pillar_projects']
            clusters.append({'id':identifier('cluster',lang,cluster['id']),'language':lang,'topic':cluster['id'],'label':cluster['label'][lang],
                'projects':members,'pillar_url':proposed if len(members)>=minimum else None,'pillar_status':'PROPOSED' if len(members)>=minimum else 'SKIPPED_SINGLE_PROJECT',
                'search_intent':cluster['intent'][lang], 'structure':'pillar → supporting guide/article → existing project pages',
                'evidence':[{'url':url,'excerpt':pages[url]['main_text'][:450]} for url in members]})
            if len(members)>=minimum and proposed not in pages:
                opportunities.append({'id':identifier('gap',lang,'pillar',cluster['id']),'language':lang,'kind':'pillar','topic':cluster['id'],
                    'title':cluster['label'][lang],'proposed_url':proposed,'priority':'MEDIUM','status':'REVIEW','search_intent':cluster['intent'][lang],
                    'source_urls':members,'reason':'Existing project evidence supports a topic hub; no supporting hub exists in the crawl.',
                    'requirements':['Human approval and original useful explanation before page creation.','Credit the studio role accurately; do not infer services or technical claims from categorization.','Link to real examples; avoid repeating project descriptions.']})
        for theme in taxonomy['themes']:
            sources = [url for url,t in topics.items() if t['language']==lang and theme['id'] in t['themes'] and pages[url]['page_type']=='project']
            covered = any(languages[url]==lang and p['page_type'] in ('guides','services','journal','article') and theme['id'] in topics[url]['themes'] and p['word_count']>=100 for url,p in pages.items())
            if len(sources)>=2 and not covered:
                opportunities.append({'id':identifier('gap',lang,'guide',theme['id']),'language':lang,'kind':'guide','topic':theme['id'],
                    'title':theme['question'][lang],'proposed_url':f"{origin}/{lang}/guides/{theme['guide_slug']}/",'priority':'MEDIUM','status':'REVIEW',
                    'search_intent':theme['question'][lang], 'source_urls':sources,'reason':'At least two real project descriptions mention this theme; no substantial supporting guide exists.',
                    'evidence':[{'url':url,**topics[url]['themes'][theme['id']]} for url in sources],
                    'requirements':['Compare the documented examples instead of duplicating their text.','Any additional explanation or technical assertion requires studio review.','Add FAQ only if it answers actual useful questions; no automatic FAQ schema.']})
    # Same-language vectors keep EN/TR boilerplate from creating false relationships.
    all_vectors = {}
    for lang in set(languages.values()): all_vectors.update(vectors([p for url,p in pages.items() if languages[url]==lang]))
    candidates = []
    for source,p in pages.items():
        if p['page_type'] not in ('project','studio'): continue
        for target,q in pages.items():
            if source==target or languages[source]!=languages[target] or q['page_type']!='project' or target in existing[source]: continue
            shared = sorted(set(topics[source]['themes']) & set(topics[target]['themes']))
            same_cluster = bool(topics[source]['cluster']) and topics[source]['cluster']==topics[target]['cluster']
            if not same_cluster and len(shared)<2: continue
            cosine = sum(value*all_vectors[target].get(word,0) for word,value in all_vectors[source].items())
            score = .7*cosine + (.2 if same_cluster else 0) + min(.1, .04*len(shared))
            if score < taxonomy['minimum_similarity']: continue
            candidates.append((score,source,target,shared,cosine,same_cluster))
    per_source = Counter(); excluded_cycles = 0; anchor_usage = Counter()
    theme_by_id = {theme['id']:theme for theme in taxonomy['themes']}
    for score,source,target,shared,cosine,same_cluster in sorted(candidates,key=lambda c:(-c[0],c[1],c[2])):
        if per_source[source]>=taxonomy['maximum_suggestions_per_page']: continue
        if reachable(semantic_graph,target,source): excluded_cycles+=1; continue
        lang = languages[source]; title = topics[target]['title']
        variations = [title,('İlgili proje: ' if lang=='tr' else 'Related project: ')+title]
        if shared: variations.append(theme_by_id[shared[0]]['label'][lang]+': '+title)
        anchor = variations[anchor_usage[target]%len(variations)]; anchor_usage[target]+=1
        proposals.append({'id':identifier('link',source,target),'source_url':source,'target_url':target,'language':lang,'status':'REVIEW',
            'anchor':anchor,'anchor_alternatives':variations,'score':round(score,4),'cosine_similarity':round(cosine,4),
            'same_cluster':same_cluster,'shared_themes':shared,'placement':'After the project explanation, only when the shared topic can be introduced naturally; never auto-insert.',
            'reason':'Shared documented project topic'+(' and themes: '+', '.join(shared) if shared else '')+'.',
            'evidence':{'source':evidence(pages[source]['main_text'],[term for theme in shared for term in theme_by_id[theme]['terms']]),
                'target':evidence(pages[target]['main_text'],[term for theme in shared for term in theme_by_id[theme]['terms']])}})
        semantic_graph[source].add(target); per_source[source]+=1
    return {'canonical_origin':origin,'crawl_updated_at':snapshot['updated_at'],'taxonomy_version':taxonomy['version'],
        'summary':{'pages':len(pages),'projects':sum(p['page_type']=='project' for p in pages.values()),'clusters':len(clusters),
            'link_suggestions':len(proposals),'content_opportunities':len(opportunities),'issues':len(issues),'cycles_prevented':excluded_cycles,
            'priorities':dict(Counter(i['priority'] for i in issues))},
        'topics':sorted(topics.values(),key=lambda t:t['url']), 'clusters':clusters,'link_suggestions':proposals,'content_opportunities':opportunities,'issues':issues,
        'editorial_rules':taxonomy['editorial_rules'],'method':'Verified taxonomy + explicit phrase evidence + same-language TF-IDF cosine; no embeddings, automatic insertion or publishing.'}


def save(result, db, output):
    path = Path(db); path.parent.mkdir(parents=True,exist_ok=True)
    with closing(sqlite3.connect(path)) as con,con:
        con.executescript('''CREATE TABLE IF NOT EXISTS topic_pages (url TEXT PRIMARY KEY, data_json TEXT);
            CREATE TABLE IF NOT EXISTS topic_clusters (id TEXT PRIMARY KEY, origin TEXT, data_json TEXT);
            CREATE TABLE IF NOT EXISTS link_suggestions (id TEXT PRIMARY KEY, origin TEXT, source_url TEXT, target_url TEXT, status TEXT, data_json TEXT);
            CREATE TABLE IF NOT EXISTS content_opportunities (id TEXT PRIMARY KEY, origin TEXT, status TEXT, data_json TEXT);
            CREATE TABLE IF NOT EXISTS link_issues (id TEXT PRIMARY KEY, origin TEXT, data_json TEXT);''')
        origin = result['canonical_origin']
        for table,key,items in [('topic_pages','url',result['topics']),('topic_clusters','id',result['clusters']),('link_suggestions','id',result['link_suggestions']),('content_opportunities','id',result['content_opportunities']),('link_issues','id',result['issues'])]:
            active = {item[key] for item in items}
            scope = ('url LIKE ?', (origin+'/%',)) if table=='topic_pages' else ('origin = ?', (origin,))
            previous = con.execute(f'SELECT {key} FROM {table} WHERE {scope[0]}',scope[1]).fetchall()
            for (value,) in previous:
                if value not in active: con.execute(f'DELETE FROM {table} WHERE {key}=?',(value,))
            for item in items:
                if table in ('link_suggestions','content_opportunities'):
                    prior = con.execute(f'SELECT status FROM {table} WHERE id=?',(item['id'],)).fetchone()
                    if prior: item['status'] = prior[0]
                encoded = json.dumps(item,ensure_ascii=False)
                if table=='topic_pages': con.execute('INSERT OR REPLACE INTO topic_pages VALUES (?,?)',(item['url'],encoded))
                elif table=='link_suggestions': con.execute('INSERT OR REPLACE INTO link_suggestions VALUES (?,?,?,?,?,?)',(item['id'],origin,item['source_url'],item['target_url'],item['status'],encoded))
                elif table=='content_opportunities': con.execute('INSERT OR REPLACE INTO content_opportunities VALUES (?,?,?,?)',(item['id'],origin,item['status'],encoded))
                else: con.execute(f'INSERT OR REPLACE INTO {table} VALUES (?,?,?)',(item['id'],origin,encoded))
    dest = Path(output); dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result['summary']))


def review_document(result, output, base):
    def cell(text): return str(text).replace('|','\\|').replace('\n',' ')
    def link(url):
        topic = next(t for t in result['topics'] if t['url']==url)
        return f"[{cell(topic['title'])}]({base.rstrip('/')}{urlsplit(url).path})"
    lines = ['# İç bağlantı ve konu önerileri — inceleme dosyası','',
        'Bu dosya önerileri listeler; bağlantılar ve yeni sayfalar siteye eklenmedi. Mevcut sayfa bağlantıları yerel önizlemeyi açar; önizleme sunucusu çalışmalıdır.', '',
        f"Kaynak tarama: `{result['crawl_updated_at']}`. {result['summary']['link_suggestions']} bağlantı ve {result['summary']['content_opportunities']} içerik fırsatı; tüm yeni öneriler insan incelemesine tabidir.",'',
        '## Konu grupları','', '| Dil | Konu | Proje sayısı | Merkez sayfa |','| --- | --- | ---: | --- |']
    for cluster in result['clusters']:
        lines.append(f"| {cluster['language']} | {cell(cluster['label'])} | {len(cluster['projects'])} | {'Aday; henüz yok' if cluster['pillar_url'] else 'Tek proje; yeni merkez sayfa önerilmedi'} |")
    for lang in ['tr','en']:
        lines += ['',f'## {lang.upper()} bağlantı önerileri','', '| Kaynak | Hedef | Önerilen bağlantı metni | Ortak konu | Durum |', '| --- | --- | --- | --- | --- |']
        for proposal in result['link_suggestions']:
            if proposal['language']!=lang: continue
            lines.append(f"| {link(proposal['source_url'])} | {link(proposal['target_url'])} | {cell(proposal['anchor'])} | {cell(', '.join(proposal['shared_themes']) or 'Aynı proje kategorisi')} | {proposal['status']} |")
        for proposal in result['link_suggestions']:
            if proposal['language']!=lang: continue
            lines += ['',f"### {cell(next(t['title'] for t in result['topics'] if t['url']==proposal['source_url']))} → {cell(next(t['title'] for t in result['topics'] if t['url']==proposal['target_url']))}",'',
                f"- Öneri kimliği: `{proposal['id']}`",f"- Alternatif metinler: {cell(' / '.join(proposal['anchor_alternatives']))}",
                '- Yerleşim: ortak konunun doğal olarak açıklandığı proje metninin sonunda; otomatik ekleme yapılmaz.',
                f"- Kaynak kanıtı: {cell(proposal['evidence']['source'])}",f"- Hedef kanıtı: {cell(proposal['evidence']['target'])}"]
    lines += ['', '## Eksik destekleyici içerik adayları','', '| Dil | Tür | Konu / okuyucu sorusu | Kaynak proje sayısı | Aday adres (yayında değil) |', '| --- | --- | --- | ---: | --- |']
    for opportunity in result['content_opportunities']:
        path = urlsplit(opportunity['proposed_url']).path
        lines.append(f"| {opportunity['language']} | {opportunity['kind']} | {cell(opportunity['title'])} | {len(opportunity['source_urls'])} | `{path}` |")
    lines += ['', 'Her içerik adayı için kaynak URL ve alıntılar JSON çıktısındadır. Merkez sayfa → ilgili rehber/yazı → gerçek proje örnekleri ilişkisi kurulmalıdır. Bu adresler veya taslak başlıklar onaylanmış hizmet kapsamı ya da yayın izni değildir.',
        '', '## İnceleme kuralları',''] + ['- '+rule for rule in result['editorial_rules']]
    lines += ['', '## Mevcut bağlantı yapısında inceleme gerektirenler','',
        f"{len(result['issues'])} inceleme kaydı var. Az bağlamsal bağlantı kaydı, sayfanın bağlantısız veya kırık olduğu anlamına gelmez. Menü, dil değiştirme ve sonraki proje bağlantıları ayrı değerlendirilir.",'']
    for issue in result['issues']: lines.append(f"- {issue['priority']}: `{urlsplit(issue['url']).path}` — {issue['code']}")
    path = Path(output); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text('\n'.join(lines)+'\n',encoding='utf8')


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--crawl',default='.seo/crawl.json')
    cli.add_argument('--taxonomy',default='seo/topic-taxonomy.json')
    cli.add_argument('--db',default='.seo/opportunities.sqlite')
    cli.add_argument('--output',default='.seo/link-proposals.json')
    cli.add_argument('--review',default='.seo/link-review.md')
    cli.add_argument('--refresh',action='store_true',help='Crawl the local build before analyzing.')
    cli.add_argument('--base',default='http://127.0.0.1:4322')
    cli.add_argument('--performance-dir')
    args = cli.parse_args()
    if args.refresh:
        command = [sys.executable,str(Path(__file__).with_name('crawl-seo.py')),'--base',args.base,'--output',args.crawl,'--db',args.db,'--fail-on-high']
        if args.performance_dir: command.extend(['--performance-dir',args.performance_dir])
        subprocess.run(command,check=True)
    result = analyze(json.loads(Path(args.crawl).read_text(encoding='utf8')),json.loads(Path(args.taxonomy).read_text(encoding='utf8')))
    save(result,args.db,args.output)
    review_document(result,args.review,args.base)
