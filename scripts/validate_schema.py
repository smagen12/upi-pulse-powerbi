from pathlib import Path
import json,urllib.request,hashlib
from jsonschema import Draft7Validator,RefResolver
R=Path(__file__).resolve().parents[1];cache=R/'.cache/schemas';cache.mkdir(parents=True,exist_ok=True)
def fetch(url):
 p=cache/(hashlib.sha256(url.encode()).hexdigest()+'.json')
 if not p.exists():
  # Some Microsoft embedded schemas advertise a dotted $id but are hosted
  # under the hyphenated filename. Preserve the document's constraints.
  actual = url.replace('schema.embedded.json', 'schema-embedded.json')
  p.write_bytes(urllib.request.urlopen(actual,timeout=35).read())
 return json.loads(p.read_text(encoding='utf-8'))
count=0
files=list((R/'UPI-Payments.Report/definition').rglob('*.json'))+[R/'UPI-Payments.Report/definition.pbir',R/'UPI-Payments.SemanticModel/definition.pbism',R/'UPI-Payments.pbip']
for p in files:
 data=json.loads(p.read_text(encoding='utf-8'));url=data['$schema'];schema=fetch(url)
 resolver=RefResolver(base_uri=url,referrer=schema,handlers={'https':fetch})
 errors=list(Draft7Validator(schema,resolver=resolver).iter_errors(data))
 if errors:
  for e in errors:print(p.relative_to(R),list(e.path),e.message)
  raise SystemExit(1)
 count+=1
print('PASS:',count,'PBIP/PBIR/PBISM JSON files conform to Microsoft published schemas. TMDL/DAX/M execution still requires Desktop.')
