# thepeninsularcompany.com

Company site for The Peninsular Company LLC, the publisher behind Joe Lint's apps. It's where the App Store seller name, Apple's organization verification, and anyone checking on the business should land. [joelint.com](https://joelint.com) stays the personal site; this one stays small.

**Live site:** [thepeninsularcompany.com](https://thepeninsularcompany.com)

## What's in here

One page in the Michigan Modern tradition: Mies at Lafayette Park, Saarinen at the GM Tech Center, Albert Kahn, Knoll's graphics. A strict grid, one typeface, a travertine ground, and color only where it means something.

- **Hero** - oversized wordmark and a building elevation: nine steel-and-glass bays, one per affiliate. Occupied bays get a glazed-brick colored spandrel; unannounced ones are dark glass, "under construction." Hovering a bay lights its row in the roster, and the other way around
- **Affiliates** - everything the company publishes, numbered, with platform, status, and each app's own support, privacy, and terms links
- **Contact** - business email and a link to joelint.com

The red square is the mark, a nod to the red signature tile on Frank Lloyd Wright's houses.

## Adding or updating an affiliate

Each affiliate appears twice in `index.html`, tied together by `data-bay`:

1. **The bay** in `#facade`: `<a class="bay" href="#pen-N" data-bay="N" data-name="App Name" style="--c: var(--color)">`
2. **The row** in `#roster`: `<li class="row" id="pen-N" data-bay="N" style="--c: var(--color)">`

Colors available: `--yellow`, `--red`, `--blue`, `--black`, `--orange`, `--green`. For an unannounced project, add `vacant` to both the bay and the row and drop the color.

When a project is announced, remove `vacant`, give it a color and its real name, and keep its number. Update the "Six affiliates, three in progress" line and the "Nine bays, six occupied" caption to match.

## Tech stack

| Layer | What |
|-------|------|
| Markup | HTML5, single file |
| Styles | CSS, all inline |
| Scripts | ~30 lines of vanilla JS linking bays to rows |
| Fonts | Inter Tight (Google Fonts) |
| Analytics | None. No cookies, no tracking |
| Hosting | GitHub Pages |
| Domain | thepeninsularcompany.com via `CNAME` (DNS on Cloudflare) |

## File structure

```
.
├── index.html            # the whole site
├── 404.html              # "Unoccupied."
├── CNAME                 # custom domain for GitHub Pages
├── favicon.svg           # red square, P
├── apple-touch-icon.png  # 180×180 home-screen icon
├── og-image.png          # 1200×630 social preview
├── robots.txt
└── sitemap.xml
```

## Local development

Open `index.html` in a browser. That's it.

## Deployment

Pushes to `main` deploy via GitHub Pages from [joe-at-heirloom/thepeninsularcompany.github.io](https://github.com/joe-at-heirloom/thepeninsularcompany.github.io). DNS lives on Cloudflare:

| Type | Name | Content |
|------|------|---------|
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| CNAME | `www` | `joe-at-heirloom.github.io` |

Set these to **DNS only** (grey cloud) so GitHub can issue the HTTPS certificate, then tick **Enforce HTTPS** in the repo's Pages settings.
