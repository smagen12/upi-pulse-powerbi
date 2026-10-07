from pathlib import Path
import csv,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch
R=Path(__file__).resolve().parents[1]
N=list(csv.DictReader((R/'data/processed/national.csv').open(encoding='utf-8', newline='')));B=list(csv.DictReader((R/'data/processed/remitter.csv').open(encoding='utf-8', newline='')));I=json.loads((R/'docs/insights.json').read_text(encoding='utf-8'))
(R/'screenshots').mkdir(parents=True, exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#334155','xtick.color':'#475569','ytick.color':'#475569','axes.titleweight':'bold','axes.edgecolor':'#CBD5E1'})
def base(title,sub):
 fig=plt.figure(figsize=(16,10),facecolor='#F1F5F9');fig.text(.04,.95,title,size=25,weight='bold',color='#0F172A');fig.text(.04,.915,sub,size=11,color='#475569');fig.text(.04,.025,'NPCI public snapshots  |  Source-data preview — not a Power BI Desktop screenshot  |  Sameer Maayiz Sirajudeen',size=10,color='#64748B');return fig

def kpis(fig,items):
 for j,(label,value,caption) in enumerate(items):
  x=.04+j*.237
  fig.patches.append(FancyBboxPatch((x,.765),.222,.12,boxstyle='round,pad=0.008',transform=fig.transFigure,facecolor='white',edgecolor='#E2E8F0',zorder=-1))
  fig.text(x+.012,.855,label,size=10,color='#64748B');fig.text(x+.012,.804,value,size=23,weight='bold',color='#0F766E');fig.text(x+.012,.78,caption,size=9,color='#64748B')
fig=base('UPI | National adoption','April 2024–March 2026  •  24 observed months  •  Monthly aggregates; no unique-user counts')
kpis(fig,[('MARCH 2026 TRANSACTIONS','22.64 B','National product statistics'),('MARCH VALUE','INR 29.53 T','Converted from crore'),('MONTH-ON-MONTH','+11.02%','Compare shorter February'),('YEAR-ON-YEAR','+23.71%','Against March 2025')])
ax=fig.add_axes([.07,.35,.59,.34],facecolor='white');v=np.array([float(x['Transactions'])/1e9 for x in N]);xx=np.arange(len(N));roll=np.array([np.nan,np.nan]+[v[k-2:k+1].mean() for k in range(2,len(v))]);ax.plot(xx,v,lw=3,color='#0F766E',label='Monthly transactions');ax.plot(xx,roll,lw=2,color='#6366F1',ls='--',label='3-month average');ax.fill_between(xx,v,alpha=.07,color='#0F766E');ax.set_xticks(xx[::3],[x['Month'][:7] for x in N][::3]);ax.set_ylabel('Transactions (billions)');ax.set_title('Monthly usage continues to grow',loc='left',pad=18);ax.grid(axis='y',alpha=.18);ax.legend(frameon=False,loc='upper left')
ax=fig.add_axes([.73,.35,.23,.34]);ax.bar(['Apr 2024','Mar 2026'],[float(N[0]['BanksLive']),float(N[-1]['BanksLive'])],color=['#94A3B8','#0F766E'],width=.5);ax.set_title('Banks live on UPI',loc='left',pad=18);ax.set_ylabel('Published live-bank count');ax.grid(axis='y',alpha=.18)
fig.text(.07,.24,'WHAT THE NUMBERS SUGGEST',size=11,weight='bold',color='#0F766E');fig.text(.07,.195,'Monthly transaction volume grew 70.18% across the window. Use this trend to inform capacity planning.',size=12,color='#0F172A');fig.text(.07,.15,'Interpret MoM growth alongside daily volume and YoY growth: different month lengths can distort comparisons.',size=11,color='#475569');fig.text(.07,.11,'Adoption here means transaction usage. This dataset does not measure unique customers or demographic reach.',size=11,color='#475569');fig.savefig(R/'screenshots/national-data-preview.png',dpi=100);plt.close(fig)
last=[x for x in B if x['Month']=='2026-03-01'];last.sort(key=lambda x:-float(x['Attempts']))
fig=base('UPI | Bank reliability','March 2026  •  Published top-50 entries consolidated to 49 labels  •  Covered remitter scope')
kpis(fig,[('WEIGHTED TECHNICAL DECLINE','0.226%','Volume-weighted across coverage'),('ESTIMATED DECLINES','55.11 M','Published rates are rounded'),('TOP-FIVE SHARE','50.66%','Of covered remitter attempts'),('COVERED LABELS','49','Source duplicate consolidated')])
ax=fig.add_axes([.20,.36,.40,.33],facecolor='white');top=last[:8][::-1];ax.barh([x['Bank'].title() for x in top],[float(x['Attempts'])/1e9 for x in top],color='#0F766E');ax.set_xlabel('Remitter attempts (billions)');ax.set_title('Largest covered remitter entries',loc='left',pad=18);ax.grid(axis='x',alpha=.18)
ax=fig.add_axes([.72,.36,.24,.33]);hot=sorted(last,key=lambda x:-float(x['Attempts'])*float(x['TDRate']))[:5][::-1];ax.barh([x['Bank'].title().replace('State Bank Of India','SBI').replace('Central Bank Of India','Central Bank').replace('Union Bank Of India','Union Bank') for x in hot],[float(x['Attempts'])*float(x['TDRate'])/1e6 for x in hot],color='#D97706');ax.set_xlabel('Estimated technical declines (millions)');ax.set_title('Highest estimated impact',loc='left',pad=18);ax.grid(axis='x',alpha=.18)
fig.text(.07,.24,'PRIORITIZE IMPACT AND RATE TOGETHER',size=11,weight='bold',color='#0F766E');fig.text(.07,.195,'SBI: 0.16% TD → about 10.02M declined attempts. Baroda U.P.: 10.17% TD → about 9.16M.',size=12,color='#0F172A');fig.text(.07,.15,'These signals guide investigation; aggregate rates cannot establish an outage, root cause, or customer loss.',size=11,color='#475569');fig.text(.07,.11,'The changing top-50 population is not the full national ecosystem. Missing banks are unknown, not zero.',size=11,color='#475569');fig.savefig(R/'screenshots/reliability-data-preview.png',dpi=100);plt.close(fig)
fig=base('UPI | Semantic model','Documented star schema  •  Different fact populations  •  Single-direction filters')
ax=fig.add_axes([.02,.13,.96,.7]);ax.set_xlim(0,10);ax.set_ylim(0,8);ax.axis('off')
def box(x,y,title,lines,color):
 ax.add_patch(FancyBboxPatch((x,y),3.5,2.2,boxstyle='round,pad=0.08',facecolor='white',edgecolor=color,lw=2));ax.text(x+.18,y+2.0,title,size=16,weight='bold',color=color,va='top');ax.text(x+.18,y+1.4,'\n'.join(lines),size=11,color='#334155',linespacing=1.8,va='top')
box(.5,5,'Dim_Date',['Date (unique, marked key)','Year · MonthKey · MonthLabel','Contiguous daily calendar'],'#0F766E');box(6,5,'Dim_Bank',['Bank (canonical label)','Auditable alias mapping','Merger/channel boundaries retained'],'#0F766E');box(.5,.8,'Fact_National',['Month → Dim_Date','Transactions · ValueINR','BanksLive (monthly snapshot)'],'#6366F1');box(6,.8,'Fact_Remitter',['Month → Dim_Date; Bank → Dim_Bank','Attempts · ApprovedRate · BDRate','TDRate (weighted when aggregated)'],'#6366F1')
for a,b,label in [((2.25,4.9),(2.25,3.1),'1 → *'),((3.7,4.9),(6.5,3.1),'1 → *'),((7.75,4.9),(7.75,3.1),'1 → *')]:ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'->','color':'#64748B','lw':2});ax.text((a[0]+b[0])/2+.12,(a[1]+b[1])/2,label,color='#475569',size=11)
fig.text(.07,.09,'17 explicit DAX measures  •  Hidden fact columns  •  No fact-to-fact relationship  •  No unsupported geography dimension',size=12,color='#475569');fig.savefig(R/'screenshots/model-diagram.png',dpi=100);plt.close(fig)
print('Rendered three source-data/model previews')
