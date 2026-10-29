# PDF reconstruction workflow

Repository instructions are in [AGENTS.md](AGENTS.md). See the
[production direction and rollout](docs/production.md) for department and campus
scaling, supported content routes, review requirements, and remaining work.

The current implementation is a local PDF pilot with a validated document catalog
and sequential batch processing. It is not a deployed service or an unattended
converter for arbitrary inaccessible content.

```sh
.venv/bin/python scripts/batch.py --department msu-cs --dry-run
.venv/bin/python scripts/batch.py --department msu-cs --stage all
python3 -m unittest discover -s tests -v
```

Register PDF jobs in [config/documents.json](config/documents.json). Batch reports
and logs are written under ignored `output/runs/`; successful checks still require
content and accessibility review. Existing single-document commands remain valid.

The 15-page `2023-BA-Year0-Plan.pdf` has been reconstructed into a canonical Markdown reading edition and generated semantic HTML. The original PDF is preserved unchanged under `input/cs/msu-accreditation/`.

Start with [the HTML reading edition](output/cs/msu-accreditation/2023-BA-Year0-Plan/html/index.html), [the canonical Markdown](source/cs/msu-accreditation/2023-BA-Year0-Plan/content.md), and [the assessment and verification record](verification/cs/msu-accreditation/2023-BA-Year0-Plan/REVIEW.md).

Document folders mirror the original web hierarchy under `input/`, `source/`, `output/`, and `verification/`. The pilot lives in `output/cs/msu-accreditation/2023-BA-Year0-Plan/`; `output/cs/msu-accreditation/2025-Year0-DS-Plan/` contains the completed Data Science conversion.

## Data Science conversion (2025)

The second PDF is reconstructed separately:

- [HTML reading edition](output/cs/msu-accreditation/2025-Year0-DS-Plan/html/index.html) and [HTML ZIP](output/cs/msu-accreditation/2025-Year0-DS-Plan/assessment-plan-html.zip)
- [Canonical Markdown](source/cs/msu-accreditation/2025-Year0-DS-Plan/content.md)
- [Assessment and verification record](verification/cs/msu-accreditation/2025-Year0-DS-Plan/REVIEW.md)
- [Source-page map](verification/cs/msu-accreditation/2025-Year0-DS-Plan/page-map.csv)

```sh
.venv/bin/python scripts/extract.py --document 2025-Year0-DS-Plan
.venv/bin/python scripts/build.py --document 2025-Year0-DS-Plan
.venv/bin/python scripts/verify_ds.py
```

All 73 content/static checks passed; all six source pages and the full desktop HTML rendering were inspected. Three source issues remain flagged: PLO wording, assessment frequency, and sampling scope. Keyboard, screen-reader, narrow-screen, zoom, contrast, and conformance checks remain manual work.

The shared scripts select document paths, title, and fingerprint from `config/documents.json`, validated by `scripts/documents.py`. Without `--document`, extraction and build still default to the original 2023 pilot. The paths and detailed pilot instructions below refer to that original document. New documents need their own reviewed configuration and content checks; the scripts are not an unattended converter for arbitrary PDFs.

## File organization

The path beneath each root follows the department's web structure. For example:

```text
input/cs/msu-accreditation/2023-BA-Year0-Plan.pdf
source/cs/msu-accreditation/2023-BA-Year0-Plan/content.md
source/cs/msu-accreditation/2023-BA-Year0-Plan/assets/
output/cs/msu-accreditation/2023-BA-Year0-Plan/html/index.html
verification/cs/msu-accreditation/2023-BA-Year0-Plan/REVIEW.md
templates/template.html
```

The 2025 document uses the same structure with `2025-Year0-DS-Plan`. Original
files belong in `input/`; editable reconstruction and document-specific assets
belong in `source/`; generated deliverables belong in ignored `output/`; review
records and extraction evidence belong in `verification/`. Shared presentation
templates live in `templates/`.

`config/documents.json` records the original URL, checksum, and each local path.
Document IDs remain stable even if a URL or folder changes. The folder structure
also accommodates DOCX and other inputs, but processing currently supports only
registered PDFs. Moving other file types into `input/` does not convert them.

| Location | Purpose |
| --- | --- |
| `input/cs/msu-accreditation/2023-BA-Year0-Plan.pdf` | Original input; never modified by the workflow |
| `source/cs/msu-accreditation/2023-BA-Year0-Plan/content.md` | Canonical content, inline semantic HTML tables, explicit editorial review notes |
| `templates/template.html` | HTML presentation and basic accessible styling; no report content |
| `source/cs/msu-accreditation/2023-BA-Year0-Plan/assets/` | Supporting source-page evidence image and draft alt-text inventory |
| `output/cs/msu-accreditation/2023-BA-Year0-Plan/html/` | Regenerable reading edition and copied assets; share the whole folder |
| `scripts/extract.py` | Dual-engine extraction, page renderings, metadata, links, geometry, and hash record |
| `scripts/build.py` | Markdown-to-HTML build using Pandoc; adds labeled scroll regions and copies assets |
| `scripts/verify.py` | Pilot-specific content comparisons and static HTML checks |
| `verification/cs/msu-accreditation/2023-BA-Year0-Plan/page-map.csv` | Canonical section IDs mapped separately to 1-based PDF page numbers |
| `verification/cs/msu-accreditation/2023-BA-Year0-Plan/REVIEW.md` | Findings, decisions, unresolved questions, and manual check status |
| `verification/cs/msu-accreditation/2023-BA-Year0-Plan/source-inventory.json` | Source metadata, SHA-256, page/tool inventory |
| `verification/cs/msu-accreditation/2023-BA-Year0-Plan/automated-checks.json` | Machine-readable results and extraction-engine disagreements |
| `verification/cs/msu-accreditation/2023-BA-Year0-Plan/extracted/`, `verification/cs/msu-accreditation/2023-BA-Year0-Plan/pages/` | Regenerable raw text, table data, text geometry, and page PNGs |
| `requirements.lock.txt` | Exact installed Python dependencies for this pilot |

Generated outputs, extraction intermediates, screenshots, and the local virtual environment are listed in `.gitignore`. Preserve the Markdown, template, scripts, original, assets, review records, page map, and lock file as the reproducible package.

## Tools and setup

Run from this workspace. The pilot used Python 3.14.7, Pandoc 3.8, PyMuPDF 2.0, pdfplumber 0.11.10 (pdfminer.six 20260107), and Beautiful Soup 4.15.0. See `verification/cs/msu-accreditation/2023-BA-Year0-Plan/source-inventory.json` and the lock file for exact runtime details. Python packages were installed into `.venv`; no system Python packages were changed. Pandoc and Tesseract were already installed. Poppler was unavailable, so PyMuPDF performed rendering instead. The environment's PDF artifact-operation marker was run before artifact creation; it is an environment bookkeeping step, not a build dependency. No output PDF was authored.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --no-cache-dir -r requirements.lock.txt
pandoc --version
.venv/bin/python scripts/extract.py
.venv/bin/python scripts/build.py
.venv/bin/python scripts/verify.py
```

The lock file reflects this macOS/Python installation; availability of pinned wheels on other platforms must be checked. Pandoc is an external dependency and must be installed separately. Network access is needed for dependency installation, not for extraction, build, or verification. The build contains no remote fonts, scripts, or stylesheets. Original external links are retained but were not fetched or validated.

For ordinary content edits, edit `source/cs/msu-accreditation/2023-BA-Year0-Plan/content.md` and run only the build and verification commands. The extraction command never overwrites Markdown. The verifier intentionally detects substantive editorial changes: review them against the original and update the documented expectations when a change has been approved. Do not change the PDF hash guard merely to make a failure disappear.

Open `output/cs/msu-accreditation/2023-BA-Year0-Plan/html/index.html` directly in a browser. For local serving:

```sh
.venv/bin/python -m http.server 8765 --bind 127.0.0.1 --directory output/cs/msu-accreditation/2023-BA-Year0-Plan/html
```

Stop the local server with Ctrl+C. Sharing the HTML alone will omit the supporting evidence image; share `output/cs/msu-accreditation/2023-BA-Year0-Plan/html/` together or its ZIP bundle.

## Reconstruction method

1. Inventory files, instructions, Git state, installed tools, PDF metadata, page sizes, text, images, and form widgets. Record the original hash before work.
2. Extract with two engines. Save raw text, coordinate-bearing blocks, and geometry-based tables separately from canonical content. Render every original page and inspect it visually.
3. Reconstruct paragraph order and hierarchy with explicit IDs. Join page and line breaks; preserve words, numbers, names, course identifiers, punctuation with substantive meaning, and original inconsistencies. Keep editorial additions visibly labeled.
4. Compare table cells individually with the source image and geometric extraction. Use row and column headers, captions, and lists within cells. The three assessment-year cells become a single list under their shared header without losing any entries.
5. Keep uncertain structures explicit. For this survey, preserve labels and outcome statements separately rather than inventing a trustworthy rating matrix. Retain the original layout as evidence and draft an alt description for review.
6. Build HTML from the canonical source. Check heading hierarchy, landmarks, link targets, table headers, alternatives, and local assets. Inspect renderings separately from content checks.
7. Review every number and symbol, every rubric entry, each table row, and all page continuations. Record unresolved subject-matter and accessibility checks before release.

The Markdown dialect is **Pandoc Markdown**, with fenced editorial-note divs, explicit heading IDs, alphabetic ordered lists, and raw HTML for tables and the evidence disclosure. This dialect is specified in `scripts/build.py`. General Markdown viewers may not honor all of it. Future Word/tagged-PDF exporters must convert the raw HTML tables/details into their target's semantic structures; blindly running a different Pandoc writer can omit raw HTML. Content is canonical here, but only the HTML export path has been implemented and checked.

## OCR and other PDFs

No OCR was needed for this digital-text pilot. For a new PDF, repeat inspection first; do not reuse its hard-coded page mappings, hash, table geometry, or review expectations. A mixed/scanned document needs per-page decisions. A possible OCR command, **not exercised in this pilot**, is:

```sh
tesseract page-01-300dpi.png page-01 -l eng --psm 3 txt tsv
```

Render scanned pages at about 300 dpi, select the correct language and segmentation mode after examining the page, preserve OCR TSV coordinates/confidence, and verify against the source. Low-confidence text, math, superscripts, footnotes, unusual symbols, and tables require special review; confidence scores do not prove correctness. Do not overwrite the original or silently replace reliable digital text with OCR. For informative figures, retain source assets, captions, and draft alt/long descriptions, and request subject-matter review when interpretation is uncertain.

## Current status

All 50 automated content/static checks passed. All 15 original pages were visually reviewed. The complete desktop HTML reading content was visually inspected in a tall isolated headless Chrome render; ordinary scrolled and narrow-screen captures were limited by local graphics failures. No keyboard session, screen-reader test, full accessibility ruleset audit, print-layout validation, or conformance assessment was completed. See the review record for the precise limits and outstanding checks. Word and tagged PDF exports remain future work.
