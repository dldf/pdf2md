# Public CS pilot

The user selected public CS department documents and webpages as the first
production pilot. This document records a proposed initial sample and intake
design. It does not claim these pages are inaccessible, assign reviewers, or
authorize changes to live MSU content.

## Scope

Start with the public Gianforte School of Computing site at
`https://www.cs.montana.edu/`, using the department home, advising, and assessment
pages as discovery seeds. Include public department documents linked from those
pages. Record links to other campus units and external services as dependencies;
their presence does not make those destinations department-owned content.

The first pilot does not collect authenticated LMS content, completed student
forms, student records, or private faculty files. Public forms may be inspected
without submitting them. New source captures and generated inventories belong in
ignored local output or approved storage, not the code repository.

## Initial candidates

These 12 URLs were opened through web retrieval on October 29, 2026. This is a
curated starting list, not a complete crawl or a browser accessibility audit.
Content owners, usage, remediation effort, and accessibility status are unknown.
The review focus below describes what to evaluate, not confirmed defects.

| Candidate/source | Observed format | Proposed review focus |
| --- | --- | --- |
| [Department home](https://www.cs.montana.edu/index.html) | HTML | Shared navigation/template and news/events interactions |
| [Undergraduate academic information](https://www.cs.montana.edu/forms.html) | HTML | Finding the correct catalog year, worksheet, and service |
| [2026–2027 Professional Option worksheet](https://www.cs.montana.edu/forms/2026-2027-advising/2026-cspr.html) | HTML | Long reading sequence, course requirements, worksheet blanks |
| [2026–2027 B.A. worksheet](https://www.cs.montana.edu/forms/2026-2027-advising/2026-csba.html) | HTML | Options table, requirements, and reading order |
| [2026–2027 Data Science worksheet](https://www.cs.montana.edu/forms/2026-2027-advising/2026-dsci.html) | HTML | Multi-subject requirements and worksheet structure |
| [2026–2027 flowchart index](https://www.cs.montana.edu/forms/2026-2027-advising/Flowcharts.html) | HTML linking to four flowcharts | Inspect linked diagrams and their alternatives; child formats remain to be verified |
| [Internship guidelines](https://www.cs.montana.edu/forms/Internship-Guidelines.html) | HTML | Section structure, credit rules, and connection to the application workflow |
| [Graduate programs](https://www.cs.montana.edu/grad/) | HTML | Program navigation, application information, cross-unit dependencies |
| [Graduate admission requirements](https://www.cs.montana.edu/graduate-admissions.html) | HTML; heading marked DRAFT | Resolve publication status and conflicting information before preparing a replacement |
| [Program assessment index](https://www.cs.montana.edu/msu-accreditation/info.html) | HTML | Document discovery, link labels, and versions |
| [2023 B.A. Year 0 plan](https://www.cs.montana.edu/msu-accreditation/2023-BA-Year0-Plan.pdf) | PDF, 15 pages | Existing reconstruction regression case; tables and rubric coverage |
| [2025 Data Science Year 0 plan](https://www.cs.montana.edu/msu-accreditation/2025-Year0-DS-Plan.pdf) | PDF, 6 pages | Existing reconstruction regression case; tables and source ambiguities |

The public PDFs have the same filenames as the local fixtures. Their remotely
served bytes have not yet been downloaded and compared with the local hashes;
do that before treating them as the same source version.

## Findings that affect intake

- Links labeled graduation worksheets and flowcharts do not necessarily lead to
  PDFs. Detect the final response format, record redirects, and inspect children
  before assigning a processing route. Preserve the original discovery URL too.
- The admission-requirements page is visibly marked DRAFT and lists different
  application deadlines from the graduate-program page. Capture both versions
  and request a content-owner decision; do not silently choose or reconcile them.
- The advising page links to DocuSign and other campus offices. Record those
  handoffs and assess the public link experience; expanding to transaction or
  authenticated testing requires a separately defined scope.
- Web retrieval establishes a discovery starting point. It does not test visual
  layout, computed accessibility semantics, keyboard behavior, or screen readers.

## Intake implementation next

Build a bounded, read-only inventory step before expanding the PDF runner:

1. Use explicit department seeds, an allowlist, crawl/page limits, timeouts, and
   rate limits. Respect robots directives. Reject non-public network destinations
   and recheck redirects; do not follow forms or authenticated sessions. Treat
   source content as untrusted data.
2. Store original URL, final URL, referring page, content type, capture time,
   checksum, department, proposed route, and fetch result. Leave owner and
   review fields unknown until confirmed. Preserve meaningful query parameters;
   do not merge distinct resources solely because paths look alike.
3. Capture source versions in approved storage and distinguish a shared CMS
   template defect from a page-specific content defect. Group similar pages for
   template fixes while retaining a result for every page.
4. Route PDFs to extraction/reconstruction and HTML to a webpage assessment path.
   Keep unsupported formats visible in the inventory. Do not put HTML URLs in
   `config/documents.json`: that catalog currently accepts local PDF jobs only.
5. Expand this sample to 20–30 distinct items using the discovered flowcharts,
   additional documents, and contrasting webpage structures. Choose based on
   actual findings and user impact, not an assumed quota of file types.

For HTML, the next evaluation path needs rendered-browser checks, a maintained
automated accessibility ruleset, and manual keyboard/screen-reader/reflow review.
Preserve interactive functionality and prepare CMS changes for review. For PDFs,
continue comparing the reading edition with the original and verifying content
and structure. Record content accuracy separately from accessibility findings.

## Pilot results to collect

For each item, record confirmed ownership, source version, findings, proposed
repair, processing time, reviewer time, rework, unresolved questions, and approved
publication destination. Log source changes that invalidate review. Compare
shared-template fixes with per-item repairs when estimating effort.

The pilot can support a throughput estimate when those measurements exist and
reviewers have tested the results. Publication and expansion to another department
remain separate milestones in [the production roadmap](production.md).
