# Legal sync

`company.json` holds the company facts that every app's privacy policy and
terms share. Change them here, push to `main`, and the **Legal sync** workflow
rewrites those facts on every site in `sites.json` and publishes them.

| Field | Printed as |
| --- | --- |
| `name` | "The Peninsular Company, LLC": © lines, "an agreement between you and …", ownership and liability clauses |
| `description` | follows the name where a page introduces the operator: "…, a Michigan limited liability company based in Detroit" |
| `location`, `country` | the line under each contact email ("Detroit, Michigan"; Heirloom adds the country) |
| `jurisdiction` | "governed by the laws of …" |
| `courts` | "resolved in …" |
| `email` | WorldSimulator's contact address (the other apps keep their own support addresses) |
| `updated` | the date the current details took effect, `YYYY-MM-DD` |

**Whenever you change a fact, set `updated` to the date it takes effect.** The
workflow refuses a change that leaves it alone. Each page's "Last updated" date
moves to it, but only on pages where a fact actually changed. Values may use
letters, digits, spaces and `. , ' ’ @ ( ) - – :`, nothing that means something
in HTML or Markdown.

Only the marked facts are shared. Everything else on a legal page, above all
what each app does with data, is that app's own text and is edited in its own
repo. This site's own `/privacy/` and `/terms/` are not synced: edit them by
hand in the same commit when a fact changes.

## How the sites carry the facts

Each fact on a page sits between markers, which render as nothing:

```
HTML, Markdown   <!--pc:KEY-->value<!--/pc:KEY-->
TSX (JSX text)   {/*pc:KEY*/}value{/*/pc:KEY*/}
```

Keys: `name`, `operator` (name + description), `location`,
`location-country`, `jurisdiction`, `courts`, `email`, `year` (the calendar year,
for ©), and `updated` (a page's "Last updated" date). To add a fact to a page,
wrap its current text in the markers; the next sync keeps it current.

- **Ollin Tuner, Learn to Play Cards, Daily Canvas, Madame Fortune**: markers in
  their HTML.
- **WorldSimulator** and **Codekeeper**: the sync writes `src/lib/company.ts`,
  which the legal pages import, and moves their `pc:updated` dates. A push to
  `main` deploys WorldSimulator on Vercel and Codekeeper on Cloudflare Pages.
  Codekeeper has a privacy policy but no terms yet.
- **Heirloom**: the legal text is Markdown in the app repo
  (`joe-at-heirloom/heirloom`, `legal/`), with markers. The sync never pushes
  there, because a push to that repo's `main` runs its CI and redeploys its
  backend. It writes `scripts/company.json` in the website repo, whose
  `build-legal.mjs` fills the markers from it, then rebuilds `privacy.html` and
  `terms.html` from the app repo's `main` and pushes the website. A rebuild
  publishes whatever the app repo's legal Markdown says at that moment.

## Running it yourself

```bash
node scripts/legal-sync.mjs --check    # which local checkouts under ~/Documents/Apps are behind
node scripts/legal-sync.mjs            # update them in place (no commits)
```

Local runs skip a checkout that is not on its site's branch.

## The token (one-time setup)

The workflow pushes to other repos, so it needs a token of its own:

1. On GitHub: **Settings → Developer settings → Fine-grained tokens → Generate
   new token**. Resource owner `joe-at-heirloom`; **Only select repositories**:
   `ollintuner.github.io`, `learntoplaycards.github.io`,
   `dailycanvas.github.io`, `madamefortune.github.io`, `heirloom.github.io`,
   `worldsimulator`, `codekeeper` and `heirloom`. Permissions: **Contents: Read
   and write**. (A token's permissions apply to every repo it covers; the sync
   only reads `heirloom`.)
2. Save it as this repo's secret:
   `gh secret set LEGAL_SYNC_TOKEN --repo joe-at-heirloom/thepeninsularcompany.github.io`
   (paste the token when asked).

When the token expires, the workflow fails with "GitHub rejected
LEGAL_SYNC_TOKEN"; make a new one and set the secret again.
