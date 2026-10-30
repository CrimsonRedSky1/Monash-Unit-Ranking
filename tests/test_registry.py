import sys, unittest, tempfile, json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from university_registry import UniversityRegistry, ImportAdapter, validate_unit
import bulk_import

class RegistryTests(unittest.TestCase):
    def details(self):
        return dict(id='example',name='Example University',short_name='Example',handbook='https://example.edu/handbook')
    def unit(self):
        return dict(id='example:101',university='example',code='101',name='Example unit',faculty='Science',source='https://example.edu/101',year='2026')
    def test_registration_and_dispatch(self):
        registry=UniversityRegistry();registry.register_university(self.details())
        adapter=ImportAdapter(lambda year:['https://example.edu/101'],lambda page,url:self.unit())
        registry.register_importer('example',adapter)
        self.assertIs(registry.importer('example','2026'),adapter)
        with self.assertRaises(ValueError):registry.register_university(self.details())
        with self.assertRaises(ValueError):registry.register_importer('example',adapter)
        with self.assertRaises(ValueError):registry.register_importer('unknown',adapter)
    def test_missing_adapter_and_unsupported_year(self):
        registry=UniversityRegistry();registry.register_university(self.details())
        with self.assertRaisesRegex(ValueError,'not configured'):registry.importer('example','2026')
        registry.register_importer('example',ImportAdapter(lambda year:[],lambda page,url:{},supported_years=('2026',)))
        with self.assertRaisesRegex(ValueError,'supports years'):registry.importer('example','2027')
    def test_record_validation(self):
        self.assertEqual(validate_unit(self.unit(),'example','2026')['description'],'')
        for update in [{'name':''},{'year':'2025'},{'university':'wrong'},{'id':'other:101'},{'source':'file:///secret'}]:
            with self.subTest(update=update),self.assertRaises(ValueError):validate_unit(self.unit()|update,'example','2026')
    def test_pipeline_records_validation_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data').mkdir()
            with patch.object(bulk_import,'ROOT',root),patch.object(bulk_import,'fetch',return_value='page'):
                bulk_import.run('example','2026',['https://example.edu/101'],lambda page,url:self.unit()|{'name':''})
            self.assertEqual(json.loads((root/'data/example.json').read_text()),[])
            report=json.loads((root/'data/example-status.json').read_text())
            self.assertEqual(report['status'],'partial');self.assertEqual(len(report['failures']),1)
    def test_empty_discovery_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data').mkdir();path=root/'data/example.json';path.write_text('["untouched"]')
            with patch.object(bulk_import,'ROOT',root),self.assertRaises(ValueError):bulk_import.run('example','2026',[],lambda page,url:{})
            self.assertEqual(path.read_text(),'["untouched"]')
    def test_coverage_limit_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data').mkdir()
            with patch.object(bulk_import,'ROOT',root),patch.object(bulk_import,'fetch',return_value='page') as fetch:
                for _ in range(2):bulk_import.run('example','2026',['https://example.edu/101'],lambda page,url:self.unit(),'First page only')
                self.assertEqual(fetch.call_count,1)
            report=json.loads((root/'data/example-status.json').read_text())
            self.assertEqual(report['status'],'partial');self.assertEqual(report['note'],'First page only')
