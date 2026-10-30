#!/usr/bin/env python3
"""Create reviewable Markdown drafts from one PDF or a folder; no AI service."""
import argparse
from collections import Counter
import hashlib
from html import escape as html_escape
import json
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
from urllib.parse import quote, urlsplit

import pdfplumber
import pymupdf
from bs4 import BeautifulSoup

from preview import find_chrome, preview


def clean(text):
    return ' '.join(re.sub(r'-\s*\n\s*', '-', text or '').split())


def escape(text):
    return re.sub(r'([\\`*_\[\]<>|])', r'\\\1', clean(text))


def infer_document_font(fonts, body_size):
    """Weight body characters over headings; use known names to check font flags."""
    names = {
        'sans': ('arial', 'helvetica', 'calibri', 'aptos', 'verdana', 'tahoma', 'segoe',
                 'roboto', 'opensans', 'sourcesans', 'notosans', 'liberationsans',
                 'dejavusans', 'nimbussans'),
        'serif': ('times', 'georgia', 'cambria', 'garamond', 'palatino', 'baskerville',
                  'bookantiqua', 'liberationserif', 'dejavuserif', 'notoserif',
                  'sourceserif', 'nimbusroman'),
    }
    scores = Counter()
    unknown, conflicts = 0, 0
    for (name, flags, size), characters in fonts.items():
        name = re.sub(r'[^a-z]', '', name.split('+')[-1].lower())
        if not characters or any(token in name for token in ('symbol', 'dingbat', 'wingding')):
            continue
        weight = characters * (4 if abs(size - body_size) <= .5 else 1)
        weight *= 1 if flags & pymupdf.TEXT_FONT_BOLD else 2
        flagged = 'serif' if flags & pymupdf.TEXT_FONT_SERIFED else 'sans'
        named = next((family for family, tokens in names.items()
                      if any(token in name for token in tokens)), None)
        family = named or flagged
        scores[family] += weight
        if named is None:
            unknown += weight
        elif named != flagged:
            conflicts += weight
    total = sum(scores.values())
    if not total:
        return 'sans', 'No usable PDF font data; sans is a temporary fallback. Set font to serif or sans after review.'
    family = max(('sans', 'serif'), key=lambda name: scores[name])
    reasons = []
    if scores[family] / total < .6:
        reasons.append('mixed serif and sans body text')
    if unknown / total > .25:
        reasons.append('unrecognized font names classified using PDF flags')
    if conflicts:
        reasons.append('font names and flags disagree; recognizable names used')
    note = f'Inferred {family}: ' + '; '.join(reasons) + '. Confirm the font setting.' if reasons else ''
    return family, note


def format_spans(spans, heading=False):
    raw = ''.join(span['text'] for span in spans)
    # Markdown list markers must remain outside emphasis delimiters.
    marker = re.match(r'^\s*(?:\d{1,2}[.)]|[a-z][.)]|[•●▪])(?:\s+|$)', raw)
    skip = marker.end() if marker else 0
    prefix = clean(marker[0]) + ' ' if marker else ''
    runs = []
    for span in spans:
        text = span['text'][skip:]
        skip = max(0, skip - len(span['text']))
        if not text:
            continue
        style = span['flags'] & (2 if heading else 18)  # Italic / bold.
        if runs and runs[-1][0] == style:
            runs[-1][1] += text
        else:
            runs.append([style, text])
    result = [prefix]
    for style, text in runs:
        if not text.strip():
            result.append(' ')
            continue
        marks = ('**' if style & 16 else '') + ('*' if style & 2 else '')
        result.append((' ' if text[0].isspace() else '') + marks + escape(text)
                      + marks + (' ' if text[-1].isspace() else ''))
    return clean(''.join(result))


def join_blocks(blocks):
    """Keep consecutive simple list items tight, with other blocks separated."""
    result, previous = [], None
    for block in blocks:
        match = re.match(r'^(?:(\d{1,2})([.)])|([a-z])([.)])|(-))\s+', block)
        kind = (('number', match[2]) if match and match[1] else
                ('letter', match[4]) if match and match[3] else
                ('bullet', '-') if match else None)
        if result:
            result.append('\n' if kind and kind == previous else '\n\n')
        result.append(block)
        previous = kind
    return ''.join(result)


def infer_line_breaks(events):
    """Preserve clear form/entry breaks; leave likely wraps and uncertain runs flowing."""
    breaks, notes = set(), []
    text = [value for _, _, kind, value in events if kind == 'text']
    if not text:
        return breaks, notes
    right_edge = max(value['bbox'][2] for value in text)

    def follows(before, after):
        size = max(before['size'], after['size'])
        return (size * .4 < after['bbox'][1] - before['bbox'][1] < size * 2.2
                and after['bbox'][1] - before['bbox'][3] <= max(4, size * .8)
                and abs(before['size'] - after['size']) <= 1)

    def field(value):
        return bool(re.search(r'_{2,}\s*$', value['text']))

    for index, (_, _, kind, value) in enumerate(events):
        if kind != 'text' or index == 0 or events[index - 1][2] != 'text':
            continue
        prior = events[index - 1][3]
        if not follows(prior, value):
            continue
        # A completed answer field is strong evidence of a separate entry.
        if field(prior) and abs(value['bbox'][0] - prior['bbox'][0]) <= 3:
            breaks.add(index)
        if not prior['text'].endswith(':') or value['bbox'][0] < prior['bbox'][0] - 3:
            continue
        run = [(index, value)]
        for offset in range(index + 1, len(events)):
            _, _, next_kind, following = events[offset]
            if (next_kind != 'text' or not follows(run[-1][1], following)
                    or abs(following['bbox'][0] - value['bbox'][0]) > 3):
                break
            run.append((offset, following))
        short = all(row['bbox'][2] < right_edge - max(24, 2 * row['size']) for _, row in run)
        starts = [row['text'].lstrip('“\"(')[:1] for _, row in run]
        independent = all(start.isupper() or start.isdigit() for start in starts)
        hyphenated = any(row['text'].endswith(('-', '–')) for _, row in run[:-1])
        if (all(field(row) for _, row in run)
                or (len(run) >= 2 and short and independent and not hyphenated)):
            breaks.update(offset for offset, _ in run)
        elif short and not hyphenated:
            notes.append(f'Possible intentional line breaks after "{prior["text"][:70]}"; '
                         'text kept flowing. Check against the original page.')
    return breaks, notes


def inside(box, region):
    x, y = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    return region[0] <= x <= region[2] and region[1] <= y <= region[3]


def is_underline(box, text_blocks):
    if box.height > 2.5 or box.width < 3:
        return False
    for block in text_blocks:
        for line in block.get('lines', []):
            if (line['bbox'][0] - 2 <= box.x0 and box.x1 <= line['bbox'][2] + 2
                    and any(-1 <= box.y0 - span['origin'][1] <= 3
                            for span in line['spans'])):
                return True
    return False


def is_decoration(drawing, text_blocks):
    """Recognize plain rules and borders around extractable text."""
    items = drawing['items']
    if len(items) != 1 or (drawing.get('width') or 0) > 1:
        return False
    box = pymupdf.Rect(drawing['rect'])
    kind = items[0][0]
    if kind == 'l':
        return box.width == 0 or box.height == 0
    if kind != 're':
        return False
    if min(box.width, box.height) <= 1:
        return True
    fill = drawing.get('fill')
    if fill is not None and not all(channel >= .99 for channel in fill):
        return False
    return any(box.contains(pymupdf.Rect(span['bbox'])) and span['text'].strip()
               for block in text_blocks for line in block.get('lines', [])
               for span in line['spans'])


def words(text):
    text = re.sub(r'!?\[([^\]]*)\]\([^\n]*?\)', r'\1', text)
    return Counter(re.findall(r'\w+', unicodedata.normalize('NFKC', clean(text)).casefold()))


def image(page, assets, name, box=None):
    assets.mkdir(parents=True, exist_ok=True)
    page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), clip=box).save(assets / name)
    return f'{assets.name}/{name}'


def simplify_header_padding(rows, geometry):
    """Collapse header padding only when every body row defines the same columns."""
    if len(rows) < 2:
        return None
    body = [[(value, cell) for value, cell in zip(row, positions.cells) if cell is not None]
            for row, positions in zip(rows[1:], geometry[1:])]
    columns = [(cell[0], cell[2]) for _, cell in body[0]]
    if not columns or len(columns) >= len(rows[0]):
        return None
    for row, positions in zip(body, geometry[1:]):
        if len(row) != len(columns) or any(
                abs(cell[0] - left) > .1 or abs(cell[2] - right) > .1
                or abs(cell[1] - positions.bbox[1]) > .1
                or abs(cell[3] - positions.bbox[3]) > .1
                for (_, cell), (left, right) in zip(row, columns)):
            return None
    groups = [[] for _ in columns]
    for value, cell in zip(rows[0], geometry[0].cells):
        if cell is None:
            continue
        matches = [i for i, (left, right) in enumerate(columns)
                   if left - .1 <= cell[0] and cell[2] <= right + .1]
        if len(matches) != 1:
            return None
        if clean(value):
            groups[matches[0]].append(value)
    if not all(len(group) == 1 for group in groups):
        return None
    return ([[group[0] for group in groups]] + [[value for value, _ in row] for row in body],
            [left for left, _ in columns] + [columns[-1][1]])


def grid_or_html(html):
    """Use a grid only if Pandoc preserves cell contents, roles, spans and caption."""
    def signature(markup):
        table = BeautifulSoup(markup, 'html.parser').find('table')
        if table is None:
            return None
        return (clean(table.caption.get_text(' ')) if table.caption else '',
                [[(cell.name, int(cell.get('rowspan', 1)), int(cell.get('colspan', 1)),
                   clean(cell.get_text(' '))) for cell in row.find_all(['td', 'th'], recursive=False)]
                 for row in table.find_all('tr')])

    try:
        grid = subprocess.run(
            ['pandoc', '--from=html', '--to=markdown-pipe_tables-simple_tables-multiline_tables-smart',
             '--wrap=none'], input=html, capture_output=True, text=True, check=True, timeout=15).stdout.strip()
        if grid.startswith('+'):
            restored = subprocess.run(
                ['pandoc', '--from=markdown-smart', '--to=html5'], input=grid,
                capture_output=True, text=True, check=True, timeout=15).stdout
            if signature(html) == signature(restored):
                return grid, 'grid'
    except (OSError, subprocess.SubprocessError):
        pass
    return html, 'HTML'


def make_table(table, previous, page_number, page):
    rows = table.extract()
    caption = ''
    # A merged title row is a caption, not part of the column headings.
    if len(rows) > 1 and sum(bool(cell) for cell in rows[0]) == 1 and None in rows[0]:
        caption = clean(next(cell for cell in rows.pop(0) if cell))
    geometry = table.rows[-len(rows):]
    simplified = simplify_header_padding(rows, geometry)
    if simplified:
        rows, simple_edges = simplified
    columns = len(rows[0])
    first = page.get_text('dict', clip=pymupdf.Rect(geometry[0].bbox))
    spans = [s for b in first['blocks'] for line in b.get('lines', [])
             for s in line['spans'] if s['text'].strip()]
    header_bold = sum(len(s['text']) for s in spans if s['flags'] & 16) > sum(len(s['text']) for s in spans) / 2
    has_header = bool(simplified or header_bold or (caption and all(clean(cell) for cell in rows[0])))
    # Only use widths when complete rows agree on the column boundaries.
    grids = [[cell[0] for cell in row.cells] + [row.cells[-1][2]]
             for row in geometry if all(cell is not None for cell in row.cells)]
    if simplified:
        grids = [simple_edges]
    widths = []
    if grids and all(len(grid) == columns + 1 and
                     all(abs(a - b) < 1 for a, b in zip(grid, grids[0])) for grid in grids):
        edges = grids[0]
        widths = [round(100 * (b - a) / (edges[-1] - edges[0]), 2)
                  for a, b in zip(edges, edges[1:])]
    if any(None in row for row in rows):
        # Pipe tables cannot express spans. Try a lossless grid representation.
        if not caption and has_header:
            caption = 'Table: ' + next(clean(cell) for cell in rows[0] if clean(cell))
        xs = sorted({cell[0] for cell in table.cells} | {table.bbox[2]})
        ys = sorted({cell[1] for cell in table.cells} | {table.bbox[3]})
        metadata = '<!-- table: ' + json.dumps({'widths': widths, 'row_header': 0}) + ' -->'
        lines = ['<table>']
        if caption:
            lines.append(f'<caption>{html_escape(caption)}</caption>')
        for index, (row, positions) in enumerate(zip(rows, geometry)):
            if index == 0:
                lines.append('<thead>' if has_header else '<tbody>')
            elif index == 1 and has_header:
                lines.append('</thead><tbody>')
            cells = []
            for value, cell in zip(row, positions.cells):
                if cell is None:
                    continue
                cols = sum(cell[0] - .1 <= x < cell[2] - .1 for x in xs)
                spans = sum(cell[1] - .1 <= y < cell[3] - .1 for y in ys)
                attrs = (f' colspan="{cols}"' if cols > 1 else '')
                attrs += f' rowspan="{spans}"' if spans > 1 else ''
                tag = 'th' if index == 0 and has_header else 'td'
                cells.append(f'<{tag}{attrs}>{html_escape(clean(value))}</{tag}>')
            lines.append('<tr>' + ''.join(cells) + '</tr>')
        lines.append('</thead>' if has_header and len(rows) == 1 else '</tbody>')
        lines.append('</table>')
        text, form = grid_or_html('\n'.join(lines))
        note = f'Merged or split cells: retained as a {form} table. Check inferred headings and header associations.'
        if form == 'HTML':
            note += ' Grid conversion could not be verified without loss; HTML retained.'
        return metadata + '\n\n' + text, note, None
    continuation = (previous and previous['page'] == page_number - 1
                    and len(previous['header']) == columns and not caption and not header_bold
                    and abs(previous['bbox'][0] - table.bbox[0]) < 8
                    and abs(previous['bbox'][2] - table.bbox[2]) < 8)
    if continuation:
        header = previous['header']
        note = 'Possible continued table: column headings reused from the preceding page; confirm the association.'
    elif has_header:
        header = rows.pop(0)
        note = 'Table structure and column headings inferred; check cell associations.'
    else:
        header = [f'Column {i + 1}' for i in range(columns)]
        note = 'Column headings uncertain: generic headings added; all extracted rows retained.'
    if not caption and (has_header or continuation):
        caption = (previous.get('caption', '') if continuation else '') or 'Table: ' + next(
            clean(cell) for cell in header if clean(cell))
    labels = [clean(row[0]) for row in rows if any(clean(cell) for cell in row)]
    row_header = int(bool(labels) and all(labels) and len(set(labels)) == len(labels)
                     and not header[0].startswith('Column '))
    if row_header:
        note += ' First column inferred as row headers; confirm or set row_header to 0.'
    if not widths:
        note += ' Column boundaries uncertain; automatic layout used.'
    render = lambda row: '| ' + ' | '.join(escape(cell) for cell in row) + ' |'
    text = '<!-- table: ' + json.dumps({'widths': widths, 'row_header': row_header}) + ' -->\n\n'
    text += '\n'.join([render(header), '| ' + ' | '.join(['---'] * columns) + ' |',
                       *[render(row) for row in rows]])
    if caption:
        text += '\n\n: ' + escape(caption)
    return text, note, {'header': header, 'bbox': table.bbox, 'page': page_number, 'caption': caption}


def convert_pdf(pdf, destination):
    if destination.exists():
        raise FileExistsError(f'{destination} exists. Choose another output folder to protect edits.')
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    with pymupdf.open(pdf) as document, pdfplumber.open(pdf) as plumb:
        if document.needs_pass:
            raise ValueError('Password-protected PDF; provide an unlocked copy.')
        if not document.page_count:
            raise ValueError('PDF has no pages.')
        sizes, fonts = Counter(), Counter()
        for page in document:
            for block in page.get_text('dict')['blocks']:
                for line in block.get('lines', []):
                    for span in line['spans']:
                        characters = len(span['text'].strip())
                        if characters:
                            size = round(span['size'], 1)
                            sizes[size] += characters
                            fonts[(span['font'], span['flags'], size)] += characters
        body_size = sizes.most_common(1)[0][0] if sizes else 11
        font, font_note = infer_document_font(fonts, body_size)
        assets = destination / 'assets'
        destination.mkdir(parents=True)
        output = [f'---\nfont: {font}\n---',
                  '> Conversion draft. Headings, reading order, and tables are inferred. '
                  'Review flagged pages and describe images before publication.',
                  f'<!-- Source: {pdf.name}; SHA-256: {digest} -->']
        if font_note:
            output.append('> **Review font:** ' + font_note)
        previous_table = None
        found_title = False
        flagged_pages = 0
        description_number = 0
        for index, page in enumerate(document):
            number = index + 1
            notes, events = [], []
            text_source = plumb.pages[index].extract_text() or ''
            try:
                tables = plumb.pages[index].find_tables()
            except Exception as exc:
                tables = []
                notes.append(f'Table extraction failed ({type(exc).__name__}); check the page image.')
            if page.rotation or abs(plumb.pages[index].width - page.rect.width) > 1 or page.cropbox != page.mediabox:
                tables = []
                notes.append('Rotated or cropped page: table coordinates may differ; check the page image.')
            boxes = [table.bbox for table in tables]
            text_blocks = page.get_text('dict')['blocks']
            for table in tables:
                events.append((table.bbox[1], table.bbox[0], 'table', table))
            for block in text_blocks:
                for line in block.get('lines', []):
                    nonempty = [i for i, s in enumerate(line['spans']) if s['text'].strip()]
                    if not nonempty or any(inside(line['bbox'], box) for box in boxes):
                        continue
                    # Spaces may be separate spans between a number and its text.
                    spans = line['spans'][nonempty[0]:nonempty[-1] + 1]
                    # Separate a large bold heading from body text on the same line.
                    split = 0
                    while split < len(spans) and spans[split]['flags'] & 16 and spans[split]['size'] > body_size + 0.5:
                        split += 1
                    groups = [('heading', spans[:split]), ('text', spans[split:])] if split else [('text', spans)]
                    for kind, group in groups:
                        if group:
                            data = {'text': clean(''.join(s['text'] for s in group)),
                                    'markdown': format_spans(group, heading=kind == 'heading'),
                                    'bbox': line['bbox'], 'size': max(s['size'] for s in group)}
                            events.append((line['bbox'][1], group[0]['bbox'][0], kind, data))
            for idx, info in enumerate(page.get_image_info()):
                box = pymupdf.Rect(info['bbox']) & page.rect
                if box.is_empty:
                    continue
                path = image(page, assets, f'page-{number}-image-{idx+1}.png', box)
                events.append((box.y0, box.x0, 'image', path))
                notes.append('Image preserved; add a meaningful description and check any text inside it.')
            drawings = [d for d in page.get_drawings()
                       if not any((pymupdf.Rect(box) + (-2, -2, 2, 2)).contains(d['rect'])
                                  for box in boxes)
                       and not is_underline(pymupdf.Rect(d['rect']), text_blocks)]
            # Keep all strokes when a figure is present, including its rules
            # and labels. A page containing only plain decoration needs no PNG.
            vectors = ([pymupdf.Rect(d['rect']) for d in drawings]
                       if any(not is_decoration(d, text_blocks) for d in drawings) else [])
            if vectors:
                box = pymupdf.Rect(vectors[0])
                for rect in vectors[1:]:
                    box |= rect
                box = (box + (-2, -2, 2, 2)) & page.rect
                if not box.is_empty:
                    path = image(page, assets, f'page-{number}-graphics.png', box)
                    events.append((box.y0, box.x0, 'image', path))
                    notes.append('Vector graphics preserved as an image; check whether they are decorative or need a description. Mermaid conversion is manual.')
            links = []
            for link in page.get_links():
                if link.get('uri'):
                    uri = link['uri']
                    label_lines = page.get_textbox(link['from']).splitlines()
                    label = clean(label_lines[0]) if label_lines else ''
                    if urlsplit(uri).scheme.lower() in ('http', 'https', 'mailto'):
                        links.append((label, quote(uri, safe=':/?#@!$&\'*,;=+%~-._')))
                    else:
                        notes.append(f'Link with unsupported scheme retained as text: {uri}')
                elif link.get('kind') == pymupdf.LINK_GOTO:
                    notes.append(f'Internal PDF link points to source page {link.get("page", 0) + 1}; restore the Markdown destination after review.')
            page_parts, paragraph = [], ''
            prior = None
            used_links = set()

            def flush():
                nonlocal paragraph
                if paragraph:
                    page_parts.append(paragraph)
                    paragraph = ''

            ordered = sorted(events, key=lambda event: (round(event[0], 1), event[1]))
            line_breaks, break_notes = infer_line_breaks(ordered)
            notes.extend(break_notes)
            for event_index, (_, _, kind, value) in enumerate(ordered):
                if kind == 'table':
                    flush()
                    md, warning, state = make_table(value, previous_table if event_index == 0 else None, number, page)
                    page_parts.append(md)
                    notes.append(warning)
                    previous_table = state
                    prior = None
                elif kind == 'image':
                    flush()
                    description_number += 1
                    page_parts.append(f'<!-- description: desc-{description_number:03d} -->\n\n'
                                      f'![Source image on page {number}; description needs review]({value})')
                    prior = None
                else:
                    raw = value['text']
                    text = value['markdown']
                    for label, uri in links:
                        if label and escape(label) in text:
                            text = text.replace(escape(label), f'[{escape(label)}]({uri})', 1)
                            used_links.add(uri)
                    bullet = re.match(r'^[•●▪]\s*', raw)
                    label = re.match(r'^(\d{1,2}[.)]|[a-z][.)])(?:\s+|$)', raw)
                    if kind == 'heading':
                        flush()
                        level = '#' if not found_title else '##'
                        page_parts.append(f'{level} {text}')
                        found_title = True
                    elif bullet or label:
                        flush()
                        paragraph = '- ' + re.sub(r'^[•●▪]\s*', '', text) if bullet else text
                    else:
                        if prior:
                            gap = value['bbox'][1] - prior['bbox'][3]
                            if gap > max(4, prior['size'] * 0.6):
                                flush()
                            # A separate list marker and its text share a row;
                            # their indentation is not a column boundary.
                            marker = re.fullmatch(r'(?:\d{1,2}[.)]|[a-z][.)]|[•●▪])', prior['text'])
                            if (abs(value['bbox'][1] - prior['bbox'][1]) < 2
                                    and value['bbox'][0] > prior['bbox'][2] + 10 and not marker):
                                notes.append('Possible columns: check reading order against the page image.')
                                flush()
                        separator = '\\\n' if event_index in line_breaks else ' '
                        paragraph += (separator if paragraph else '') + text
                    prior = value if kind != 'heading' else None
            flush()
            for label, uri in links:
                if uri not in used_links:
                    page_parts.append(f'[{escape(label or "Source link")}]({uri})')
                    notes.append('A link was retained separately; confirm its placement.')
            if len(text_source.strip()) < 30:
                notes.append('Little or no extractable text. Page image preserved; OCR or transcription is needed.')
            if '\ufffd' in text_source or '\ufffd' in '\n'.join(page_parts):
                notes.append('Unrecognized characters found; compare with the page image.')
            missing = words(text_source) - words('\n'.join(page_parts))
            if missing:
                sample = ', '.join(f'{word} ({count})' for word, count in list(missing.items())[:12])
                notes.append(f'Possible text loss compared with independent extraction: {sample}. Check the page image.')
            if previous_table and (not ordered or ordered[-1][2] != 'table'):
                previous_table = None
            output.append(f'<!-- Source page {number} -->')
            if notes:
                flagged_pages += 1
                review = destination / 'review'
                review.mkdir(exist_ok=True)
                reference = image(page, review, f'p{number:03d}-original.png')
                output.append(f'> **Review page {number}:** [Original page image]({reference})\n>\n'
                              + '\n'.join('> - ' + note for note in dict.fromkeys(notes)))
            output.extend(page_parts)
        (destination / 'content.md').write_text(join_blocks(output) + '\n', encoding='utf-8')
        return len(document), flagged_pages


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog='Existing document folders are never overwritten. Use a new output directory to rerun.')
    parser.add_argument('input', type=Path, help='PDF file or folder (folders are scanned recursively)')
    parser.add_argument('output', type=Path, nargs='?', default=Path('output'), help='Output root (default: output)')
    parser.add_argument('--chrome', help='Chrome executable used to generate review images and HTML')
    args = parser.parse_args()
    source, target = args.input.resolve(), args.output.resolve()
    if source.is_file() and source.suffix.lower() == '.pdf':
        pdfs, base = [source], source.parent
    elif source.is_dir():
        pdfs, base = sorted(p for p in source.rglob('*') if p.is_file() and p.suffix.lower() == '.pdf'), source
    else:
        parser.error('Input must be an existing PDF or folder.')
    if not pdfs:
        parser.error('No PDFs found.')
    try:
        chrome = find_chrome(args.chrome)
    except ValueError as exc:
        parser.error(str(exc))
    failures = 0
    for pdf in pdfs:
        destination = target / pdf.relative_to(base).with_suffix('')
        try:
            pages, flagged = convert_pdf(pdf, destination)
            print(f'{pdf.name}: {pages} pages, {flagged} flagged for review -> {destination / "content.md"}')
            try:
                preview(pdf, destination / 'content.md', chrome)
            except Exception as exc:
                raise RuntimeError(f'Markdown saved, but preview failed: {exc}. '
                                   f'Retry preview.py with this PDF and {destination / "content.md"}.') from exc
        except Exception as exc:
            failures += 1
            print(f'{pdf.name}: {exc}', file=sys.stderr)
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
