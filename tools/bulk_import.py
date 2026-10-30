"""Resumable catalogue import. Public sources only; checkpoints per university."""
import argparse, concurrent.futures, datetime, hashlib, json, re, subprocess, time
from pathlib import Path
from xml.etree import ElementTree as ET
from importer import parse_page, plain
from universities import DEAKIN_FACULTIES, REGISTRY
from university_registry import ImportAdapter, validate_unit
from urllib.parse import urljoin
import html
ROOT=Path(__file__).resolve().parent.parent; CACHE=ROOT/'data/.cache'
def fetch(url):
    CACHE.mkdir(exist_ok=True)
    key=CACHE/(hashlib.sha256(url.encode()).hexdigest()+'.html')
    if key.exists(): return key.read_text()
    p=subprocess.run(['curl','--fail','--silent','--show-error','--location','--max-time','45','--retry','2',url],capture_output=True,text=True)
    if p.returncode: raise RuntimeError(p.stderr.strip())
    if '_Incapsula_Resource' in p.stdout or 'Just a moment...' in p.stdout: raise RuntimeError('Public catalogue returned an access challenge')
    key.write_text(p.stdout);time.sleep(.25);return p.stdout
def sitemap(url,year):
    root=ET.fromstring(fetch(url)); locs=[x.text for x in root.iter() if x.tag.endswith('}loc')]
    if root.tag.endswith('sitemapindex'):
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex: lists=list(ex.map(lambda u:sitemap(u,year),locs))
        return sorted(set(u for items in lists for u in items))
    return [u for u in locs if re.search(rf'/{year}/units/[A-Z]+\d+/?$',u)]
def save_json(path,value):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2));tmp.replace(path)
def run(university,year,urls,parser,coverage_note=""):
    urls=sorted(set(urls))
    if not urls: raise ValueError("No unit URLs discovered; existing catalogue retained")
    path=ROOT/f'data/{university}.json'; records={u['source']:u for u in json.loads(path.read_text())} if path.exists() else {}
    for record in records.values(): validate_unit(record,university,year)
    report={'university':university,'year':year,'discovered':len(urls),'status':'running','failures':[]}
    def save():
        report['imported']=len(records);report['updated_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        save_json(path,list(records.values()));save_json(ROOT/f'data/{university}-status.json',report)
    save();print(f'{university}: {len(urls)} discovered, {len(records)} already imported',flush=True)
    def one(url):
        try:return url,validate_unit(parser(fetch(url),url),university,year),None
        except Exception as e:return url,None,str(e)
    pending=[u for u in urls if u not in records]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        for n,(url,record,error) in enumerate(ex.map(one,pending),1):
            if error:
                report['failures'].append({'url':url,'error':error})
                if any(term in error for term in ['403','429','access challenge']):
                    report['note']='Import stopped after the source denied or rate-limited access. Remaining URLs have not been retried.'
                    ex.shutdown(wait=False,cancel_futures=True)
                    break
            elif record:
                if any(old['id']==record['id'] and source!=url for source,old in records.items()):
                    report['failures'].append({'url':url,'error':'Duplicate unit ID from another source URL'})
                else: records[url]=record
            if n%25==0:save();print(f'{university}: {len(records)}/{len(urls)} imported; {len(report["failures"])} failed',flush=True)
    report['status']='complete' if not report['failures'] and len(records)==len(urls) and not coverage_note else 'partial'
    if coverage_note: report['note']=coverage_note
    save()
    print(f'{university}: {report["status"]}; {len(records)} imported, {len(report["failures"])} failed',flush=True)
def discover_deakin(year):
    urls=set()
    for level in [0,1,2,3,4,5,6,7,8,9]:
        page=fetch(f'https://handbook.deakin.edu.au/courses-search/unit-search.php?hidType=max&year={year}&selLevel={level}&chkSortby=unit_cd')
        found=re.findall(r'href=["\'](unit.php\?[^"\']+)',page)
        urls.update(urljoin('https://handbook.deakin.edu.au/courses-search/',html.unescape(u)) for u in found)
    if not urls: raise ValueError('No Deakin units found')
    return sorted(urls)
def parse_deakin(page,url):
    meta={k:html.unescape(v) for k,v in re.findall(r"<meta name='([^']+)'\s+content\s*=\s*'([^']*)'",page)}
    title=meta.get('dknunitname',''); code,sep,name=title.partition(' - ')
    if not sep or not meta.get('dknunityear'): raise ValueError('Not a valid Deakin unit page')
    description=re.search(r'<h3>Content</h3>(.*?)(?:<h3>|$)',page,re.S)
    return dict(id='deakin:'+code,university='deakin',code=code,name=name,faculty=DEAKIN_FACULTIES.get(code[0],'Faculty not provided by source'),credits=meta.get('dknunitcreditpoints',''),year=meta['dknunityear'],description=plain(description.group(1)) if description else '',offering=meta.get('dknunitoffered',''),source=url,imported_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
def discover_rmit(year):
    page=fetch('https://handbook.rmit.edu.au/ords/r/rmit/catalogue/browse1?p3_browse_id=06')
    groups=re.findall(r'<script id="gCard[^>]+>(.*?)</script>',page,re.S)
    rows=[r for group in groups for r in json.loads(group)['values'] if r[1]=='course']
    # Only the first public page is available without a live APEX pagination session.
    return ['https://handbook.rmit.edu.au/ords/r/rmit/catalogue/course?p6_code='+r[0] for r in rows]
def parse_rmit(page,url):
    def field(key):
        m=re.search(r'<span id="'+key+r'"[^>]*>(.*?)</span>',page,re.S)
        return plain(m.group(1)) if m else ''
    title=field('P6_TITLE');internal,sep,name=title.partition(' - ')
    if not sep:raise ValueError('RMIT course record missing')
    codes=sorted(set(re.findall(r'headers="COURSE_CODE"[^>]*>\s*([A-Z]+[0-9]+)',page)))
    desc=re.search(r'aria-label="Course&#x20;Description".*?<div class="t-Region-orderBy"></div>(.*?)(?:<div class="t-Region-buttons|</section>)',page,re.S)
    return dict(id='rmit:'+internal,university='rmit',code=' / '.join(codes) or internal,name=name,faculty=field('P6_HE_COURSE_ACADEMIC_GROUP') or field('P6_FACULTY') or 'College not listed',school=field('P6_HE_DEPARTMENT'),credits=field('P6_HE_UNITS'),year='2026',description=plain(desc.group(1)) if desc else '',source=url,imported_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
def discover_monash(year):
    return sitemap('https://handbook.monash.edu/sitemap.xml',year)

# Each source adapter uses the same discovery -> parse -> validate -> checkpoint pipeline.
REGISTRY.register_importer('monash',ImportAdapter(discover_monash,parse_page))
REGISTRY.register_importer('deakin',ImportAdapter(discover_deakin,parse_deakin))
REGISTRY.register_importer('rmit',ImportAdapter(discover_rmit,parse_rmit,
    coverage_note='Only the first public course listing page is imported. Full catalogue pagination is not connected.',
    supported_years=('2026',)))

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--university',choices=list(REGISTRY.universities),default='monash')
    ap.add_argument('--year',default='2026')
    ap.add_argument('--list',action='store_true',help='List registered universities and import availability')
    args=ap.parse_args(argv)
    if args.list:
        for uid,details in REGISTRY.universities.items():
            status='automatic import available' if uid in REGISTRY.adapters else 'existing catalogue only; adapter not configured'
            print(f'{uid}: {details["name"]} — {status}')
        return
    try:
        if not re.fullmatch(r'\d{4}',args.year): raise ValueError('Year must have four digits')
        adapter=REGISTRY.importer(args.university,args.year)
        run(args.university,args.year,adapter.discover(args.year),adapter.parse,adapter.coverage_note)
    except ValueError as error:
        ap.error(str(error))

if __name__=='__main__':main()
