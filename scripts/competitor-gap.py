"""Bounded public architecture comparison; stores metrics, never competitor prose."""
import argparse
from collections import Counter, deque
from datetime import datetime, timezone
import importlib.util
import ipaddress
import json
from pathlib import Path
import re
import socket
import time
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, build_opener
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('crawler',ROOT/'scripts/crawl-seo.py')
crawler=importlib.util.module_from_spec(spec); spec.loader.exec_module(crawler)
LIMIT=512_000


def public_url(url, host=None):
    parsed=urlsplit(url)
    if parsed.scheme!='https' or parsed.username or parsed.password or parsed.port not in (None,443) or not parsed.hostname:
        raise ValueError('Only public HTTPS URLs on port 443 are allowed.')
    if host and parsed.hostname!=host: raise ValueError('Cross-host redirect/link rejected.')
    addresses=socket.getaddrinfo(parsed.hostname,443,type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError('Private/local addresses are forbidden.')
    return parsed.hostname


def fetch(url, host):
    public_url(url,host)
    opener=build_opener(crawler.NoRedirect())
    request=Request(url,headers={'User-Agent':'PusncoArchitectureAudit/1.0 (+https://pusnco.com)','Accept':'text/html,application/xml,text/plain'})
    try:
        with opener.open(request,timeout=15) as response:
            body=response.read(LIMIT+1)
            if len(body)>LIMIT: raise ValueError('Response exceeds audit size limit.')
            return response.status,response.headers,body.decode('utf8',errors='replace')
    except HTTPError as error:
        # Redirects remain observations; no cross-host or unvalidated target fetch.
        return error.code,error.headers,''


class ArchitectureParser(crawler.PageParser):
    def __init__(self):
        super().__init__(); self.visible=[]
    def handle_data(self,data):
        super().handle_data(data)
        if not self.ignore and data.strip(): self.visible.append(data.strip())


def classify(url, types):
    path=urlsplit(url).path.lower()
    if path=='/': return 'home'
    for kind,terms in [('project',['project','work']),('studio',['about','studio','practice']),('contact',['contact']),('article',['news','journal','publication','article']),('service',['service'])]:
        if any(term in path for term in terms): return kind
    if 'Article' in types: return 'article'
    return 'other'


def measure(url,status,html,taxonomy):
    parser=ArchitectureParser(); parser.feed(html)
    text=' '.join(parser.visible); lower=text.lower()
    types=sorted(set().union(*(crawler.schema_types(s) for s in parser.schema))) if parser.schema else []
    topics=[t['id'] for t in taxonomy['clusters']+taxonomy['themes'] if any(term.lower() in lower for term in t['terms'])]
    return {'url':url,'status':status,'page_type':classify(url,types),'words':len(re.findall(r'\w+',text)),
        'has_title':bool(parser.title),'has_description':bool(parser.description),'has_canonical':bool(parser.canonical),
        'h1_count':sum(h['level']==1 for h in parser.headings),'schema_types':types,'topics':topics,
        'internal_links':0,'inbound_links':0,'noindex':any('noindex' in r.lower() for r in parser.robots),
        'title_fingerprint':__import__('hashlib').sha256(parser.title.encode()).hexdigest() if parser.title else None,
        'description_fingerprint':__import__('hashlib').sha256(parser.description.encode()).hexdigest() if parser.description else None},parser.links


def inspect(studio,policy,taxonomy):
    origin=studio['url'].rstrip('/'); host=public_url(origin)
    status,_,robots_text=fetch(origin+'/robots.txt',host)
    if status not in [200,404]: raise ValueError('Cannot verify robots policy; comparison skipped.')
    robots=RobotFileParser(); robots.parse(robots_text.splitlines() if status==200 else [])
    delay=max(1,policy['request_delay_seconds'],robots.crawl_delay('PusncoArchitectureAudit') or 0)
    if delay>15: raise ValueError('Requested crawl delay exceeds this bounded audit budget; use manual comparison.')
    queue=deque([origin+'/']); visited=set(); pages=[]; edges={}; errors=[]
    sitemap_available=False
    sitemap=origin+'/sitemap.xml'
    if robots.can_fetch('PusncoArchitectureAudit',sitemap):
        time.sleep(delay)
        code,_,body=fetch(sitemap,host)
        if code==200:
            try:
                xml=ET.fromstring(body); sitemap_available=True
                if xml.tag.split('}')[-1]=='urlset':
                    for loc in xml.findall('.//{*}loc')[:policy['max_pages_per_studio']]:
                        if loc.text and urlsplit(loc.text).hostname==host: queue.append(loc.text)
                # Nested sitemap indexes are observed but not exhaustively crawled.
            except ET.ParseError: errors.append('Sitemap XML could not be parsed.')
    cap=min(20,policy['max_pages_per_studio'])
    while queue and len(visited)<cap:
        url=queue.popleft(); parsed=urlsplit(url)
        url=parsed._replace(query='',fragment='').geturl()
        if url in visited or parsed.hostname!=host or parsed.scheme!='https': continue
        if re.search(r'\.(?:jpg|png|webp|pdf|zip|mp4|svg)$',parsed.path,re.I): continue
        if not robots.can_fetch('PusncoArchitectureAudit',url): continue
        visited.add(url); time.sleep(delay)
        try:
            status,headers,body=fetch(url,host)
            if status==200 and 'text/html' not in headers.get('Content-Type',''): continue
            page,links=measure(url,status,body,taxonomy)
            targets=set()
            for link in links:
                target=urlsplit(urljoin(url,link))._replace(query='',fragment='')
                if target.scheme=='https' and target.hostname==host:
                    targets.add(target.geturl()); queue.append(target.geturl())
            page['internal_links']=len(targets); edges[url]=targets; pages.append(page)
        except Exception as error: errors.append({'url':url,'error':str(error)})
    for page in pages: page['inbound_links']=sum(page['url'] in targets for targets in edges.values())
    return {'name':studio['name'],'origin':origin,'pages':pages,'errors':errors,'sitemap_available':sitemap_available,
        'scope':'Sample of at most 20 robot-permitted public pages; no JavaScript rendering or complete-site claim.'}


def compare(own,sample,taxonomy):
    own_topics=set()
    for page in own['pages']:
        if not page['indexable']: continue
        text=page.get('main_text','').lower()
        own_topics.update(t['id'] for t in taxonomy['clusters']+taxonomy['themes'] if any(term.lower() in text for term in t['terms']))
    theirs=set(t for page in sample['pages'] if page['status']==200 for t in page['topics'])
    candidates=[]
    for topic in sorted(theirs-own_topics):
        candidates.append({'topic':topic,'action':'Validate actual studio expertise and unique reader value before proposing content.','status':'REVIEW_ONLY'})
    ours=[p for p in own['pages'] if p['indexable']]
    public=[p for p in sample['pages'] if p['status']==200 and not p['noindex']]
    avg=lambda values: round(sum(values)/len(values),1) if values else None
    duplicate=lambda field: sum(n-1 for value,n in Counter(p.get(field) for p in public).items() if value and n>1)
    return {'our_topics':sorted(own_topics),'sample_topics':sorted(theirs),'candidate_gaps':candidates,
        'our_page_types':dict(Counter(p.get('page_type','unknown') for p in ours)),
        'content_architecture_opportunities':[{'kind':'guides/journal','status':'REVIEW_ONLY',
            'action':'Review original process guides supported by actual PUS&CO projects; never reuse competitor articles.'}]
            if any(p['page_type']=='article' for p in public) and not any('/guides/' in p['url'] for p in ours) else [],
        'depth_and_links':{'our_average_main_words':avg([len(p.get('main_text','').split()) for p in ours]),
            'sample_average_visible_words':avg([p['words'] for p in public]),
            'our_average_internal_links':avg([p.get('internal_link_count',0) for p in ours]),
            'sample_average_internal_links':avg([p['internal_links'] for p in public]),
            'note':'Competitor visible-text fallback can include interface text. Word counts are not comparable quality scores.'},
        'duplicate_titles_in_sample':duplicate('title_fingerprint'),
        'duplicate_descriptions_in_sample':duplicate('description_fingerprint'),
        'page_types':dict(Counter(p['page_type'] for p in sample['pages'])),
        'missing_title':sum(not p['has_title'] for p in sample['pages'] if p['status']==200),
        'missing_description':sum(not p['has_description'] for p in sample['pages'] if p['status']==200),
        'missing_canonical':sum(not p['has_canonical'] for p in sample['pages'] if p['status']==200),
        'missing_schema':sum(not p['schema_types'] for p in sample['pages'] if p['status']==200),
        'interpretation':'Keyword matches and word counts are descriptive heuristics, not quality/ranking judgments. Absence in the sample is not absence across the site.'}


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--config',default='seo/competitors.json'); cli.add_argument('--crawl',default='.seo/crawl.json')
    cli.add_argument('--output',default='.seo/competitor-gap.json'); args=cli.parse_args()
    policy=json.loads(Path(args.config).read_text(encoding='utf8'))
    taxonomy=json.loads((ROOT/'seo/topic-taxonomy.json').read_text(encoding='utf8'))
    own=json.loads(Path(args.crawl).read_text(encoding='utf8')); results=[]
    for studio in policy['studios']:
        try:
            sample=inspect(studio,policy,taxonomy); sample['comparison']=compare(own,sample,taxonomy); results.append(sample)
        except Exception as error: results.append({'name':studio['name'],'origin':studio['url'],'error':str(error),'pages':[]})
    result={'checked_at':datetime.now(timezone.utc).isoformat(),'studios':results,'retains_competitor_prose':False}
    dest=Path(args.output); dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'studios':len(results),'pages':sum(len(s['pages']) for s in results),'errors':[s.get('error') for s in results if s.get('error')]}))
