"""Import public Monash handbook records. Run --all for sitemap discovery."""
import argparse, datetime, html, json, re, subprocess, time
from pathlib import Path
from xml.etree import ElementTree as ET
BASE = Path(__file__).resolve().parent.parent
SEEDS = 'FIT1045 FIT1047 FIT1051 FIT2094 FIT2099 FIT3178 ATS1261 ECC1000 ETC1000 MGC1010 ENG1011 MTH1020 BIO1011 CHM1011 PSY1011 LAW1111 PHA2022'.split()
def fetch(url):
    if not url.startswith('https://handbook.monash.edu/'):
        raise ValueError('Only public Monash handbook URLs are supported')
    return subprocess.check_output(['curl','--fail','--silent','--show-error','--location','--max-time','40','--retry','2',url],text=True)
def plain(value):
    return re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ',value or ''))).strip()
def parse_page(source, url):
    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',source,re.S)
    if not match: raise ValueError('Handbook structured data missing')
    p=json.loads(match.group(1))['props']['pageProps']['pageContent']
    if not p.get('unit_code') or not p.get('academic_org',{}).get('value'): raise ValueError('Not a unit record')
    return dict(id='monash:'+p['unit_code'],university='monash',code=p['unit_code'],name=p['title'],faculty=(p.get('school',{}).get('value') or p['academic_org']['value']).removeprefix('Faculty of '),credits=p.get('credit_points',''),year=str(p['implementation_year']),description=plain(p.get('handbook_synopsis') or p.get('overview')),source=url,imported_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
def discover(year):
    pending=['https://handbook.monash.edu/sitemap.xml']; seen=set(); urls=set()
    while pending:
        url=pending.pop()
        if url in seen: continue
        seen.add(url); root=ET.fromstring(fetch(url))
        locs=[x.text for x in root.iter() if x.tag.endswith('}loc')]
        if root.tag.endswith('sitemapindex'): pending.extend(locs)
        else: urls.update(u for u in locs if re.search(rf'/{year}/units/[A-Z]+\d+/?$',u))
        time.sleep(.2)
    return sorted(urls)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--all',action='store_true'); ap.add_argument('--year',default='2026'); ap.add_argument('--codes',nargs='+'); args=ap.parse_args()
    path=BASE/'data/units.json'; units={u['id']:u for u in json.loads(path.read_text())} if path.exists() else {}
    urls=discover(args.year) if args.all else [f'https://handbook.monash.edu/{args.year}/units/{c}' for c in args.codes or SEEDS]
    failures=[]
    for i,url in enumerate(urls):
        try:
            from university_registry import validate_unit
            unit=validate_unit(parse_page(fetch(url),url),"monash",args.year); units[unit['id']]=unit
            temp=path.with_suffix('.tmp'); temp.write_text(json.dumps(list(units.values()),indent=2)); temp.replace(path)
            print(f'{i+1}/{len(urls)} {unit["code"]}',flush=True)
        except Exception as e: failures.append(url); print(f'FAILED {url}: {e}',flush=True)
        time.sleep(.3)
    print(f'{len(units)} saved; {len(failures)} failures')
    if failures: raise SystemExit(1)
if __name__=='__main__': main()
