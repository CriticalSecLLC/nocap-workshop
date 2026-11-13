# Tools

## Publishing an approved proposal

Leads propose through one Google Form (single session or multi-day track), and can edit
their answers there until the deadline. The Steering Committee reviews the responses
sheet. When it is time to publish a proposal, `generate_session.py` turns it into the
files the site needs:

- `content/sessions/<slug>.md` for each session
- `content/tracks/<track>.md` for a multi-day track
- an entry in `data/leads.yaml` for any lead not already listed

```
python3 tools/generate_session.py payload.json --dry-run   # preview
python3 tools/generate_session.py payload.json             # write the files
```

The payload is a small JSON document (its shape is described at the top of
`generate_session.py`) with the lead, any co-leads, the track if there is one, and each
session including the start and end times the committee set in the sheet. It never takes
an email address or the disclosures. Proposal text comes from the public, so the
generator strips HTML and Hugo shortcode braces, allows only `https://` links, quotes every
YAML value, and refuses to overwrite existing files.

`test_generate_session.py` covers this, and uses the Rampart track
(`fixtures/rampart-track.json`) as the model: the generator must reproduce the real Rampart
files exactly.

```
python3 tools/test_generate_session.py
```

The Apps Script that builds the form contains a private group address, so it is kept
outside this repository.

## Sponsor summary PDF

`sponsor-summary.html` is the source of `static/nocap-sponsor-summary.pdf`, which the Sponsors page links to. The tiers and
availability in it are typed in, not read from `data/sponsors.yaml`, so update both when a sponsor signs. To rebuild the PDF
(one Letter page):

```
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --no-pdf-header-footer \
  --print-to-pdf=static/nocap-sponsor-summary.pdf tools/sponsor-summary.html
```

## Press kit images

`python3 tools/press/build.py` (needs Google Chrome) regenerates `static/press/img/` and `data/press.yaml` for the unlinked `/press/` page. Re-run it whenever `data/sponsors.yaml` or the taglines in `data/headlines.yaml` change.
