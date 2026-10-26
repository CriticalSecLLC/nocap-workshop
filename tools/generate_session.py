#!/usr/bin/env python3
"""Turn an approved proposal (JSON) into site content.

Usage:
    python3 tools/generate_session.py payload.json [--root DIR] [--dry-run] [--force]

Writes, relative to the site root:
    content/sessions/<slug>.md      one per session
    content/tracks/<track>.md       for a multi-day track
    data/leads.yaml                 appends any lead not already listed

and prints a JSON summary (branch, pull-request title and body, files) on stdout.

Payload shape (the Google Sheets publisher builds this; see the proposal-form script):
    {
      "type": "session" | "track",
      "lead":   {"name", "org", "org_url"?, "bio", "photo_url"?},
      "coleads": [{"name", "org", "bio"}],
      "track":  {"name", "slug"?, "url"?, "summary", "overview"},      # tracks only
      "sessions": [{"title", "day", "start", "end", "description",
                    "tagline"?, "outcome"?, "prerequisites"?, "slug"?}]
    }

Proposal text comes from the public, so everything is cleaned before it is
written: HTML is stripped, Hugo shortcode braces are removed, only http(s) links
are allowed, YAML values are quoted safely, and contact details are never
accepted. A person still reviews the pull request before anything is published.
"""
import argparse
import json
import os
import re
import sys
import unicodedata
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SLUG_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
ISO_RE = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$')
URL_RE = re.compile(r'^https://[^\s<>"\']+$')
TAG_RE = re.compile(r'<[^>]*>')
LINK_RE = re.compile(r'(!?)\[[^\]]*\]\(\s*<?([^)\s>]*)')
CTRL_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')


class PayloadError(ValueError):
    pass


# --- cleaning --------------------------------------------------------------

def clean(text, maxlen, field, multiline=False, required=True):
    if text is None:
        text = ''
    if not isinstance(text, str):
        raise PayloadError(f'{field}: expected text')
    s = unicodedata.normalize('NFC', text).replace('\r\n', '\n').replace('\r', '\n')
    s = CTRL_RE.sub('', s)
    s = TAG_RE.sub('', s)
    for token in ('{{', '}}', '{%', '%}'):
        s = s.replace(token, '')
    if multiline:
        paras = [re.sub(r'\s+', ' ', p).strip() for p in re.split(r'\n\s*\n', s)]
        s = '\n\n'.join(p for p in paras if p)
    else:
        s = re.sub(r'\s+', ' ', s).strip()
    if required and not s:
        raise PayloadError(f'{field}: required')
    if len(s) > maxlen:
        raise PayloadError(f'{field}: {len(s)} characters, limit is {maxlen}')
    for bang, target in LINK_RE.findall(s):
        if bang:
            raise PayloadError(f'{field}: images are not allowed')
        if not target.startswith(('https://', 'http://')):
            raise PayloadError(f'{field}: only http(s) links are allowed')
    return s


def clean_url(url, field, required=False):
    if url is None or str(url).strip() == '':
        if required:
            raise PayloadError(f'{field}: required')
        return ''
    u = str(url).strip()
    if not URL_RE.match(u):
        raise PayloadError(f'{field}: must be an https:// link')
    return u


def slugify(text):
    s = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()
    s = re.sub(r'[^a-zA-Z0-9]+', '-', s).strip('-').lower()
    return s


def check_slug(slug, field):
    if not SLUG_RE.match(slug or ''):
        raise PayloadError(f'{field}: "{slug}" is not a valid slug')
    return slug


# --- YAML (hand-written so no dependency, and always safely quoted) --------

_PLAIN_BAD_START = set('-?:,[]{}#&*!|>\'"%@`')
_RESERVED = re.compile(r'^(?:true|false|yes|no|on|off|null|~|[-+]?[0-9][0-9_.,:eE+-]*)$', re.I)


def yscalar(s):
    plain = (
        s == s.strip() and s != '' and '\n' not in s and '\t' not in s
        and s[0] not in _PLAIN_BAD_START and ': ' not in s and ' #' not in s
        and not s.endswith(':') and not _RESERVED.match(s)
    )
    return s if plain else json.dumps(s, ensure_ascii=False)


def front_matter(pairs):
    lines = ['---']
    for key, value in pairs:
        if value is None:
            continue
        if isinstance(value, raw):
            lines.append(f'{key}: {value}')
        elif isinstance(value, list):
            lines.append(f'{key}: [' + ', '.join(yscalar(v) for v in value) + ']')
        else:
            lines.append(f'{key}: {yscalar(str(value))}')
    lines.append('---')
    return '\n'.join(lines) + '\n'


class raw(str):
    """A value written as-is (validated dates)."""


# --- site data -------------------------------------------------------------

def schedule_dates(root):
    path = os.path.join(root, 'data', 'schedule.yaml')
    with open(path, encoding='utf-8') as f:
        text = f.read()
    dates = {}
    for m in re.finditer(r'-\s*day:\s*(\d+)\s*\n\s*date:\s*"?(\d{4}-\d{2}-\d{2})"?', text):
        dates[int(m.group(1))] = m.group(2)
    return dates


def existing_lead_ids(root):
    path = os.path.join(root, 'data', 'leads.yaml')
    if not os.path.exists(path):
        return set()
    with open(path, encoding='utf-8') as f:
        return set(re.findall(r'^- id:\s*(\S+)\s*$', f.read(), re.M))


def lead_entry(lead_id, name, org, org_url, bio):
    lines = [f'- id: {lead_id}', f'  name: {yscalar(name)}']
    if org:
        lines.append(f'  org: {yscalar(org)}')
    if org_url:
        lines.append(f'  org_url: {org_url}')
    lines.append('  bio: >-')
    lines.append('    ' + bio)
    return '\n'.join(lines) + '\n'


# --- main ------------------------------------------------------------------

def build(payload, root):
    kind = payload.get('type')
    if kind not in ('session', 'track'):
        raise PayloadError('type: must be "session" or "track"')
    dates = schedule_dates(root)
    notes = []

    people = []
    lead = payload.get('lead') or {}
    people.append({
        'name': clean(lead.get('name'), 80, 'lead.name'),
        'org': clean(lead.get('org'), 80, 'lead.org', required=False),
        'org_url': clean_url(lead.get('org_url'), 'lead.org_url'),
        'bio': clean(lead.get('bio'), 1200, 'lead.bio'),
    })
    if lead.get('photo_url'):
        notes.append('Headshot link from the proposal: ' + clean_url(lead['photo_url'], 'lead.photo_url')
                     + ' (save a square crop under assets/img/ and add a photo: line to data/leads.yaml)')
    for i, c in enumerate(payload.get('coleads') or [], 1):
        people.append({
            'name': clean(c.get('name'), 80, f'colead{i}.name'),
            'org': clean(c.get('org'), 80, f'colead{i}.org', required=False),
            'org_url': '',
            'bio': clean(c.get('bio'), 1200, f'colead{i}.bio'),
        })
    for p in people:
        p['id'] = check_slug(slugify(p['name']), f'lead id for {p["name"]}')
    ids = [p['id'] for p in people]
    if len(set(ids)) != len(ids):
        raise PayloadError('leads: two leads have the same name')

    sessions_in = payload.get('sessions') or []
    if not sessions_in:
        raise PayloadError('sessions: at least one is required')

    track = None
    track_slug = None
    if kind == 'track':
        t = payload.get('track') or {}
        track = {
            'name': clean(t.get('name'), 80, 'track.name'),
            'url': clean_url(t.get('url'), 'track.url'),
            'summary': clean(t.get('summary'), 240, 'track.summary'),
            'overview': clean(t.get('overview'), 4000, 'track.overview', multiline=True),
        }
        base = re.sub(r'-?track$', '', slugify(track['name']))
        track_slug = check_slug(t.get('slug') or base, 'track.slug')
        if sorted(int(s.get('day', 0)) for s in sessions_in) != [1, 2, 3]:
            raise PayloadError('sessions: a track needs one session on each of days 1, 2, and 3')

    sessions = []
    for i, s in enumerate(sessions_in, 1):
        f = f'session{i}'
        day = s.get('day')
        if day not in (1, 2, 3):
            raise PayloadError(f'{f}.day: must be 1, 2, or 3')
        start, end = str(s.get('start', '')), str(s.get('end', ''))
        for label, v in (('start', start), ('end', end)):
            if not ISO_RE.match(v):
                raise PayloadError(f'{f}.{label}: needs a date and time with offset, like 2027-01-26T10:00:00-08:00')
        if datetime.fromisoformat(end) <= datetime.fromisoformat(start):
            raise PayloadError(f'{f}: end must be after start')
        if dates.get(day) and start[:10] != dates[day]:
            raise PayloadError(f'{f}.start: day {day} is {dates[day]}, but start is {start[:10]}')
        title = clean(s.get('title'), 120, f'{f}.title')
        body = clean(s.get('description'), 2500, f'{f}.description', multiline=True)
        outcome = clean(s.get('outcome'), 800, f'{f}.outcome', multiline=True, required=False)
        prereq = clean(s.get('prerequisites'), 600, f'{f}.prerequisites', multiline=True, required=False)
        if outcome:
            body += '\n\n**You will leave with:** ' + outcome
        if prereq:
            body += '\n\n**Prerequisites:** ' + prereq
        slug = check_slug(s.get('slug') or slugify(title), f'{f}.slug')
        pairs = [
            ('title', title),
            ('tagline', clean(s.get('tagline'), 200, f'{f}.tagline', required=False) or None),
            ('day', raw(str(day))),
            ('start', raw(start)),
            ('end', raw(end)),
        ]
        if track_slug:
            pairs.append(('track', track_slug))
        pairs.append(('leads', ids))
        sessions.append((slug, front_matter(pairs) + body + '\n', title, day))

    files = {}
    for slug, text, title, day in sessions:
        files[f'content/sessions/{slug}.md'] = text
    if track:
        pairs = [('title', track['name']), ('link', track['url'] or None), ('description', track['summary'])]
        files[f'content/tracks/{track_slug}.md'] = front_matter(pairs) + track['overview'] + '\n'

    have = existing_lead_ids(root)
    new_leads = [p for p in people if p['id'] not in have]
    leads_text = ''.join(lead_entry(p['id'], p['name'], p['org'], p['org_url'], p['bio']) for p in new_leads)
    for p in people:
        if p['id'] in have:
            notes.append(f'{p["name"]} is already in data/leads.yaml and was left unchanged.')

    primary = sessions[0][0] if kind == 'session' else track_slug
    title = sessions[0][2] if kind == 'session' else track['name']
    summary = {
        'branch': f'proposal/{primary}',
        'pr_title': ('Add session: ' if kind == 'session' else 'Add track: ') + title,
        'files': sorted(list(files) + (['data/leads.yaml'] if leads_text else [])),
        'notes': notes,
    }
    body_lines = ['Generated from an approved proposal. Review the files, then merge to publish.', '']
    body_lines += [f'- `{p}`' for p in summary['files']]
    body_lines += ['', 'Before merging, check:',
                   '- the start and end times and the day',
                   '- the lead details and any headshot',
                   '- that nothing in the text reads as a pitch or a disparagement (see the Lead Agreement)']
    if notes:
        body_lines += [''] + [f'- Note: {n}' for n in notes]
    summary['pr_body'] = '\n'.join(body_lines) + '\n'
    return files, leads_text, summary


def write_all(root, files, leads_text, force):
    for rel, text in files.items():
        path = os.path.join(root, rel)
        if os.path.exists(path) and not force:
            raise PayloadError(f'{rel} already exists (use --force to replace it)')
    for rel, text in files.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path + '.tmp', 'w', encoding='utf-8') as f:
            f.write(text)
        os.replace(path + '.tmp', path)
    if leads_text:
        path = os.path.join(root, 'data', 'leads.yaml')
        with open(path, 'a+', encoding='utf-8') as f:
            f.seek(0)
            existing = f.read()
            if existing and not existing.endswith('\n'):
                f.write('\n')
            f.write(leads_text)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('payload')
    ap.add_argument('--root', default=ROOT)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--force', action='store_true')
    args = ap.parse_args(argv)
    try:
        with open(args.payload, encoding='utf-8') as f:
            payload = json.load(f)
        files, leads_text, summary = build(payload, args.root)
        if not args.dry_run:
            write_all(args.root, files, leads_text, args.force)
    except (PayloadError, json.JSONDecodeError, OSError) as e:
        print(f'error: {e}', file=sys.stderr)
        return 1
    json.dump(summary, sys.stdout, indent=2)
    print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
