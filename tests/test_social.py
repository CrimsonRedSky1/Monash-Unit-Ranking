import sys, tempfile, unittest, json, threading, http.client, sqlite3
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import server
from http.server import ThreadingHTTPServer
class SocialTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.old_db=server.DB;server.DB=Path(cls.tmp.name)/'test.sqlite3'
  server.connect().close();server.AUTH_ATTEMPTS.clear()
  cls.http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
  cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start()
 @classmethod
 def tearDownClass(cls):
  cls.http.shutdown();cls.http.server_close();cls.thread.join();server.DB=cls.old_db;cls.tmp.cleanup()
 def request(self,path,data=None,cookie='',csrf='',origin=None):
  conn=http.client.HTTPConnection('127.0.0.1',self.http.server_port)
  headers={'Cookie':cookie,'X-CSRF-Token':csrf,'Content-Type':'application/json'}
  if origin:headers['Origin']=origin
  conn.request('GET' if data is None else 'POST','/api/'+path,None if data is None else json.dumps(data),headers)
  response=conn.getresponse();status=response.status;cookie=response.getheader('Set-Cookie');body=json.loads(response.read());conn.close();return status,body,cookie
 def test_account_social_lifecycle(self):
  payload={'username':'alex','password':'a long test password','university':'monash','enrolment_year':2024,'study_year':3,'semester':2}
  status,alex,cookie=self.request('signup',payload);self.assertEqual(status,201);self.assertIn('HttpOnly',cookie);self.assertIn('SameSite=Strict',cookie)
  self.assertEqual(alex['user']['enrolment_year'],2024);self.assertNotIn('password',alex['user'])
  csrf=alex['csrf'];uid=alex['user']['id']
  self.assertEqual(self.request('signup',payload|{'username':'ALEX'})[0],409)
  self.assertEqual(self.request('login',{'username':'alex','password':'wrong password here'})[0],401)
  self.assertEqual(self.request('profile',payload,cookie,'wrong')[0],403)
  self.assertEqual(self.request('profile',payload,cookie,csrf,'https://evil.example')[0],403)
  self.assertEqual(self.request('profile',payload|{'semester':9},cookie,csrf)[0],400)
  status,bea,bcookie=self.request('signup',payload|{'username':'bea','university':'deakin'});self.assertEqual(status,201)
  self.assertEqual(self.request('follow',{'username':'bea','follow':True},cookie,csrf)[0],200)
  self.request('follow',{'username':'bea','follow':True},cookie,csrf)
  self.assertEqual(self.request('profile?username=bea')[1]['followers'],1)
  self.assertEqual(self.request('follow',{'username':'alex','follow':True},cookie,csrf)[0],400)
  unit=server.units()[0]['id']
  review={'unit':unit,'rating':5,'author':'IMPERSONATED','body':'An enjoyable unit with thoughtful teaching and practical projects.','year':2025,'semester':'Semester 2'}
  self.assertEqual(self.request('reviews',review)[0],401)
  self.assertEqual(self.request('reviews',review,bcookie,bea['csrf'])[0],201)
  self.assertEqual(self.request('reviews',review,bcookie,bea['csrf'])[0],409)
  self.assertEqual(self.request('reviews')[1][0]['author'],'bea')
  self.assertEqual(self.request('recommendations',{'unit':unit,'note':'Recommended!'},bcookie,bea['csrf'])[0],200)
  self.assertEqual(len(self.request('feed?scope=following',cookie=cookie)[1]['items']),2)
  self.assertEqual(self.request('profile?username=bea')[1]['reviews'][0]['user_id'],bea['user']['id'])
  self.request('recommendations',{'unit':unit,'remove':True},cookie,csrf)
  self.assertEqual(len(self.request('profile?username=bea')[1]['recommendations']),1)
  self.request('follow',{'username':'bea','follow':False},cookie,csrf)
  self.assertEqual(self.request('feed?scope=following',cookie=cookie)[1]['items'],[])
  self.assertEqual(self.request('logout',{},cookie,csrf)[0],200)
  self.assertIsNone(self.request('me',cookie=cookie)[1]['user'])
  self.assertEqual(self.request('recommendations',{'unit':unit},cookie,csrf)[0],401)
  status,logged,newcookie=self.request('login',{'username':'alex','password':payload['password']});self.assertEqual(status,200)
  self.assertEqual(logged['user']['id'],uid)
  with server.connect() as db:
   self.assertNotEqual(db.execute('SELECT password FROM users WHERE id=?',(uid,)).fetchone()[0],payload['password'])
   db.execute('INSERT INTO reviews(id,unit,author,rating,body,semester) VALUES(?,?,?,?,?,?)',('legacy',unit,'Old student',4,'Legacy review stays intact','Semester 1'))
  with server.connect() as db:self.assertIsNone(db.execute("SELECT user_id FROM reviews WHERE id='legacy'").fetchone()[0])
class MigrationTests(unittest.TestCase):
 def test_original_schema_is_preserved(self):
  with tempfile.TemporaryDirectory() as tmp:
   previous=server.DB;server.DB=Path(tmp)/'legacy.sqlite3'
   try:
    with sqlite3.connect(server.DB) as db:
     db.execute('CREATE TABLE reviews(id TEXT PRIMARY KEY,unit TEXT,author TEXT,rating INTEGER,body TEXT,semester TEXT,created TEXT)')
     db.execute("INSERT INTO reviews VALUES('old','monash:FIT1045','Original student',5,'Original review','Semester 1, 2024','2024-01-01')")
    with server.connect() as db:
     row=db.execute("SELECT * FROM reviews WHERE id='old'").fetchone()
     self.assertEqual(row['author'],'Original student');self.assertIsNone(row['user_id']);self.assertIsNone(row['year'])
    with server.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM reviews').fetchone()[0],1)
   finally:server.DB=previous
if __name__=='__main__':unittest.main()
