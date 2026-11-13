#!/usr/bin/env python3
"""Generate the press-kit promo images (static/press/img) and the manifest the
/press/ page reads (data/press.yaml). Needs only Python 3 and Google Chrome.

    python3 tools/press/build.py

Re-run it whenever data/sponsors.yaml or the taglines change. "Made possible by"
images show only Founding, Gold and Silver sponsors; every sponsor, Community
included, gets a single "We're sponsoring" set of their own.
"""
import html, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "static", "press", "img")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SIZES = [("social", "LinkedIn", 1200, 627), ("wide", "X and link previews", 1600, 900),
         ("square", "Square", 1080, 1080), ("banner", "Email banner", 600, 200)]
DATE = "January 19–21, 2027"


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def taglines():
    out = []
    idx = open(os.path.join(ROOT, "content", "_index.md"), encoding="utf-8").read()
    m = re.search(r"^headline:\s*(.+)$", idx, re.M)
    if m:
        out.append(m.group(1).strip())
    for line in open(os.path.join(ROOT, "data", "headlines.yaml"), encoding="utf-8"):
        if line.startswith("- "):
            out.append(line[2:].strip().strip('"'))
    return out


def sponsors():
    tiers, cur = [], None
    for line in open(os.path.join(ROOT, "data", "sponsors.yaml"), encoding="utf-8"):
        if line.startswith("- tier:"):
            cur = {"tier": line.split(":", 1)[1].strip(), "sponsors": []}
            tiers.append(cur)
        elif cur is not None:
            m = re.match(r'\s+- name:\s*"?(.*?)"?\s*$', line)
            if m:
                cur["sponsors"].append({"name": m.group(1)})
            m = re.match(r'\s+(url|logo):\s*"?(.*?)"?\s*$', line)
            if m and cur["sponsors"]:
                cur["sponsors"][-1][m.group(1)] = m.group(2)
    return tiers


def logo_uri(s):
    return "file://" + os.path.join(ROOT, "assets", s["logo"]) if s.get("logo") else None


CSS = """
*{box-sizing:border-box;margin:0}
html,body{width:%(W)dpx;height:%(H)dpx;overflow:hidden}
body{background:#f6f4ef;color:#1f2630;position:relative;
 font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
 background-image:linear-gradient(#e3e6ee 1px,transparent 1px),linear-gradient(90deg,#e3e6ee 1px,transparent 1px);
 background-size:%(g)dpx %(g)dpx}
.mono{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace}
.card{position:absolute;inset:%(p)dpx;display:flex;flex-direction:column;justify-content:space-between}
.mark{font-family:ui-monospace,"SF Mono",Menlo,monospace;font-weight:500;letter-spacing:.1em;font-size:%(mk)dpx}
.mark i{display:inline-block;width:.6em;height:%(dash)dpx;background:#6fa6bd;vertical-align:middle;margin:0 .15em;border-radius:1px}
.mid{flex:1;display:flex;flex-direction:column;justify-content:center;min-height:0;padding:%(mp)dpx 0}
.eyebrow{font-family:ui-monospace,"SF Mono",Menlo,monospace;font-size:%(eb)dpx;letter-spacing:.09em;text-transform:uppercase;color:#5b6470;margin-bottom:%(ebm)dpx}
.tag{font-weight:600;line-height:1.08;letter-spacing:-.02em;font-size:%(tg)dpx}
.sp{display:flex;align-items:center;gap:%(sg)dpx;flex-wrap:wrap;margin-bottom:%(spm)dpx}
.sp .lbl{font-family:ui-monospace,"SF Mono",Menlo,monospace;font-size:%(eb)dpx;letter-spacing:.09em;text-transform:uppercase;color:#5b6470}
.sp img{height:%(lh)dpx;max-width:%(lw)dpx;width:auto;display:block}
.sp .nm{font-size:%(lh)dpx;font-weight:600}
.foot{display:flex;justify-content:space-between;align-items:baseline;font-family:ui-monospace,"SF Mono",Menlo,monospace;font-size:%(ft)dpx;letter-spacing:.06em;text-transform:uppercase;color:#5b6470;gap:%(sg)dpx}
.foot b{font-weight:500;color:#1f2630}
.big{display:block;height:%(bh)dpx;max-width:%(bw)dpx;width:auto;margin-top:%(ebm)dpx}
"""

# Per size: W, H, grid, padding, mark px, dash px, mid padding, eyebrow px, eyebrow margin,
# tagline max px, gap, sponsor margin, logo height, logo max width, footer px, big-logo h/w
CFG = {
    "social": dict(g=30, p=64, mk=28, dash=3, mp=10, eb=15, ebm=14, tg=84, sg=18, spm=22, lh=34, lw=200, ft=16, bh=84, bw=560),
    "wide": dict(g=40, p=84, mk=36, dash=4, mp=14, eb=19, ebm=18, tg=110, sg=24, spm=28, lh=44, lw=260, ft=21, bh=110, bw=740),
    "square": dict(g=36, p=76, mk=32, dash=4, mp=14, eb=18, ebm=18, tg=118, sg=22, spm=26, lh=42, lw=240, ft=19, bh=110, bw=700),
    "banner": dict(g=20, p=22, mk=15, dash=2, mp=4, eb=9, ebm=6, tg=34, sg=10, spm=6, lh=18, lw=110, ft=9, bh=34, bw=220),
}


def page(kind, size, tag=None, sponsor=None, rollup=None):
    key, _, W, H = next(s for s in SIZES if s[0] == size)
    c = dict(CFG[size], W=W, H=H)
    banner = size == "banner"
    parts = []
    if sponsor:
        uri = logo_uri(sponsor)
        big = '<img class="big" src="%s" alt="">' % uri if uri else '<div class="tag">%s</div>' % html.escape(sponsor["name"])
        mid = ('<div class="mid"><div class="eyebrow">We’re proud to sponsor</div>'
               '<div class="tag" data-fit>The No-CAP Workshop</div>%s</div>') % big
    else:
        mid = '<div class="mid"><div class="tag" data-fit>%s</div></div>' % html.escape(tag)
    sp = ""
    if rollup:
        items = "".join('<img src="%s" alt="%s">' % (logo_uri(s), html.escape(s["name"])) if logo_uri(s)
                        else '<span class="nm">%s</span>' % html.escape(s["name"]) for s in rollup)
        sp = '<div class="sp"><span class="lbl">Made possible by</span>%s</div>' % items
    foot_l = "Jan 19–21, 2027 · Online · Free" if banner else "Jan 19–21, 2027 · Online · Free · No registration"
    body = ('<div class="card"><div class="mark">No<i></i>CAP Workshop</div>%s%s'
            '<div class="foot"><span><b>%s</b></span><span>nocap-workshop.com</span></div></div>') % (mid, sp, foot_l)
    fit = ("<script>for(const e of document.querySelectorAll('[data-fit]')){const m=e.closest('.mid');"
           "let s=parseFloat(getComputedStyle(e).fontSize);"
           "while(m.scrollHeight>m.clientHeight+1&&s>12){s-=2;e.style.fontSize=s+'px'}}</script>")
    return "<!doctype html><meta charset=utf-8><style>%s</style><body>%s%s" % (CSS % c, body, fit)


def shoot(htmlsrc, dest, W, H, tmp):
    f = os.path.join(tmp, "p.html")
    open(f, "w", encoding="utf-8").write(htmlsrc)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                    "--window-size=%d,%d" % (W, H), "--screenshot=" + dest, "file://" + f],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    if not os.path.exists(CHROME):
        sys.exit("Google Chrome not found at " + CHROME)
    tiers = sponsors()
    rollup = [s for t in tiers if t["tier"] in ("Founding", "Gold", "Silver") for s in t["sponsors"]]
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT)
    sets, tmp = [], tempfile.mkdtemp()

    def make(group, title, name, **kw):
        files = []
        for size, label, W, H in SIZES:
            fn = "%s-%s-%dx%d.png" % (group, name, W, H)
            shoot(page(group, size, **kw), os.path.join(OUT, fn), W, H, tmp)
            files.append((label, "%dx%d" % (W, H), "/press/img/" + fn))
        return {"title": title, "files": files}

    plain, made = [], []
    for t in taglines():
        plain.append(make("plain", t, slug(t), tag=t))
        if rollup:
            made.append(make("made-possible-by", t, slug(t), tag=t, rollup=rollup))
    sets.append(("Plain", "The tagline, the dates, and the URL.", plain))
    if made:
        sets.append(("Made Possible By", "The same, with the Founding, Gold and Silver sponsors' logos.", made))
    spons = [make("sponsor", s["name"], slug(s["name"]), sponsor=s) for t in tiers for s in t["sponsors"]]
    if spons:
        sets.append(("We're Sponsoring", "One for each sponsor to post.", spons))

    y = ["# Generated by tools/press/build.py. Do not edit by hand.", "sets:"]
    for title, desc, items in sets:
        y += ['  - title: "%s"' % title, '    description: "%s"' % desc, "    items:"]
        for it in items:
            y += ['      - title: "%s"' % it["title"].replace('"', '\\"'), "        files:"]
            for label, size, path in it["files"]:
                y += ['          - {label: "%s", size: "%s", path: "%s"}' % (label, size, path)]
    open(os.path.join(ROOT, "data", "press.yaml"), "w", encoding="utf-8").write("\n".join(y) + "\n")
    shutil.rmtree(tmp, ignore_errors=True)
    print("wrote %d images" % len(os.listdir(OUT)))


if __name__ == "__main__":
    main()
