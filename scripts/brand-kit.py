#!/usr/bin/env python3
"""Build the brand kit from the source signatures and the homepage lake drawing.

The source signatures are synchronized into the public pages and exports:
the stacked and compact logos (outlined Archivo), the solid green block,
and the line drawing of the lake. Run from the repo root:

    python3 scripts/brand-kit.py

Needs rsvg-convert (brew install librsvg), fontTools and Pillow (pip), Google
Chrome (for the letterhead PDF) and Poppler for PDF previews. brand/index.html is written by hand
and is not touched.
"""

import os
import base64
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.svgLib.path import parse_path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'brand'
# Playwright's headless shell exits when the PDF is written; full Chrome sometimes lingers.
CHROMES = sorted(Path.home().glob('Library/Caches/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell'))
CHROME = str(CHROMES[-1]) if CHROMES else '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
SITE = 'https://thepeninsularcompany.com'

GROUND = '#F1EEE6'
INK = '#1B2926'
PINE = '#234B40'
WHITE = '#FFFFFF'

# The lake after dark, from the page's own palette (index.html, paint()).
NIGHT_GROUND = '#141C2E'
NIGHT_LINE = '#D6D2C7'
LANTERN = '#F0B54A'

HTML = (ROOT / 'index.html').read_text()


def run(*cmd):
    subprocess.run(cmd, check=True)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def fmt(v):
    return ('%.3f' % v).rstrip('0').rstrip('.')


def sync_identity():
    """Keep the public-page signatures equal to the editable SVG masters."""
    masters = {kind: (OUT / 'source' / ('peninsular-signature-%s.svg' % kind)).read_text() for kind in ('line', 'stacked')}
    pages = [ROOT / name for name in ('index.html', '404.html', 'privacy/index.html', 'terms/index.html')]
    pages += list((ROOT / 'work').glob('*/index.html'))
    for page in pages:
        current = page.read_text()
        updated = current
        for kind, master in masters.items():
            def replace(match):
                return master.replace(INK, GROUND).replace(PINE, GROUND) if GROUND in match.group(0) else master
            updated = re.sub(r'<svg class="mark-%s".*?</svg>' % kind, replace, updated, flags=re.S)
        if updated != current:
            page.write_text(updated)


# ---------- Logos ----------

def logo_parts(cls):
    """The rects and paths of one logo SVG on the page, in drawing order."""
    name = cls.removeprefix('mark-')
    master = (OUT / 'source' / ('peninsular-signature-%s.svg' % name)).read_text()
    body = re.search(r'<svg[^>]*>(.*?)</svg>', master, re.S).group(1)
    return re.findall(r'<(?:rect|path)[^>]*/>', body)


def bounds(parts):
    """Exact bounds of every shape, so no overshoot (the C, the r, the y) gets clipped."""
    x0 = y0 = float('inf')
    x1 = y1 = float('-inf')
    for el in parts:
        if el.startswith('<rect'):
            a = dict(re.findall(r'(\w+)="([^"]+)"', el))
            b = (float(a['x']), float(a['y']),
                 float(a['x']) + float(a['width']), float(a['y']) + float(a['height']))
        else:
            pen = BoundsPen(None)
            parse_path(re.search(r' d="([^"]+)"', el).group(1), pen)
            b = pen.bounds
        x0, y0, x1, y1 = min(x0, b[0]), min(y0, b[1]), max(x1, b[2]), max(y1, b[3])
    return x0, y0, x1, y1


def logo_svg(cls, ink, square):
    parts = logo_parts(cls)
    x0, y0, x1, y1 = bounds(parts)
    w, h = x1 - x0, y1 - y0
    body = '\n'.join(parts).replace(INK, '@INK').replace(PINE, '@SQ')
    body = body.replace('@INK', ink).replace('@SQ', square)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="%s %s %s %s" width="%s" height="%s">\n'
        '<title>The Peninsular Company</title>\n%s\n</svg>\n'
        % (fmt(x0), fmt(y0), fmt(w), fmt(h), fmt(w), fmt(h), body)
    )


COLORWAYS = {
    '': (INK, PINE),          # full color: ink wordmark with pine symbol
    '-black': ('#000000', '#000000'),     # one color
    '-white': (WHITE, WHITE), # one color, for dark or photographic backgrounds
}


def build_logos():
    for name, cls in (('stacked', 'mark-stacked'), ('line', 'mark-line')):
        for suffix, (ink, square) in COLORWAYS.items():
            base = OUT / 'logo' / ('peninsular-logo-%s%s' % (name, suffix))
            write(base.with_suffix('.svg'), logo_svg(cls, ink, square))
            run('rsvg-convert', '-w', '2400', '-o', str(base.with_suffix('.png')), str(base.with_suffix('.svg')))
            run('rsvg-convert', '-f', 'pdf', '-o', str(base.with_suffix('.pdf')), str(base.with_suffix('.svg')))


# ---------- Icon ----------

MARK_SOURCE = (OUT / 'source' / 'peninsular-mark.svg').read_text()
MARK_PATH = re.search(r'<rect[^>]*/>', MARK_SOURCE).group(0)

def icon_svg(scale=1.0):
    """A solid pine block on a limestone tile, visible on light and dark browser chrome."""
    side = 64 * scale
    inset = (96 - side) / 2
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96" width="1024" height="1024">'
            '<title>The Peninsular Company</title><rect width="96" height="96" fill="%s"/>'
            '<rect x="%s" y="%s" width="%s" height="%s" fill="%s"/></svg>' % (GROUND, fmt(inset), fmt(inset), fmt(side), fmt(side), PINE))


def build_icons():
    write(ROOT / 'favicon.svg', icon_svg())
    icon = OUT / 'icon' / 'peninsular-icon.svg'
    write(icon, icon_svg())
    for size in (1024, 512, 180):
        run('rsvg-convert', '-w', str(size), '-h', str(size), '-o',
            str(icon.with_name('peninsular-icon-%d.png' % size)), str(icon))

    # Circle-safe avatar, with the same optical center as the square icon.
    avatar = OUT / 'social' / 'peninsular-avatar.svg'
    write(avatar, icon_svg(0.90))
    run('rsvg-convert', '-w', '1024', '-h', '1024', '-o', str(avatar.with_suffix('.png')), str(avatar))

    # The website and downloadable identity share the same source icon.
    run('rsvg-convert', '-w', '180', '-h', '180', '-o', str(ROOT / 'apple-touch-icon.png'), str(icon))
    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / 'favicon.png'
        run('rsvg-convert', '-w', '256', '-h', '256', '-o', str(png), str(icon))
        with Image.open(png) as im:
            im.save(ROOT / 'favicon.ico', sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])


# ---------- The lake ----------

LAKE = re.search(r'<svg class="lake".*?</svg>', HTML, re.S).group(0)


def strip_group(svg, cls):
    return re.sub(r'<g class="%s"[^>]*>.*?</g>\n?' % cls, '', svg, flags=re.S)


def lake_svg(night):
    svg = LAKE
    svg = re.sub(r'<svg class="lake"[^>]*>', '', svg)
    svg = re.sub(r'<title[^>]*>.*?</title>\n?', '', svg)
    svg = re.sub(r'<g clip-path="url\(#sky\)">.*?</g></g>\n?', '', svg, flags=re.S)  # sun and moon
    svg = strip_group(svg, 'glint')
    svg = svg.replace('<clipPath id="sky"><rect width="1200" height="205"/></clipPath>\n', '')
    if night:
        style = (
            '.ground,.o{fill:%(g)s}.draw{fill:none;stroke:%(l)s;stroke-width:.8}'
            '.s{fill:%(l)s}.glass{fill:%(lantern)s}.stars{fill:#E6E2D6;opacity:.85}'
            '.nav{fill:#FFF6DE}.lamp .core{fill:#FFF4D6}.lampref{stroke:%(lantern)s;stroke-width:.8;opacity:.85}'
            % {'g': NIGHT_GROUND, 'l': NIGHT_LINE, 'lantern': LANTERN}
        )
    else:
        for cls in ('stars', 'nav', 'lampref', 'lamp'):
            svg = strip_group(svg, cls)
        svg = re.sub(r'<defs>.*?</defs>\n?', '', svg, flags=re.S)
        style = (
            '.ground,.o,.glass{fill:%(g)s}.draw{fill:none;stroke:%(l)s;stroke-width:.8}.s{fill:%(l)s}'
            % {'g': GROUND, 'l': INK}
        )
    svg = svg.replace('</svg>', '').strip()
    title = ('The east end of Belle Isle at night: the William Livingstone Memorial Lighthouse and a freighter'
             if night else
             'The east end of Belle Isle: the William Livingstone Memorial Lighthouse and a freighter')
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 360" width="1200" height="360">\n'
        '<title>%s</title>\n<style>%s</style>\n%s\n</svg>\n' % (title, style, svg)
    )


def crop_lake(svg, x, y, w, h):
    """The same drawing, framed on a window of it (in drawing units)."""
    return re.sub(r'viewBox="[^"]+" width="1200" height="360"',
                  'viewBox="%s %s %s %s" preserveAspectRatio="xMidYMid slice"' % (fmt(x), fmt(y), fmt(w), fmt(h)),
                  svg, count=1)


def render(svg_text, out, w, h):
    with tempfile.NamedTemporaryFile('w', suffix='.svg', delete=False) as f:
        f.write(svg_text)
    try:
        run('rsvg-convert', '-w', str(w), '-h', str(h), '-o', str(out), f.name)
    finally:
        os.unlink(f.name)


def build_lake():
    day, night = lake_svg(False), lake_svg(True)
    for name, svg in (('day', day), ('night', night)):
        path = OUT / 'lake' / ('peninsular-lake-%s.svg' % name)
        write(path, svg)
        run('rsvg-convert', '-w', '3600', '-o', str(path.with_suffix('.png')), str(path))

    social = OUT / 'social'
    social.mkdir(parents=True, exist_ok=True)
    # X header, 3:1. The profile picture covers the lower left, so only water sits there;
    # the lighthouse stands a third of the way in and the freighter clears the right edge.
    render(crop_lake(day, 0, 44, 750, 250), social / 'peninsular-x-header.png', 1500, 500)
    render(crop_lake(night, 0, 44, 750, 250), social / 'peninsular-x-header-night.png', 1500, 500)
    # LinkedIn page cover, 1128 x 191: the whole width of the drawing, lantern to water.
    render(crop_lake(day, 0, 66, 1200, 1200 * 191 / 1128), social / 'peninsular-linkedin-cover.png', 1128 * 2, 191 * 2)


# ---------- Stationery ----------

def font_url():
    return (ROOT / 'fonts' / 'inter-tight-latin.woff2').as_uri()


def build_letterhead():
    stacked = logo_svg('mark-line', INK, PINE)
    page = """<!doctype html>
<html><head><meta charset="utf-8"><style>
@font-face { font-family: 'Inter Tight'; font-weight: 400 600; src: url(%(font)s) format('woff2'); }
@page { size: letter; margin: 0; }
html, body { margin: 0; }
body { font-family: 'Inter Tight', 'Helvetica Neue', Helvetica, Arial, sans-serif; color: %(ink)s;
       -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.page { position: relative; width: 8.5in; height: 11in; }
.logo { position: absolute; left: 0.75in; top: 0.7in; width: 2.2in; }
.logo svg { display: block; width: 100%%; height: auto; }
.contact { position: absolute; left: 4.75in; top: 0.7in; height: 0.48in;
           display: flex; flex-direction: column; justify-content: flex-end;
           font-size: 8.5pt; line-height: 1.45; font-weight: 500; }
.contact p, .foot p { margin: 0; }
.muted { color: #5E665F; }
.foot { position: absolute; left: 0.75in; right: 0.75in; bottom: 0.55in;
        border-top: 0.5pt solid #CBCDC2; padding-top: 9pt;
        display: flex; justify-content: space-between; font-size: 7.5pt; font-weight: 500; color: #5E665F; }
</style></head><body><div class="page">
<div class="logo">%(logo)s</div>
<div class="contact">
  <p>hello@thepeninsularcompany.com</p>
  <p>thepeninsularcompany.com</p>
  <p class="muted">Detroit, Michigan</p>
</div>
<div class="foot"><p>The Peninsular Company, LLC</p><p>If you seek a pleasant peninsula, look about you.</p></div>
</div></body></html>
""" % {'font': font_url(), 'ink': INK, 'logo': stacked}
    out = OUT / 'stationery' / 'peninsular-letterhead.pdf'
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / 'letterhead.html'
        src.write_text(page)
        try:
            subprocess.run([CHROME, '--headless', '--disable-gpu', '--no-pdf-header-footer',
                            '--user-data-dir=' + str(Path(tmp) / 'profile'),
                            '--print-to-pdf=' + str(out), src.as_uri()],
                           check=True, timeout=45, stderr=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            if not out.exists():
                raise
        # The same page as a 200 dpi image, to use as a page background in Pages, Word, or Docs.
        subprocess.run([CHROME, '--headless', '--disable-gpu', '--hide-scrollbars',
                        '--user-data-dir=' + str(Path(tmp) / 'profile'),
                        '--window-size=816,1056', '--force-device-scale-factor=%s' % (200 / 96),
                        '--screenshot=' + str(out.with_suffix('.png')), src.as_uri()],
                       check=True, timeout=45, stderr=subprocess.DEVNULL)


def build_signature():
    """Email signatures to paste into Mail or Gmail. The logo loads from the live site,
    so it shows only once brand/ is published."""
    folder = OUT / 'stationery'
    logo = folder / 'peninsular-email-logo.png'
    run('rsvg-convert', '-w', '452', '-o', str(logo), str(OUT / 'logo' / 'peninsular-logo-line.svg'))
    with Image.open(logo) as im:
        h = round(im.height * 226 / im.width)
    src = '%s/brand/stationery/%s' % (SITE, logo.name)

    font = "font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif"
    def block(person):
        name = ('<p style="margin: 0 0 2px; font-size: 14px; font-weight: 600; color: %s">Joe Lint</p>'
                '<p style="margin: 0 0 14px; font-size: 13px; color: #5E665F">Principal</p>' % INK) if person else ''
        return (
            '<table cellpadding="0" cellspacing="0" border="0" style="%(font)s; color: %(ink)s"><tr><td>'
            '%(name)s'
            '<a href="%(site)s" style="display: block; line-height: 0"><img src="%(src)s" width="226" height="%(h)d" '
            'alt="The Peninsular Company" style="display: block; border: 0"></a>'
            '<p style="margin: 10px 0 0; font-size: 13px; line-height: 1.5; color: #5E665F">'
            '<a href="mailto:hello@thepeninsularcompany.com" style="color: %(ink)s; text-decoration: none">hello@thepeninsularcompany.com</a><br>'
            '<a href="%(site)s" style="color: %(ink)s; text-decoration: none">thepeninsularcompany.com</a><br>'
            'Detroit, Michigan</p>'
            '</td></tr></table>'
            % {'font': font, 'ink': INK, 'name': name, 'site': SITE, 'src': src, 'h': h}
        )

    text = ('Joe Lint\nPrincipal\nThe Peninsular Company\nhello@thepeninsularcompany.com\n'
            'thepeninsularcompany.com\nDetroit, Michigan')
    page = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Email signature · The Peninsular Company</title>
<meta name="robots" content="noindex">
<style>
body { margin: 0; padding: 48px 24px; background: #FFFFFF; color: %(ink)s; %(font)s; font-size: 15px; line-height: 1.5; }
main { max-width: 640px; margin: 0 auto; }
h1 { font-size: 22px; margin: 0 0 8px; letter-spacing: -0.01em; }
h2 { font-size: 13px; font-weight: 600; margin: 48px 0 16px; padding-top: 12px; border-top: 1px solid %(ink)s; }
.how { color: #5E665F; margin: 0; }
pre { margin: 0; font: 13px/1.5 ui-monospace, Menlo, monospace; white-space: pre-wrap; }
</style></head><body><main>
<h1>Email signature</h1>
<p class="how">Select a signature, copy it, and paste it into your mail app's signature settings.
Publish the brand kit before using the signature, so its logo is available to email recipients.</p>
<h2>With name</h2>
%(person)s
<h2>Company only</h2>
%(company)s
<h2>Plain text</h2>
<pre>%(text)s</pre>
</main></body></html>
''' % {'ink': INK, 'font': font, 'person': block(True), 'company': block(False), 'text': text}
    write(folder / 'peninsular-email-signature.html', page)


# ---------- Zip ----------

def build_zip():
    kit = OUT / 'peninsular-brand-kit.zip'
    kit.unlink(missing_ok=True)
    folders = ['logo', 'icon', 'social', 'lake', 'stationery', 'source', 'standards']
    write(OUT / 'README.txt', '''THE PENINSULAR COMPANY - BRAND FILES

Use the supplied wordmarks rather than typing or recreating the logo.

WORDMARKS
Full color: paper or white backgrounds.
Black: a single-color application.
White: pine, ink, or a quiet dark background.
Use ink on limestone and lake. Reserve brick for large graphic fields.
Screen colors are RGB; approve a printer proof before a production print run.
SVG and PDF are vectors. Logo PNG files have transparent backgrounds.
Minimum width: stacked 160 px; horizontal 180 px.
Clear space: half the block width on every side.
Minimum block height: 12 px on screen; 4 mm in print.

ICONS
Use the square icon for listings and favicons.
Use the inset avatar for profiles that crop to a circle.

COLORS
Limestone #F1EEE6 / Ink #1B2926 / Pine #234B40
Brick #C45136 / Lake #BCCDCB
Secondary text #5E665F / Rules #CBCDC2 / Night #141C2E

TYPE
Archivo for display. Inter Tight for reading and labels.
The wordmark uses optically spaced Archivo outlines, weight 650, width 94.
Use supplied artwork rather than typesetting the logo.
Fallback: Helvetica Neue, Helvetica, Arial.

STATIONERY
Letterhead: US Letter, vector PDF and 200 dpi PNG.
Email signature: publish the brand kit before using the hosted logo in email.

Open index.html for the interactive brand guide, including logo previews.

The Peninsular Company, LLC / Detroit, Michigan
https://thepeninsularcompany.com
''')
    licenses = 'INTER TIGHT\n\n' + (ROOT / 'fonts' / 'OFL.txt').read_text() + '\n\nARCHIVO\n\n' + (ROOT / 'fonts' / 'Archivo-OFL.txt').read_text()
    write(OUT / 'TYPE-LICENSE.txt', '\n'.join(line.rstrip() for line in licenses.splitlines()) + '\n')
    # Make the guide usable after extraction, with its font and all previews local.
    guide = (OUT / 'index.html').read_text()
    guide = guide.replace('/fonts/', 'fonts/')
    guide = re.sub(r'\s*<link rel="preload"[^>]+>', '', guide)
    font_data = base64.b64encode((ROOT / 'fonts' / 'inter-tight-latin.woff2').read_bytes()).decode('ascii')
    guide = guide.replace('url(fonts/inter-tight-latin.woff2)', 'url(data:font/woff2;base64,%s)' % font_data)
    archivo_data = base64.b64encode((ROOT / 'fonts' / 'archivo-latin.ttf').read_bytes()).decode('ascii')
    guide = guide.replace('url(fonts/archivo-latin.ttf)', 'url(data:font/ttf;base64,%s)' % archivo_data)
    guide = guide.replace('href="/favicon.svg"', 'href="icon/peninsular-icon.svg"')
    guide = guide.replace('href="/apple-touch-icon.png"', 'href="icon/peninsular-icon-180.png"')
    for route in ('/', '/privacy/', '/terms/'):
        guide = guide.replace('href="%s"' % route, 'href="%s%s"' % (SITE, route))
    guide = guide.replace('href="peninsular-brand-kit.zip" download', 'href="#downloads"')
    guide = guide.replace('Download the brand kit', 'Browse the brand files').replace('Download all files', 'Browse the files')
    with zipfile.ZipFile(kit, 'w', zipfile.ZIP_DEFLATED) as archive:
        for folder in folders:
            for path in sorted((OUT / folder).rglob('*')):
                if path.is_file():
                    archive.write(path, path.relative_to(OUT))
        for name in ('README.txt', 'TYPE-LICENSE.txt'):
            archive.write(OUT / name, name)
        archive.writestr('index.html', guide)
        archive.write(ROOT / 'fonts' / 'inter-tight-latin.woff2', 'fonts/inter-tight-latin.woff2')
        archive.write(ROOT / 'fonts' / 'OFL.txt', 'fonts/OFL.txt')
        archive.write(ROOT / 'fonts' / 'archivo-latin.ttf', 'fonts/archivo-latin.ttf')
        archive.write(ROOT / 'fonts' / 'Archivo-OFL.txt', 'fonts/Archivo-OFL.txt')


def build_share_image():
    """The link preview says what the home page says: the signature, the headline, and the lake under it.
    The company cover for social profiles stays name-first."""
    lake = re.sub(r'<svg[^>]*>', '<svg x="0" y="326" width="1200" height="304" viewBox="0 0 1200 360" preserveAspectRatio="xMidYMid slice">', lake_svg(False), count=1)

    # The share card is set in the site's own Archivo, so Chrome draws it from the same font file the page serves.
    logo = re.sub(r' width="[^"]+" height="[^"]+"', '', logo_svg('mark-line', INK, PINE), count=1)
    card_lake = re.sub(r'<svg x="0" y="326" width="1200" height="304"', '<svg class="lake" width="1200" height="304"', lake, count=1)
    page = """<!doctype html><html><head><meta charset="utf-8"><style>
@font-face { font-family: Archivo; font-weight: 500 700; src: url(%(font)s) format('woff2'); }
html, body { margin: 0; width: 1200px; height: 630px; overflow: hidden; background: %(ground)s; }
.logo { position: absolute; left: 72px; top: 60px; width: 286px; }
.logo svg { display: block; width: 100%%; height: auto; }
h1 { position: absolute; left: 72px; top: 172px; margin: 0; color: %(ink)s;
     font: 620 70px/0.99 Archivo, 'Helvetica Neue', Arial, sans-serif; letter-spacing: -0.045em; }
.lake { position: absolute; left: 0; top: 326px; display: block; }
</style></head><body>
<div class="logo">%(logo)s</div>
<h1>Helping businesses<br>work better and grow.</h1>
%(lake)s
</body></html>""" % {'font': (ROOT / 'fonts' / 'archivo-display.woff2').as_uri(), 'ground': GROUND, 'ink': INK, 'logo': logo, 'lake': card_lake}
    out = ROOT / 'og-image.png'
    with tempfile.TemporaryDirectory() as tmp:
        src, shot = Path(tmp) / 'share.html', Path(tmp) / 'share@2x.png'
        src.write_text(page)
        try:
            subprocess.run([CHROME, '--headless', '--disable-gpu', '--hide-scrollbars', '--virtual-time-budget=3000',
                            '--user-data-dir=' + str(Path(tmp) / 'profile'),
                            '--window-size=1200,630', '--force-device-scale-factor=2',
                            '--screenshot=' + str(shot), src.as_uri()],
                           check=True, timeout=45, stderr=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            if not shot.exists():
                raise
        # Drawn at twice the size and brought down, so the lake's hairlines stay crisp.
        Image.open(shot).convert('RGB').resize((1200, 630), Image.LANCZOS).save(out, optimize=True)

    logo = re.sub(r'width="[^"]+" height="[^"]+"', 'x="70" y="68" width="865" height="196"', logo_svg('mark-line', INK, PINE), count=1)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="500" viewBox="0 0 1200 400">'
           '<rect width="1200" height="630" fill="%s"/>%s%s</svg>' % (GROUND, lake, logo))
    render(svg, OUT / 'social' / 'peninsular-company-cover.png', 1500, 500)

if __name__ == '__main__':
    sync_identity()
    for d in ('logo', 'icon', 'social', 'lake', 'stationery'):
        shutil.rmtree(OUT / d, ignore_errors=True)
    build_logos()
    build_icons()
    build_lake()
    build_letterhead()
    build_signature()
    build_share_image()
    from brand_standards import build_standards
    build_standards(ROOT, OUT, CHROME)
    build_zip()
    for p in sorted(OUT.rglob('*')):
        if p.is_file():
            print('%8.1f KB  %s' % (p.stat().st_size / 1024, p.relative_to(ROOT)))
