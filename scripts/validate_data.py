from pathlib import Path
import csv, json, math, re, collections
R = Path(__file__).resolve().parents[1]

def require(condition, message):
    if not condition:
        raise ValueError(message)

def read(p):
    with (R / p).open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))
n = read('data/processed/national.csv')
b = read('data/processed/remitter.csv')
require(len(n) == 24 and len(b) == 1199, 'Failed: len(n) == 24 and len(b) == 1199')
require(len(set((x['Month'] for x in n))) == 24, "Failed: len(set((x['Month'] for x in n))) == 24")
require(len(set(((x['Month'], x['Bank']) for x in b))) == 1199, 'Duplicate canonical bank-month')
require(set((x['Month'] for x in n)) == set((x['Month'] for x in b)), "Failed: set((x['Month'] for x in n)) == set((x['Month'] for x in b))")
require(set(collections.Counter((x['Month'] for x in b)).values()) == {49, 50}, "Failed: set(collections.Counter((x['Month'] for x in b)).values()) == {49, 50}")
for x in n:
    require(all(math.isfinite(float(x[k])) and float(x[k]) > 0 for k in ('Transactions', 'ValueINR')), "Failed: float(x['Transactions']) > 0 and float(x['ValueINR']) > 0")
for x in b:
    require(math.isfinite(float(x['Attempts'])) and float(x['Attempts']) > 0, "Failed: float(x['Attempts']) > 0")
    for k in ['ApprovedRate', 'BDRate', 'TDRate']:
        require(0 <= float(x[k]) <= 1, 'Failed: 0 <= float(x[k]) <= 1')
    require(abs(sum((float(x[k]) for k in ['ApprovedRate', 'BDRate', 'TDRate'])) - 1) < 0.00021, "Failed: abs(sum((float(x[k]) for k in ['ApprovedRate', 'BDRate', 'TDRate'])) - 1) < 0.00021")
last = [x for x in b if x['Month'] == '2026-03-01']
require(math.isclose(sum((float(x['Attempts']) * float(x['TDRate']) for x in last)), 55113056, abs_tol=1), "Failed: math.isclose(sum((float(x['Attempts']) * float(x['TDRate']) for x in last)), 55113056, abs_tol=1)")
require(float(n[-1]['Transactions']) == 22641110000, "Failed: float(n[-1]['Transactions']) == 22641110000")
raw = read('data/raw/national_monthly.csv')
require(len(raw) == len(n), 'Raw/processed national row counts differ')
for source, clean in zip(raw, n):
    require(source['Month'] == clean['Month'], 'Raw/processed month mismatch')
    require(float(source['VolumeMn'].replace(',', '')) * 1000000 == float(clean['Transactions']), "Failed: float(source['VolumeMn'].replace(',', '')) * 1000000 == float(clean['Transactions'])")
    require(float(source['ValueCr'].replace(',', '')) * 10000000 == float(clean['ValueINR']), "Failed: float(source['ValueCr'].replace(',', '')) * 10000000 == float(clean['ValueINR'])")
for p in R.rglob('*.json'):
    json.loads(p.read_text(encoding='utf-8'))
require(not list(R.rglob('*.pbix')), "Failed: not list(R.rglob('*.pbix'))")
measures = []
for p in (R / 'UPI-Payments.SemanticModel/definition/tables').glob('*.tmdl'):
    s = p.read_text(encoding='utf-8')
    measures += re.findall("measure '([^']+)'", s)
    for block in s.split('\n\tmeasure ')[1:]:
        require('formatString:' in block and 'displayFolder:' in block, "Failed: 'formatString:' in block and 'displayFolder:' in block")
require(len(measures) == 17, 'Failed: len(measures) == 17')
refs = []
for p in (R / 'UPI-Payments.Report').rglob('visual.json'):
    x = json.loads(p.read_text(encoding='utf-8'))
    for role in x['visual'].get('query', {}).get('queryState', {}).values():
        for proj in role['projections']:
            field = proj['field']
            key = next(iter(field))
            if key == 'Measure':
                require(field[key]['Property'] in measures, "Failed: field[key]['Property'] in measures")
print('PASS: 24 months; 1,199 distinct bank-month rows; 49–50 canonical labels/month; rates, unit conversions, reference totals, JSON, 17 measure formats/folders, visual measure references and PBIP-only policy.')
