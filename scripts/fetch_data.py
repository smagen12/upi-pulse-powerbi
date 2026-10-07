import urllib.request, urllib.parse, concurrent.futures,json,pathlib,calendar
root=pathlib.Path(__file__).resolve().parents[1]
def f(k,u):
 try:
  with urllib.request.urlopen(u,timeout=35) as response: b=response.read()
  x=json.loads(b)
  if x.get('status')!=200 or not x.get('data',{}).get('results'): raise ValueError('unsuccessful or empty response')
  return k,b
 except Exception as e:raise RuntimeError(f'{k}: download failed') from e
def main():
 urls={}
 (root/'data/raw').mkdir(parents=True,exist_ok=True)
 for y in (2024,2025,2026):
  for m in range(1,13):
   if (y,m)<(2024,4) or (y,m)>(2026,3):continue
   p=dict(product_name='UPI',tab_name='top50-member',type_name='remitter',month=calendar.month_abbr[m],year=y,page_no=1,size=100)
   urls[f'remitter-{y}-{m:02}']='https://www.npci.org.in/api/ecosystem-statistics/get-statistics?'+urllib.parse.urlencode(p)
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex: snapshots=list(ex.map(lambda kv:f(*kv),urls.items()))


 for fiscal in ('2024-25', '2025-26'):
     url = 'https://www.npci.org.in/api/product-statistic/tab/detail?' + urllib.parse.urlencode(dict(product_name='upi', tab_name='product-statistics-upi', year_range=fiscal, excel_type='monthly', page_no=1, page_size=100))
     with urllib.request.urlopen(url, timeout=35) as response: payload = response.read()
     result = json.loads(payload)
     if result.get('status') != 200 or not result.get('data',{}).get('results'): raise RuntimeError('National source failed or empty')
     snapshots.append(('national-'+fiscal, payload))
     urls['national-'+fiscal] = url
 for key,payload in snapshots:
     temporary=root/'data/raw'/f'{key}.json.tmp'
     temporary.write_bytes(payload)
     temporary.replace(root/'data/raw'/f'{key}.json')
 (root/'data/raw'/'sources.json').write_text(json.dumps(urls,indent=2),encoding='utf-8')
 print(f'Downloaded {len(snapshots)} snapshots')


if __name__ == '__main__':
 main()
