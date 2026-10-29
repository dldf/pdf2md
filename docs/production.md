# Production direction

Status: production foundation, not a deployed service. The repository currently
reconstructs two PDF reading editions. It does not automatically remediate
arbitrary PDFs, Office files, websites, or media. A successful batch is not an
accessibility approval.

## What exists now

- A validated PDF catalog in `config/documents.json`, replacing the hard-coded
  Python registry. Each entry has an ID, department, original file and checksum,
  canonical Markdown, evidence directory, title, evidence images, and optional
  document-specific verifier. `msu-cs` is a local project slug, not an official
  university identifier or access-control boundary.
- A sequential batch runner with department/document selection, dry runs,
  per-stage timeouts, per-document logs, and a JSON report updated after each
  document. A failed document does not stop the remaining documents.
- Source checksum checks before extraction/build and before/after each batch job.
- The existing 50 and 73 content/static checks for the two pilot documents.
- Unit tests for catalog validation, source changes, failures, timeouts,
  department selection, missing reconstruction/verifiers, and review status.
- GitHub Actions runs those standard-library tests and a dry-run plan on Python
  3.13. It does not yet run PDF reconstruction or accessibility audits; those
  require the deployment dependency work described below.

The runner is for one operator in one workspace. It has no durable queue,
automatic retries/resume, access control, review UI, OCR workflow, external AI
integration, or publishing connector. Do not run overlapping batches against the
same files. A timeout stops the direct subprocess; full process-tree and resource
isolation are deployment work. The current generated paths are mutable; run logs
are separate, but outputs are not immutable releases.

## Operating the local pilot

```sh
# Inspect the plan without processing or writing files.
.venv/bin/python scripts/batch.py --department msu-cs --dry-run

# Extract, build, and verify all registered CS documents.
.venv/bin/python scripts/batch.py --department msu-cs --stage all

# Rebuild and verify a selected document after an editorial change.
.venv/bin/python scripts/batch.py --document 2025-Year0-DS-Plan --stage build
.venv/bin/python scripts/batch.py --document 2025-Year0-DS-Plan --stage verify
```

Logs and `report.json` live in ignored `output/runs/<run-id>/`. Exit code 0 means
the requested stages finished; even `checks_passed_needs_review` needs human
review. Exit code 1 indicates failed, timed-out, or blocked documents. Rerun
specific IDs after resolving the problem. An interrupted report can retain
`running`/`not_started`; it is not proof of completion. A dry run validates the
catalog and selection, not input-file availability or tool installation.

To register another PDF, add a unique ID and department to the catalog, record
its actual SHA-256, and choose dedicated source/evidence paths. IDs use letters,
numbers, hyphens, and underscores. Paths stay within the workspace. Originals
may live in a local ignored collection. `source` names the expected Markdown;
the build is blocked until that file exists. `verifier: null` explicitly means
fidelity verification is not implemented and blocks a successful full run.
Verifier scripts are trusted repository code, invoked without document arguments;
each registered verifier must check that particular document. Do not reuse the
pilot verifier unchanged for unrelated PDFs. Catalog edits require code review.

The current Pandoc Markdown includes raw HTML tables. It is an HTML-oriented
representation, not yet a portable document model for every exporter.

## Service design for hundreds of items

Use one shared service with department workspaces, rather than a repository or
code fork per department. The user selected public CS department documents and
webpages for the first pilot. See [the public CS pilot](public-cs-pilot.md) for
scope, initial source candidates, and intake requirements. Restricted course
materials and other departments remain later phases; campus roles and publishing
access have not been assigned.

```text
Inventory -> Triage -> Extract -> Reconstruct -> Automated checks
                                  ^                    |
                                  |---- Review --------|
                                           |
                                 Approved version -> CMS draft -> Publish -> Monitor
```

1. **Inventory and triage.** Record owning unit, content owner, source location,
   audience/access classification, format, language, checksum, page count, usage,
   required output, and intended destination. Unknowns stay unknown. Prioritize
   active student services, current course needs, requested accommodations, and
   heavily used material. Prefer a good editable original when one exists.
   Route duplicates, replacements, and retention questions to the owner; do not
   silently delete or assume older content is exempt.
2. **Versioned storage.** Keep originals and derived artifacts in approved object
   storage. Keep source versions, findings, jobs, and approvals in a relational
   database. Git holds code, templates, tests, and approved small fixtures, not
   the campus document collection. Retain provenance back to pages, cells,
   slides, timestamps, and source URLs.
3. **Workers and queue.** Use a durable job queue and a small bounded worker pool.
   Key a stage by unit, source checksum, canonical revision, pipeline version,
   configuration, and tool/model versions. Retry transient errors; route broken
   documents to a visible failure queue. Make completion idempotent. Put parsers
   in isolated workers with CPU, memory, file-size, page-count, time, and network
   limits. Write immutable outputs, then atomically register their completion.
4. **Review workbench.** Show original and proposed edition together, with
   findings and source references. Track content accuracy and accessibility
   separately. Human reviewers resolve uncertain tables, equations, diagrams,
   forms, and OCR. If AI assists reconstruction, retain its provenance, constrain
   it to draft outputs, and treat embedded source instructions as untrusted.
5. **Publish and maintain.** Export approved content to a CMS draft through the
   supported campus process. Preserve source-to-published-URL mappings and
   rollback history. Check the actual published page, including its CMS template.
   Source, canonical content, template, or output changes invalidate approvals
   for the affected version. Monitor broken links and later accessibility changes.

An initial single-server database/worker deployment may be adequate, but capacity
must be measured. Add workers when queue measurements justify it. Distributing
the workers before solving review and ownership will not fix those bottlenecks.

## Content-specific routes

| Content | Proposed route | Required review |
| --- | --- | --- |
| Digital-text PDF | Layout/text extraction, semantic reconstruction, HTML edition | Reading order, content coverage, tables, links, figures |
| Scanned PDF/image | OCR with language selection and page evidence, then reconstruction | Uncertain text, numbers, equations, page completeness |
| Word | Repair the editable source and produce semantic HTML or an accessible document | Styles, headings, tables, alternatives, exported semantics |
| PowerPoint | Repair slide structure and reading order; provide an appropriate reading edition | Slide sequence, visuals, notes, meaningful alternatives |
| Excel | Repair workbook structure and provide accessible tables where appropriate | Headers, formulas, relationships, charts; preserve function |
| Webpage/form | Fix the CMS template or component and its content | Keyboard use, focus, labels, errors, dynamic behavior |
| Audio/video | Caption/transcript workflow and audio description where needed | Timing, speaker identification, meaningful visual information |
| Math, charts, technical diagrams | Structured math and contextual descriptions with source evidence | Subject-matter accuracy and assistive-technology use |

Only the first row has a limited implementation today. HTML cannot substitute
for essential spreadsheet functions, interactive forms, or equivalent access to
media. Required downloadable formats need separate export validation; tagged
PDF output is a distinct workstream.

## Campus ownership and review

Proposed roles, not assigned people: a campus service owner maintains the
platform and common checks; each department identifies content owners and
subject reviewers; accessibility reviewers evaluate usability; authorized
publishers release approved versions. Confirm staffing and responsibilities with
MSU before treating this as an operational service.

Use campus SSO, unit-scoped roles, separate restricted storage, and audited
permissions. A department filter is not security. Shared files still need unit
ownership and review; deduplication must not reveal restricted content across
units. Set retention, backup/restore, incident handling, external processing
permissions, and cost limits before accepting protected material.

Review records should bind reviewer identity, scope, findings, evidence, and
decision to exact source/canonical/output versions. Publication requires resolved
blocking findings, content review, accessibility review, and an authorized
destination. Approval is invalid when those versions change. Exceptions belong
to the university's established process, not an agent decision.

The published [MSU Web Accessibility Policy](https://www.montana.edu/policy/enterprise_it/web_accessibility_policy.html)
requires university CMS/templates for covered public web content unless an
exception is approved, assigns responsibilities to content developers, and
addresses accessibility and multimedia. Its definition covers content available
without login; that scope does not establish that restricted course material has
no accessibility obligations. Confirm the applicable campus requirements for
each collection. The service should integrate with the CMS and existing
accessibility support, not claim to replace them.

[W3C's evaluation guidance](https://www.w3.org/WAI/test-evaluate/tools/selecting/)
explains why automated tools cannot establish accessibility on their own. Use
maintained automated checks plus keyboard, screen-reader, zoom/reflow, contrast,
and content-specific human testing. Confirm the applicable standard and review
criteria with MSU; this repository does not determine legal deadlines or certify
conformance.

## Capacity and rollout

Measure compute time and review time separately, by format and complexity. Track
pages, extraction failures, time to first draft, reviewer minutes, rework rate,
blocking findings, and published items. Compute throughput does not establish
end-to-end remediation throughput.

For illustration only: 500 documents averaging 20 minutes of human review need
about 167 reviewer hours, before additional reconstruction, rework, or publishing.
At 90 minutes each, they need 750 hours. Neither rate is measured by this pilot.
Use `documents × measured average review minutes / 60` and separately budget
setup, exceptional items, and maintenance. No capacity or price guarantee is
supported by two documents.

Proposed rollout, without committed dates:

1. Inventory public CS documents and webpages and select 20–30 varied items with
   content owners, starting from the linked pilot candidates. Include different
   structures and formats actually found in that collection; do not benchmark
   only easy PDFs or assume scans and Office files are present. Establish review
   criteria and measure time per content class.
2. Implement durable intake/versioning, review records, isolated workers, and
   the first supported CMS draft export. Add reusable validators and benchmark
   fixtures for those content classes. Retain the two existing regression cases.
3. Pilot with a second department with different content needs. Verify permissions,
   review handoffs, terminology, template reuse, and access to published outputs.
4. Expand in measured batches after the operational gates below are met. Train
   authors and provide accessible source templates to reduce recurring backlog.

Before live production: verify a reproducible deployment from a clean machine;
separate and validate runtime dependencies for that platform (the present lock
file is a local pilot snapshot); run full pipeline and accessibility regression
checks in CI; test queue retries, duplicate jobs, crashes, oversized files, and
timeouts; test permissions and restoration from backup; validate publication and
rollback; establish service ownership and monitoring. These are outstanding work,
not capabilities supplied by the local batch runner.
