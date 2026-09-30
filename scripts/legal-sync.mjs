#!/usr/bin/env node
// Keeps the company facts in every app's privacy policy and terms in step with
// legal/company.json: who publishes the app, where the company is, which law
// governs, the © line and each page's "Last updated" date.
//
// Each site marks the spots that carry a fact, and this script rewrites what
// sits between each pair of markers:
//
//   HTML, Markdown, .mjs   <!--pc:KEY-->value<!--/pc:KEY-->
//   TSX (JSX text)         {/*pc:KEY*/}value{/*/pc:KEY*/}
//
// A site can also take a generated module (WorldSimulator's src/lib/company.ts,
// which its pages import) or a vendored copy of the values its own build reads
// (Heirloom's scripts/company.json, which build-legal.mjs applies to the app
// repo's Markdown). legal/sites.json lists the sites and their files.
//
// Keys: name, operator (name + description), location, location-country,
// jurisdiction, courts, email, year (the calendar year, for ©) and updated.
// A page's pc:updated moves to company.json's "updated" date when, and only
// when, a fact on that page changes; the © year never moves it.
//
//   node scripts/legal-sync.mjs                        # sync the checkouts under ~/Documents/Apps
//   node scripts/legal-sync.mjs --root DIR             # … under DIR
//   node scripts/legal-sync.mjs --check                # report only; exit 1 if a site is behind
//   node scripts/legal-sync.mjs --clone DIR [--push]   # CI: clone, sync, build, commit, push
//
// Local runs never commit and skip a checkout that is not on its site's
// branch. In --clone mode GH_TOKEN authenticates to GitHub (the
// LEGAL_SYNC_TOKEN secret in the workflow). No dependencies.

import { readFileSync, writeFileSync, existsSync, mkdirSync, rmSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { homedir } from 'node:os';

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, '..');
const COMPANY_FILE = 'legal/company.json';
const SITES_FILE = 'legal/sites.json';

const FIELDS = ['name', 'description', 'location', 'country', 'jurisdiction', 'courts', 'email', 'updated'];
// Values land in HTML, Markdown, JS template literals and JSX text unescaped,
// so they may only use characters that mean nothing special in any of them.
const SAFE = /^[\p{L}\p{N} .,'’@()\-–:]+$/u;
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

export function formatDate(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  return `${MONTHS[m - 1]} ${d}, ${y}`;
}

/** "September 30, 2026 (…)" → "2026-09-30", or null. */
export function parseDate(text) {
  const m = /^\s*([A-Z][a-z]+) (\d{1,2}), (\d{4})/.exec(text);
  const month = m ? MONTHS.indexOf(m[1]) : -1;
  if (month < 0) return null;
  return `${m[3]}-${String(month + 1).padStart(2, '0')}-${m[2].padStart(2, '0')}`;
}

export function loadCompany(text) {
  const company = JSON.parse(text);
  for (const f of FIELDS) {
    if (typeof company[f] !== 'string' || !company[f].trim()) throw new Error(`${COMPANY_FILE}: "${f}" is missing`);
    if (f !== 'updated' && !SAFE.test(company[f])) {
      throw new Error(`${COMPANY_FILE}: "${f}" may only use letters, digits, spaces and . , ' ’ @ ( ) - – :`);
    }
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(company.updated) || !parseDate(formatDate(company.updated))) {
    throw new Error(`${COMPANY_FILE}: "updated" must be a date written YYYY-MM-DD`);
  }
  return company;
}

export function tokens(company, year) {
  return {
    name: company.name,
    operator: `${company.name}, ${company.description}`,
    location: company.location,
    'location-country': `${company.location}, ${company.country}`,
    jurisdiction: company.jurisdiction,
    courts: company.courts,
    email: company.email,
    year: String(year),
  };
}

const SYNTAX = {
  html: {
    re: () => /<!--pc:([a-z-]+)-->([\s\S]*?)<!--\/pc:\1-->/g,
    wrap: (k, v) => `<!--pc:${k}-->${v}<!--/pc:${k}-->`,
    escape: (v) => v,
  },
  jsx: {
    re: () => /\{\/\*pc:([a-z-]+)\*\/\}([\s\S]*?)\{\/\*\/pc:\1\*\/\}/g,
    wrap: (k, v) => `{/*pc:${k}*/}${v}{/*/pc:${k}*/}`,
    escape: (v) => v.replace(/'/g, '&apos;'),
  },
};
const syntaxFor = (path) => (/\.(tsx|jsx)$/.test(path) ? SYNTAX.jsx : SYNTAX.html);

/**
 * Rewrite the markers in one file's text. `bump` forces the pc:updated check
 * even when no marker here changed (a module the page reads did). Returns the
 * new text, the keys that changed and how many markers the file has.
 */
export function applyMarkers(text, path, values, updated, bump = false) {
  const { re, wrap, escape } = syntaxFor(path);
  const changed = new Set();
  let count = 0;
  let out = text.replace(re(), (whole, key, inner) => {
    count += 1;
    if (key === 'updated') return whole;
    if (!(key in values)) throw new Error(`${path}: unknown marker pc:${key}`);
    const value = escape(values[key]);
    if (inner === value) return whole;
    changed.add(key);
    return wrap(key, value);
  });
  if (bump || [...changed].some((k) => k !== 'year')) {
    out = out.replace(re(), (whole, key, inner) => {
      if (key !== 'updated') return whole;
      const own = parseDate(inner);
      if (!own) throw new Error(`${path}: pc:updated does not start with a date ("${inner}")`);
      if (own >= updated) return whole;
      changed.add('updated');
      return wrap(key, formatDate(updated));
    });
  }
  return { text: out, changed: [...changed], count };
}

export function renderModule(values, keys) {
  const lines = keys.map((k) => `  ${/^[a-z]+$/.test(k) ? k : JSON.stringify(k)}: ${JSON.stringify(values[k])},`);
  return [
    '// Generated by the legal sync in joe-at-heirloom/thepeninsularcompany.github.io',
    '// from legal/company.json. Edit that file, not this one: a push there rewrites',
    '// this module and moves the "Effective date" on the pages that read it.',
    '',
    'export const COMPANY = {',
    ...lines,
    '} as const;',
    '',
  ].join('\n');
}

function pick(values, keys) {
  return Object.fromEntries(keys.map((k) => [k, values[k]]));
}

/** The vendored values, keeping the old "updated" unless one of them changed. */
export function renderVendor(values, keys, updated, currentText) {
  const next = pick(values, keys);
  let current = null;
  try {
    current = currentText ? JSON.parse(currentText) : null;
  } catch {
    current = null;
  }
  const same = current && keys.every((k) => current[k] === next[k]);
  const date = same ? current.updated : current?.updated > updated ? current.updated : updated;
  const body = {
    _generated: 'By the legal sync in joe-at-heirloom/thepeninsularcompany.github.io from legal/company.json. Do not edit.',
    ...next,
    updated: date,
  };
  return { text: `${JSON.stringify(body, null, 2)}\n`, changed: keys.filter((k) => !current || current[k] !== next[k]) };
}

/** Sync one site checked out at `dir`. Writes only when `write` is set. */
export function syncSite(site, dir, values, updated, { write }) {
  const changes = [];
  const save = (rel, text) => {
    if (write) {
      mkdirSync(dirname(join(dir, rel)), { recursive: true });
      writeFileSync(join(dir, rel), text);
    }
  };
  const read = (rel) => (existsSync(join(dir, rel)) ? readFileSync(join(dir, rel), 'utf8') : '');

  let moduleKeys = [];
  if (site.module) {
    const current = read(site.module.path);
    const next = renderModule(values, site.module.keys);
    if (current !== next) {
      moduleKeys = site.module.keys.filter((k) => !current.includes(`${JSON.stringify(values[k])},`));
      changes.push({ path: site.module.path, keys: moduleKeys });
      save(site.module.path, next);
    }
  }

  if (site.vendor) {
    const current = read(site.vendor.path);
    const { text, changed } = renderVendor(values, site.vendor.keys, updated, current);
    if (current !== text) {
      changes.push({ path: site.vendor.path, keys: changed });
      save(site.vendor.path, text);
    }
  }

  for (const rel of site.files) {
    if (!existsSync(join(dir, rel))) throw new Error(`${rel} not found`);
    const text = read(rel);
    const bump = moduleKeys.some((k) => new RegExp(`\\bCOMPANY\\.${k}\\b`).test(text));
    const result = applyMarkers(text, rel, values, updated, bump);
    if (result.count === 0) throw new Error(`${rel} has no pc: markers`);
    if (result.text !== text) {
      changes.push({ path: rel, keys: result.changed });
      save(rel, result.text);
    }
  }
  return changes;
}

/** After a sync, each verified page must name the operator. */
function verify(site, dir, values) {
  for (const rel of site.verify ?? []) {
    const text = readFileSync(join(dir, rel), 'utf8');
    if (!text.includes(values.operator)) throw new Error(`${rel} does not name "${values.operator}" after the sync`);
  }
}

function git(cwd, ...args) {
  return execFileSync('git', args, { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
}

function authArgs() {
  const token = process.env.GH_TOKEN;
  if (!token || process.env.LEGAL_SYNC_GIT_BASE) return [];
  const basic = Buffer.from(`x-access-token:${token}`).toString('base64');
  return ['-c', `http.https://github.com/.extraheader=AUTHORIZATION: basic ${basic}`];
}

function remoteUrl(repo) {
  return `${process.env.LEGAL_SYNC_GIT_BASE ?? 'https://github.com/'}${repo}.git`;
}

function clone(repo, ref, dir, sparsePaths) {
  const args = [...authArgs(), 'clone', '--quiet', '--depth', '1', '--branch', ref];
  if (sparsePaths) args.push('--filter=blob:none', '--sparse');
  git(undefined, ...args, remoteUrl(repo), dir);
  if (sparsePaths) git(dir, 'sparse-checkout', 'set', '--no-cone', ...sparsePaths.map((p) => `/${p}`));
}

async function tokenIdentity() {
  const res = await fetch('https://api.github.com/user', {
    headers: { authorization: `Bearer ${process.env.GH_TOKEN}`, 'user-agent': 'legal-sync' },
  });
  if (!res.ok) throw new Error(`GitHub rejected LEGAL_SYNC_TOKEN (HTTP ${res.status}); it may have expired`);
  const user = await res.json();
  // The token owner's noreply address, so commits are attributed to the account
  // (Vercel, for one, refuses to deploy commits from authors it cannot match).
  return { name: user.name || user.login, email: `${user.id}+${user.login}@users.noreply.github.com` };
}

/** Refuse a company.json whose facts changed while its "updated" date did not. */
function checkUpdatedMoved(company) {
  const before = process.env.BEFORE;
  const ref = before && !/^0+$/.test(before) ? before : process.env.CI ? null : 'HEAD';
  if (!ref) return;
  let previous;
  try {
    previous = JSON.parse(git(repoRoot, 'show', `${ref}:${COMPANY_FILE}`));
  } catch {
    return; // no earlier version to compare with
  }
  const moved = FIELDS.some((f) => f !== 'updated' && previous[f] !== company[f]);
  if (moved && previous.updated === company.updated) {
    throw new Error(`${COMPANY_FILE} changed but its "updated" date did not: set it to the date the new details take effect (YYYY-MM-DD)`);
  }
}

function describe(changes) {
  return changes.map((c) => `${c.path}${c.keys.length ? ` (${c.keys.join(', ')})` : ''}`).join('; ');
}

async function main() {
  const args = process.argv.slice(2);
  const option = (name) => {
    const i = args.indexOf(name);
    return i >= 0 ? args[i + 1] : undefined;
  };
  const check = args.includes('--check');
  const cloneDir = option('--clone');
  const push = args.includes('--push');

  const company = loadCompany(readFileSync(join(repoRoot, COMPANY_FILE), 'utf8'));
  const today = new Date().toISOString().slice(0, 10);
  if (company.updated > today) throw new Error(`${COMPANY_FILE}: "updated" (${company.updated}) is in the future`);
  checkUpdatedMoved(company);
  const values = tokens(company, new Date().getUTCFullYear());
  const { sites } = JSON.parse(readFileSync(join(repoRoot, SITES_FILE), 'utf8'));
  const failures = [];
  let behind = 0;

  if (!cloneDir) {
    const root = resolve(option('--root') ?? join(homedir(), 'Documents', 'Apps'));
    for (const site of sites) {
      const dir = join(root, site.local);
      try {
        if (!existsSync(dir)) {
          console.log(`${site.name}: skipped (no checkout at ${dir})`);
          continue;
        }
        const branch = git(dir, 'branch', '--show-current');
        if (branch !== (site.branch ?? 'main')) {
          console.log(`${site.name}: skipped (checkout is on "${branch}", not "${site.branch ?? 'main'}")`);
          continue;
        }
        const changes = syncSite(site, dir, values, company.updated, { write: !check });
        if (!changes.length) {
          console.log(`${site.name}: up to date`);
          continue;
        }
        behind += 1;
        console.log(`${site.name}: ${check ? 'behind' : 'updated'}: ${describe(changes)}`);
        if (check) continue;
        // A built site's pages only follow once its build runs, which needs
        // its sources checked out where `env` says.
        if (site.build) console.log(`  then run in ${dir}: ${site.build.join(' && ')} (with ${Object.keys(site.env ?? {}).join(', ')} set)`);
        else verify(site, dir, values);
      } catch (error) {
        failures.push(`${site.name}: ${error.message}`);
      }
    }
  } else {
    if (!process.env.GH_TOKEN && !process.env.LEGAL_SYNC_GIT_BASE) {
      throw new Error(
        'GH_TOKEN is not set. Add a fine-grained token with Contents: read and write on the site repos as the ' +
          'LEGAL_SYNC_TOKEN secret: gh secret set LEGAL_SYNC_TOKEN --repo joe-at-heirloom/thepeninsularcompany.github.io',
      );
    }
    const identity = push && process.env.GH_TOKEN && !process.env.LEGAL_SYNC_GIT_BASE ? await tokenIdentity() : null;
    const source = process.env.GITHUB_SHA ?? git(repoRoot, 'rev-parse', 'HEAD');
    const work = resolve(cloneDir);
    rmSync(work, { recursive: true, force: true });
    mkdirSync(work, { recursive: true });

    // Access problems are collected and explained together at the end, so one
    // run names everything the token is missing.
    const access = [];
    const guard = (repo, need, step) => {
      try {
        return step();
      } catch (error) {
        const said = `${error.stderr ?? ''} ${error.message}`;
        if (!/\b40[134]\b|not granted|not found|Authentication failed|could not read Username/i.test(said)) throw error;
        access.push(`${repo} (${need})`);
        throw new Error(`the token cannot ${need} ${repo}`);
      }
    };

    for (const site of sites) {
      try {
        const dir = join(work, site.repo.replace('/', '__'));
        const branch = site.branch ?? 'main';
        const paths = [...site.files, ...(site.outputs ?? []), site.module?.path, site.vendor?.path].filter(Boolean);
        guard(site.repo, 'read', () => clone(site.repo, branch, dir, site.sparse ? paths : null));
        // A public repo clones without any access at all, so prove the token
        // can push before relying on it, even when there is nothing to push.
        if (push) guard(site.repo, 'write', () => git(dir, ...authArgs(), 'push', '--dry-run', '--quiet', 'origin', `HEAD:${branch}`));

        let sourcesDir;
        if (site.sources) {
          sourcesDir = join(work, `${site.sources.repo.replace('/', '__')}@sources`);
          guard(site.sources.repo, 'read', () => clone(site.sources.repo, site.sources.ref ?? 'main', sourcesDir, site.sources.files));
          for (const rel of site.sources.files) {
            const text = readFileSync(join(sourcesDir, rel), 'utf8');
            if (!SYNTAX.html.re().test(text)) {
              throw new Error(`${site.sources.repo}@${site.sources.ref ?? 'main'}:${rel} has no pc: markers, so its build would drop the company facts`);
            }
          }
        }

        const changes = syncSite(site, dir, values, company.updated, { write: true });
        if (!changes.length) {
          console.log(`${site.name}: up to date`);
          continue;
        }
        behind += 1;
        console.log(`${site.name}: ${describe(changes)}`);

        let built = '';
        if (site.build) {
          const env = { ...process.env };
          for (const [k, v] of Object.entries(site.env ?? {})) env[k] = v.replace('{sources}', sourcesDir ?? '');
          for (const command of site.build) execFileSync('sh', ['-c', command], { cwd: dir, env, stdio: 'inherit' });
          if (sourcesDir) built = `\nRebuilt from ${site.sources.repo}@${git(sourcesDir, 'rev-parse', '--short', 'HEAD')}.`;
        }
        verify(site, dir, values);

        if (push) {
          git(dir, 'add', '--sparse', '--', ...paths.filter((p) => existsSync(join(dir, p))));
          const who = identity ? ['-c', `user.name=${identity.name}`, '-c', `user.email=${identity.email}`] : [];
          const body = `From joe-at-heirloom/thepeninsularcompany.github.io@${source.slice(0, 7)} (legal/company.json).\nChanged: ${describe(changes)}.${built}`;
          git(dir, ...who, 'commit', '--quiet', '-m', 'Legal sync: company details from thepeninsularcompany.com', '-m', body);
          git(dir, ...authArgs(), 'push', '--quiet', 'origin', `HEAD:${site.branch ?? 'main'}`);
          console.log(`  pushed ${git(dir, 'rev-parse', '--short', 'HEAD')} to ${site.repo}`);
        }
      } catch (error) {
        failures.push(`${site.name}: ${error.stderr?.toString().trim() || error.message}`);
      }
    }

    if (access.length) {
      const message =
        `LEGAL_SYNC_TOKEN is missing access to: ${access.join(', ')}. ` +
        'Edit the token at https://github.com/settings/personal-access-tokens: under "Repository access" choose ' +
        '"Only select repositories" and include every repo in legal/sites.json, and under "Repository permissions" ' +
        'set "Contents" to "Read and write". Saving is enough (the secret does not change); then run the workflow again.';
      console.error(process.env.GITHUB_ACTIONS ? `::error title=Token access::${message}` : message);
    }
  }

  for (const f of failures) console.error(`FAILED ${f}`);
  if (failures.length || (check && behind)) process.exit(1);
}

const invokedDirectly = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invokedDirectly) {
  main().catch((error) => {
    console.error(error.message);
    process.exit(1);
  });
}
