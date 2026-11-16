# Sponsorship Agreement

The blank agreement that sponsors sign, built as a PDF with fillable fields and a Word file with
form controls. `agreement.json` is the single source of the text; `build.py` renders both files.

```
pip install -r tools/agreement/requirements.txt     # pypdf, python-docx
python3 tools/agreement/build.py                    # writes static/nocap-sponsorship-agreement.{pdf,docx}
python3 tools/agreement/build.py my-sponsor.json    # per-sponsor draft into tools/agreement/build/ (untracked)
```

It also needs Google Chrome or Chromium (set `CHROME` to its path if it is not found) and poppler's
`pdftotext`. The blank files in `static/` are what the Sponsors page links to, so rebuild and commit
them with any change to the agreement.

## Changing the agreement

1. Edit `agreement.json`. Clauses are in `clauses`, the signature page in `info` and `signatures`, and
   the tier table in `exhibit`. `{{name}}` marks a fillable field defined under `fields`.
2. Bump `version` and `version_date`. Every change to the text is a new version, however small, because
   sponsors sign a specific copy.
3. Run `build.py`, check the PDF (4 pages, 9 fillable fields), and commit the JSON and both files in `static/`.

The version appears in four places in each file: the footer of every page, an "Agreement Version" row
on the Sponsorship Information page, which the signers see, and the document properties (title and
subject). To find which version a sponsor signed, read that row or the footer.

## Per-sponsor drafts

A JSON file of field names to fixed text (see `overrides.example.json`) fills those fields instead of
leaving them blank. Drafts for named sponsors hold their address and contact details, so keep them
out of the repository. The output folder `tools/agreement/build/` is ignored.

## Versions

| Version | Date | Change |
| --- | --- | --- |
| 1.0 | November 10, 2026 | First release. Predates version stamping, so copies of it carry no version. |
| 1.1 | November 16, 2026 | Exhibit A: Founding, Gold and Silver also get their name in the description of every recording, as Community does. Version shown in the footer and on the signature page. |

The tier table here must match `data/sponsors.yaml`, `content/sponsors.md` and `tools/sponsor-summary.html`.
