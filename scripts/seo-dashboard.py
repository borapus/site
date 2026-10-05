"""Authenticated, read-only loopback dashboard; never enters the public site build."""
import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
from pathlib import Path
import secrets
import sqlite3
from urllib.parse import parse_qs, urlsplit


def read_json(path, default):
    return json.loads(path.read_text(encoding='utf8')) if path.exists() else default


def database_rows(db, table, order=''):
    if not db.exists(): return []
    with sqlite3.connect('file:'+db.resolve().as_posix()+'?mode=ro',uri=True) as con:
        con.row_factory=sqlite3.Row
        if not con.execute('SELECT 1 FROM sqlite_master WHERE type=? AND name=?',('table',table)).fetchone(): return []
        return [dict(row) for row in con.execute('SELECT * FROM '+table+order)]


def dashboard_data(directory):
    directory=Path(directory); crawl=read_json(directory/'crawl.json',{})
    pages=[p for p in crawl.get('pages',[]) if p['indexable']]; tasks=crawl.get('tasks',[])
    db=directory/'opportunities.sqlite'; content=database_rows(db,'content_items')
    counts=Counter(row['status'] for row in content)
    duplicate=lambda field: sum(count-1 for value,count in Counter(p.get(field) for p in pages).items() if value and count>1)
    links=read_json(directory/'link-proposals.json',{})
    return {'updated_at':crawl.get('updated_at'),'summary':{
        'indexable':len(pages),'seo_health':round(sum(p['seo_health_score'] for p in pages)/len(pages),1) if pages else None,
        'orphans':sum(p['inbound_link_count']==0 for p in pages),
        'broken_links':sum(t['code'].startswith(('broken_link:','broken_image:')) for t in tasks),
        'missing_metadata':sum(not p['title'] or not p['description'] or not p['canonical'] for p in pages),
        'duplicate_titles':duplicate('title'),'duplicate_descriptions':duplicate('description'),'duplicate_content':duplicate('content_hash'),
        'missing_schema':sum(not p['schema_types'] or p['schema_errors'] for p in pages),
        'sitemap_urls':crawl.get('summary',{}).get('sitemap_urls'),
        'sitemap_errors':len(crawl.get('sitemap_errors',[]))+sum(t['code'] in ['missing_sitemap','invalid_sitemap_entry'] for t in tasks),
        'link_suggestions':len(links.get('link_suggestions',[])), 'link_review_issues':len(links.get('issues',[])),
        'opportunities':len(database_rows(db,'seo_keywords')),
        'pending_content':sum(counts[s] for s in ['DRAFT','REVIEW','APPROVED']), 'published':counts['PUBLISHED']},
        'pages':pages,'tasks':tasks,'content':[{'id':r['id'],'status':r['status'],'updated_at':r['updated_at'],'url':r['url']} for r in content],
        'opportunities':database_rows(db,'seo_keywords'),
        'events':database_rows(db,'content_events',' ORDER BY id DESC LIMIT 30'),
        'changes':database_rows(db,'monitoring_changes',' ORDER BY rowid DESC LIMIT 30'),
        'competitors':read_json(directory/'competitor-gap.json',{}),
        'monitor':read_json(directory/'monitor.json',{})}


def filtered(data, query):
    search=query.get('q',[''])[0].casefold()[:200]
    priority=query.get('priority',[''])[0]; status=query.get('status',[''])[0]
    result=dict(data)
    for key in ['pages','tasks','content','opportunities']:
        result[key]=[r for r in data[key] if (not search or search in json.dumps(r,ensure_ascii=False).casefold())
            and (key not in ['tasks','opportunities'] or not priority or r['priority']==priority)
            and (key not in ['content','opportunities'] or not status or r.get('status',r.get('content_status'))==status)]
    return result


def render(data, query):
    labels={'indexable':'İndekslenebilir sayfa','seo_health':'SEO sağlık puanı','orphans':'Bağlantısız sayfa','broken_links':'Kırık bağlantı/resim',
        'missing_metadata':'Eksik metadata','duplicate_titles':'Tekrarlanan başlık','duplicate_descriptions':'Tekrarlanan açıklama','duplicate_content':'Tekrarlanan metin',
        'missing_schema':'Eksik/hatalı schema','sitemap_urls':'Sitemap sayfası','sitemap_errors':'Sitemap sorunu','link_suggestions':'Bağlantı önerisi',
        'link_review_issues':'Bağlantı inceleme kaydı','opportunities':'İçerik fırsatı','pending_content':'Bekleyen taslak','published':'Doğrulanmış yayın'}
    cards=''.join(f'<div class="card"><strong>{escape(str(value if value is not None else "Ölçüm yok"))}</strong><span>{labels[key]}</span></div>' for key,value in data['summary'].items())
    def table(rows,fields):
        if not rows: return '<p>Kayıt yok.</p>'
        return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+escape(label)+'</th>' for _,label in fields)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+escape(str(row.get(key,'')))+'</td>' for key,_ in fields)+'</tr>' for row in rows)+'</tbody></table></div>'
    date=data['updated_at'] or 'Henüz tarama yapılmadı'
    sections=[('Öncelikli kontroller',table(data['tasks'],[('priority','Öncelik'),('url','Sayfa'),('message','Açıklama')])),
        ('Sayfa sağlığı',table(data['pages'],[('url','Sayfa'),('seo_health_score','Puan'),('inbound_link_count','Gelen bağlantı'),('internal_link_count','İç bağlantı'),('content_completeness','İçerik')])),
        ('İçerik fırsatları',table(data['opportunities'],[('keyword','Konu'),('intent','Okuyucu amacı'),('priority','Öncelik'),('recommended_url','Önerilen adres'),('content_status','Durum')])),
        ('İnceleme ve yayın durumları',table(data['content'],[('id','Taslak'),('status','Durum'),('updated_at','Güncelleme')])),
        ('Son içerik işlemleri',table(data['events'],[('created_at','Tarih'),('item_id','İçerik'),('action','İşlem'),('actor','İnceleyen')])),
        ('SEO değişiklikleri',table(data['changes'],[('url','Sayfa'),('kind','Değişim'),('fields_json','Alanlar')])),
        ('Rakip karşılaştırması','<pre>'+escape(json.dumps(data['competitors'],ensure_ascii=False,indent=2))+'</pre>')]
    return '<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><meta name="robots" content="noindex,nofollow,noarchive"><title>PUS&CO · SEO Yönetimi</title><style>body{font:16px system-ui;margin:0;background:#f4f3f0;color:#222}main{max-width:1200px;margin:auto;padding:32px}h1{font-weight:500}h2{margin-top:40px}p{line-height:1.6}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}.card{background:white;padding:20px}.card strong{display:block;font-size:26px}.card span{font-size:13px;color:#555}form{display:flex;flex-wrap:wrap;gap:12px;margin:24px 0}input,select,button{font:inherit;padding:10px}table{border-collapse:collapse;width:100%;background:white}th,td{text-align:left;padding:12px;border-bottom:1px solid #ddd;overflow-wrap:anywhere}th{font-size:13px}.scroll{overflow:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:white;padding:20px;font-size:12px}</style></head><body><main><h1>PUS&CO · SEO Yönetimi</h1><p>Son tarama: '+escape(date)+'</p><p>Bu panel bilgisayarınızda çalışır. Ölçümler son taramaya aittir; canlı veri değildir. Sağlık puanı yerel kontrol puanıdır. Yayın için içeriklerin ayrıca incelenmesi gerekir.</p><div class="cards">'+cards+'</div><form method="get" action="/admin/seo/"><input name="q" placeholder="Sayfa veya konu ara" aria-label="Arama" value="'+escape(query.get('q',[''])[0],quote=True)+'"><select name="priority" aria-label="Öncelik"><option value="">Tüm öncelikler</option>'+''.join(f'<option {"selected" if query.get("priority",[""])[0]==p else ""}>{p}</option>' for p in ['HIGH','MEDIUM','LOW'])+'</select><select name="status" aria-label="İçerik durumu"><option value="">Tüm durumlar</option>'+''.join(f'<option {"selected" if query.get("status",[""])[0]==s else ""}>{s}</option>' for s in ['DRAFT','REVIEW','APPROVED','PUBLISHED','ARCHIVED'])+'</select><button>Filtrele</button></form>'+''.join('<section><h2>'+title+'</h2>'+body+'</section>' for title,body in sections)+'</main></body></html>'


def handler(directory, password):
    expected=('pusnco:'+password).encode()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def respond(self,status,body,kind='text/html; charset=utf-8',challenge=False):
            self.send_response(status)
            for key,value in {'Content-Type':kind,'X-Robots-Tag':'noindex, nofollow, noarchive','Cache-Control':'no-store',
                'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Frame-Options':'DENY',
                'Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"}.items(): self.send_header(key,value)
            if challenge: self.send_header('WWW-Authenticate','Basic realm="PUS&CO SEO", charset="UTF-8"')
            self.end_headers(); self.wfile.write(body.encode())
        def do_GET(self):
            if self.headers.get('Host') not in [f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}']:
                return self.respond(403,'Erişim reddedildi.')
            auth=self.headers.get('Authorization','')
            try: credentials=base64.b64decode(auth[6:],validate=True) if auth.startswith('Basic ') and len(auth)<1024 else b''
            except ValueError: credentials=b''
            if not hmac.compare_digest(credentials,expected): return self.respond(401,'Giriş gerekli.',challenge=True)
            parsed=urlsplit(self.path)
            if parsed.path=='/robots.txt': return self.respond(200,'User-agent: *\nDisallow: /\n','text/plain')
            if parsed.path not in ['/admin/seo/','/api/seo/']: return self.respond(404,'Sayfa bulunamadı.')
            query=parse_qs(parsed.query)
            try:
                data=filtered(dashboard_data(directory),query)
                if parsed.path=='/api/seo/': return self.respond(200,json.dumps(data,ensure_ascii=False),'application/json; charset=utf-8')
                return self.respond(200,render(data,query))
            except Exception: return self.respond(503,'Rapor okunamadı. Tarama dosyalarını kontrol edin.')
        def do_POST(self): return self.respond(405,'Bu panel yalnızca okuma içindir.')
    return Handler


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=4330); parser.add_argument('--directory',default='.seo')
    args=parser.parse_args(); directory=Path(args.directory); directory.mkdir(parents=True,exist_ok=True)
    password_file=directory/'dashboard-password.txt'
    if not password_file.exists():
        with password_file.open('x',encoding='utf8') as file: file.write(secrets.token_urlsafe(32)+'\n')
        password_file.chmod(0o600)
    password=password_file.read_text(encoding='utf8').strip()
    if len(password)<32: raise ValueError('Dashboard password must contain at least 32 characters.')
    server=ThreadingHTTPServer(('127.0.0.1',args.port),handler(directory,password))
    print(f'Dashboard: http://127.0.0.1:{args.port}/admin/seo/; user: pusnco; password file: {password_file.resolve()}',flush=True)
    server.serve_forever()
