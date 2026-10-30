import json
import unittest
from urllib.parse import urlsplit
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Links(HTMLParser):
 def __init__(self): super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ('href','src'):self.links.append(v)
class PagesTests(unittest.TestCase):
 def test_root_entry_and_subpath_safe_assets(self):
  parser=Links();parser.feed((ROOT/'index.html').read_text())
  for link in parser.links:
   self.assertFalse(link.startswith('/'),link)
   if link.startswith('./') and link!='./':self.assertTrue((ROOT/urlsplit(link).path[2:]).is_file(),link)
  self.assertTrue((ROOT/'.nojekyll').exists())
 def test_footer_pages_have_valid_local_links(self):
  for path in ROOT.glob('*.html'):
   source=path.read_text();parser=Links();parser.feed(source)
   self.assertIn('class="site-footer"',source)
   self.assertLess(source.index('</main>'),source.index('<footer'))
   for link in parser.links:
    if link.startswith('./') and link!='./':self.assertTrue((ROOT/urlsplit(link).path[2:]).is_file(),link)
 def test_static_export_contains_catalogue_not_reviews(self):
  payload=json.loads((ROOT/'data/catalog.json').read_text())
  self.assertEqual(set(payload),{'universities','units','coverage'})
  self.assertEqual(len(payload['universities']),4)
  self.assertTrue(payload['units'])
  for report in payload['coverage'].values():self.assertNotIn('failures',report)
  for unit in payload['units']:self.assertNotIn('reviews',unit)
 def test_pages_defaults_to_no_backend(self):
  self.assertIn('window.UNIT_CLUB_API_BASE = null',(ROOT/'assets/runtime-config.js').read_text())
  self.assertFalse((ROOT/'public').exists())
if __name__=='__main__':unittest.main()
