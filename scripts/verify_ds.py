#!/usr/bin/env python3
"""Content and static HTML checks specific to the 2025 Data Science plan."""
from pathlib import Path
from collections import Counter
from bs4 import BeautifulSoup
from zipfile import ZipFile
import csv, hashlib, json, re, unicodedata
from documents import ROOT, DOCUMENTS

NAME = '2025-Year0-DS-Plan'
CONFIG = DOCUMENTS[NAME]
VERIFY = ROOT / CONFIG['verification']
HTML = ROOT / 'output' / NAME / 'html/index.html'
soup = BeautifulSoup(HTML.read_text(), 'html.parser')
checks = []
def check(name, condition, detail=''):
    checks.append({'check':name,'passed':bool(condition),'detail':detail})
def tokens(value):
    return re.findall(r'[a-z0-9]+',unicodedata.normalize('NFKC',value).lower())
def text(node):
    return node.get_text(' ',strip=True)
def numbered(node):
    clone=BeautifulSoup(str(node),'html.parser')
    for ol in clone.find_all('ol'):
        for i,li in enumerate(ol.find_all('li',recursive=False),int(ol.get('start',1))):
            li.insert(0,str(i)+' ')
    return text(clone)
def extracted(n,engine='pdfplumber'):
    raw=(VERIFY/f'extracted/page-{n:02d}-{engine}.txt').read_text()
    # Remove only the final standalone printed page number, after verifying it.
    assert raw.rstrip().splitlines()[-1].strip()==str(n)
    return '\n'.join(raw.rstrip().splitlines()[:-1])
def section(ident):
    node=soup.find(id=ident)
    parts=[node]
    for sibling in node.next_siblings:
        if getattr(sibling,'name','') in ('h1','h2','h3','h4'): break
        if getattr(sibling,'get',None) and 'editorial-note' in sibling.get('class',[]): continue
        parts.append(sibling)
    return numbered(''.join(str(x) for x in parts))

check('Original PDF checksum unchanged',hashlib.sha256((ROOT/(NAME+'.pdf')).read_bytes()).hexdigest()==CONFIG['sha256'])
check('Document language and title',soup.html.get('lang')=='en-US' and text(soup.title)==CONFIG['title'])
check('One main and one h1',len(soup.find_all('main'))==1 and len(soup.find_all('h1'))==1)
levels=[int(h.name[1]) for h in soup.main.find_all(re.compile('^h[1-6]$'))]
check('Heading hierarchy without skips',all(b<=a+1 for a,b in zip(levels,levels[1:])))
ids=[e['id'] for e in soup.select('[id]')]
check('Unique IDs',len(ids)==len(set(ids)))
check('Internal links resolve',all(a['href'][1:] in ids for a in soup.select('a[href^="#"]')))
check('Skip link targets focusable main',soup.select_one('a.skip-link')['href']=='#main' and soup.main.get('tabindex')=='-1')
check('Three tables with captions and scoped column/row headers',len(soup.find_all('table'))==3 and all(t.caption and t.thead and all(h.get('scope')=='col' for h in t.thead.find_all('th')) and all(r.find('th',scope='row') for r in t.tbody.find_all('tr')) for t in soup.find_all('table')))
check('Labeled keyboard-focusable table regions',all(t.parent.get('role')=='region' and t.parent.get('tabindex')=='0' and t.parent.get('aria-labelledby')==t.caption['id'] for t in soup.find_all('table')))
check('No missing-character markers or fake form inputs','\ufffd' not in text(soup.main) and not soup.select('input,textarea,select,form'))
check('Three source review notes present',all(soup.find(id=f'review-{i}') for i in range(1,4)))
check('No source images requiring alternatives',not soup.find_all('img') and all(p['embedded_images']==0 for p in json.loads((VERIFY/'source-inventory.json').read_text())['pages']))
check('Pipeline arrow sequence retained','acquisition → cleaning → analysis → visualization → modeling → communication' in text(soup.main))
check('Inclusive threshold retained in both locations',all('at least 50%' in section(i) for i in ['thresholds','portfolio-performance']))
check('Submission address preserved',bool(soup.find('a',href='mailto:programassessment@montana.edu')))

def table_data(page):
    return json.loads((VERIFY/f'extracted/page-{page:02d}-tables.json').read_text())
def compare_row(label,source,row):
    target=row.find_all(['td','th'],recursive=False)
    check(label,len(source)==len(target) and all(tokens(a or '')==tokens(text(b)) for a,b in zip(source,target)))
compare_row('Program and blank Options cell',table_data(1)[0][1],soup.select('#programs-table tbody tr')[0])
for i,row in enumerate(table_data(1)[1][1:]):
    compare_row(f'PLO {i+1} cells',[row[0],row[3]],soup.select('#plos-table tbody tr')[i])
for i,row in enumerate(table_data(2)[0][1:]):
    compare_row(f'Planning row {i+1}: outcome, courses, artifacts, three years',[*row[:3],' '.join(row[3:])],soup.select('#planning-table tbody tr')[i])

raw='\n'.join(extracted(i) for i in range(1,7))
rubric=raw[raw.index('Indicator 1:'):raw.index('Section II.')]
indicators=[x for x in re.split(r'(?=Indicator \d+\s*[:–])',rubric) if x.strip()]
check('Six rubric indicators',len(indicators)==6)
for i,source in enumerate(indicators,1):
    a,b=tokens(source),tokens(section(f'portfolio-i{i}'))
    check(f'Indicator {i}: ordered prompt, scores and all words match source',a==b,
          '' if a==b else f'Missing {dict(Counter(a)-Counter(b))}; added {dict(Counter(b)-Counter(a))}')
check('24 scoring entries with four per indicator',len(soup.main.find_all('ol'))==6 and all(len(o.find_all('li',recursive=False))==4 for o in soup.main.find_all('ol')))
clean=BeautifulSoup(str(soup.main),'html.parser')
for el in clean.select('.editorial-note,[data-editorial]'): el.decompose()
a,b=Counter(tokens(raw)),Counter(tokens(numbered(clean)))
missing,added=a-b,b-a
check('Whole-document lexical coverage; only four sub-bullet o glyphs omitted',missing==Counter({'o':4}) and not added,f'Source-only {dict(missing)}; output-only {dict(added)}')
# Every narrative paragraph and its internal word/number order must occur in the source.
raw_sequence=' '+' '.join(tokens(raw))+' '
paras=[p for p in clean.find_all('p') if not p.find_parent('table')]
for i,p in enumerate(paras,1):
    value=' '+' '.join(tokens(text(p)))+' '
    check(f'Narrative paragraph {i}: source wording and internal order',value in raw_sequence)
with ZipFile(HTML.parent.parent/'assessment-plan-html.zip') as archive:
    check('HTML ZIP integrity and current contents',archive.testzip() is None and archive.read('index.html')==HTML.read_bytes())
map_path=VERIFY/'page-map.csv'
if map_path.exists():
    with map_path.open() as f: rows=list(csv.DictReader(f))
    check('Source-page map targets resolve',all(None not in row and row['canonical_id'] in ids for row in rows))
engine_diffs=[]
for i in range(1,7):
    a,b=Counter(tokens(extracted(i))),Counter(tokens(extracted(i,'mupdf')))
    engine_diffs.append({'page':i,'pdfplumber_only':dict(a-b),'mupdf_only':dict(b-a)})
result={'scope':'Content and static HTML checks; not an accessibility conformance audit.', 'passed':sum(x['passed'] for x in checks),'total':len(checks),'checks':checks,'engine_token_differences':engine_diffs}
(VERIFY/'automated-checks.json').write_text(json.dumps(result,indent=2)+'\n')
for c in checks:
    if not c['passed']: print('FAIL',c['check'],c['detail'])
print(f"{result['passed']}/{result['total']} checks passed.")
raise SystemExit(0 if all(x['passed'] for x in checks) else 1)
