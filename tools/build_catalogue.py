"""Build the public GitHub Pages catalogue without exporting student reviews."""
import json
from server import BASE, units, catalogue_status
from universities import UNIVERSITIES

def build():
    payload={'universities':UNIVERSITIES,'units':units(),'coverage':catalogue_status()}
    path=BASE/'data/catalog.json'
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')))
    temp.replace(path)
    print(f'Exported {len(payload["units"])} units to {path}')
if __name__=='__main__':build()
