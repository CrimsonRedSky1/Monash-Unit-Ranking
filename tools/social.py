"""Account and social persistence; public serializers never return credentials."""
import hashlib, hmac, secrets, re, time
from http.cookies import SimpleCookie
from datetime import datetime
from zoneinfo import ZoneInfo

class Problem(Exception):
    def __init__(self, message, status=400): self.message, self.status = message, status

def migrate(db):
    db.executescript('''
    CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, username TEXT NOT NULL COLLATE NOCASE UNIQUE,
      password TEXT NOT NULL, university TEXT NOT NULL, enrolment_year INTEGER NOT NULL,
      study_year INTEGER NOT NULL, semester INTEGER NOT NULL, bio TEXT NOT NULL DEFAULT '', created TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), csrf TEXT NOT NULL, expires INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS follows(follower TEXT NOT NULL REFERENCES users(id), followed TEXT NOT NULL REFERENCES users(id),
      PRIMARY KEY(follower,followed), CHECK(follower != followed));
    CREATE TABLE IF NOT EXISTS recommendations(user_id TEXT NOT NULL REFERENCES users(id), unit TEXT NOT NULL, note TEXT NOT NULL,
      created TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(user_id,unit));
    ''')
    if 'user_id' not in {r['name'] for r in db.execute('PRAGMA table_info(reviews)')}:
        db.execute('ALTER TABLE reviews ADD COLUMN user_id TEXT REFERENCES users(id)')
    db.execute('CREATE INDEX IF NOT EXISTS review_user ON reviews(user_id)')
    db.execute('CREATE UNIQUE INDEX IF NOT EXISTS review_offering_owner ON reviews(user_id,unit,year,semester) WHERE user_id IS NOT NULL')
    db.execute('CREATE INDEX IF NOT EXISTS followed_user ON follows(followed)')
    db.commit()

def password_hash(password, salt=None):
    if not isinstance(password,str) or not 12<=len(password)<=128:
        raise Problem('Use a password of 12–128 characters.')
    salt=salt or secrets.token_hex(16)
    digest=hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=131072,r=8,p=1,maxmem=256*1024*1024).hex()
    return salt+':'+digest

def profile_fields(data, universities):
    if data.get('university') not in universities: raise Problem('Choose a university from the directory.')
    year=datetime.now(ZoneInfo('Australia/Melbourne')).year
    for key,low,high in [('enrolment_year',1958,year),('study_year',1,12),('semester',1,3)]:
        if type(data.get(key)) is not int or not low<=data[key]<=high: raise Problem('Enter a valid enrolment year, study year (1–12) and semester (1–3).')
    bio=data.get('bio','')
    if not isinstance(bio,str) or len(bio)>280: raise Problem('Keep your bio to 280 characters.')
    return (data['university'],data['enrolment_year'],data['study_year'],data['semester'],bio.strip())

def public_user(db,user,viewer=None):
    result={k:user[k] for k in ('id','username','university','enrolment_year','study_year','semester','bio','created')}
    result['followers']=db.execute('SELECT count(*) FROM follows WHERE followed=?',(user['id'],)).fetchone()[0]
    result['following']=db.execute('SELECT count(*) FROM follows WHERE follower=?',(user['id'],)).fetchone()[0]
    result['is_following']=bool(viewer and db.execute('SELECT 1 FROM follows WHERE follower=? AND followed=?',(viewer,user['id'])).fetchone())
    return result

def session(db,headers):
    cookie=SimpleCookie()
    try: cookie.load(headers.get('Cookie','')); token=cookie['lunchtable_session'].value
    except Exception: return None
    return db.execute('SELECT * FROM sessions WHERE token=? AND expires>?',(hashlib.sha256(token.encode()).hexdigest(),int(time.time()))).fetchone()

def new_session(db,user_id):
    token=secrets.token_urlsafe(32); csrf=secrets.token_urlsafe(32)
    db.execute('DELETE FROM sessions WHERE expires<=?',(int(time.time()),))
    db.execute('INSERT INTO sessions VALUES(?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),user_id,csrf,int(time.time())+604800))
    return token,csrf

def require_session(db,headers):
    s=session(db,headers)
    if not s: raise Problem('Sign in to continue.',401)
    if not hmac.compare_digest(headers.get('X-CSRF-Token',''),s['csrf']): raise Problem('Please refresh the page and try again.',403)
    return s

def get(db,path,query,headers):
    s=session(db,headers); viewer=s['user_id'] if s else None
    if path=='me':
        user=db.execute('SELECT * FROM users WHERE id=?',(viewer,)).fetchone()
        return {'user':public_user(db,user) if user else None,'csrf':s['csrf'] if s else None}
    if path=='people':
        q=query.get('q',[''])[0][:60]
        rows=db.execute('SELECT * FROM users WHERE instr(lower(username),lower(?))>0 ORDER BY username LIMIT 50',(q,))
        return {'users':[public_user(db,r,viewer) for r in rows]}
    if path=='profile':
        user=db.execute('SELECT * FROM users WHERE username=?',(query.get('username',[''])[0],)).fetchone()
        if not user: raise Problem('Profile not found.',404)
        uid=user['id']; result=public_user(db,user,viewer)
        result['reviews']=[dict(r) for r in db.execute('SELECT * FROM reviews WHERE user_id=? ORDER BY created DESC',(uid,))]
        result['recommendations']=[dict(r) for r in db.execute('SELECT unit,note,created FROM recommendations WHERE user_id=? ORDER BY created DESC',(uid,))]
        for key,col,other in [('followers','followed','follower'),('following','follower','followed')]:
            result[key+'_users']=[{'username':r['username']} for r in db.execute(f'SELECT username FROM users JOIN follows ON users.id=follows.{other} WHERE follows.{col}=? ORDER BY username LIMIT 100',(uid,))]
        return result
    if path=='feed':
        following=query.get('scope',['all'])[0]=='following'
        if following and not viewer: raise Problem('Sign in to see people you follow.',401)
        try: offset=max(0,int(query.get('offset',['0'])[0]))
        except ValueError: raise Problem('Invalid page.')
        condition='AND user_id IN (SELECT followed FROM follows WHERE follower=?)' if following else ''
        params=(viewer,) if following else ()
        rows=db.execute(f'''SELECT * FROM (
          SELECT 'review' kind,r.id,r.user_id,u.username,r.unit,r.body content,r.rating,r.year,r.semester,r.created FROM reviews r JOIN users u ON u.id=r.user_id
          UNION ALL SELECT 'recommendation',r.user_id||r.unit,r.user_id,u.username,r.unit,r.note,NULL,NULL,NULL,r.created FROM recommendations r JOIN users u ON u.id=r.user_id
        ) WHERE 1=1 {condition} ORDER BY created DESC,id DESC LIMIT 21 OFFSET ?''',params+(offset,)).fetchall()
        return {'items':[dict(r) for r in rows[:20]],'has_more':len(rows)>20}
    raise Problem('Not found.',404)

def post(db,path,data,headers,universities,units):
    if not isinstance(data,dict): raise Problem('Expected an object.')
    if path in ('signup','login'):
        username=data.get('username',''); password=data.get('password','')
        if not isinstance(username,str) or not re.fullmatch(r'[A-Za-z0-9_]{3,24}',username): raise Problem('Username must contain 3–24 letters, numbers or underscores.')
        if path=='signup':
            fields=profile_fields(data,universities)
            if db.execute('SELECT 1 FROM users WHERE username=?',(username,)).fetchone(): raise Problem('That username is taken.',409)
            hashed=password_hash(password); uid=secrets.token_hex(16)
            db.execute('INSERT INTO users(id,username,password,university,enrolment_year,study_year,semester,bio) VALUES(?,?,?,?,?,?,?,?)',(uid,username,hashed)+fields)
        else:
            user=db.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
            stored=user['password'] if user else '00'*16+':'+'00'*64
            try: valid=hmac.compare_digest(password_hash(password,stored.split(':')[0]),stored)
            except Problem: valid=False
            if not user or not valid: raise Problem('Incorrect username or password.',401)
            uid=user['id']
        old=session(db,headers)
        if old: db.execute('DELETE FROM sessions WHERE token=?',(old['token'],))
        token,csrf=new_session(db,uid)
        return {'user':public_user(db,db.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()),'csrf':csrf},token
    s=require_session(db,headers); uid=s['user_id']
    if path=='logout': db.execute('DELETE FROM sessions WHERE token=?',(s['token'],)); return {'ok':True},''
    if path=='profile':
        fields=profile_fields(data,universities)
        db.execute('UPDATE users SET university=?,enrolment_year=?,study_year=?,semester=?,bio=? WHERE id=?',fields+(uid,))
    elif path=='follow':
        if not isinstance(data.get('username'),str): raise Problem('Choose a valid username.')
        target=db.execute('SELECT id FROM users WHERE username=?',(data.get('username',''),)).fetchone()
        if not target: raise Problem('Profile not found.',404)
        if target['id']==uid: raise Problem('You cannot follow yourself.')
        if type(data.get('follow')) is not bool: raise Problem('Choose follow or unfollow.')
        if data['follow']: db.execute('INSERT OR IGNORE INTO follows VALUES(?,?)',(uid,target['id']))
        else: db.execute('DELETE FROM follows WHERE follower=? AND followed=?',(uid,target['id']))
    elif path=='recommendations':
        if data.get('unit') not in units: raise Problem('Choose an existing unit.')
        note=data.get('note','')
        if not isinstance(note,str) or len(note)>1000: raise Problem('Keep recommendations to 1,000 characters.')
        if data.get('remove') is True: db.execute('DELETE FROM recommendations WHERE user_id=? AND unit=?',(uid,data['unit']))
        else: db.execute('INSERT INTO recommendations(user_id,unit,note) VALUES(?,?,?) ON CONFLICT(user_id,unit) DO UPDATE SET note=excluded.note,created=CURRENT_TIMESTAMP',(uid,data['unit'],note.strip()))
    else: raise Problem('Not found.',404)
    return {'ok':True},None
