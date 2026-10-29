# Assessment and verification record

Inspection and reconstruction date: October 28, 2026. Page references are 1-based PDF pages; the source has no printed page numbers. This record describes evidence gathered by the conversion agent, not an independent human sign-off or accessibility certification.

## Source assessment

- **Input:** `2023-BA-Year0-Plan.pdf`, 332,374 bytes, 15 US Letter pages (612 × 792 points), PDF 1.7. SHA-256: `1625ff6a4f7b8d0397b09b8b0a934fde01f32fd22b9b3c0a46c5313f4d8389e1`.
- **Digital versus scanned:** All pages contain extractable digital text. Zero embedded raster images. No OCR was necessary. The distorted questionnaire is composed of text/vector elements, not a scanned image.
- **Metadata and tagging:** Created by Microsoft Word for Microsoft 365; language `en-US`; catalog contains `StructTreeRoot` and `MarkInfo /Marked true`. Title metadata is empty. Author metadata says Ronald W Larsen, while visible submission credits say John Paxton / Daniel DeFrance. Visible credits were preserved. Tag correctness, PDF reading order, PDF/UA, and conformance were not audited; tag presence is not proof of accessibility.
- **Layout:** Main report on pp. 1-5; custom exam on pp. 5-8; portfolio rubrics on pp. 9-11; survey on pp. 12-15. Predominantly one-column prose, with tables, a floating deadline callout, substantial blank template areas, and page-spanning paragraphs/lists. Four logical report tables: program, PLOs, threshold, and assessment planning. Survey ratings are an additional damaged matrix-like structure, not verified as a usable table.
- **Headings:** Five report parts, three appendices, rubric sections, 12 exam questions, seven portfolio indicators, and survey subsections. Reconstructed as an explicit h1-h4 hierarchy.
- **Reading order:** Geometric sorting interleaves planning-chart cells; raw extraction cannot be used directly as reading order. The due-date callout interrupts metadata. Paragraphs continue from p. 4 to p. 5, Question 3 from p. 5 to p. 6, Indicator 3's score 4 from p. 9 to p. 10, and the final survey outcome from p. 14 to p. 15. These joins were visually checked.
- **Images and visual content:** No substantive illustrations, charts, photographs, or diagrams. Requests to draw diagrams in questions are prompts, not missing figures. Blank form rules and circles were replaced by semantic prompt/option lists. A full rendering of p. 14 is retained as evidence, with a draft alt description requiring review.
- **Equations and symbols:** No displayed equations. Question 3 contains literal `k << n`, preserved with a math role and spoken label “k is much less than n”; assistive-technology announcement remains untested. Numeric ranges, percentages, numbered rubric levels, and course identifiers are material.
- **Footnotes:** None found by visual review. The superscript “th” in “15th” is an ordinal, not a footnote. No footnotes were invented.
- **Extraction problems:** Artificial line breaks within cells and year ranges; interleaved columns; misread circle glyphs (`O`, `Q`, `0`); circles touching words in PyMuPDF extraction (`0responsibilities`, `0ethical`). Independent pdfplumber extraction separates those words. On p. 14 the visible original itself has misplaced labels/circles, so better extraction alone cannot resolve the intended relationships.

## Reconstruction decisions

Original wording was preserved, including grammatical awkwardness and discrepancies. Repairs are structural: wrapped lines and page continuations joined; headings assigned; scoring levels made true ordered lists; all table cells transcribed; three year columns under a shared heading consolidated into lists. Added captions and editorial labels are marked in source, and review notices are visibly distinct in HTML. Punctuation used only as a heading/list delimiter was normalized; curly apostrophes in prose were retained. No historical claims were updated or externally fact-checked.

Blank response areas and two entirely blank program-table rows were omitted. The blank Options cell remains blank and has an explanatory note. Source emphasis on action words and “avoid harm” was retained where meaningful; red table text and blanket bolding of portfolio rubric scores were not treated as independent information. The score numbers themselves are preserved. The evidence disclosure is supporting verification, not the primary route to reading the survey.

The source-page map is separate from the reading text. It identifies page-spanning items and review issues without scattering page markers through the canonical prose.

## Unresolved subject-matter review

| Reference | Source evidence | Required decision |
| --- | --- | --- |
| Review 1 | p. 3 Part 3b says ESOF 483, then ESOF 423 | Confirm intended course; also confirm printed “Computer B.S.” in Part 3a if editing content |
| Review 2 | p. 4 describes both external links as custom exam/rubric | Confirm the description for the portfolios link |
| Review 3 | p. 8 sentence reads “achieved 50% or more…”; pp. 6-8 hour-based bands overlap | Confirm missing connective and intended score boundaries; source text is unchanged |
| Reviews 3-4 | p. 2 and p. 8 use inclusive 50%; p. 11 says more than 50% and students taking the exam | Confirm strict versus inclusive threshold and portfolio/exam terminology |
| Review 5 | p. 12 title says Portfolio Criteria with Evaluation Rubric over a survey | Confirm appendix title |
| Review 6 | p. 14 ratings/circles are displaced; Excellent wraps; six statements extend to p. 15 | Confirm scale order and intended row/choice mapping; review the evidence image description |

Additional content questions, not conversion corrections: Part 2 specifies assessment every second year, while Part 5 describes assessment following Spring Semester; clarify cadence if the plan is revised. Appendix A Question 4's speaking outcome is paired with an involvement/hours prompt; confirm intended alignment if revising the assessment. Appendix B Indicator 3 asks for yellow highlighting; consider a non-color identification method when revising the assignment. The document is a historical 2023-2024 plan; names, deadlines, courses, links, and referenced standards were not checked for present-day validity.

## Completed checks

**Visual source review:** All 15 PNGs inspected against extracted text. All table rows and material numeric values were reviewed, including 18 assessment-year entries; 50% thresholds; 10,000; 11,500; 2010; P7003; course numbers; hour thresholds; UML type counts; score levels; and the `<<` symbol. No original page was omitted. The p. 14 rating relationships remain unresolved despite visual review.

**Automated checks:** `scripts/verify.py` passed 50/50 checks. The JSON report records every check. Coverage includes:

- Source hash unchanged; English language and title; one main and h1; no heading-level skips; unique IDs; valid internal targets; skip-link target.
- Captions and scoped table headers; image alt text and existing local asset; no replacement characters; six review notices; no pretend survey form controls.
- Ordered lexical comparison of every exam question and portfolio indicator, including subquestions and all 76 scoring entries, against independent pdfplumber text.
- Cell-by-cell comparisons of the populated program row, all six PLO rows, the threshold row, and all six planning-chart rows.
- Full-document normalized token coverage, including generated list labels. Only expected differences remain: 30 rating-circle zeros and the `O`/`Q` option markers are omitted; six list numbers are added to the survey statements. Added editorial matter is excluded from this comparison.
- Independent extraction-engine token differences recorded for each page. The only token discrepancies are on p. 14 where PyMuPDF joins two zeros to words.

These token tests normalize case and punctuation. They detect loss and, for rubric sections/table cells, ordering problems; they do not independently prove punctuation fidelity, intended meaning, semantic accessibility, or correct source layout. Source rendering review supplies complementary evidence. The tests are tailored to this pilot and are not a generic PDF-conversion validator.

**HTML visual review:** The browser connector reported no available browser. Isolated headless Chrome rendered the opening and then an unscrolled 1440 × 16000 screenshot; all document content through the final survey was inspected in eight consecutive crops. Desktop table layout, paragraph wrapping, heading separation, list numbering, and review-note presentation showed no clipping or overlap in that view. The supporting evidence image was inspected separately as the original page rendering; its expanded HTML disclosure was not interactively tested. Anchor-scrolled screenshots returned blank images with local compositor errors and were discarded. Narrow-screen, real zoom, and interactive checks remain pending. A tall viewport is useful for inspection but is not a substitute for ordinary scrolling, reflow, or assistive-technology testing.

To reproduce the successful visual evidence on macOS with Chrome installed, start the local server described in the README, then run:

```sh
'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' --headless --disable-gpu --no-first-run --no-default-browser-check --user-data-dir=/private/tmp/converter-html-review-tall --screenshot="$PWD/verification/browser-tall.png" --window-size=1440,16000 http://127.0.0.1:8765
```

This profile is temporary and separate from the user's regular browser profile. No browser credentials or sessions were read. Graphics failures may make rendering unreliable in other environments; inspect the resulting image, not only the command exit code.

## Remaining manual accessibility and release checks

- Have a subject-matter reviewer resolve or accept the six notes, especially the survey scale and threshold discrepancies; approve any wording changes explicitly.
- Test keyboard navigation: first-tab skip link, visible focus, contents anchors, table scroll regions, evidence disclosure, and absence of traps.
- Test with representative screen reader/browser combinations: heading navigation, list score announcements, row/column header associations, editorial-note distinction, math announcement, image alternative and caption, and disclosure state.
- Inspect at 200%/400% zoom and narrow viewports (including 320 CSS pixels), enlarged text and spacing, forced colors, and across supported browsers. Verify that wide tables scroll without forcing the entire page sideways and remain understandable.
- Measure contrast for text, links, focus indicators, and meaningful boundaries; visual color inspection alone is insufficient. Run a maintained accessibility ruleset and an HTML validator, then manually assess findings. Neither was run in this pass.
- Verify external destinations if the document is being reissued. No links were followed during transcription.
- Decide whether a future survey deliverable is a reading edition or an interactive form; the current HTML collects and submits nothing. A usable form needs confirmed relationships, explicit labels/groups, instructions, and separate interaction testing.
- Inspect print layout if printing is required. Future Word/tagged-PDF outputs need their own semantic conversion and validation, including reading order, table associations, alternatives, metadata, and target-specific accessibility checks.

**Status:** Canonical content and HTML first pass completed with explicit uncertainties. Accessibility conformance has not been established.
