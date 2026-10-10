# thepeninsularcompany.com

Company site for The Peninsular Company, LLC: a privately held company in Detroit, Michigan, for new ventures in technology and beyond. It is the page Apple, banks, vendors, and anyone checking on the business should land on. [joelint.com](https://joelint.com) stays the personal site.

**Live site:** [thepeninsularcompany.com](https://thepeninsularcompany.com)

## What's on the page

- **Logo**: the name stacked on three lines under one roof rule, with a white pine green square (#1F4B3E) at cap height. A one-line version sits in the header. Both are outlined vector paths from Inter Tight 600, so they render the same with or without the web font.
- **The lake**: a line drawing across the full width of the page, looking across the water at the east end of Belle Isle. On the left is the William Livingstone Memorial Lighthouse (Albert Kahn, architect; Géza Maróti, sculptor; 1930), drawn from measured proportions. In the middle is a freighter; to the right is open water. The drawing is pinned to its left edge and never taller than half its width, so a phone still shows the lighthouse and the whole freighter. It follows the real light in Detroit: afternoon, golden hour, sunset, blue hour, and night, with the sun and moon placed where they actually are. After dark the lighthouse lamp blinks the way the Coast Guard lists it (occulting white, 4 s).
- **Works**: everything the company runs, numbered, with status, platform, and each one's own support, privacy, and terms links.
- **Contact**: email, one line about client work, and a link to joelint.com.
- **Footer**: legal name, Detroit, and the state motto.

## Adding a work

Copy an `<li class="work">` in `index.html`, give it the next number and a color in `style="--c: #..."`, and fill in its links. Each small link carries an `aria-label` naming the work ("Support for The Ollin Tuner"), so change those to the new name too. Use `class="no outlined small"` for a very light color so the marker still shows.

## The apps' legal pages

`legal/company.json` holds the company facts every app's privacy policy and terms share (legal name, where, which law governs). Change it and push: the **Legal sync** workflow updates and publishes every app site. See [legal/README.md](legal/README.md). `_config.yml` keeps `legal/` and `scripts/` off the published site.

## How the page is built

`index.html` is one self-contained file and the source of truth: the logo, the lake drawing, and the sun and moon code are edited in place. (The parts it was first assembled from, kept outside the repo, are gone.)

- The logos are outlined paths, so they do not depend on the web font.
- The lake is one inline SVG. The High Lift Pumping Station at Water Works Park was taken out of it on October 2, 2026; leave it out.
- Two scripts sit in the `<head>`, above the page. `ASTRO` works out where the sun and moon are over Detroit (NOAA low-precision sun, Schlyter moon, checked against the April 8, 2024 solar eclipse and the March 14, 2025 lunar eclipse). `LAKE` turns that into the lake's colors and sets them before the page first draws, so a visitor at night never sees a flash of the day drawing. It runs again right after the drawing, to place the sun and moon, and every 30 seconds after that.

`privacy/` and `terms/` carry the same base, header, and footer styles as the home page, plus their own "Legal pages" block, and nothing for the hero, lake, or Works. A change to the header, footer, or type goes in all three files.

The stylesheet ends with three blocks worth knowing about:

- **Touch** gives the small links a full-size tap target on phones and tablets without moving anything.
- **High contrast** hands the logo and the lake the system's colors when Windows high contrast (or any forced-color theme) is on. Without it the logo would be black on black.
- **Paper** is the print version, for anyone who files the page as a PDF: white ground, the lake as the day drawing, Works starting on page two, and a footer that reads without its dark panel.

Until Inter Tight loads, the text is set in Helvetica or Arial scaled to Inter Tight's width (the `Inter Tight Fallback` faces at the top of the stylesheet), so lines do not rewrap when the font arrives.

To see the lake at another time, add `?at=` to the address:

```
index.html?at=19:30              today at 7:30 PM, Detroit time
index.html?at=2026-10-14T20:15   a given date and time
```

## Tech stack

| Layer | What |
|-------|------|
| Markup | HTML5, single file, inline SVG |
| Styles | CSS, all inline |
| Scripts | Vanilla JS, all inline: sun and moon positions, lake colors |
| Fonts | Inter Tight, served from `fonts/` (SIL Open Font License); the logo doesn't need it |
| Analytics | None. No cookies, no tracking |
| Hosting | GitHub Pages |
| Domain | thepeninsularcompany.com via `CNAME` (DNS on Cloudflare) |

## Local development

Open `index.html` in a browser, or serve the folder (`python3 -m http.server 4173`).

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
