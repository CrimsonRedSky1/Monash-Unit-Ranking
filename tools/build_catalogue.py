"""Build the public GitHub Pages catalogue without exporting student reviews."""
import json
from server import BASE, units, catalogue_status
from universities import UNIVERSITIES, REGISTRY
from university_registry import validate_unit

def build():
    records=units()
    for unit in records:
        if unit.get('university') not in REGISTRY.universities: raise ValueError('Unknown university in catalogue')
    records=[validate_unit(u,u['university']) for u in records]
    payload={'universities':UNIVERSITIES,'units':records,'coverage':catalogue_status()}
    path=BASE/'data/catalog.json'
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')))
    temp.replace(path)
    print(f'Exported {len(payload["units"])} units to {path}')
if __name__=='__main__':build()
