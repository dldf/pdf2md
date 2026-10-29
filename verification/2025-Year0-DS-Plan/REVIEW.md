# Data Science plan: conversion and verification record

Completed October 28, 2026. This is an agent-reviewed first pass, not independent human approval or accessibility certification.

## Deliverables and regeneration

- Canonical content: `source/2025-Year0-DS-Plan/assessment-plan.md`.
- Generated reading edition: `output/2025-Year0-DS-Plan/html/index.html`.
- Shareable HTML bundle: `output/2025-Year0-DS-Plan/assessment-plan-html.zip`.
- Supporting verification: this directory's `page-map.csv`, `source-inventory.json`, `automated-checks.json`, `pages/`, and `extracted/`.

From the workspace root:

```sh
.venv/bin/python scripts/extract.py --document 2025-Year0-DS-Plan
.venv/bin/python scripts/build.py --document 2025-Year0-DS-Plan
.venv/bin/python scripts/verify_ds.py
```

After editing only the Markdown, run the last two commands. Extraction never overwrites canonical content. No dependency installation or OCR was needed for this second conversion. Shared extraction/build scripts now accept `--document`; their default remains the 2023 pilot. Paths, titles, and source checksums are declared in `scripts/documents.py`. Fidelity checks remain document-specific, because table geometry, page continuations, and source ambiguities differ between PDFs.

The canonical dialect remains Pandoc Markdown with explicit IDs, editorial divs, and semantic HTML tables. Future Word/tagged-PDF writers must convert those HTML tables into their own semantic structures; they cannot assume raw HTML will survive an arbitrary exporter. No Word or PDF output was generated.

## Source assessment

The six-page `2025-Year0-DS-Plan.pdf` is digital text on US Letter pages. Its SHA-256 is `798dab9341e8a9e4aadf8aa6b243cd068aeee50d07c1516823176c5caf224565`. The original was opened read-only and its checksum verified after reconstruction.

All six pages have extractable text. There are no embedded raster images, substantive vector illustrations, displayed equations, or footnotes. Indicator 4's request for figures refers to future student work; no figures are missing from this plan. No image assets or alternative descriptions were required. Source renderings are verification evidence, not reading-edition assets.

The source is PDF 1.7, created in Microsoft Word for Microsoft 365, with language `en`, a structure tree, and the marked-content flag. Its title metadata is empty. Author metadata says Ronald W Larsen; the visible credits say Neda Nazemi / John Paxton and were preserved. Existing PDF tags were not audited for correctness or conformance.

The layout contains six report parts and one appendix, with three logical tables: program, four PLOs, and four assessment-planning rows. Appendix A has six indicators, 24 scoring entries, a performance threshold, and an evaluation methodology. The reading order is mostly linear; tables need cell reconstruction. Indicator 3's heading is on p. 4 and its text on p. 5. Indicator 6's first score is on p. 5 and its remaining scores on p. 6. The narrative introduction to Part 3 is on p. 2 and its questions/answers are on p. 3.

Tools reused: PyMuPDF 2.0 for text/geometry/rendering, pdfplumber 0.11.10 for independent extraction and table geometry, Pandoc 3.8 for HTML, Beautiful Soup 4.15.0 for structure and checks, and isolated headless Chrome for visual review. Python version and metadata are recorded in `source-inventory.json`; exact installed dependencies remain in the root lock file. No external sources were consulted to change or update the material.

## Reconstruction decisions

- Preserved all substantive text, template instructions, names, numbers, course titles/codes, thresholds, deadlines, and scoring levels.
- Joined line/page wraps, restored paragraphs and numbered scoring lists, and assigned an h1-h4 hierarchy. Printed page numbers 1-6 were removed from body content and recorded separately through the page map.
- Added table captions, column headers, and row headers. Combined the three assessment-year cells in each row into a list under their shared header, retaining all 12 entries.
- Retained the blank Options cell; omitted two completely blank program-table rows and blank response rules. Retained both YES answers and all unmarked conditional prompts, with an explicit note that no selections were inferred.
- Preserved the five arrows in `acquisition → cleaning → analysis → visualization → modeling → communication` and the emphasis on “two key figures.” No diagram was invented from that sequence.
- Normalized dash punctuation used as separators to ASCII hyphens. Preserved substantive punctuation, parenthetical examples, curly quotation/apostrophe characters, and the missing terminal period on Indicator 1's fourth score. Broad italic styling was replaced by semantic structure where it carried no separate information.
- Added three clearly labeled editorial review notes. Original content was not silently reconciled or rewritten.

## Subject-matter questions

| Note | Source pages | Unresolved issue |
| --- | --- | --- |
| Review 1 | 1-2 | Planning-chart PLO 1 shortens the full PLO and omits storage and visualization from its cycle list. Confirm intended wording. |
| Review 2 | 2-3 | Part 3 says evaluation occurs each year; Parts 2 and 5 describe a two-year analysis/reporting or review cycle. Confirm how these activities relate. |
| Review 3 | 3 and 6 | Part 3 specifies a random sample; Appendix A says each portfolio. Confirm whether that means each sampled portfolio or all submissions. |

No missing text was inferred. No unreadable substantive passage remains. These questions concern the source's intended meaning, not uncertainty in transcription. Course information, deadlines, and named assignments were preserved as historical document content and not checked for present-day validity.

## Verification completed

**Source visual review:** Inspected every original page at 108 dpi. Checked all table cells, names, dates, percentages, course numbers, 12 assessment-year entries, six indicator titles, 24 scoring entries, and both rubric page continuations. Checked the arrow sequence and the “two key figures” requirement. No OCR was necessary.

**Automated:** 73/73 checks passed. These include:

- Unchanged source checksum; title/language; one main landmark and h1; ordered heading levels; unique IDs; resolved internal links; a skip link; labeled focusable table regions; scoped row/column headers.
- Cell comparisons for the program row, all four PLO rows, and all four planning rows, including every course, indicator reference, and year.
- Exact normalized word/number order for each rubric indicator and all score labels, plus checks that each narrative paragraph's wording and internal order occur in the independent extraction.
- Full-document lexical coverage, excluding marked editorial additions and added captions. The only unmatched source tokens are four `o` sub-bullet markers, now semantic bullets. There are no unexplained missing or added lexical tokens.
- Pipeline arrows, inclusive thresholds in both locations, submission address, all three review notes, page-map targets, and HTML ZIP contents.

Per-page extraction-engine token differences are recorded in `automated-checks.json`. Lexical comparisons normalize case and punctuation, so they are not proof of punctuation fidelity, global reading order, or intended meaning. Visual review and table/rubric-specific checks provide additional evidence. These tests are not a comprehensive accessibility ruleset.

**HTML visual review:** Inspected the entire 1440-pixel-wide document, including footer, using a tall 1440 × 11000 local Chrome rendering split into consecutive inspection images. No clipping, overlap, broken glyphs, or misplaced table content was observed. The page rendered directly from its local file using a fresh temporary profile, without accessing the user's browser session. This does not test keyboard interaction, ordinary scrolling, mobile layout, or screen-reader output.

The earlier document still passes its 50 checks after the shared script/template changes.

## Remaining manual checks

- Resolve or explicitly accept the three subject-matter notes.
- Test keyboard focus, skip navigation, contents links, and horizontal table scrolling; verify no traps.
- Test screen-reader heading/list navigation and table header associations, and how the pipeline arrows are announced.
- Check narrow viewports, 200%/400% zoom, increased text spacing, forced colors, and supported browser combinations.
- Measure text/link/focus contrast and run a maintained accessibility ruleset plus HTML validation; assess findings manually.
- Check print layout if required. Any future Word/tagged-PDF export needs independent semantic and accessibility verification.

Accessibility conformance has not been established. The HTML is a structured reading edition, not an interactive form.
