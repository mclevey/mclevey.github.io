# johnmclevey.com

Personal website served via GitHub Pages from the `docs/` directory.

## Architecture

This site uses a **unified template-based build system** that separates content from presentation:

- **Content** lives in `content/` (markdown with YAML frontmatter)
- **Templates** live in `templates/` (Jinja2 HTML templates)
- **Output** goes to `docs/` (static HTML served by GitHub Pages)

```
.
├── content/                 # CONTENT: All source content
│   ├── index.md             # Home page
│   ├── research.md          # Research page
│   ├── teaching.md          # Teaching overview
│   ├── software-data.md     # Software page
│   ├── books/               # Book pages
│   │   ├── dcss.md
│   │   ├── face-to-face.md
│   │   ├── industrial-development.md
│   │   └── sage-handbook.md
│   ├── teaching/            # Course pages
│   │   └── 3040.md
│   └── posts/               # Blog posts (.qmd notebooks)
│       ├── _quarto.yml      # Quarto project config
│       ├── .gitignore       # Ignores intermediate files
│       └── *.qmd            # Blog post sources
├── templates/               # PRESENTATION: Jinja2 templates
│   ├── base.html            # Common structure (nav, footer, theme)
│   ├── page.html            # Generic content page
│   ├── index.html           # Home page with profile
│   ├── blog_post.html       # Blog post with syntax highlighting
│   ├── blog_index.html      # Blog listing
│   ├── book.html            # Book page layout
│   ├── course.html          # Course page layout
│   └── cv.html              # CV with TOC sidebar
├── records/                 # DATA: Structured data sources
│   ├── cv.md                # CV data in YAML frontmatter
│   └── github_cache.json    # Cached GitHub API responses
├── docs/                    # OUTPUT: Built static site
│   ├── styles.css           # Site-wide styles (edit this)
│   ├── footer.html          # Shared footer (edit this)
│   ├── images/              # Static images (edit this)
│   └── pdfs/                # PDF files (edit this)
└── scripts/                 # Build scripts
    ├── build_site.py        # Unified site builder
    └── build_cv.py          # CV-specific builder
```

## Prerequisites

- [Pixi](https://pixi.sh) for environment management
- [Quarto](https://quarto.org) for rendering `.qmd` notebooks
- Run `pixi install` to set up Python dependencies

## Build Commands

| Command                | Description                                 |
| ---------------------- | ------------------------------------------- |
| `pixi run build`       | Build entire site (pages + blog + CV)       |
| `pixi run build-pages` | Build static pages only                     |
| `pixi run build-blog`  | Build blog posts only                       |
| `pixi run build-cv`    | Build CV only                               |
| `pixi run preview`     | Start local server at http://localhost:8080 |

Legacy aliases `update-blog` and `update-cv` also work.

## Content Workflow

### Static Pages

Content files use YAML frontmatter to specify the template and metadata:

```markdown
---
template: page
title: Research
active: research
---

Page content in markdown (can include raw HTML)...
```

**Available templates:**

- `page` - Generic content page
- `index` - Home page with profile section
- `book` - Book page with cover image and metadata
- `course` - Course page with schedule info

**Common frontmatter fields:**

- `template` - Which template to use (defaults to `page`)
- `active` - Which nav item to highlight (cv, research, teaching, software, blog)
- `title` - Page title (appears in browser tab)

### Book Pages

```markdown
---
template: book
title: Doing Computational Social Science
authors: John McLevey
publisher: Sage, London
year: 2022
image: DCSS.png
---

Book description and content...
```

### Course Pages

```markdown
---
template: course
title: Quantitative Research Methods
code: SOCI/CRIM 3040-001
schedule: Tuesday and Thursday, 1:30-2:50 pm in C2003
term: Winter 2026
active: teaching
---

Course content...
```

### Blog Posts

Blog posts are Quarto notebooks (`.qmd`) with executable Python code.

1. **Create:** Add `content/posts/YYYY-MM-DD-slug.qmd`
2. **Add minimal frontmatter** (execution/format settings inherited from `_quarto.yml`):
   ```yaml
   ---
   title: Your Post Title
   date: 2026-02-03
   excerpt: Brief description for blog index.
   ---
   ```
3. **Write content** with executable Python code blocks:
   ````markdown
   ```{python}
   import pandas as pd
   print("Hello from Python!")
   ```
   ````
4. **Build:** Run `pixi run build-blog`

**Shared settings in `_quarto.yml`** (don't repeat in posts):

- `author: John McLevey`
- `execute:` echo, warning, message, cache, freeze
- `format: gfm` with all rendering options

**Optional per-post overrides:**

- `author` - If different from default
- `execute.echo: false` - To hide code for a specific post
- `categories` - For tagging

The build process:

- Executes all Python code blocks via Quarto
- Embeds outputs (text, tables, figures) in the HTML
- Copies generated figures to `docs/blog/figures/`
- Cleans up intermediate files
- Updates the blog index and home page "Latest Posts"

### CV

The CV is built from YAML data in `records/cv.md`:

1. **Edit** the YAML frontmatter in `records/cv.md`
2. **Build:** Run `pixi run build-cv`

For software entries with GitHub URLs, the build fetches metadata (version, stars, last commit) from the GitHub API. Responses are cached in `records/github_cache.json` with a 15-minute TTL. Set the `GITHUB_TOKEN` environment variable for higher API rate limits.

## Build Pipeline

```
                           ┌─────────────────────┐
                           │  templates/*.html   │
                           │  (Jinja2 templates) │
                           └──────────┬──────────┘
                                      │
┌──────────────────┐                  │                  ┌───────────────────┐
│ content/*.md     │──────┐           │           ┌──────│ docs/*.html       │
│ content/books/   │      │           │           │      │ docs/books/       │
│ content/teaching/│      │           │           │      │ docs/teaching/    │
└──────────────────┘      │           │           │      └───────────────────┘
                          │           │           │
┌──────────────────┐      │     ┌─────┴─────┐     │      ┌───────────────────┐
│ content/posts/   │──────┼────▸│build_site │─────┼─────▸│ docs/blog/*.html  │
│ (*.qmd files)    │      │     │   .py     │     │      │ docs/blog.html    │
└──────────────────┘      │     └─────┬─────┘     │      └───────────────────┘
                          │           │           │
┌──────────────────┐      │           │           │      ┌───────────────────┐
│ records/cv.md    │──────┘           │           └──────│ docs/cv.html      │
│ (YAML data)      │                  │                  └───────────────────┘
└──────────────────┘                  │
                           ┌──────────┴──────────┐
                           │    GitHub API       │
                           │ (software metadata) │
                           └─────────────────────┘
```

## File Reference

### Source Files (Edit These)

| Location                    | Purpose                              |
| --------------------------- | ------------------------------------ |
| `content/*.md`              | Top-level pages                      |
| `content/books/*.md`        | Book pages                           |
| `content/teaching/*.md`     | Course pages                         |
| `content/posts/*.qmd`       | Blog posts                           |
| `content/posts/_quarto.yml` | Quarto config for blog               |
| `records/cv.md`             | CV data (YAML frontmatter)           |
| `templates/*.html`          | Page templates                       |
| `docs/styles.css`           | Site-wide CSS styles                 |
| `docs/footer.html`          | Shared footer content                |
| `docs/images/*`             | Static images (profile, book covers) |
| `docs/pdfs/*`               | PDF files                            |

### Generated Files (Don't Edit Directly)

| File                      | Source                       |
| ------------------------- | ---------------------------- |
| `docs/index.html`         | `content/index.md`           |
| `docs/research.html`      | `content/research.md`        |
| `docs/teaching.html`      | `content/teaching.md`        |
| `docs/software-data.html` | `content/software-data.md`   |
| `docs/books/*.html`       | `content/books/*.md`         |
| `docs/teaching/*.html`    | `content/teaching/*.md`      |
| `docs/blog/*.html`        | `content/posts/*.qmd`        |
| `docs/blog.html`          | Generated blog index         |
| `docs/blog/figures/*`     | Generated from code in posts |
| `docs/cv.html`            | `records/cv.md`              |

## Deployment

The site deploys automatically when you push to `master`. GitHub Pages serves the `docs/` directory.

```bash
pixi run build
git add .
git commit -m "Update site"
git push
```

The custom domain is configured via `docs/CNAME`.

## Technical Notes

### Why This Architecture?

1. **All content in one place** - Everything you edit is in `content/`
2. **Consistent workflow** - All pages work the same way
3. **Single build script** - One command builds everything
4. **Easy to maintain** - Change a template, rebuild, done

### Intermediate Files

These are generated during builds and ignored by git (via `content/posts/.gitignore`):

- `content/posts/*.md` - Intermediate markdown from Quarto
- `content/posts/*_files/` - Quarto figure directories
- `content/posts/.quarto/` - Quarto cache
- `content/posts/_freeze/` - Quarto freeze directory
- `content/posts/.jupyter_cache/` - Jupyter execution cache

### Template Inheritance

All templates extend `base.html`, which provides:

- Navigation header with theme toggle (light/dark mode)
- Footer (loaded via JavaScript from `footer.html`)
- Theme persistence via localStorage

Templates can override these blocks:

- `{% block head_extra %}` - Additional `<head>` content
- `{% block before_main %}` - Content before `<main>` (e.g., sidebars)
- `{% block content %}` - Main page content
- `{% block scripts %}` - Additional scripts at end of body
