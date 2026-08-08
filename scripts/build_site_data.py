import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=ROOT/'public/data'
items=[]
for p in sorted(data.glob('*.json')):
    try:
        x=json.loads(p.read_text())
        items.append({'file':p.name, 'scanner':x.get('scanner'), 'updated_at':x.get('updated_at'), 'count':x.get('count',0)})
    except Exception:
        pass
(data/'index.json').write_text(json.dumps({'updated_at':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'scanners':items},indent=2))
