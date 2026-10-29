#!/usr/bin/env python3
"""Build HTML exclusively from canonical Markdown and presentation template."""
from pathlib import Path
import shutil
import subprocess
import zipfile
from bs4 import BeautifulSoup

from documents import ROOT, select_document, verify_input
PDF_STEM, config = select_document()
verify_input(config)
SOURCE = ROOT / config['source']
OUTPUT_DIR = ROOT / 'output' / PDF_STEM
OUT = OUTPUT_DIR / 'html'
OUT.mkdir(parents=True, exist_ok=True)
result = subprocess.run([
    'pandoc', str(SOURCE),
    '--from=markdown+raw_html+fenced_divs+header_attributes+fancy_lists-smart',
    '--to=html5', '--metadata=pagetitle:' + config['title'], '--standalone', '--toc', '--toc-depth=2', '--wrap=none',
    '--template=' + str(ROOT / 'source/template.html'),
], check=True, capture_output=True, text=True)
soup = BeautifulSoup(result.stdout, 'html.parser')
for table in soup.select('main table'):
    caption = table.find('caption')
    caption['id'] = table['id'] + '-caption'
    region = soup.new_tag('div', attrs={'class': 'table-region', 'role': 'region', 'tabindex': '0',
                                      'aria-labelledby': caption['id']})
    table.wrap(region)
for img in soup.select('main img'):
    source = (SOURCE.parent / img['src']).resolve()
    if not source.is_relative_to(ROOT / 'assets'):
        raise ValueError('Image must come from the canonical assets directory')
    (OUT / 'assets').mkdir(exist_ok=True)
    shutil.copyfile(source, OUT / 'assets' / source.name)
    img['src'] = 'assets/' + source.name
(OUT / 'index.html').write_text(str(soup) + '\n', encoding='utf-8')
with zipfile.ZipFile(OUTPUT_DIR / 'assessment-plan-html.zip', 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(OUT.rglob('*')):
        if path.is_file():
            info = zipfile.ZipInfo(str(path.relative_to(OUT)), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
print(f'Built output/{PDF_STEM}/html/index.html and output/{PDF_STEM}/assessment-plan-html.zip.')
