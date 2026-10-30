"""Local development API. Standard-library only; SQLite review persistence."""
import json, os, sqlite3, uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from universities import UNIVERSITIES, DEAKIN_FACULTIES
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
BASE=Path(__file__).resolve().parent.parent
DB=Path(os.environ.get('UNIT_DB',BASE/'data/reviews.sqlite3'))
def connect():
    db=sqlite3.connect(DB); db.row_factory=sqlite3.Row
    db.execute('CREATE TABLE IF NOT EXISTS reviews (id TEXT PRIMARY KEY, unit TEXT NOT NULL, author TEXT NOT NULL, rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5), body TEXT NOT NULL, semester TEXT NOT NULL, created TEXT DEFAULT CURRENT_TIMESTAMP)')
    if 'year' not in {row['name'] for row in db.execute('PRAGMA table_info(reviews)')}:
        db.execute('ALTER TABLE reviews ADD COLUMN year INTEGER')
        # Keep older reviews intact; their combined semester string still displays.
        db.commit()
    return db
def units():
    records={u['id']:u for u in json.loads((BASE/'data/units.json').read_text())}
    for university in UNIVERSITIES:
        path=BASE/f"data/{university['id']}.json"
        if path.exists(): records.update({u['id']:u for u in json.loads(path.read_text())})
    for unit in records.values():
        if unit['university']=='deakin':
            unit['faculty']=DEAKIN_FACULTIES.get(unit['code'][0],unit['faculty'])
            unit['faculty_source']='https://www.deakin.edu.au/students/enrolment-and-fees/enrol/enrolment-codes-and-terminology'
    return list(records.values())
def catalogue_status():
    statuses={}
    for university in UNIVERSITIES:
        path=BASE/f"data/{university['id']}-status.json"
        if path.exists():
            report=json.loads(path.read_text())
            statuses[university['id']]={k:v for k,v in report.items() if k!='failures'}
            statuses[university['id']]['failed_count']=len(report.get('failures',[]))
        else: statuses[university['id']]={'status':'partial','note':'Catalogue import is not yet complete.'}
    return statuses
def validate(data):
    if not isinstance(data,dict): raise ValueError('Invalid review')
    if data.get('unit') not in {u['id'] for u in units()}: raise ValueError('Choose an existing unit')
    if type(data.get('rating')) is not int or not 1<=data['rating']<=5: raise ValueError('Choose 1–5 stars')
    if type(data.get('year')) is not int or not 1958 <= data['year'] <= datetime.now(ZoneInfo('Australia/Melbourne')).year: raise ValueError('Enter the year you took the unit')
    if data.get('semester') not in ('Semester 1','Semester 2','Summer semester','Winter semester','Trimester 1','Trimester 2','Trimester 3','Full year','Other teaching period'): raise ValueError('Choose a teaching period')
    for key,low,high in [('author',2,60),('body',20,2000),('semester',1,40)]:
        if not isinstance(data.get(key),str) or not low<=len(data[key].strip())<=high: raise ValueError(f'{key.capitalize()} must be {low}–{high} characters')
    return data
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw): super().__init__(*a,directory=str(BASE),**kw)
    def send_json(self,data,status=200):
        body=json.dumps(data).encode(); self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/assets/runtime-config.js':
            self.send_response(200);self.send_header('Content-Type','application/javascript');self.send_header('Cache-Control','no-store');self.end_headers()
            self.wfile.write(b"window.UNIT_CLUB_API_BASE = './api/';");return
        if path=='/api/catalog':
            self.send_json({'universities':UNIVERSITIES,'units':units(),'coverage':catalogue_status()}); return
        if path=='/api/reviews':
            with connect() as db: rows=[dict(r) for r in db.execute('SELECT * FROM reviews ORDER BY created DESC, rowid DESC')]
            self.send_json(rows); return
        if path not in ('/','/index.html','/top10.html','/saved.html','/privacy.html','/terms.html','/university-data.html','/guidelines.html','/about.html','/contact.html','/assets/saved.js','/assets/rankings.js','/assets/universities/monash.svg','/assets/universities/unimelb.svg','/assets/universities/rmit.svg','/assets/universities/deakin.svg','/assets/demo-reviews.js','/assets/top10.js','/assets/app.js','/assets/navigation.js','/assets/university-search.js','/assets/style.css','/assets/theme-midnight.css','/assets/lunchtable-midnight.jpg','/assets/icon.svg','/assets/lunchtable-logo.svg','/assets/lunchtable-logo.jpg','/assets/lunchtable-wordmark.jpg','/assets/lunchtable-book.jpg','/assets/lunchtable-book-icon.png','/assets/lunchtable-wordmark.jpg','/assets/lunchtable-book.jpg','/assets/lunchtable-book-icon.png','/data/catalog.json'):
            self.send_error(404);return
        super().do_GET()
    def do_POST(self):
        if self.path!='/api/reviews': self.send_json({'error':'Not found'},404); return
        origin=self.headers.get('Origin')
        if origin and urlparse(origin).netloc!=self.headers.get('Host'):
            self.send_json({'error':'Origin not allowed'},403); return
        try:
            length=int(self.headers.get('Content-Length',0))
            if not 0<length<=12000: raise ValueError('Invalid request size')
            data=validate(json.loads(self.rfile.read(length)))
            with connect() as db:
                db.execute('INSERT INTO reviews(id,unit,author,rating,body,semester,year) VALUES(?,?,?,?,?,?,?)',(str(uuid.uuid4()),data['unit'],data['author'].strip(),data['rating'],data['body'].strip(),data['semester'].strip(),data['year']))
            self.send_json({'ok':True},201)
        except (ValueError,TypeError): self.send_json({'error':'Enter a name (2–60 characters), 1–5 stars, a valid year and semester, and a review (20–2000 characters).'},400)
if __name__=='__main__':
    connect().close(); port=int(os.environ.get('PORT','8000')); print(f'LunchTable running at http://localhost:{port}',flush=True); ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
