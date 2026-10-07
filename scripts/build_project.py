from pathlib import Path
import json,csv,datetime,uuid,math
R=Path(__file__).resolve().parents[1];name='UPI-Payments'; SM=R/(name+'.SemanticModel'); RP=R/(name+'.Report')
def write(p,s):p=R/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def js(p,o):write(p,json.dumps(o,indent=2,ensure_ascii=False)+'\n')
def csvout(p,rows):
 p=R/p;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def num(v):
 value = float(str(v).replace(',', '').replace('%', '').strip())
 if not math.isfinite(value): raise ValueError(f'Non-finite number: {v!r}')
 return value
def records(path):
 payload = json.loads(path.read_text(encoding='utf-8'))
 results = payload.get('data', {}).get('results')
 if payload.get('status') != 200 or not isinstance(results, list) or not results:
  raise ValueError(f'{path}: unsuccessful or empty snapshot')
 return results

def main():
 nat=[];banks=[]
 for f in sorted((R/'data/raw').glob('national-*.json')):
  for x in records(f):
   d=datetime.datetime.strptime(x['month'],'%B-%Y').date();nat.append(dict(Month=d.isoformat(),BanksLive=x['no_of_banks_live_on_upi'],VolumeMn=x['volume_in_mn'],ValueCr=x['value_in_cr']))
 for f in sorted((R/'data/raw').glob('remitter-*.json')):
  for x in records(f):
   d=datetime.datetime.strptime(x['month']+'-'+x['year'],'%b-%Y').date()
   if f.stem != 'remitter-' + d.strftime('%Y-%m'): raise ValueError(f'{f}: unexpected month {d}')
   banks.append(dict(Month=d.isoformat(),Bank=x['upi_remitter_banks'].strip(),VolumeMn=x['total_volume_in_mn'],ApprovedPct=x['approved_percent'],BusinessDeclinePct=x['bd_percent'],TechnicalDeclinePct=x['td_percent']))
 nat.sort(key=lambda x:x['Month'])
 cleanN=[dict(Month=x['Month'],BanksLive=int(num(x['BanksLive'])),Transactions=num(x['VolumeMn'])*1e6,ValueINR=num(x['ValueCr'])*1e7) for x in nat]
 with (R/'data/raw/bank_aliases.csv').open(encoding='utf-8', newline='') as stream:
  alias_rows = list(csv.DictReader(stream))
 aliases = {x['SourceBank'].strip(): x['CanonicalBank'].strip() for x in alias_rows}
 if len(aliases) != len(alias_rows) or not all(aliases.values()):
  raise ValueError('Duplicate or empty bank aliases')
 expected = {datetime.date(y,m,1).isoformat() for y in (2024,2025,2026) for m in range(1,13) if (2024,4) <= (y,m) <= (2026,3)}
 if len(nat) != 24 or {r['Month'] for r in nat} != expected:
  raise ValueError('Expected exactly one national row per month, April 2024 through March 2026')
 counts = {}
 for row in banks:
  counts[row['Month']] = counts.get(row['Month'], 0) + 1
  if not aliases.get(row['Bank']): raise ValueError(f"Unmapped bank: {row['Bank']!r}; update bank_aliases.csv")
  if num(row['VolumeMn']) <= 0: raise ValueError(f'Invalid remitter volume: {row}')
  rates = [num(row[k]) for k in ('ApprovedPct','BusinessDeclinePct','TechnicalDeclinePct')]
  if any(not 0 <= r <= 100 for r in rates) or abs(sum(rates)-100) >= 0.021:
   raise ValueError(f'Invalid remitter percentages: {row}')
 if set(counts) != expected or set(counts.values()) != {50}:
  raise ValueError('Expected 50 remitter entries in each of the 24 months')
 for row in nat:
  if num(row['BanksLive']) <= 0 or not num(row['BanksLive']).is_integer() or num(row['VolumeMn']) <= 0 or num(row['ValueCr']) <= 0:
   raise ValueError(f'Invalid national values: {row}')
 csvout('data/raw/national_monthly.csv',nat)
 csvout('data/raw/remitter_monthly.csv',banks)
 cleanB=[dict(Month=x['Month'],Bank=aliases[x['Bank']],Attempts=num(x['VolumeMn'])*1e6,ApprovedRate=num(x['ApprovedPct'])/100,BDRate=num(x['BusinessDeclinePct'])/100,TDRate=num(x['TechnicalDeclinePct'])/100) for x in banks]
 # Consolidate repeated published labels at bank-month grain using weighted rates.
 groups = {}
 for row in cleanB:
     groups.setdefault((row['Month'], row['Bank']), []).append(row)
 cleanB = [dict(Month=month, Bank=bank, Attempts=sum(r['Attempts'] for r in rows), **{k: sum(r['Attempts']*r[k] for r in rows)/sum(r['Attempts'] for r in rows) for k in ['ApprovedRate','BDRate','TDRate']}) for (month,bank),rows in groups.items()]
 csvout('data/processed/national.csv',cleanN);csvout('data/processed/remitter.csv',cleanB)
 js(name+'.pbip',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json','version':'1.0','artifacts':[{'report':{'path':name+'.Report'}}],'settings':{'enableAutoRecovery':True}})
 js(name+'.Report/definition.pbir',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../'+name+'.SemanticModel'}}})
 js(name+'.SemanticModel/definition.pbism',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json','version':'1.0','settings':{}})
 write(name+'.SemanticModel/definition/database.tmdl','database Unknown\n\tcompatibilityLevel: 1601\n\tcompatibilityMode: powerBI\n')
 write(name+'.SemanticModel/definition/model.tmdl',"model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tdiscourageImplicitMeasures\n\tsourceQueryCulture: en-US\n\tdataAccessOptions\n\t\tlegacyRedirects\n\t\treturnErrorValuesAsNull\n\nannotation __PBI_TimeIntelligenceEnabled = 0\n\n"+''.join(f'ref table {t}\n' for t in ['Dim_Date','Dim_Bank','Fact_National','Fact_Remitter'])+'\nref expression DataRoot\nref expression Raw_National\nref expression Raw_Remitter\n')
 expressions='''expression DataRoot = "C:\\Projects\\upi-payments-dashboard\\data\\raw" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]
\tannotation PBI_ResultType = Text

expression Raw_National =
\t\tlet
\t\t    Source = Csv.Document(File.Contents(DataRoot & "/national_monthly.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
\t\t    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
\t\t    Trimmed = Table.TransformColumns(Headers, List.Transform(Table.ColumnNames(Headers), each {_, Text.Trim, type text})),
\t\t    NumberText = Table.TransformColumns(Trimmed, List.Transform({"BanksLive", "VolumeMn", "ValueCr"}, each {_, (v) => Number.FromText(Text.Replace(v, ",", ""), "en-US"), type number})),
\t\t    Typed = Table.TransformColumnTypes(NumberText, {{"Month", type date}, {"BanksLive", Int64.Type}}),
\t\t    Volume = Table.AddColumn(Typed, "Transactions", each [VolumeMn] * 1000000, type number),
\t\t    Value = Table.AddColumn(Volume, "ValueINR", each [ValueCr] * 10000000, type number),
\t\t    Selected = Table.SelectColumns(Value, {"Month", "BanksLive", "Transactions", "ValueINR"})
\t\t in Selected
\tannotation PBI_ResultType = Table

expression Raw_Remitter =
\t\tlet
\t\t    Source = Csv.Document(File.Contents(DataRoot & "/remitter_monthly.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
\t\t    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
\t\t    Trimmed = Table.TransformColumns(Headers, List.Transform(Table.ColumnNames(Headers), each {_, Text.Trim, type text})),
\t\t    Volume = Table.TransformColumns(Trimmed, {{"VolumeMn", each Number.FromText(Text.Replace(_, ",", ""), "en-US") * 1000000, type number}}),
\t\t    Rates = Table.TransformColumns(Volume, List.Transform({"ApprovedPct", "BusinessDeclinePct", "TechnicalDeclinePct"}, each {_, (v) => Number.FromText(Text.Replace(v, "%", ""), "en-US") / 100, type number})),
\t\t    AliasSource = Csv.Document(File.Contents(DataRoot & "/bank_aliases.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
\t\t    AliasHeaders = Table.PromoteHeaders(AliasSource, [PromoteAllScalars=true]),
\t\t    Aliases = Table.TransformColumns(AliasHeaders, {{"SourceBank", Text.Trim, type text}, {"CanonicalBank", Text.Trim, type text}}),
\t\t    Joined = Table.NestedJoin(Rates, {"Bank"}, Aliases, {"SourceBank"}, "Alias", JoinKind.LeftOuter),
\t\t    Expanded = Table.ExpandTableColumn(Joined, "Alias", {"CanonicalBank"}),
\t\t    NoMissingAliases = if List.Contains(Expanded[CanonicalBank], null) then error "Unmapped bank: update bank_aliases.csv" else Expanded,
\t\t    RemovedSource = Table.RemoveColumns(NoMissingAliases, {"Bank"}),
\t\t    BankNames = Table.RenameColumns(RemovedSource, {{"CanonicalBank", "Bank"}}),
\t\t    Typed = Table.TransformColumnTypes(BankNames, {{"Month", type date}}),
\t\t    Renamed = Table.RenameColumns(Typed, {{"VolumeMn", "Attempts"}, {"ApprovedPct", "ApprovedRate"}, {"BusinessDeclinePct", "BDRate"}, {"TechnicalDeclinePct", "TDRate"}})
\t\t in Table.Group(Renamed, {"Month", "Bank"}, {{"Attempts", each List.Sum([Attempts]), type number}, {"ApprovedRate", each List.Sum(List.Transform(Table.ToRecords(_), (r) => r[Attempts] * r[ApprovedRate])) / List.Sum([Attempts]), type number}, {"BDRate", each List.Sum(List.Transform(Table.ToRecords(_), (r) => r[Attempts] * r[BDRate])) / List.Sum([Attempts]), type number}, {"TDRate", each List.Sum(List.Transform(Table.ToRecords(_), (r) => r[Attempts] * r[TDRate])) / List.Sum([Attempts]), type number}})
\tannotation PBI_ResultType = Table
'''
 # Keep a configured path across rebuilds; new checkouts use their local raw folder.
 expression_path = SM/'definition/expressions.tmdl'
 import re
 existing = expression_path.read_text(encoding='utf-8') if expression_path.exists() else ''
 match = re.search(r'^expression DataRoot = ("(?:[^"]|"")*") meta', existing, re.MULTILINE)
 root_value = match.group(1) if match else '"' + (R/'data/raw').as_posix().replace('"','""') + '"'
 expressions = re.sub(r'^expression DataRoot = .*? meta', lambda _: 'expression DataRoot = ' + root_value + ' meta', expressions, count=1, flags=re.MULTILINE)
 write(name+'.SemanticModel/definition/expressions.tmdl',expressions)
 measures=[
 ('Total Transactions','SUM(Fact_National[Transactions])','#,0','Adoption'),('Total Value INR','SUM(Fact_National[ValueINR])','₹#,0','Adoption'),
 ('Avg Transaction Value','DIVIDE([Total Value INR], [Total Transactions])','₹#,0.00','Adoption'),
 ('Active Months','DISTINCTCOUNT(Fact_National[Month])','0','Coverage'),('Banks Live Latest','VAR LastMonth = MAX(Fact_National[Month]) RETURN CALCULATE(MAX(Fact_National[BanksLive]), Fact_National[Month] = LastMonth)','0','Coverage'),
 ('MoM Growth %','VAR CurrentMonth = MAX(Fact_National[Month]) VAR CurrentVolume = CALCULATE([Total Transactions], REMOVEFILTERS(Dim_Date), Fact_National[Month] = CurrentMonth) VAR PreviousVolume = CALCULATE([Total Transactions], REMOVEFILTERS(Dim_Date), Fact_National[Month] = EDATE(CurrentMonth, -1)) RETURN IF(NOT ISBLANK(CurrentVolume) && NOT ISBLANK(PreviousVolume), DIVIDE(CurrentVolume - PreviousVolume, PreviousVolume))','0.00%','Growth'),
 ('YoY Growth %','VAR CurrentMonth = MAX(Fact_National[Month]) VAR CurrentVolume = CALCULATE([Total Transactions], REMOVEFILTERS(Dim_Date), Fact_National[Month] = CurrentMonth) VAR PreviousVolume = CALCULATE([Total Transactions], REMOVEFILTERS(Dim_Date), Fact_National[Month] = EDATE(CurrentMonth, -12)) RETURN IF(NOT ISBLANK(CurrentVolume) && NOT ISBLANK(PreviousVolume), DIVIDE(CurrentVolume - PreviousVolume, PreviousVolume))','0.00%','Growth'),
 ('Rolling 3 Month Avg','VAR CurrentMonth = MAX(Fact_National[Month]) VAR WindowMonths = FILTER(ALL(Dim_Date), Dim_Date[Date] >= EDATE(CurrentMonth, -2) && Dim_Date[Date] <= EOMONTH(CurrentMonth, 0)) VAR MonthCount = CALCULATE(DISTINCTCOUNT(Fact_National[Month]), REMOVEFILTERS(Dim_Date), WindowMonths) RETURN IF(MonthCount = 3, DIVIDE(CALCULATE([Total Transactions], REMOVEFILTERS(Dim_Date), WindowMonths), 3))','#,0','Growth'),
 ('Growth Status','IF(ISBLANK([MoM Growth %]), BLANK(), IF([MoM Growth %] >= 0, 1, -1))','0','Formatting'),
 ('Average Daily Transactions','VAR DayCount = SUMX(VALUES(Fact_National[Month]), DAY(EOMONTH(Fact_National[Month], 0))) RETURN DIVIDE([Total Transactions], DayCount)','#,0','Adoption')]
 bm=[('Bank Attempts','SUM(Fact_Remitter[Attempts])','#,0','Reliability'),('Covered Banks','DISTINCTCOUNT(Fact_Remitter[Bank])','0','Coverage'),('Estimated Technical Declines','SUMX(Fact_Remitter, Fact_Remitter[Attempts] * Fact_Remitter[TDRate])','#,0','Reliability'),('Technical Decline Rate %','DIVIDE([Estimated Technical Declines], [Bank Attempts])','0.00%','Reliability'),('Business Decline Rate %','DIVIDE(SUMX(Fact_Remitter, Fact_Remitter[Attempts] * Fact_Remitter[BDRate]), [Bank Attempts])','0.00%','Reliability'),('Approved Rate %','DIVIDE(SUMX(Fact_Remitter, Fact_Remitter[Attempts] * Fact_Remitter[ApprovedRate]), [Bank Attempts])','0.00%','Reliability'),('Top 5 Share %','VAR CandidateBanks = ALLSELECTED(Dim_Bank[Bank]) VAR Ranked = TOPN(5, CandidateBanks, [Bank Attempts], DESC, Dim_Bank[Bank], ASC) RETURN DIVIDE(CALCULATE([Bank Attempts], KEEPFILTERS(Ranked)), CALCULATE([Bank Attempts], CandidateBanks))','0.00%','Concentration')]
 def table(t,cols,m,ms=(),date=False):
  s=f'table {t}\n'+('\tdataCategory: Time\n' if date else '')
  for n,e,fmt,folder in ms:s+=f"\n\tmeasure '{n}' = {e}\n\t\tformatString: {fmt}\n\t\tdisplayFolder: {folder}\n"
  for n,typ,hidden in cols:
   s+=f'\n\tcolumn {n}\n\t\tdataType: {typ}\n'+('\t\tisHidden\n' if hidden else '')+'\t\tsummarizeBy: none\n'+f'\t\tsourceColumn: {n}\n'
   if typ=='dateTime':s+='\t\tformatString: yyyy-MM-dd\n'
   if date and n=='Date':s+='\t\tisKey\n\n\t\tannotation UnderlyingDateTimeDataType = Date\n'
   if n=='MonthLabel':s+='\t\tsortByColumn: MonthKey\n'
  s+=f'\n\tpartition {t} = m\n\t\tmode: import\n\t\tsource =\n'+''.join('\t\t\t\t'+l+'\n' for l in m.splitlines())
  write(name+f'.SemanticModel/definition/tables/{t}.tmdl',s)
 table('Fact_National',[('Month','dateTime',True),('BanksLive','int64',True),('Transactions','double',True),('ValueINR','double',True)],'Raw_National',measures)
 table('Fact_Remitter',[('Month','dateTime',True),('Bank','string',True),('Attempts','double',True),('ApprovedRate','double',True),('BDRate','double',True),('TDRate','double',True)],'Raw_Remitter',bm)
 table('Dim_Bank',[('Bank','string',False)],'let\n    Source = Table.Distinct(Table.SelectColumns(Raw_Remitter, {"Bank"})),\n    Sorted = Table.Sort(Source, {{"Bank", Order.Ascending}})\nin Sorted')
 table('Dim_Date',[('Date','dateTime',False),('Year','int64',False),('MonthKey','int64',True),('MonthLabel','string',False)],'''let
    Start = Date.StartOfYear(List.Min(Raw_National[Month])),
    End = Date.EndOfYear(List.Max(Raw_National[Month])),
    Dates = Table.FromList(List.Dates(Start, Duration.Days(End - Start) + 1, #duration(1,0,0,0)), Splitter.SplitByNothing(), {"Date"}),
    Typed = Table.TransformColumnTypes(Dates, {{"Date", type date}}),
    Year = Table.AddColumn(Typed, "Year", each Date.Year([Date]), Int64.Type),
    Key = Table.AddColumn(Year, "MonthKey", each Date.Year([Date])*100 + Date.Month([Date]), Int64.Type),
    Label = Table.AddColumn(Key, "MonthLabel", each Date.ToText([Date], "yyyy-MM", "en-US"), type text)
in Label''',date=True)
 rels=''
 for fact,col,dim,key in [('Fact_National','Month','Dim_Date','Date'),('Fact_Remitter','Month','Dim_Date','Date'),('Fact_Remitter','Bank','Dim_Bank','Bank')]:
  rels+=f'relationship {uuid.uuid5(uuid.NAMESPACE_DNS,fact+dim)}\n\tfromColumn: {fact}.{col}\n\ttoColumn: {dim}.{key}\n\tcrossFilteringBehavior: oneDirection\n\n'
 write(name+'.SemanticModel/definition/relationships.tmdl',rels)
 # Enhanced report definition, chart query projections refer to explicit measures.
 base='https://developer.microsoft.com/json-schemas/fabric/item/report/definition/'
 js(name+'.Report/definition/version.json',{'$schema':base+'versionMetadata/1.0.0/schema.json','version':'2.0.0'})
 js(name+'.Report/definition/report.json',{'$schema':base+'report/2.0.0/schema.json','themeCollection':{'baseTheme':{'name':'CY24SU02','reportVersionAtImport':'5.55','type':'SharedResources'}},'settings':{'useDefaultAggregateDisplayName':True}})
 pages=['NationalAdoption','BankReliability'];js(name+'.Report/definition/pages/pages.json',{'$schema':base+'pagesMetadata/1.0.0/schema.json','pageOrder':pages,'activePageName':pages[0]})
 def col(t,n):return {'Column':{'Expression':{'SourceRef':{'Entity':t}},'Property':n}}
 def measure(t,n):return {'Measure':{'Expression':{'SourceRef':{'Entity':t}},'Property':n}}
 def visual(page,n,typ,roles,title,pos):
  q={}
  for role,fields in roles.items():q[role]={'projections':[{'field':field,'queryRef':t+'.'+p,'nativeQueryRef':p} for field,t,p in fields]}
  v={'visualType':typ,'query':{'queryState':q},'drillFilterOtherVisuals':True,'visualContainerObjects':{'title':[{'properties':{'show':{'expr':{'Literal':{'Value':'true'}}},'text':{'expr':{'Literal':{'Value':"'"+title.replace("'","''")+"'"}}}}}]}}
  if typ in ['lineChart','tableEx','barChart']:
   role = 'Category' if typ == 'lineChart' else ('Y' if typ == 'barChart' else 'Values')
   chosen = roles[role][0]
   if n == 'FailureHotspots': chosen = roles['Values'][3]
   v['query']['sortDefinition'] = {'sort':[{'field':chosen[0], 'direction':'Ascending' if typ == 'lineChart' or page == 'NationalAdoption' else 'Descending'}], 'isDefaultSort':False}
  js(name+f'.Report/definition/pages/{page}/visuals/{n}/visual.json',{'$schema':base+'visualContainer/2.1.0/schema.json','name':n,'position':dict(zip(['x','y','width','height','z'],pos)),'visual':v})
 def mf(t,n):return measure(t,n),t,n
 def cf(t,n):return col(t,n),t,n
 for p,display in zip(pages,['UPI | National adoption','UPI | Bank reliability — covered top 50']):js(name+f'.Report/definition/pages/{p}/page.json',{'$schema':base+'page/1.0.0/schema.json','name':p,'displayName':display,'displayOption':'FitToPage','height':800,'width':1280})
 for i,(n,title) in enumerate([('Total Transactions','Transactions | selected months'),('Total Value INR','Value INR | selected months'),('MoM Growth %','MoM | latest selected month'),('Avg Transaction Value','Average payment INR')]):visual(pages[0],['TotalTransactions','TotalValue','MoMGrowth','AveragePayment'][i],'card',{'Values':[mf('Fact_National',n)]},title,[20+i*310,20,300,140,i])
 visual(pages[0],'MonthlyVolumeTrend','lineChart',{'Category':[cf('Dim_Date','MonthLabel')],'Y':[mf('Fact_National','Total Transactions'),mf('Fact_National','Rolling 3 Month Avg')]},'Monthly volume and 3-month average',[20,180,830,380,5])
 visual(pages[0],'MonthFilter','slicer',{'Values':[cf('Dim_Date','MonthLabel')]},'Select months',[870,180,390,380,6])
 visual(pages[0],'MonthlySummary','tableEx',{'Values':[cf('Dim_Date','MonthLabel'),mf('Fact_National','Total Transactions'),mf('Fact_National','YoY Growth %'),mf('Fact_National','Average Daily Transactions')]},'Read growth with month length and prior-year context',[20,580,1240,200,7])
 for i,(n,title) in enumerate([('Bank Attempts','Covered remitter attempts'),('Technical Decline Rate %','Weighted technical decline'),('Estimated Technical Declines','Estimated technical declines'),('Top 5 Share %','Top 5 share | selected banks')]):visual(pages[1],['CoveredAttempts','WeightedTD','EstimatedTD','TopFiveShare'][i],'card',{'Values':[mf('Fact_Remitter',n)]},title,[20+i*310,20,300,140,i])
 visual(pages[1],'BankVolume','barChart',{'Category':[cf('Dim_Bank','Bank')],'Y':[mf('Fact_Remitter','Bank Attempts')]},'Bank attempts | covered top 50 each month',[20,180,600,340,5])
 visual(pages[1],'ReliabilityTrend','lineChart',{'Category':[cf('Dim_Date','MonthLabel')],'Y':[mf('Fact_Remitter','Technical Decline Rate %')]},'Weighted technical decline by month',[640,180,400,340,6])
 visual(pages[1],'BankFilter','slicer',{'Values':[cf('Dim_Bank','Bank')]},'Select banks',[1060,180,200,340,7])
 visual(pages[1],'MonthFilter','slicer',{'Values':[cf('Dim_Date','MonthLabel')]},'Select months',[1060,540,200,240,8])
 visual(pages[1],'FailureHotspots','tableEx',{'Values':[cf('Dim_Bank','Bank'),mf('Fact_Remitter','Bank Attempts'),mf('Fact_Remitter','Technical Decline Rate %'),mf('Fact_Remitter','Estimated Technical Declines'),mf('Fact_Remitter','Business Decline Rate %')]},'Hotspots: compare estimated impact alongside rate',[20,540,1020,240,9])
 if not (R/'.gitignore').exists(): write('.gitignore','*.pbix\n**/.pbi/localSettings.json\n**/.pbi/cache.abf\n**/.pbi/unappliedChanges.json\n.cache/\n**/.cache/\n__pycache__/\n.venv/\n.DS_Store\n')
 # Compute reproducible evidence
 latest=cleanN[-1];prev=cleanN[-2];yearago=cleanN[-13];start=cleanN[0]
 latestB=[x for x in cleanB if x['Month']==latest['Month']];attempts=sum(x['Attempts'] for x in latestB);td=sum(x['Attempts']*x['TDRate'] for x in latestB)
 ins={'period':[start['Month'],latest['Month']],'national_months':len(cleanN),'bank_month_rows':len(cleanB),'unique_banks':len(set(x['Bank'] for x in cleanB)),'latest_month':latest,'growth_from_first_month':latest['Transactions']/start['Transactions']-1,'latest_mom':latest['Transactions']/prev['Transactions']-1,'latest_yoy':latest['Transactions']/yearago['Transactions']-1,'latest_weighted_td':td/attempts,'latest_estimated_td':td,'latest_top5_share':sum(x['Attempts'] for x in sorted(latestB,key=lambda x:-x['Attempts'])[:5])/attempts,'latest_hotspots':sorted(latestB,key=lambda x:-x['Attempts']*x['TDRate'])[:5]}
 js('docs/insights.json',ins);print(json.dumps(ins,indent=2))
 # Theme and fixed scope notes belong to the report; notes are not dynamic claims.
 theme={'name':'UPI Teal','dataColors':['#0F766E','#6366F1','#D97706','#64748B'],'background':'#FFFFFF','foreground':'#0F172A','tableAccent':'#0F766E','textClasses':{'label':{'fontFace':'Segoe UI','fontSize':11},'title':{'fontFace':'Segoe UI','fontSize':13},'callout':{'fontFace':'Segoe UI','fontSize':28}}}
 js(name+'.Report/StaticResources/RegisteredResources/UPITheme.json',theme)
 p=RP/'definition/report.json';report=json.loads(p.read_text(encoding='utf-8'));report['themeCollection']['customTheme']={'name':'UPITheme','reportVersionAtImport':'5.55','type':'RegisteredResources'};report['resourcePackages']=[{'name':'RegisteredResources','type':'RegisteredResources','items':[{'name':'UPITheme','path':'UPITheme.json','type':'CustomTheme'}]}];js(name+'.Report/definition/report.json',report)
 for page,text in [('NationalAdoption','Read MoM with month length and YoY context. Transaction volume measures usage, not unique customers. This is a fixed April 2024–March 2026 snapshot.'),('BankReliability','Prioritize estimated declined attempts alongside TD rate. Covered top-50 entries change each month; missing banks are unknown. Rounded rates yield estimates, not exact event counts.')]:
  p=RP/'definition/pages'/page/'page.json';d=json.loads(p.read_text(encoding='utf-8'));d['height']=900;js(str(p.relative_to(R)),d)
  js(name+f'.Report/definition/pages/{page}/visuals/ScopeAndInterpretation/visual.json',{'$schema':base+'visualContainer/2.1.0/schema.json','name':'ScopeAndInterpretation','position':{'x':20,'y':800,'width':1240,'height':80,'z':10},'visual':{'visualType':'textbox','objects':{'general':[{'properties':{'paragraphs':[{'textRuns':[{'value':text,'textStyle':{'fontSize':'12pt','fontFamily':'Segoe UI','color':'#334155'}}]}]}}]},'drillFilterOtherVisuals':True}})


if __name__ == '__main__':
 main()
