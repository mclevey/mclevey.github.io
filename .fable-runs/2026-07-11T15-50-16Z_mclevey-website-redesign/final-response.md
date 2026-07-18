The redesign is implemented, built, and validated. The existing Markdown + Jinja2 + Python architecture was fully retained; all five reference designs are reproduced with shared templates and a single stylesheet, and `docs/` contains the complete generated site ready to copy back.

## What changed

**Templates (`templates/`)** — all rebuilt around a shared `base.html` with the reference's compact header (brand left, Research / Teaching / Code & Data / Blog / CV right), an inline footer (© year, email, phone, office), a skip link, and a hamburger menu below 720px with proper `aria-expanded`/Escape handling. The dark-mode toggle and the JavaScript-fetched `footer.html` are gone; neither exists in the approved design. Two new templates, `research.html` and `teaching.html`, render the featured-book rows and course groups. `blog_post.html` keeps highlight.js (light theme) and the lightbox; `cv.html` keeps the TOC sidebar with scroll spy and now flows through the shared base.

**Styles (`docs/styles.css`)** — rewritten from scratch on the reference tokens: `#fcfcfa` ground, `#191918` ink, hairline rules (`#e6e4de`/`#f0efeb`), muted `#8a877f` uppercase section labels, Instrument Sans, 720px column, blue `#2a78d6` only on hover/focus. Responsive rules cover every layout: book grid 4→2 columns, teaching grid 3→1, publication rows stack, research book rows collapse, tables scroll, TOC sidebar hides under 1340px, profile stacks under 420px. Visible `:focus-visible` states throughout.

**Content (`content/`)** — the four top-level pages now carry structured frontmatter (books, articles, course groups) instead of design-baked inline HTML, so templates own all presentation. Book and course files had heading levels shifted down one (page title is the only h1) and standalone `<br>` layout hacks removed. No copy was mocked: books link to the real book pages, 3040 to its course page, GitHub/email/department links are real. Design `#` placeholders for Google Scholar, ORCID, and article DOIs were removed rather than guessed, since web lookup was not permitted in this sandbox (see limitations).

**Builders (`scripts/`)** — `build_site.py` gained a typed, docstringed `format_date_display()` (posts now show "Feb 3, 2026") and a `current_year` template global. `build_cv.py` had its 140-line hardcoded HTML page replaced by `render_cv_page()`, which renders through the shared `cv.html` template, so the CV can no longer drift from the site chrome.

**Output hygiene** — copied the approved headshot to `docs/images/john-mclevey-headshot.jpeg`; deleted stale, orphaned artifacts (`footer.html`, `data.html`, `software.html`, `supervision.html`, three old unreferenced blog HTML files). README updated to match. `docs-redesign/` untouched; nothing committed or pushed (the sandbox is not a git repo).

## Verification

- `pixi run build` completes cleanly (pixi at `~/.pixi/bin/pixi`; quarto obtained via a cached `pixi exec` environment plus `QUARTO_SHARE_PATH`, a sandbox-only workaround that changes nothing in the repo). All 11 pages regenerate: home, research, teaching, code/data, blog index, blog post, 4 book pages, course page, CV.
- Link check: 130 internal hrefs/srcs resolve, verified case-sensitively (GitHub Pages is case-sensitive), zero `#` placeholders remain.
- HTML well-formedness pass over every generated page: no mismatched tags, no template artifacts.
- Responsive verification was static only (no browser tooling in the sandbox): every fixed grid and row layout was checked to have a mobile override, and viewport meta is present on all pages. A quick visual pass at desktop and ~375px width on the real Mac is worth doing.

## Limitations

- Google Scholar and ORCID profile URLs plus article DOIs couldn't be verified without network access, so those links were omitted. Add them to `content/index.md` (`social:`) and `content/research.md` (`articles[].href`) when you can paste the real URLs.
- The CV data itself (`records/cv.md`) still lists the old Waterloo email; I left data files untouched.
