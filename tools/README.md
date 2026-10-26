# Tools

## Approved proposal to pull request

Proposals come in through two Google Forms (a session, and a multi-day track) into two
Google Sheets. The Steering Committee reviews them there. Setting a row's **Status** to
**Approved** starts this chain:

1. A Google Apps Script on the sheet turns the row into a JSON payload (no email addresses
   or disclosures) and sends it to GitHub as a `session-approved` dispatch.
2. `.github/workflows/new-session.yml` runs `generate_session.py`, builds the site as a
   check, and opens a pull request with the new session, track, and lead files.
3. A person reviews the pull request and merges it. Merging publishes; nothing is
   published before that.

`generate_session.py` is the only part that writes site files. Proposal text comes from
the public, so it strips HTML and Hugo shortcode braces, allows only `https://` links,
quotes every YAML value, and refuses to overwrite existing files. `test_generate_session.py`
covers this, and uses the Rampart track (`fixtures/rampart-track.json`) as the model: the
generator must reproduce the real Rampart files exactly.

```
python3 tools/test_generate_session.py
python3 tools/generate_session.py payload.json --dry-run
```

The Apps Script that builds the forms and sends the dispatch contains a private group
address and a token setting, so it is kept outside this repository.
