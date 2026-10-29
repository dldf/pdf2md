#!/usr/bin/env python3
"""Pilot-specific content fidelity and static HTML checks; not a conformance test."""
from pathlib import Path
from collections import Counter
from bs4 import BeautifulSoup
import hashlib
import json
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / 'output/2023-BA-Year0-Plan/html/index.html'
soup = BeautifulSoup(HTML.read_text(), 'html.parser')
checks = []
def check(name, condition, detail=''):
    checks.append({'check': name, 'passed': bool(condition), 'detail': detail})
def tokens(s):
    return re.findall(r'[a-z0-9]+', unicodedata.normalize('NFKC', s).lower().replace('’', "'"))
def text(el):
    return el.get_text(' ', strip=True)
def extracted(page):
    return (ROOT / f'verification/extracted/page-{page:02d}-pdfplumber.txt').read_text()
def numbered(el):
    clone = BeautifulSoup(str(el), 'html.parser')
    for ol in clone.find_all('ol'):
        for i, li in enumerate(ol.find_all('li', recursive=False), int(ol.get('start', 1))):
            label = chr(96+i) if ol.get('type') == 'a' else str(i)
            li.insert(0, label + ' ')
    return clone.get_text(' ', strip=True)
def section(ident):
    h = soup.find(id=ident)
    parts = [h]
    for sibling in h.next_siblings:
        if getattr(sibling, 'name', '') in ('h1','h2','h3','h4'):
            break
        if getattr(sibling, 'get', None) and 'editorial-note' in sibling.get('class', []):
            continue
        parts.append(sibling)
    return numbered(''.join(str(p) for p in parts))

check('Original PDF SHA-256 unchanged', hashlib.sha256((ROOT/'2023-BA-Year0-Plan.pdf').read_bytes()).hexdigest() == '1625ff6a4f7b8d0397b09b8b0a934fde01f32fd22b9b3c0a46c5313f4d8389e1')
check('English document language', soup.html.get('lang') == 'en-US')
check('Nonempty document title', bool(text(soup.title)))
check('One main landmark and one level-one heading', len(soup.find_all('main')) == 1 and len(soup.find_all('h1')) == 1)
headings = [int(h.name[1]) for h in soup.main.find_all(re.compile('^h[1-6]$'))]
check('Heading levels do not skip', all(b <= a+1 for a,b in zip(headings,headings[1:])))
ids = [e['id'] for e in soup.select('[id]')]
check('Unique element IDs', len(ids) == len(set(ids)))
check('Internal link targets exist', all(a['href'][1:] in ids for a in soup.select('a[href^="#"]')))
check('Skip link targets focusable main', soup.select_one('a.skip-link')['href'] == '#main' and soup.main.get('tabindex') == '-1')
check('Every table has caption and scoped headers', all(t.caption and t.thead and all(h.get('scope') in ('row','col') for h in t.find_all('th')) and all(r.find('th',scope='row') for r in t.tbody.find_all('tr')) for t in soup.find_all('table')))
check('Images have nonempty alt and existing local files', all(i.get('alt','').strip() and (HTML.parent / i['src']).is_file() for i in soup.find_all('img')))
check('No replacement characters', '\ufffd' not in text(soup.main))
check('Mathematical symbols retained', 'k << n' in text(soup.main))
check('All six review notices present', all(soup.find(id=f'review-{i}') for i in range(1,7)))
check('No fake form controls or submitted answers', not soup.select('input,textarea,select,form'))

# Compare each exam question and portfolio indicator, including all score labels,
# against the independent pdfplumber text. Punctuation and case are normalized.
raw_exam = '\n'.join(extracted(i) for i in range(5,9))
raw_exam = raw_exam[raw_exam.index('Question 1 ('):raw_exam.index('Section II.')]
qs = re.split(r'(?=Question \d+ \()',raw_exam)
qs = [q for q in qs if q.strip()]
check('Exam question count',len(qs)==12)
for i, q in enumerate(qs,1):
    a,b=tokens(q),tokens(section(f'exam-q{i}'))
    check(f'Exam question {i}: ordered words, numbers and score labels match source', a==b,
          '' if a==b else f'source-only {dict(Counter(a)-Counter(b))}; output-only {dict(Counter(b)-Counter(a))}')
raw_portfolio='\n'.join(extracted(i) for i in range(9,12))
raw_portfolio=raw_portfolio[raw_portfolio.index('Indicator 1:'):raw_portfolio.index('Section II.')]
indicators=[x for x in re.split(r'(?=Indicator \d+:)',raw_portfolio) if x.strip()]
check('Portfolio indicator count',len(indicators)==7)
for i,q in enumerate(indicators,1):
    a,b=tokens(q),tokens(section(f'portfolio-i{i}'))
    check(f'Portfolio indicator {i}: ordered words, numbers and score labels match source',a==b,
          '' if a==b else f'source-only {dict(Counter(a)-Counter(b))}; output-only {dict(Counter(b)-Counter(a))}')

# Cell comparisons use table geometry from pdfplumber, visually checked against PNGs.
def table_data(p):
    return json.loads((ROOT/f'verification/extracted/page-{p:02d}-tables.json').read_text())
def compare_row(name, source_cells, target_row):
    target_cells=target_row.find_all(['td','th'],recursive=False)
    check(name, len(source_cells)==len(target_cells) and all(tokens(a or '')==tokens(text(b)) for a,b in zip(source_cells,target_cells)))
compare_row('Program table: populated row and blank Options cell',table_data(1)[0][1],soup.select('#programs-table tbody tr')[0])
for i,row in enumerate(table_data(1)[1][1:]):
    compare_row(f'PLO table row {i+1}',[row[0],row[3]],soup.select('#plos-table tbody tr')[i])
compare_row('Threshold table: all three data cells',table_data(2)[0][2],soup.select('#thresholds-table tbody tr')[0])
rows=[[r[0],r[2],r[3],' '.join(r[4:7])] for r in table_data(2)[1][2:]]
rows += [[*r[:3], ' '.join(r[3:])] for r in table_data(3)[0]]
for i,row in enumerate(rows):
    compare_row(f'Planning chart row {i+1}: outcome, courses, artifacts and three years',row,soup.select('#planning-table tbody tr')[i])

# Whole-document lexical coverage is a loss detector, not reading-order proof.
clean=BeautifulSoup(str(soup.main),'html.parser')
for e in clean.select('.editorial-note, .editorial-label, details, [data-editorial]'):
    e.decompose()
source_words=Counter(tokens('\n'.join(extracted(i) for i in range(1,16))))
output_words=Counter(tokens(numbered(clean)))
missing=source_words-output_words
added=output_words-source_words
# Source circles have text values 0 (30), O and Q; added 1..6 label the survey list.
expected_missing=Counter({'0':30,'o':1,'q':1})
expected_added=Counter({str(i):1 for i in range(1,7)})
check('Whole-document lexical coverage: only documented survey markers/list numbers differ',missing==expected_missing and added==expected_added,
      f'source-only {dict(missing)}; output-only {dict(added)}')
# Independent engines: record disagreements to aid review; not a pass/fail equivalence assertion.
engine_diffs=[]
for i in range(1,16):
    a=Counter(tokens(extracted(i)))
    b=Counter(tokens((ROOT/f'verification/extracted/page-{i:02d}-mupdf.txt').read_text()))
    engine_diffs.append({'page':i,'pdfplumber_only':dict(a-b),'mupdf_only':dict(b-a)})
result={'scope':'Static and content checks only; no accessibility conformance claim.',
        'passed':sum(c['passed'] for c in checks),'total':len(checks),'checks':checks,'engine_token_differences':engine_diffs}
(ROOT/'verification/automated-checks.json').write_text(json.dumps(result,indent=2)+'\n')
for c in checks:
    if not c['passed']: print('FAIL',c['check'],c['detail'])
print(f"{result['passed']}/{result['total']} checks passed. See verification/automated-checks.json")
raise SystemExit(0 if all(c['passed'] for c in checks) else 1)
