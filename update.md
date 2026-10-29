# accessConverter: current state and practical next steps

This is a local, command-line PDF reconstruction pilot. It can reproduce and
check two prepared reading editions. It is not yet a student-operated converter
for the CS website. The missing capability is turning a new document or webpage
into a reviewable, accessible draft without custom programming for each item.

## What has been done

The starting folder contained two original PDFs, manually reconstructed Markdown,
an HTML template, extraction/build scripts, and document-specific checks. The
reconstruction happened during assisted work; it is not implemented as a reusable
automatic conversion step.

The subsequent work:

- Created the private `dldf/accessConverter` GitHub repository.
- Added a JSON document catalog and a sequential batch runner with logs, source
  checksum checks, timeouts, and separate results for each document.
- Added repository instructions, tests, GitHub CI, a production roadmap, and a
  public CS pilot plan containing 12 candidate URLs.
- Moved both documents into matching folders and updated scripts and references.
  Moved the shared template out of the document source directory.

The last refactor passed 20 unit tests and 123 document-specific checks. Generated
HTML and ZIP bundles were byte-identical before and after the move. Those checks
are regression evidence, not an accessibility certification. The changes were
delivered in draft PRs [#1](https://github.com/dldf/accessConverter/pull/1) and
[#2](https://github.com/dldf/accessConverter/pull/2). Nothing was deployed to MSU.

## Why the work became expensive

Higher reasoning effort can increase model work and latency; OpenAI documents
that lower effort favors speed and lower token usage. Trying Low for small edits
is reasonable, reserving High for difficult debugging or design decisions.
[Official OpenAI documentation](https://developers.openai.com/api/docs/guides/reasoning)

The model setting does not explain all the overhead. I expanded the production
discussion into implementation, planning documents, CI, and PR work before
delivering the core student workflow. I also used repeated inspection and
verification calls. Some checks were necessary, but the overall process was too
heavy for several small requests. I cannot determine the exact share of usage
attributable to the model setting from this conversation.

The Python software currently makes no AI API calls. Running its extraction,
build, and verification commands does not itself consume model tokens. The AI
usage came from the assistant's development and research work.

## Directory and file guide

Both documents use `cs/msu-accreditation/` beneath the following roots:

```text
input/cs/msu-accreditation/<document>.pdf
source/cs/msu-accreditation/<document>/content.md
source/cs/msu-accreditation/<document>/assets/       # when needed
output/cs/msu-accreditation/<document>/html/index.html
output/cs/msu-accreditation/<document>/assessment-plan-html.zip
verification/cs/msu-accreditation/<document>/
```

The document names are `2023-BA-Year0-Plan` and `2025-Year0-DS-Plan`.

| Folder or file | Purpose |
| --- | --- |
| `input/` | Unchanged originals. The two pilot PDFs are tracked fixtures. Other formats can be stored here, but the processing catalog currently accepts only PDFs. |
| `source/` | Editable reconstructed content. Each document has `content.md`, using Pandoc Markdown with some semantic HTML. This is the content the builder reads. |
| Document `assets/` | Supporting images belonging to that document. The 2023 document contains `survey-outcomes-source-page-14.png` and an `assets/README.md` describing its meaning and review needs. |
| `output/` | Regenerable HTML, copied assets, and ZIP bundles. Ignored by Git. These are local reading editions, not published MSU pages. |
| `output/runs/<run-id>/` | Per-stage logs and `report.json` for each batch. These record processing results, not human approvals. |
| `verification/` | Per-document review records and evidence, described below. |
| `templates/template.html` | Shared HTML layout, styling, navigation, and accessibility-related markup. It contains no document-specific report text. |
| `config/documents.json` | Registers each document's stable ID, department, URL, checksum, local paths, title, evidence images, and verifier script. Adding a record does not reconstruct its content. |
| `scripts/documents.py` | Loads and validates the catalog, checks path boundaries, and verifies original-file hashes. |
| `scripts/extract.py` | Extracts PDF text and tables using two engines and renders source pages for inspection. It does not create `content.md`. |
| `scripts/build.py` | Turns an existing `content.md` into HTML and a ZIP using Pandoc and the template. Copies document assets. |
| `scripts/verify.py` | Custom content and HTML checks for the 2023 B.A. document. |
| `scripts/verify_ds.py` | Custom content and HTML checks for the 2025 Data Science document. Neither verifier is a general document validator. |
| `scripts/batch.py` | Runs extraction, building, and verification for registered documents; continues with other documents after a failure. |
| `tests/test_pipeline.py` | Tests catalog validation, source changes, selection, failure handling, and related orchestration behavior. |
| `.github/workflows/checks.yml` | Runs unit tests and a dry-run batch plan on GitHub. It does not run the full PDF pipeline or browser accessibility testing. |
| `requirements.lock.txt` | Python package versions from the local pilot environment. A clean installation on another platform still needs verification. Pandoc is installed separately. |
| `.venv/` | Local Python environment containing installed packages. Ignored by Git. |
| `.gitignore` | Excludes generated output, extraction intermediates, screenshots, Python caches, and local environment files from Git. |
| `.git/` | Local Git history and repository metadata. |
| `AGENTS.md` | Instructions for the coding assistant. It is not runtime enforcement or a student operating interface. |
| `README.md` | Existing detailed setup, processing instructions, reconstruction method, and pilot limitations. |
| `docs/production.md` | Proposed production architecture and remaining work. Most service features described there are plans. |
| `docs/public-cs-pilot.md` | Public CS scope, 12 initial candidate URLs, and proposed intake work. It is not an implemented crawler or completed audit. |
| `update.md` | This consolidated explanation of what exists and what to build next. |

Within each document's `verification/` folder:

| File or folder | Purpose |
| --- | --- |
| `REVIEW.md` | Reconstruction decisions, completed reviews, source ambiguities, and outstanding manual checks. |
| `page-map.csv` | Maps sections in the reconstructed content to original PDF pages. |
| `source-inventory.json` | Original metadata, checksum, page information, and extraction tool versions. |
| `automated-checks.json` | Results from that document's custom checks. |
| `pages/` | Generated page images for visual comparison; ignored by Git. |
| `extracted/` | Generated text, table data, and geometry; ignored by Git. |
| `browser-*.png` / `browser-*.json` | Existing browser-review artifacts where present; ignored by Git. |

## How to use it now

On the existing configured machine, run from the repository root:

```sh
# Show which registered documents would be processed; write nothing.
.venv/bin/python scripts/batch.py --department msu-cs --dry-run

# Reproduce both prepared editions and run their custom checks.
.venv/bin/python scripts/batch.py --department msu-cs --stage all
```

Open the desired `output/cs/msu-accreditation/<document>/html/index.html` in a
browser. Share the ZIP or the entire HTML folder so supporting assets travel
with it. A result of `checks_passed_needs_review` still needs review.

To revise an existing edition, edit its `source/.../content.md`, then run:

```sh
.venv/bin/python scripts/batch.py --document 2025-Year0-DS-Plan --stage build
.venv/bin/python scripts/batch.py --document 2025-Year0-DS-Plan --stage verify
```

For a new PDF, someone must still register it, extract it, reconstruct its content
into Markdown, and provide suitable fidelity verification. Missing Markdown
blocks the build; a missing verifier blocks a successful full batch. Even valid
Markdown needs checking against the original. The two existing verifier scripts
contain assumptions specific to their documents.

## Can a work-study student convert everything reachable on cs.montana.edu?

**No, not efficiently with the current software.** A trained student can rebuild
the two examples, inspect evidence, and help with manual reconstruction. New
documents still need substantial editorial work and developer involvement.

There is no implemented site inventory, general draft-conversion step, OCR
workflow, DOCX/slide/spreadsheet conversion, webpage repair workflow, student
interface, or CMS publishing integration. There is also no measured throughput
for a varied collection. A folder layout and batch command do not supply these
capabilities.

“Everything reachable” also includes other departments, external services,
interactive pages, and material discovered only through search or login. Define
the public CS-owned collection and report coverage limits. A crawler alone
cannot promise complete discovery or correct ownership.

Students can perform repeatable intake, routine remediation, and guided checks.
Complex equations, diagrams, forms, and source ambiguities need escalation to
appropriate reviewers. Automated tools cannot establish accessibility alone.
[W3C evaluation guidance](https://www.w3.org/WAI/test-evaluate/tools/selecting/)

## Recommended next work: a small student workflow

Build one usable end-to-end workflow before adding more campus infrastructure.

1. **Inventory and prioritize.** Produce a bounded list of public CS pages and
   linked files, recording URL, format, duplicate status, owner if known, and
   processing status. Use the existing CMS inventory/export if available; add a
   small crawler only where needed. Prioritize active student-facing material.
2. **Prepare drafts for common documents.** Start with ordinary digital-text PDFs
   and DOCX originals. Add a reusable draft-generation step that preserves source
   references and flags uncertainty. Prefer repairing an editable original when
   available. Route scans, complex math, and other unsupported content to review.
   If AI is used, make it explicit and set per-document cost limits.
3. **Provide a simple review screen.** Let a student select a queued item, compare
   original and draft, correct content, run checks, and mark it ready for review.
   Students should not need to edit JSON or write Python verification scripts.
   Start with a single-operator local tool and a simple saved work list.
4. **Make verification reusable.** Combine common structure/link/accessibility
   checks with source-content comparison and a short manual checklist. Retain
   specialized tests for difficult cases, but do not require custom code for
   every document. Record findings and reviewer decisions for the exact version.
5. **Separate webpage fixes from document conversion.** For HTML pages, identify
   shared template issues and content issues, then prepare the appropriate CMS
   changes. A replacement reading edition will not repair interactive behavior.
6. **Train, review, and measure.** Give the student examples and escalation rules,
   with an identified supervisor and accessibility-review support. Test 10 varied
   items through the entire workflow and measure student time, reviewer time,
   rework, and remaining barriers before estimating hundreds of items.

Aim for a reviewed CMS draft or approved handoff as the first useful output.
MSU's published policy generally requires its CMS and templates for covered public
web content unless an exception is approved.
[MSU policy](https://www.montana.edu/policy/enterprise_it/web_accessibility_policy.html)

The smallest useful next milestone is: a student can select one ordinary new
document, get a draft, correct it, run guided checks, and hand it to a reviewer
without developer intervention. Defer distributed workers, campus-wide roles,
and additional architecture documents until that workflow works and measurements
show what is actually needed.
