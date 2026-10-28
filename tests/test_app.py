import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import json, unittest
from importer import parse_page
from server import validate
class AppTests(unittest.TestCase):
 def test_parse_real_schema(self):
  page={'props':{'pageProps':{'pageContent':{'unit_code':'FIT1045','title':'Programming','academic_org':{'value':'Faculty of Information Technology'},'implementation_year':'2026','credit_points':'6','handbook_synopsis':'<p>Code &amp; learn</p>'}}}}
  u=parse_page('<script id="__NEXT_DATA__">'+json.dumps(page)+'</script>','https://handbook.monash.edu/2026/units/FIT1045')
  self.assertEqual(u['faculty'],'Information Technology');self.assertEqual(u['description'],'Code & learn')
 def test_invalid_record(self):
  with self.assertRaises(ValueError): parse_page('<html>Maintenance</html>','url')
 def test_review_validation(self):
  d={'unit':'monash:FIT1045','author':'Alex','rating':5,'body':'A really enjoyable unit with interesting assignments.','semester':'Semester 1','year':2026}
  self.assertEqual(validate(d),d)
  for change in [{'year':None},{'year':True},{'year':'2026'},{'year':1957},{'year':9999},{'semester':''},{'semester':'Earlier'},{'rating':True},{'rating':6},{'rating':'5'},{'unit':'fake'},{'body':'short'},{'author':' '}]:
   with self.assertRaises(ValueError):validate(d|change)
if __name__=='__main__':unittest.main()
