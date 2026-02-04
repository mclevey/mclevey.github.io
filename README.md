# johnmclevey.com

Personal website served via GitHub Pages from the `docs/` directory.

## Architecture

This site uses a **unified template-based build system** that separates content from presentation:

- **Content** lives in `content/` (markdown with YAML frontmatter)
- **Templates** live in `templates/` (Jinja2 HTML templates)
- **Output** goes to `docs/` (static HTML served by GitHub Pages)

```
.
├── content/                 # CONTENT: Markdown files with YAML frontmatter
│   ├── index.md             # Home page content
│   ├── research.md          # Research page
│   ├── teaching.md          # Teaching page
│   ├── software-data.md     # Software page
│   └── books/               # Book pages
│       ├── dcss.md
│       ├── face-to-face.md
│       ├── industrial-development.md
│       └── sage-handbook.md
├── templates/               # PRESENTATION: Jinja2 templates
│   ├── base.html            # Common page structure (nav, footer, theme)
│   ├── page.html            # Generic content page
│   ├── index.html           # Home page with profile section
│   ├── blog_post.html       # Blog post with syntax highlighting
│   ├── blog_index.html      # Blog listing page
│   ├── book.html            # Book page layout
│   └── cv.html              # CV with TOC sidebar
├── posts/                   # Blog sources (.qmd notebooks)
├── records/                 # CV data sources
│   └── cv.md                # CV data in YAML frontmatter
├── docs/                    # OUTPUT: Built static site
└── scripts/                 # Build scripts
    ├── build_site.py        # Unified site builder
    └── build_cv.py          # CV-specific builder (used by build_site.py)
```

## Prerequisites

- [Pixi](https://pixi.sh) for environment management
- [Quarto](https://quarto.org) for rendering `.qmd` notebooks
- Run `pixi install` to set up Python dependencies

## Build Commands

| Command | Description |
|---------|-------------|
| `pixi run build` | Build entire site (pages + blog + CV) |
| `pixi run build-pages` | Build static pages only |
| `pixi run build-blog` | Build blog posts only |
| `pixi run build-cv` | Build CV only |
| `pixi run preview` | Start local server at http://localhost:8080 |

Legacy aliases (`update-blog`, `update-cv`) still work for backwards compatibility.

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

**Special frontmatter fields:**
- `template` - Which template to use (defaults to `page`)
- `active` - Which nav item to highlight
- `title` - Page title
- `show_title` - Whether to show an h1 with the title

### Blog Posts

Blog posts are Quarto notebooks with executable Python code:

1. **Create:** Add `posts/YYYY-MM-DD-slug.qmd`
2. **Add frontmatter:**
   ```yaml
   ---
   title: Your Post Title
   author: John McLevey
   date: 2026-02-03
   excerpt: Brief description for blog index.
   execute:
     echo: true
     warning: false
   format:
     gfm: default
   ---
   ```
3. **Write content** with executable code blocks
4. **Build:** Run `pixi run build-blog`

### CV

The CV is built from YAML data in `records/cv.md`:

1. **Edit** the YAML frontmatter in `records/cv.md`
2. **Build:** Run `pixi run build-cv`

GitHub API data (software versions, stars) is cached for 15 minutes.

## Build Pipeline

```
                           ┌─────────────────────┐
                           │  templates/*.html   │
                           │  (Jinja2 templates) │
                           └──────────┬──────────┘
                                      │
┌──────────────────┐                  │                  ┌───────────────────┐
│ content/*.md     │──────┐           │           ┌──────│ docs/*.html       │
│ (static pages)   │      │           │           │      │ (static pages)    │
└──────────────────┘      │           │           │      └───────────────────┘
                          │           │           │
┌──────────────────┐      │     ┌─────┴─────┐     │      ┌───────────────────┐
│ posts/*.qmd      │──────┼────▸│build_site │─────┼─────▸│ docs/blog/*.html  │
│ (blog sources)   │      │     │   .py     │     │      │ (blog posts)      │
└──────────────────┘      │     └─────┬─────┘     │      └───────────────────┘
                          │           │           │
┌──────────────────┐      │           │           │      ┌───────────────────┐
│ records/cv.md    │──────┘           │           └──────│ docs/cv.html      │
│ (CV data)        │                  │                  │ (CV page)         │
└──────────────────┘                  │                  └───────────────────┘
                                      │
                           ┌──────────┴──────────┐
                           │    GitHub API       │
                           │ (software metadata) │
                           └─────────────────────┘
```

## Template Structure

All templates extend `base.html` which provides:
- Navigation header with theme toggle
- Footer (loaded via JS)
- Theme persistence (light/dark mode)

Templates can override blocks:
- `{% block head_extra %}` - Additional head elements
- `{% block before_main %}` - Content before main (e.g., sidebars)
- `{% block content %}` - Main page content
- `{% block scripts %}` - Additional scripts

## File Reference

### Source Files (Edit These)

| Location | Purpose |
|----------|---------|
| `content/*.md` | Static page content |
| `content/books/*.md` | Book page content |
| `posts/*.qmd` | Blog post sources |
| `records/cv.md` | CV data |
| `templates/*.html` | Page templates |
| `docs/styles.css` | Site styles |
| `docs/footer.html` | Shared footer |
| `docs/images/*` | Static images |

### Generated Files (Don't Edit)

| File | Source |
|------|--------|
| `docs/index.html` | `content/index.md` |
| `docs/research.html` | `content/research.md` |
| `docs/teaching.html` | `content/teaching.md` |
| `docs/software-data.html` | `content/software-data.md` |
| `docs/books/*.html` | `content/books/*.md` |
| `docs/blog/*.html` | `posts/*.qmd` |
| `docs/blog.html` | Generated from all posts |
| `docs/cv.html` | `records/cv.md` |

## Deployment

The site deploys automatically when you push to `master`. GitHub Pages serves `docs/`.

```bash
pixi run build
git add .
git commit -m "Update site"
git push
```

## Technical Notes

### Why This Architecture?

Previous iterations used a mix of approaches (raw HTML, partial templates, different build scripts). This unified system:

1. **Separates concerns** - Content in markdown, presentation in templates
2. **Single build script** - One entry point (`build_site.py`) for everything
3. **Consistent workflow** - All pages work the same way
4. **Easy to maintain** - Change a template, rebuild, done

### Intermediate Files

These are generated during builds and ignored by git:

- `posts/*.md` - Intermediate markdown from Quarto
- `posts/*_files/` - Quarto figure directories
- `posts/.quarto/`, `posts/_freeze/`, `posts/.jupyter_cache/` - Caches

### GitHub API Caching

Software entries fetch metadata from GitHub. Responses are cached in `records/github_cache.json` with a 15-minute TTL. Set `GITHUB_TOKEN` for higher rate limits.
