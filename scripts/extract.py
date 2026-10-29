#!/usr/bin/env python3
"""Read-only extraction; never edits the PDF or canonical Markdown."""
import hashlib
import json
import platform
import importlib.metadata
import pymupdf
import pdfplumber
from documents import ROOT, select_document

name, config = select_document()
PDF = ROOT / (name + '.pdf')
VERIFY = ROOT / config['verification']
digest = hashlib.sha256(PDF.read_bytes()).hexdigest()
if digest != config['sha256']:
    raise SystemExit('Source PDF differs from the inspected original. Review before proceeding.')
for directory in (VERIFY / 'pages', VERIFY / 'extracted'):
    directory.mkdir(parents=True, exist_ok=True)
report = {'source': PDF.name, 'sha256': digest, 'python': platform.python_version(),
          'tools': {p: importlib.metadata.version(p) for p in ('pymupdf', 'pdfplumber', 'beautifulsoup4')},
          'pages': []}
with pymupdf.open(PDF) as doc:
    report['metadata'] = doc.metadata
    report['catalog'] = doc.xref_object(doc.pdf_catalog())
    for i, page in enumerate(doc, 1):
        prefix = VERIFY / f'extracted/page-{i:02d}'
        text = page.get_text(sort=True)
        prefix.with_name(prefix.name + '-mupdf.txt').write_text(text, encoding='utf-8')
        prefix.with_name(prefix.name + '-blocks.json').write_text(json.dumps(page.get_text('dict'), indent=2), encoding='utf-8')
        image = page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5))
        image.save(VERIFY / f'pages/page-{i:02d}.png')
        if i in config['evidence_pages']:
            dest = ROOT / config['evidence_pages'][i]
            dest.parent.mkdir(parents=True, exist_ok=True)
            image.save(dest)
        report['pages'].append({'page': i, 'size_points': list(page.rect), 'text_characters': len(text),
                                'embedded_images': len(page.get_images()), 'vector_drawings': len(page.get_drawings()),
                                'form_widgets': len(list(page.widgets() or [])), 'links': page.get_links()})
with pdfplumber.open(PDF) as doc:
    for i, page in enumerate(doc.pages, 1):
        text = page.extract_text(layout=False) or ''
        (VERIFY / f'extracted/page-{i:02d}-pdfplumber.txt').write_text(text, encoding='utf-8')
        tables = page.extract_tables()
        if tables:
            (VERIFY / f'extracted/page-{i:02d}-tables.json').write_text(json.dumps(tables, indent=2), encoding='utf-8')
(VERIFY / 'source-inventory.json').write_text(json.dumps(report, indent=2, default=list), encoding='utf-8')
print(f'Extracted and rendered {len(report["pages"])} pages for {name}; source hash verified. Canonical Markdown untouched.')
