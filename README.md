# pdf2md

Convert PDFs into editable Markdown drafts, with HTML previews and paired
original/revised page images for review. An optional website scanner discovers
PDFs, downloads them with confirmation, and tracks review status.

The tools run locally without an AI service or API key. Conversion infers document
structure; it does not perform OCR, automatically reconstruct diagrams, or certify
accessibility. Review the Markdown against the original before publishing it.

## Requirements

- **Python 3.11 or newer**, with `pip` and `venv`. See the
  [Python downloads](https://www.python.org/downloads/) and
  [virtual-environment instructions](https://docs.python.org/3/library/venv.html).
- **Pandoc**, available on your `PATH`. Pandoc 3.8 is the tested version;
  use a recent release for grid tables with merged cells. Follow the
  [Windows, macOS, or Linux installation instructions](https://pandoc.org/installing.html).
- **Google Chrome or Chromium**, used in headless mode to make review images.
  Install [Chrome](https://www.google.com/chrome/) or use your Linux distribution's
  Chromium package.
- **Git**, if cloning the repository. Downloading and extracting its ZIP is another option.

The workflow has been tested on macOS with Python 3.14, Pandoc 3.8, and Chrome.
Windows and Linux setup commands are provided below; those platforms have not
been verified end to end.

## Get the project

```sh
git clone https://github.com/dldf/pdf2md.git
cd pdf2md
```

If you downloaded a ZIP, open a terminal in its extracted project folder instead.

### macOS and Linux

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Some Linux distributions package `venv` separately; install the package for your
Python version if environment creation reports that it is missing.

### Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, use Command Prompt instead:

```bat
py -3 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

Activation is optional: substitute `.venv/bin/python` on macOS/Linux or
`.\.venv\Scripts\python.exe` on Windows for `python` in subsequent commands.
This avoids changing PowerShell execution policies. If `py` is unavailable,
use the command for your installed Python 3.11+ interpreter.

Run `python --version` and `pandoc --version` to check setup. Reactivate the
virtual environment in each new terminal. Recreate `.venv` if you move or rename
the project folder; virtual environments contain absolute paths.

## Convert a PDF

Place a PDF at `input/document.pdf`, or substitute the path to your own file.
Quote paths containing spaces. From the project folder, run:

```sh
python convert.py "input/document.pdf" output
```

This creates `output/document/` containing:

| Path | Purpose |
| --- | --- |
| `content.md` | Editable draft, metadata, and review warnings |
| `assets/` | Extracted figures; omitted when there are no assets |
| `review/preview.html` | Browser preview generated from Markdown |
| `review/p001-original.png`, `review/p001-revised.png`, ... | Paired page images |

Conversion generates the initial preview automatically. A folder input converts
PDFs recursively. Existing document folders are protected from overwriting;
choose a new output root, such as `output/second-pass`, for another conversion.
If preview generation fails after extraction, the saved Markdown remains available.

### Selecting Chrome or Chromium

The tools look for `google-chrome` or `chromium` on `PATH`, then the usual macOS
Chrome application. On Windows, or for another installation location, supply
`--chrome` to both conversion and preview commands. For a common Windows install:

```powershell
python convert.py "input/document.pdf" output --chrome "C:\Program Files\Google\Chrome\Application\chrome.exe"
```

Use the actual executable path on your computer. A per-user Windows installation
or a Linux executable named `chromium-browser` may need a different path.

## Review and edit

Edit `output/document/content.md`, then refresh the preview:

```sh
python preview.py "input/document.pdf" "output/document/content.md"
```

On Windows, include the browser path again:

```powershell
python preview.py "input/document.pdf" "output/document/content.md" --chrome "C:\Program Files\Google\Chrome\Application\chrome.exe"
```

Append `--inspect` to open the saved HTML, or open `review/preview.html` yourself.
It remains available after the command finishes. Rerun preview and refresh the
browser after editing Markdown.

Sort the PNGs by filename in an image viewer to compare original/revised pairs.
Revised pages may be taller to preserve content. Check reading order, wording,
lists, tables, and image descriptions; exact visual matching is not the goal.
Use the HTML for keyboard and screen-reader review. PNGs cannot verify those
interactions, and a successful conversion does not establish accessibility.

Keep the `<!-- Source page N -->` markers and any `assets/` directory beside
`review/`. Preview generation preserves Markdown and checks that the source PDF
matches the recorded hash.

### Fonts, emphasis, and line breaks

The converter preserves detected bold and italic text and infers serif or sans
from the predominant body font. You can override the choice at the top of Markdown:

```yaml
---
font: serif
---
```

Use `serif` or `sans`. This selects a family, not an exact PDF font. Intentional
line breaks are inferred conservatively; ambiguous cases are flagged for review.
Nested lists and unusual layouts may still need manual correction.

### Images

Each figure has a stable description ID. Find it in Markdown and replace the
placeholder inside `![...]` with a meaningful description:

```md
<!-- description: desc-001 -->

![A description of what the figure communicates.](assets/figure-1.png)
```

Keep IDs unique. Add an unused ID immediately before each manually added image.
Descriptions become image alt text; the preview also displays them for review.

### Tables

The converter prefers pipe tables, then grid tables for merged cells, and HTML
when a grid cannot preserve the extracted structure. Existing captions are
preserved; otherwise a detected first column heading supplies the caption.
Confirm that the resulting title describes the table.

Table metadata is editable:

```md
<!-- table: {"widths": [25, 25, 30, 10, 10], "row_header": 1} -->
```

Widths are proportions, one per actual column; `[]` permits automatic layout.
For simple tables, `row_header: 1` makes the first column row headers; use `0` for
ordinary data. Pandoc captions use a line such as `: Table: Program Learning Outcomes`
below the table. Grid-table borders must stay aligned in a monospaced editor.

Merged cells and complex header relationships still need human review. Simplify
where appropriate, or use HTML with suitable `th`, `scope`, `rowspan`, `colspan`,
and `id`/`headers` associations. Image-only or undetected tables need reconstruction.

## Optional: discover PDFs on a website

Replace `https://example.edu/department/` with the website folder to scan:

```sh
python site.py scan "https://example.edu/department/" --scan-only --max-pages 25
python site.py tree
python site.py download
```

The scanner follows links within the same host and URL folder and respects
`robots.txt`. It cannot discover unlinked files or JavaScript-only links. The
limit counts visited URLs, including PDFs; increase it if the scan is cut short.

Downloading shows the pending count and reported sizes and asks for confirmation.
Enter `y` to download; Enter or `n` cancels. Files go under
`input/<hostname>/<website-path>/`, and existing files are not overwritten.
Omitting `--scan-only` offers the download prompt immediately after scanning.

Results and manual status are saved in local `inventory.json`. That file, new
PDF downloads, generated output, and virtual environments are excluded from Git.
Three previously tracked sample PDFs remain in `input/cs/msu-accreditation/`.

### Track review status

Use an exact PDF URL from the scan, including any query string:

```sh
python site.py status "PDF_URL" R
python site.py tree
```

| Status | Meaning |
| --- | --- |
| U | Unreviewed |
| R | In review; downloading is optional |
| C | Converted and reviewed; pending publication |
| A | Accessible at its published URL; verified by a human |

Statuses do not advance automatically. To record completed accessibility review:

```sh
python site.py status "PDF_URL" A --reviewer "YOUR_NAME" --checks "CHECKS_PERFORMED" --published-url "PUBLISHED_PAGE_URL"
```

Replace the placeholders with actual details. Omit `--published-url` when the
original URL serves the reviewed document. This records your verification;
it does not upload, test, or publish the document. Publication is not implemented.

## Troubleshooting

- **Missing Pandoc or browser:** check `pandoc --version` and supply `--chrome`
  with the full executable path. Python requirements do not install these programs.
- **`CERTIFICATE_VERIFY_FAILED` during scanning:** repair the certificate setup
  for your Python installation. On macOS, python.org installers provide an
  `Install Certificates.command` in that Python version's Applications folder.
  On managed computers, ask your IT team about required certificate authorities.
- **Existing output folder:** select a new output root for reconversion. Use
  `preview.py` when you only want to render Markdown edits.
- **Little or no extracted text:** this converter has no OCR stage. Obtain a
  text-bearing PDF or transcribe/OCR the content separately before review.

Run `python convert.py --help`, `python preview.py --help`, or
`python site.py --help` for command options.
