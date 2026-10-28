#!/usr/bin/env python3
"""Tests for generate_session.py. Run: python3 tools/test_generate_session.py

The Rampart track is the model: the fixture is Rampart written as a proposal, and
the first test checks that the generator reproduces the real Rampart files.
"""
import copy
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import generate_session as g  # noqa: E402

with open(os.path.join(HERE, 'fixtures', 'rampart-track.json'), encoding='utf-8') as f:
    RAMPART = json.load(f)


def make_root():
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, 'data'))
    shutil.copy(os.path.join(REPO, 'data', 'schedule.yaml'), os.path.join(root, 'data', 'schedule.yaml'))
    with open(os.path.join(root, 'data', 'leads.yaml'), 'w') as f:
        f.write('# leads\n')
    return root


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


class RampartRoundTrip(unittest.TestCase):
    def setUp(self):
        self.root = make_root()
        self.addCleanup(shutil.rmtree, self.root)

    def test_sessions_match_real_files(self):
        files, leads, summary = g.build(RAMPART, self.root)
        g.write_all(self.root, files, leads, False)
        for slug in ('rampart-data-collection', 'rampart-vdr-evaluation', 'rampart-remediation-reporting'):
            rel = f'content/sessions/{slug}.md'
            self.assertEqual(read(os.path.join(self.root, rel)), read(os.path.join(REPO, rel)), rel)

    def test_track_matches_real_file_minus_placeholder_note(self):
        files, leads, summary = g.build(RAMPART, self.root)
        real = read(os.path.join(REPO, 'content/tracks/rampart.md'))
        head, body = real.split('---\n', 2)[1], real.split('---\n', 2)[2]
        paras = [p for p in body.strip('\n').split('\n\n') if not p.startswith('**Placeholder.**')]
        expected = '---\n' + head + '---\n' + '\n\n'.join(paras) + '\n'
        self.assertEqual(files['content/tracks/rampart.md'], expected)

    def test_lead_entry(self):
        files, leads, summary = g.build(RAMPART, self.root)
        self.assertIn('- id: george-chamales\n  name: George Chamales\n  org: CriticalSec\n  org_url: https://criticalsec.com\n  bio: >-\n', leads)
        self.assertEqual(summary['branch'], 'proposal/rampart')
        self.assertEqual(summary['pr_title'], 'Add track: Rampart Track')

    def test_existing_lead_left_alone(self):
        with open(os.path.join(self.root, 'data', 'leads.yaml'), 'a') as f:
            f.write('- id: george-chamales\n  name: George Chamales\n')
        files, leads, summary = g.build(RAMPART, self.root)
        self.assertEqual(leads, '')
        self.assertTrue(any('already in data/leads.yaml' in n for n in summary['notes']))


class SingleSession(unittest.TestCase):
    def setUp(self):
        self.root = make_root()
        self.addCleanup(shutil.rmtree, self.root)
        self.p = {
            'type': 'session',
            'lead': {'name': 'Ada Example', 'org': 'Example Co', 'org_url': 'https://example.com', 'bio': 'Ran VDR at scale.'},
            'coleads': [{'name': 'Bo Second', 'org': 'Other Inc', 'bio': 'Built the scanners.'}],
            'sessions': [{'title': 'Inventory: What Counts?', 'day': 1, 'start': '2027-01-19T13:00:00-08:00',
                          'end': '2027-01-19T14:30:00-08:00', 'description': 'Walk through building an inventory.',
                          'outcome': 'A working inventory template.', 'prerequisites': 'A scanner export.'}],
        }

    def test_basic(self):
        files, leads, summary = g.build(self.p, self.root)
        text = files['content/sessions/inventory-what-counts.md']
        self.assertIn('title: "Inventory: What Counts?"', text)
        self.assertIn('leads: [ada-example, bo-second]', text)
        self.assertIn('**You will leave with:** A working inventory template.', text)
        self.assertIn('**Prerequisites:** A scanner export.', text)
        self.assertNotIn('track:', text)
        self.assertIn('- id: bo-second', leads)

    def test_html_and_shortcodes_stripped(self):
        self.p['sessions'][0]['description'] = 'Hello <script>alert(1)</script> world {{< youtube abc >}} done'
        files, _, _ = g.build(self.p, self.root)
        text = files['content/sessions/inventory-what-counts.md']
        self.assertNotIn('<script', text)
        self.assertNotIn('{{', text)
        self.assertIn('alert(1)', text)  # text kept, tags removed

    def test_yaml_injection_is_quoted(self):
        self.p['sessions'][0]['title'] = 'x"\nday: 3\nleads: [evil]'
        files, _, _ = g.build(self.p, self.root)
        text = list(files.values())[0]
        self.assertEqual(text.count('\nday:'), 1)
        self.assertEqual(text.count('\nleads:'), 1)

    def test_javascript_link_rejected(self):
        self.p['sessions'][0]['description'] = 'See [this](javascript:alert(1)).'
        with self.assertRaises(g.PayloadError):
            g.build(self.p, self.root)

    def test_image_rejected(self):
        self.p['sessions'][0]['description'] = '![x](https://example.com/x.png)'
        with self.assertRaises(g.PayloadError):
            g.build(self.p, self.root)

    def test_http_link_allowed(self):
        self.p['sessions'][0]['description'] = 'See [this](https://example.com/a).'
        g.build(self.p, self.root)

    def test_bad_dates(self):
        for bad in ('2027-01-19 13:00', '2027-01-19T13:00:00'):
            q = copy.deepcopy(self.p); q['sessions'][0]['start'] = bad
            with self.assertRaises(g.PayloadError):
                g.build(q, self.root)
        q = copy.deepcopy(self.p); q['sessions'][0]['end'] = '2027-01-19T12:00:00-08:00'
        with self.assertRaises(g.PayloadError):
            g.build(q, self.root)

    def test_day_must_match_schedule(self):
        self.p['sessions'][0]['day'] = 2
        with self.assertRaises(g.PayloadError):
            g.build(self.p, self.root)

    def test_refuses_to_overwrite(self):
        files, leads, _ = g.build(self.p, self.root)
        g.write_all(self.root, files, leads, False)
        with self.assertRaises(g.PayloadError):
            g.write_all(self.root, files, '', False)
        g.write_all(self.root, files, '', True)

    def test_url_must_be_https(self):
        self.p['lead']['org_url'] = 'http://example.com'
        with self.assertRaises(g.PayloadError):
            g.build(self.p, self.root)

    def test_track_needs_three_days(self):
        q = copy.deepcopy(RAMPART); q['sessions'] = q['sessions'][:2]
        with self.assertRaises(g.PayloadError):
            g.build(q, self.root)

    def test_no_contact_details_accepted(self):
        # email is simply not a field; extra keys are ignored and never written
        self.p['lead']['email'] = 'ada@example.com'
        files, leads, _ = g.build(self.p, self.root)
        self.assertNotIn('ada@example.com', ''.join(files.values()) + leads)


if __name__ == '__main__':
    unittest.main(verbosity=1)
