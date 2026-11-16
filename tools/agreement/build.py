#!/usr/bin/env python3
"""Build the No-CAP Sponsorship Agreement (PDF with fillable fields + Word) from agreement.json.

Usage:  python3 tools/agreement/build.py [overrides.json]
No argument builds the blank TEMPLATE into static/ (the files the Sponsors page links to).
An overrides file (see overrides.example.json) fills named fields with fixed text and builds a
per-sponsor DRAFT into tools/agreement/build/ (not tracked).
Edit agreement.json (the single source of text, including "version") and re-run.
Needs: pip install -r tools/agreement/requirements.txt; Google Chrome or Chromium (set CHROME to
override the lookup); poppler's pdftotext.
"""
import html, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
_RAW = (HERE / 'agreement.json').read_text(encoding='utf-8')
VERSION = json.loads(_RAW)['version']
VERSION_LINE = f'Version {VERSION}, {json.loads(_RAW)["version_date"]}'
DATA = json.loads(_RAW.replace('@VERSION_LINE@', VERSION_LINE))   # signature page records which version is signed
CSS = (HERE / 'style.css').read_text(encoding='utf-8')
DOC_TITLE = f'No-CAP Workshop {DATA["title"]} v{VERSION}'

def find_chrome():
    for c in [os.environ.get('CHROME'), '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
              *(shutil.which(n) for n in ('google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'chrome'))]:
        if c and Path(c).exists(): return c
    sys.exit('Chrome or Chromium not found. Install it or set CHROME to its path.')
CHROME = find_chrome()
OVR = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')) if len(sys.argv) > 1 else {}   # optional: values that replace fillable fields
# The blank template is the published copy; a sponsor draft is a working file.
OUT = (HERE / 'build') if OVR else (REPO / 'static')
OUT.mkdir(exist_ok=True)
BASENAME = f'NoCAP-Sponsorship-Agreement-v{VERSION}-{Path(sys.argv[1]).stem.capitalize()}-DRAFT' if OVR else 'nocap-sponsorship-agreement'
FIELDS = {k: v for k, v in DATA['fields'].items() if k not in OVR}
TOKEN = re.compile(r'\{\{(\w+)\}\}')
e = html.escape

# ---------------------------------------------------------------- HTML / PDF
def h_field(name, marker):
    f = FIELDS[name]
    mk = f'<i class="mk">FLD_{name}</i>' if marker else ''
    return f'<span class="fld" style="width:{f["w"]}pt">{mk}&nbsp;</span>'

def h_text(t, marker):
    out, pos = '', 0
    for m in TOKEN.finditer(t):
        out += e(t[pos:m.start()]) + (e(OVR[m.group(1)]) if m.group(1) in OVR else h_field(m.group(1), marker)); pos = m.end()
    return out + e(t[pos:])

def build_html(marker):
    d = DATA; o = []
    o.append(f'<!doctype html><html><head><meta charset="utf-8"><title>{e(DOC_TITLE)}</title><style>\n'
             '@page { size: 8.5in 11in; margin: .65in .8in .65in; '
             '@bottom-center { content: "Sponsorship Agreement v' + VERSION + ' · Page " counter(page) " of " counter(pages); font: 8pt ui-monospace, Menlo, monospace; color: #5b6470; letter-spacing: .06em; } }\n'
             'body { font-family: Arial, Helvetica, sans-serif; font-size: 9.6pt; line-height: 1.24; color: #111; }\n'
             'h2 { font-size: 12pt; margin: 14pt 0 4pt; break-after: avoid; } p { margin: 0 0 5pt; } mark { background: #fff59d; }\n'
             'table.d { border-collapse: collapse; width: 100%; margin: 4pt 0 4pt; } table.d td { border: 1px solid #bbb; padding: 1.5pt 6pt; vertical-align: top; }\n'
             'table.sig { width: 100%; margin-top: 2pt; } table.sig td { width: 50%; vertical-align: top; padding-right: 18pt; } table.sig p { margin: 0 0 2pt; } tr { break-inside: avoid; }\n'
             + CSS + '\n.pb { break-before: page; } .ks { font-size: 6.5pt; font-weight: 400; } .blk { break-inside: avoid; }\n.fld{display:inline-block;position:relative;border-bottom:.6pt solid #4a86a1;height:1em;vertical-align:-2pt}\n'
             '.mk{position:absolute;left:0;bottom:0;font-size:1px;color:#fff;font-style:normal}\n</style></head><body>\n')
    o.append(f'<h1>{e(d["title"])}</h1><p class="sub1">No<i class="edge"></i>CAP Workshop &middot; {e(d["subtitle"])}</p>\n')
    for i, c in enumerate(d['clauses'], 1):
        o.append(f'<p class="t"><b>{i}.&nbsp;&nbsp;{e(c["h"])}:</b> {h_text(c["t"], marker)}</p>\n')
    o.append(f'<div class="blk"><h1 style="margin-top:6pt;margin-bottom:2pt">{e(d["info_heading"])}</h1><p>{e(d["info_intro"])}</p><table class="d">')
    for k, v in d['info']:
        lab = '<b>' + e(k.split('|')[0]) + '</b>' + (f'<br><span class="ks">{e(k.split("|")[1])}</span>' if '|' in k else '')
        o.append(f'<tr><td class="k">{lab}</td><td>{h_text(v, marker)}</td></tr>')
    o.append('</table><table class="sig"><tr>')
    for sg in d['signatures']:
        o.append(f'<td><p><b>{e(sg["role"])}</b></p>' + (f'<p>{h_text(sg["company"], marker)}</p>' if sg['company'] else '<p>&nbsp;</p>'))
        for lab, val in sg['lines']:
            o.append(f'<p>{e(lab)}: ' + ('______________________' if val is None else h_text(val, marker)) + '</p>')
        o.append('</td>')
    o.append('</tr></table></div>\n')
    x = d['exhibit']
    o.append(f'<div class="pb"></div><h1>{e(x["heading"])}</h1><p class="sub1">{e(x["subtitle"])}</p><table class="d ex"><tr class="h"><td class="k"></td>')
    o += [f'<td class="k"><b>{e(c)}</b></td>' for c in x['columns']] + ['</tr>']
    for r in x['rows']:
        o.append('<tr><td class="k"><b>' + e(r[0]) + '</b></td>' + ''.join(f'<td>{e(c)}</td>' for c in r[1:]) + '</tr>')
    o.append('</table>')
    for i, (b, t) in enumerate(x['notes']):
        o.append(f'<p{" style=\"margin-top:10pt\"" if i == 0 else ""}><b>{e(b)}</b> {e(t)}</p>')
    o.append('<style>.blk h1{padding-top:4pt}table.ex{table-layout:fixed;width:100%}table.ex td{font-size:9pt;width:19.5%}table.ex td.k{width:22%}</style></body></html>')
    return ''.join(o)

def pdf_from(html_text, path):
    with tempfile.TemporaryDirectory() as td:
        hp = Path(td) / 'a.html'; hp.write_text(html_text)
        subprocess.run([CHROME, '--headless', '--disable-gpu', '--no-pdf-header-footer', f'--print-to-pdf={path}', str(hp)], check=True, capture_output=True)

def build_pdf():
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import (ArrayObject, BooleanObject, DictionaryObject, FloatObject, NameObject, NumberObject, TextStringObject)
    with tempfile.TemporaryDirectory() as td:
        marked, clean = Path(td) / 'marked.pdf', Path(td) / 'clean.pdf'
        pdf_from(build_html(True), marked); pdf_from(build_html(False), clean)
        bb = subprocess.run(['pdftotext', '-bbox', str(marked), '-'], check=True, capture_output=True, text=True).stdout
        pages = [(m.start(), float(m.group(2))) for m in re.finditer(r'<page width="([\d.]+)" height="([\d.]+)"', bb)]
        pos = {}
        for m in re.finditer(r'<word xMin="([\d.]+)" yMin="[\d.]+" xMax="[\d.]+" yMax="([\d.]+)">FLD_(\w+)</word>', bb):
            pi = max(i for i, p in enumerate(pages) if p[0] < m.start())
            pos[m.group(3)] = (pi, float(m.group(1)), float(m.group(2)), pages[pi][1])
        used = {n for n in pos}
        assert used == set(FIELDS), set(FIELDS) ^ used
        w = PdfWriter(); w.append(PdfReader(str(clean)))
        refs = ArrayObject()
        for name, f in FIELDS.items():
            pi, x, yb, H = pos[name]; y0 = H - yb - 1.5
            d = DictionaryObject({NameObject('/Type'): NameObject('/Annot'), NameObject('/Subtype'): NameObject('/Widget'),
                NameObject('/FT'): NameObject('/Ch' if f['type'] == 'combo' else '/Tx'), NameObject('/T'): TextStringObject(name),
                NameObject('/Rect'): ArrayObject([FloatObject(x), FloatObject(y0), FloatObject(x + f['w']), FloatObject(y0 + 14)]),
                NameObject('/F'): NumberObject(4), NameObject('/DA'): TextStringObject('/Helv 10 Tf 0 g'),
                NameObject('/MK'): DictionaryObject(), NameObject('/Ff'): NumberObject(131072 if f['type'] == 'combo' else 0)})
            if f['type'] == 'combo': d[NameObject('/Opt')] = ArrayObject([TextStringObject(o) for o in f['options']])
            if f.get('default'): d[NameObject('/V')] = TextStringObject(f['default'])
            ref = w._add_object(d); refs.append(ref)
            w.pages[pi].setdefault(NameObject('/Annots'), ArrayObject()).append(ref)
        helv = w._add_object(DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'),
            NameObject('/BaseFont'): NameObject('/Helvetica'), NameObject('/Encoding'): NameObject('/WinAnsiEncoding')}))
        w._root_object[NameObject('/AcroForm')] = DictionaryObject({NameObject('/Fields'): refs, NameObject('/NeedAppearances'): BooleanObject(True),
            NameObject('/DA'): TextStringObject('/Helv 10 Tf 0 g'), NameObject('/DR'): DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/Helv'): helv})})})
        w.add_metadata({'/Title': DOC_TITLE, '/Subject': VERSION_LINE, '/Author': 'CriticalSec LLC'})
        w.write(str(OUT / f'{BASENAME}.pdf'))

# ---------------------------------------------------------------- DOCX
def build_docx():
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import parse_xml
    from docx.oxml.ns import nsdecls, qn
    from docx.shared import Inches, Pt, RGBColor
    INK, MUTED, ACC, ACC_INK, LINE, PANEL = '1F2630', '5B6470', '6FA6BD', '4A86A1', 'E3DFD6', 'F6F4EF'
    SERIF, SANS, MONO = 'Georgia', 'Arial', 'Consolas'
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    sec.left_margin = sec.right_margin = Inches(1); sec.top_margin = Inches(.85); sec.bottom_margin = Inches(.9)
    cp = doc.core_properties; cp.author = 'CriticalSec LLC'; cp.title = DOC_TITLE; cp.subject = VERSION_LINE; cp.version = VERSION; cp.comments = ''; cp.last_modified_by = 'CriticalSec LLC'

    def font(style_or_run, name=None, size=None, color=None, bold=None):
        f = style_or_run.font
        if name:
            f.name = name
            rpr = (style_or_run.element if hasattr(style_or_run, 'element') and hasattr(style_or_run.element, 'get_or_add_rPr') else style_or_run._element).get_or_add_rPr() if not hasattr(style_or_run, 'base_style') else style_or_run.element.get_or_add_rPr()
            rf = rpr.find(qn('w:rFonts'))
            for a in ('asciiTheme', 'hAnsiTheme', 'eastAsiaTheme', 'cstheme'):
                if rf is not None and rf.get(qn('w:' + a)) is not None: del rf.attrib[qn('w:' + a)]
            for a in ('ascii', 'hAnsi', 'eastAsia', 'cs'): rf.set(qn('w:' + a), name)
        if size: f.size = Pt(size)
        if color: f.color.rgb = RGBColor.from_string(color)
        if bold is not None: f.bold = bold

    st = doc.styles
    n = st['Normal']; font(n, SANS, 10, '111111'); n.paragraph_format.space_after = Pt(6); n.paragraph_format.line_spacing = 1.1
    h1 = st['Heading 1']; font(h1, SERIF, 21, INK, True)
    h1.paragraph_format.space_before = Pt(18); h1.paragraph_format.space_after = Pt(4); h1.paragraph_format.keep_with_next = True
    t = st['Title']; font(t, SERIF, 21, INK, True)
    pPr = t.element.get_or_add_pPr()
    for b in pPr.findall(qn('w:pBdr')): pPr.remove(b)
    t.paragraph_format.space_before = Pt(0); t.paragraph_format.space_after = Pt(4)
    ft = st['Footer']; font(ft, MONO, 8, MUTED)

    # numbering for clauses
    num = doc.part.numbering_part.element
    absn = parse_xml(f'<w:abstractNum {nsdecls("w")} w:abstractNumId="90"><w:multiLevelType w:val="singleLevel"/><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="432" w:hanging="432"/></w:pPr><w:rPr><w:rFonts w:ascii="{SERIF}" w:hAnsi="{SERIF}"/><w:b/><w:color w:val="{INK}"/></w:rPr></w:lvl></w:abstractNum>')
    first_num = num.find(qn('w:num'))
    (first_num.addprevious(absn) if first_num is not None else num.append(absn))
    num.append(parse_xml(f'<w:num {nsdecls("w")} w:numId="90"><w:abstractNumId w:val="90"/></w:num>'))

    sdt_id = [1000]
    def sdt_xml(name):
        f = FIELDS[name]; sdt_id[0] += 1
        label = e(f['label'])
        pr = f'<w:alias w:val="{label}"/><w:tag w:val="{name}"/><w:id w:val="{sdt_id[0]}"/>'
        if f.get('default'):
            content = f'<w:r><w:t>{e(f["default"])}</w:t></w:r>'
        else:
            pr += '<w:showingPlcHdr/>'
            content = f'<w:r><w:rPr><w:color w:val="7F7F7F"/></w:rPr><w:t>[{label}]</w:t></w:r>'
        if f['type'] == 'combo':
            pr += '<w:dropDownList>' + ''.join(f'<w:listItem w:displayText="{e(o)}" w:value="{e(o)}"/>' for o in f['options']) + '</w:dropDownList>'
        else:
            pr += '<w:text/>'
        return parse_xml(f'<w:sdt {nsdecls("w")}><w:sdtPr>{pr}</w:sdtPr><w:sdtContent>{content}</w:sdtContent></w:sdt>')

    def add_runs(p, text, **kw):
        pos = 0
        def run(s):
            r = p.add_run(s)
            if kw.get('font'): font(r, kw['font'], kw.get('size'), kw.get('color'), kw.get('bold'))
            return r
        for m in TOKEN.finditer(text):
            if m.start() > pos: run(text[pos:m.start()])
            if m.group(1) in OVR: run(OVR[m.group(1)])
            else: p._p.append(sdt_xml(m.group(1)))
            pos = m.end()
        if pos < len(text): run(text[pos:])

    def rule(p, color=ACC, sz=12):
        p._p.get_or_add_pPr().append(parse_xml(f'<w:pBdr {nsdecls("w")}><w:top w:val="single" w:sz="{sz}" w:space="8" w:color="{color}"/></w:pBdr>'))

    def mono_label(run, size=8.5, color=ACC_INK):
        font(run, MONO, size, color)
        rpr = run._r.get_or_add_rPr()
        rpr.append(parse_xml(f'<w:caps {nsdecls("w")}/>')); rpr.append(parse_xml(f'<w:spacing {nsdecls("w")} w:val="12"/>'))

    def subtitle(p, lead_dash, text):
        pre, post = ('No', 'CAP Workshop · ' + text) if lead_dash else ('', text)
        r = p.add_run(pre); mono_label(r, 8.5, MUTED)
        if lead_dash:
            d = p.add_run('—'); mono_label(d, 8.5, ACC); d.bold = True
        r2 = p.add_run(post); mono_label(r2, 8.5, MUTED)
        p.paragraph_format.space_after = Pt(14)

    def borders(tbl, inside=True, color=LINE):
        tblPr = tbl._tbl.tblPr
        edge = ''.join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="{color}"/>' for s in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'))
        tblPr.append(parse_xml(f'<w:tblBorders {nsdecls("w")}>{edge}</w:tblBorders>'))
    def no_borders(tbl):
        edge = ''.join(f'<w:{s} w:val="nil"/>' for s in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'))
        tbl._tbl.tblPr.append(parse_xml(f'<w:tblBorders {nsdecls("w")}>{edge}</w:tblBorders>'))
    def fix_table(tbl, widths, margins=True):
        tbl.autofit = False
        tblPr = tbl._tbl.tblPr
        tblPr.append(parse_xml(f'<w:tblLayout {nsdecls("w")} w:type="fixed"/>'))
        if margins: tblPr.append(parse_xml(f'<w:tblCellMar {nsdecls("w")}><w:top w:w="70" w:type="dxa"/><w:left w:w="110" w:type="dxa"/><w:bottom w:w="70" w:type="dxa"/><w:right w:w="110" w:type="dxa"/></w:tblCellMar>'))
        for row in tbl.rows:
            row._tr.get_or_add_trPr().append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
            for c, wd in zip(row.cells, widths): c.width = Inches(wd)
        grid = tbl._tbl.tblGrid
        for gc, wd in zip(grid.findall(qn('w:gridCol')), widths): gc.set(qn('w:w'), str(int(wd * 1440)))
    def shade(cell, fill): cell._tc.get_or_add_tcPr().append(parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{fill}"/>'))
    def cell_text(cell, text, size=10, **kw):
        p = cell.paragraphs[0]; p.paragraph_format.space_after = Pt(0)
        add_runs(p, text, font=SANS, size=size, **kw); return p
    def keep_all(tbl, last_row_too=False):
        rows = tbl.rows if last_row_too else tbl.rows[:-1]
        for r in rows:
            for c in r.cells:
                for p in c.paragraphs: p.paragraph_format.keep_with_next = True

    # title block
    p = doc.add_paragraph(DATA['title'], style='Title'); p.paragraph_format.keep_with_next = True
    p = doc.add_paragraph(); subtitle(p, True, DATA['subtitle'])
    # clauses
    for c in DATA['clauses']:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p._p.get_or_add_pPr().append(parse_xml(f'<w:numPr {nsdecls("w")}><w:ilvl w:val="0"/><w:numId w:val="90"/></w:numPr>'))
        r = p.add_run(c['h'] + ':'); font(r, SERIF, 11, INK, True)
        r = p.add_run(' '); 
        add_runs(p, c['t'])
        p.paragraph_format.space_after = Pt(6)
    # information block
    p = doc.add_paragraph(DATA['info_heading'], style='Heading 1'); rule(p); p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.keep_with_next = True
    p = doc.add_paragraph(DATA['info_intro']); p.paragraph_format.keep_with_next = True
    tbl = doc.add_table(rows=len(DATA['info']), cols=2); borders(tbl); fix_table(tbl, [1.8, 4.7])
    for row, (k, v) in zip(tbl.rows, DATA['info']):
        shade(row.cells[0], PANEL)
        p = row.cells[0].paragraphs[0]; p.paragraph_format.space_after = Pt(0)
        main, _, sub = k.partition('|')
        mono_label(p.add_run(main))
        if sub:
            br = p.add_run(); br.add_break(); mono_label(p.add_run(sub), 6.5)
        cell_text(row.cells[1], v)
    keep_all(tbl, True)
    sp = doc.add_paragraph(); sp.paragraph_format.space_after = Pt(2); sp.paragraph_format.keep_with_next = True
    sig = doc.add_table(rows=1, cols=2); no_borders(sig); fix_table(sig, [3.25, 3.25], margins=False)
    for cell, sg in zip(sig.rows[0].cells, DATA['signatures']):
        p = cell.paragraphs[0]; p.paragraph_format.space_after = Pt(6); mono_label(p.add_run(sg['role']))
        p = cell.add_paragraph(); add_runs(p, sg['company'] or ''); p.paragraph_format.space_after = Pt(18)
        for lab, val in sg['lines']:
            p = cell.add_paragraph(); p.paragraph_format.space_after = Pt(9)
            p.add_run(lab + ': ')
            if val is None: p.add_run('_' * 22)
            else: add_runs(p, val)
    # exhibit
    x = DATA['exhibit']
    p = doc.add_paragraph(x['heading'], style='Heading 1'); rule(p); p.paragraph_format.page_break_before = True; p.paragraph_format.space_before = Pt(0)
    p = doc.add_paragraph(); subtitle(p, False, x['subtitle'].upper() if False else x['subtitle'])
    tbl = doc.add_table(rows=1 + len(x['rows']), cols=5); borders(tbl); fix_table(tbl, [1.4] + [1.275] * 4)
    hdr = tbl.rows[0]
    for c in hdr.cells: shade(c, PANEL)
    for i, name in enumerate(x['columns'], 1):
        p = hdr.cells[i].paragraphs[0]; p.paragraph_format.space_after = Pt(0); mono_label(p.add_run(name))
    for row, r in zip(tbl.rows[1:], x['rows']):
        shade(row.cells[0], PANEL)
        p = row.cells[0].paragraphs[0]; p.paragraph_format.space_after = Pt(0); mono_label(p.add_run(r[0]))
        for c, v in zip(row.cells[1:], r[1:]): cell_text(c, v, 9)
    hdr._tr.get_or_add_trPr().append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
    for i, (b, t) in enumerate(x['notes']):
        p = doc.add_paragraph(); r = p.add_run(b + ' '); r.bold = True; p.add_run(t)
        if i == 0: p.paragraph_format.space_before = Pt(10)
    # footer
    fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER; fp.style = st['Footer']
    def fld(instr, shown):
        fp._p.append(parse_xml(f'<w:fldSimple {nsdecls("w")} w:instr="{instr}"><w:r><w:t>{shown}</w:t></w:r></w:fldSimple>'))
    fp.add_run(f'Sponsorship Agreement v{VERSION} \u00b7 Page '); fld('PAGE', '1'); fp.add_run(' of '); fld('NUMPAGES', '4')
    doc.save(str(OUT / f'{BASENAME}.docx'))

if __name__ == '__main__':
    build_pdf(); build_docx(); print('built', BASENAME)
