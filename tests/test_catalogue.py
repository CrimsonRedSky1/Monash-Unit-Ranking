import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import unittest
from bulk_import import parse_deakin, parse_rmit
from server import units
from universities import UNIVERSITIES
class CatalogueTests(unittest.TestCase):
    def test_deakin_metadata_and_faculty(self):
        page="""<meta name='dknunitname' content = 'SIT102 - Introduction to Programming'><meta name='dknunityear' content = '2026'><meta name='dknunitcreditpoints' content = '1'><h3>Content</h3><p>Build &amp; test programs.</p><h3>Learning outcomes</h3>"""
        unit=parse_deakin(page,'https://handbook.deakin.edu.au/courses-search/unit.php?unit=SIT102&year=2026')
        self.assertEqual(unit['id'],'deakin:SIT102')
        self.assertEqual(unit['faculty'],'Science, Engineering and Built Environment')
        self.assertEqual(unit['description'],'Build & test programs.')
    def test_rmit_preserves_internal_identity_and_offering_code(self):
        page='<span id="P6_TITLE">001034 - Biology</span><span id="P6_HE_COURSE_ACADEMIC_GROUP">STEM</span><span id="P6_HE_UNITS">12</span><td headers="COURSE_CODE">BIOL1010</td>'
        unit=parse_rmit(page,'https://handbook.rmit.edu.au/ords/r/rmit/catalogue/course?p6_code=001034')
        self.assertEqual((unit['id'],unit['code'],unit['faculty']),('rmit:001034','BIOL1010','STEM'))
    def test_error_pages_are_not_units(self):
        for parser in [parse_deakin,parse_rmit]:
            with self.assertRaises(ValueError):parser('<h1>Unavailable</h1>','https://example.com')
    def test_catalogue_ids_are_unique_and_namespaced(self):
        records=units(); ids=[u['id'] for u in records]
        self.assertEqual(len(ids),len(set(ids)))
        supported={u['id'] for u in UNIVERSITIES}
        for unit in records:
            self.assertIn(unit['university'],supported)
            self.assertTrue(unit['id'].startswith(unit['university']+':'))
            self.assertTrue(unit['source'].startswith('https://'))
            self.assertTrue(unit['name'])
if __name__=='__main__':unittest.main()
