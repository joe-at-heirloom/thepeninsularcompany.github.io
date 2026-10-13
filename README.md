# thepeninsularcompany.com

Company site for The Peninsular Company, LLC, a privately held company in Detroit, Michigan: strategy, design, and technology for businesses, and ventures of its own. It is the page clients, Apple, banks, vendors, and anyone checking on the business should land on. [joelint.com](https://joelint.com) stays the personal site.

**Live site:** [thepeninsularcompany.com](https://thepeninsularcompany.com)

## What's on the page

The home page says each thing once, in this order:

- **Header**: the compact signature (a solid pine-green block, #234B40, with the Archivo wordmark) and five links. On a phone the links take their own row; there is no menu button.
- **Hero**: the headline, one statement, one link to Contact.
- **The lake**: a line drawing across the full width of the page, directly under the hero, looking across the water at the east end of Belle Isle. On the left is the William Livingstone Memorial Lighthouse (Albert Kahn, architect; Géza Maróti, sculptor; 1930), drawn from measured proportions. In the middle is a freighter; to the right is open water. The drawing is pinned to its left edge and never taller than half its width, so a phone still shows the lighthouse and the whole freighter. It follows the real light in Detroit: afternoon, golden hour, sunset, blue hour, and night, with the sun and moon placed where they actually are. After dark the lighthouse lamp blinks the way the Coast Guard lists it (occulting white, 4 s). It carries no caption.
- **Work**: three client projects, each a small screenshot, the name, the industry, and one sentence giving scope and credit. Each links to its page under `work/`.
- **Services**: one statement and three services, a sentence each.
- **Auction houses**: one statement and six areas, a sentence each.
- **Ventures**: the company's own products, numbered, with status, platform, and each one's own support, privacy, and terms links.
- **Contact**: one question, the email address, and a link to joelint.com.
- **Footer**: the page's one pine field, holding the white signature, the legal name, Detroit, the state motto, and links to Privacy, Terms, and Brand.

Keep it this spare. A new sentence should replace one, not join it. Screenshots stay small on the home page; the project pages are where they get room.

## Adding a work

**A venture:** copy an `<li class="work">` in `index.html`, give it the next number and a color in `style="--c: #..."`, and fill in its links. Each small link carries an `aria-label` naming the venture ("Support for Heirloom"), so change those to the new name too. Use `class="no outlined small"` for a very light color so the marker still shows.

**A client project:** copy a folder under `work/`, change its title, facts, summary, three points, and images, and add an `<li class="card">` to the Work list in `index.html`. Each project needs three images in `images/portfolio/`: `name-website.jpg` (1280 × 860), `name-website-768.jpg` (the same, 768 × 516, for the home page card), and `name-mobile.jpg` (390 × 844). Keep the credit accurate: say whose work it was and in what role. Add the page to `sitemap.xml`.

## The apps' legal pages

`legal/company.json` holds the company facts every app's privacy policy and terms share (legal name, where, which law governs). Change it and push: the **Legal sync** workflow updates and publishes every app site. See [legal/README.md](legal/README.md). `_config.yml` keeps `legal/` and `scripts/` off the published site.

## Brand kit

`brand/` holds six signature variants, icons, lake illustrations, social covers, letterhead, a two-sided business card, email signatures, and a six-page identity standard. The interactive guide at `/brand/` is linked from the footer and marked `noindex`. The ZIP includes a working offline guide, the licensed fonts, source vectors, and usage notes.

`brand/source/` is the source of truth for the solid block and outlined signatures. `index.html` owns the lake drawing and its sky behavior. Shared identity tokens and display typography live in `styles/brand.css`; every page's layout lives in `styles/site.css`.

```sh
python3 scripts/brand-kit.py
```

The generator synchronizes the master signatures into the public pages, then creates the logo, icon, social, and stationery exports, PDFs, and ZIP. It needs `rsvg-convert` and `pdftoppm` (Homebrew librsvg and poppler), Python fontTools and Pillow, and Chrome or Playwright's headless shell. `scripts/brand_standards.py` lays out the identity standard and business card. The brand guide HTML is maintained by hand.

The supplied colors are RGB. Letterhead is US Letter; cards are 3.5 × 2 inches, without bleed. Approve stock and a printer's proof before production. The email signature references a hosted logo and should be used only after its assets are published.

## How the page is built

The site is static HTML with two shared stylesheets and self-hosted fonts. No build step.

- `styles/brand.css` is the identity: the two font families, their stand-ins, and the colors (limestone, ink, pine, brick, lake, night).
- `styles/site.css` is everything else, for every page: the home page, the project pages under `work/`, `privacy/`, `terms/`, and `404.html`. No page carries its own pasted copy of the styles. `brand/index.html`, the brand guide, is the exception: it is self-contained so it also works from the ZIP.
- The header signature is outlined paths pasted into each page (the generator keeps them equal to `brand/source/`). The footer's white signature is the kit's own file, `brand/logo/peninsular-logo-line-white.svg`.
- The lake is one inline SVG in `index.html`. The High Lift Pumping Station at Water Works Park was taken out of it on October 2, 2026; leave it out.
- Two scripts sit in the `<head>` of `index.html`. `ASTRO` works out where the sun and moon are over Detroit (NOAA low-precision sun, Schlyter moon, checked against the April 8, 2024 solar eclipse and the March 14, 2025 lunar eclipse). `LAKE` turns that into the lake's colors and sets them before the page first draws, so a visitor at night never sees a flash of the day drawing. It runs again right after the drawing, to place the sun and moon, and every 30 seconds after that. By day the lake's ground is the page's limestone and its line is the page's ink.

`site.css` ends with three blocks worth knowing about:

- **Touch** gives the small links a full-size tap target on phones and tablets without moving anything.
- **High contrast** hands the signature and the lake the system's colors when Windows high contrast (or any forced-color theme) is on.
- **Paper** is the print version, for anyone who files the page as a PDF: white ground, the lake as the day drawing, the name and the lake on page one, work and services on page two, and a footer that reads without its pine field.

**Fonts.** Archivo is the display face, used only at width 94 and weights 500 to 700, so the site serves `fonts/archivo-display.woff2`, cut to exactly that (30 KB). `fonts/archivo-latin.ttf` is the full file; the brand kit generator and the ZIP use it, the site does not. Inter Tight is for reading and labels. Until either font loads, Helvetica or Arial stands in at its width (the `Fallback` faces in `brand.css`), so lines do not rewrap when it arrives. Neither font has arrow glyphs, so the site does not use arrows.

## Tech stack

| Layer | What |
|-------|------|
| Markup | Static HTML5 pages, inline SVG |
| Styles | `styles/brand.css` (identity) and `styles/site.css` (every page) |
| Scripts | Vanilla JS, all inline: sun and moon positions, lake colors |
| Fonts | Archivo and Inter Tight, served from `fonts/` under SIL Open Font License; logos are outlines |
| Analytics | None. No cookies, no tracking |
| Hosting | GitHub Pages |
| Domain | thepeninsularcompany.com via `CNAME` (DNS on Cloudflare) |

## Local development

Serve the folder with `python3 -m http.server 4173 --bind 127.0.0.1`, then open `http://127.0.0.1:4173/`. The extracted brand kit also works by opening its `index.html` directly.

## Deployment

Pushes to `main` deploy via GitHub Pages from [joe-at-heirloom/thepeninsularcompany.github.io](https://github.com/joe-at-heirloom/thepeninsularcompany.github.io). DNS lives on Cloudflare:

| Type | Name | Content |
|------|------|---------|
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| CNAME | `www` | `thepeninsularcompany.github.io` |

Keep these set to **DNS only** (grey cloud) so GitHub can issue and renew the HTTPS certificate. **Enforce HTTPS** is on in the repo's Pages settings.
