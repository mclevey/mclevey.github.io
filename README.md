# johnmclevey.com

Personal website served via GitHub Pages from the `docs/` directory.

## Prerequisites

- [Pixi](https://pixi.sh) for environment management
- [Quarto](https://quarto.org) for rendering `.qmd` notebooks
- Run `pixi install` to set up Python dependencies

## Site Structure

```
.
├── docs/                    # Built site (served by GitHub Pages)
│   ├── blog/                # Generated blog post HTML
│   │   └── figures/         # Generated figures from code execution
│   ├── books/               # Book pages (manual HTML)
│   ├── images/              # All images (profile, book covers, etc.)
│   ├── pdfs/                # PDF files (publications, etc.)
│   ├── teaching/            # Teaching materials (manual HTML)
│   ├── styles.css           # Site-wide styles
│   ├── footer.html          # Shared footer (loaded via JS)
│   └── *.html               # Main site pages
├── posts/                   # Blog post sources (.qmd files)
│   └── _quarto.yml          # Quarto project config
├── records/                 # Data sources for generated content
│   ├── cv.md                # CV data in YAML frontmatter
│   └── github_cache.json    # Cached GitHub API responses
└── scripts/                 # Build scripts
    ├── build_blog.py        # Blog build pipeline
    └── build_cv.py          # CV build pipeline
```

## Build Pipelines

This site uses two automated build pipelines for generated content.

### Blog Pipeline

```
posts/*.qmd  →  [Quarto]  →  .md (with executed code)  →  [build_blog.py]  →  docs/blog/*.html
                                                                           →  docs/blog.html (index)
                                                                           →  docs/blog/figures/
```

**Source files:** `posts/*.qmd` (Quarto notebooks with executable Python code)

**What happens:**
1. Quarto renders each `.qmd` file, executing Python code blocks
2. Code outputs (text, tables, figures) are embedded in intermediate `.md` files
3. `build_blog.py` converts the markdown to HTML using the site template
4. Generated figures are copied to `docs/blog/figures/`
5. Intermediate files are cleaned up (only `.qmd` sources remain)
6. Blog index (`docs/blog.html`) is regenerated with all posts
7. Home page (`docs/index.html`) "Latest Posts" section is updated with the two most recent posts

**Command:** `pixi run update-blog`

### CV Pipeline

```
records/cv.md  →  [build_cv.py]  →  docs/cv.html
                       ↓
              GitHub API (cached)
```

**Source file:** `records/cv.md` (YAML frontmatter with all CV data)

**What happens:**
1. `build_cv.py` parses the YAML frontmatter from `cv.md`
2. For software entries, it fetches metadata from GitHub API (version, last commit, etc.)
3. API responses are cached in `records/github_cache.json` (15 min TTL)
4. CV sections are rendered to HTML with the site template
5. Table of contents is auto-generated from section headings

**Command:** `pixi run update-cv`

**Note:** Set `GITHUB_TOKEN` environment variable for higher API rate limits.

## Updating Content

### Blog Posts

Blog posts are Quarto notebooks (`.qmd`) with executable Python code.

1. **Create a new post:** Add `posts/YYYY-MM-DD-slug.qmd`
2. **Add frontmatter and content:**

   ```yaml
   ---
   title: Your Post Title
   author: John McLevey
   date: 2026-02-03
   excerpt: A brief description for the blog index.
   execute:
     echo: true
     warning: false
   format:
     gfm: default
   ---

   Your content here with executable code blocks:

   ```{python}
   import pandas as pd
   print("This code will be executed!")
   ```
   ```

3. **Build:** Run `pixi run update-blog`
4. **Preview:** Run `pixi run preview` and open http://localhost:8080/blog.html

**Image handling:**
- Static images: Place in `docs/images/`, reference as `../images/filename.png`
- Generated figures: Automatically saved to `docs/blog/figures/`

### CV Updates

1. **Edit source:** Open `records/cv.md` and update the YAML frontmatter
2. **Rebuild:** Run `pixi run update-cv`
3. **Preview:** Run `pixi run preview` and open http://localhost:8080/cv.html

Example CV entry structure:

```yaml
---
name: John McLevey
email: john.mclevey@example.com

education:
  - year: 2013
    subject: PhD, Sociology
    institute: McMaster University
    city: Hamilton, ON, Canada

articles:
  - year: 2022
    authors: John McLevey, Coauthor Name
    title: "Article Title"
    journal: Journal Name
    volume: 59
    issue: 2
    pages: 228-250

software:
  - package: pdpp
    description: Network data preprocessing
    github: https://github.com/mclevey/pdpp
    language: Python
    license: MIT License
    status: Active Development
    development: John McLevey
---
```

### Static Pages (Manual HTML)

These pages are edited directly in `docs/`:

| File | Purpose |
|------|---------|
| `docs/index.html` | Home page |
| `docs/research.html` | Research overview |
| `docs/teaching.html` | Teaching & supervision |
| `docs/software-data.html` | Software & data |
| `docs/books/*.html` | Individual book pages |
| `docs/teaching/*.html` | Course/workshop pages |

**To edit:**
1. Open the file in `docs/`
2. Make changes directly to the HTML
3. Preview with `pixi run preview`

### Shared Elements

| File | Purpose | Used By |
|------|---------|---------|
| `docs/styles.css` | All site styles | All pages |
| `docs/footer.html` | Footer content | Loaded via JS on all pages |
| `docs/images/` | Shared images | All pages |

## Pixi Commands

| Command | Description |
|---------|-------------|
| `pixi run preview` | Start local server at http://localhost:8080 |
| `pixi run update-blog` | Render `.qmd` files and build blog HTML |
| `pixi run update-cv` | Rebuild CV from `records/cv.md` |

## Deployment

The site deploys automatically when you push to the `master` branch. GitHub Pages serves the `docs/` directory.

```bash
git add .
git commit -m "Update site"
git push
```

The custom domain is configured via `docs/CNAME`.

## File Reference

### Generated Files (Do Not Edit Directly)

| File | Generated By | Source |
|------|--------------|--------|
| `docs/blog/*.html` | `build_blog.py` | `posts/*.qmd` |
| `docs/blog.html` | `build_blog.py` | `posts/*.qmd` |
| `docs/blog/figures/*` | Quarto + `build_blog.py` | Code in `.qmd` files |
| `docs/cv.html` | `build_cv.py` | `records/cv.md` |

**Partially generated:** `docs/index.html` - The "Latest Posts" section is auto-updated by `build_blog.py`, but the rest of the page is manually edited.

### Source Files

| File | Purpose | Build Command |
|------|---------|---------------|
| `posts/*.qmd` | Blog post sources | `pixi run update-blog` |
| `records/cv.md` | CV data (YAML) | `pixi run update-cv` |

### Manual Files

| File | Purpose |
|------|---------|
| `docs/index.html` | Home page |
| `docs/research.html` | Research page |
| `docs/teaching.html` | Teaching page |
| `docs/software-data.html` | Software page |
| `docs/books/*.html` | Book pages |
| `docs/teaching/*.html` | Course pages |
| `docs/styles.css` | Site styles |
| `docs/footer.html` | Shared footer |
| `docs/images/*` | Static images |
| `docs/pdfs/*` | PDF files |

## Technical Notes

### Blog Build Details

The blog build script (`scripts/build_blog.py`) performs these steps:

1. Find all `.qmd` files in `posts/`
2. For each file:
   - Run `quarto render <file> --to gfm` (executes code, produces `.md`)
   - Copy generated figures to `docs/blog/figures/`
   - Parse YAML frontmatter for title, date, excerpt
   - Clean Quarto artifacts (redundant title/author/date lines)
   - Convert markdown to HTML with site template
   - Delete intermediate `.md` file
3. Clean Quarto cache directories
4. Regenerate blog index page (`docs/blog.html`)
5. Update "Latest Posts" section in `docs/index.html` with the two most recent posts

### CV Build Details

The CV build script (`scripts/build_cv.py`) performs these steps:

1. Parse YAML frontmatter from `records/cv.md`
2. For software entries with GitHub URLs:
   - Check cache (`records/github_cache.json`)
   - If stale (>15 min), fetch from GitHub API
   - Extract version, last commit, stars, etc.
3. Render each CV section to HTML
4. Generate table of contents from h2 headings
5. Write final HTML with site template

### Intermediate Files

These files are generated during builds and should not be committed:

- `posts/*.md` - Intermediate markdown from Quarto (deleted after build)
- `posts/*_files/` - Quarto figure directories (deleted after build)
- `posts/.quarto/` - Quarto cache (deleted after build)
- `posts/_freeze/` - Quarto freeze directory (deleted after build)
- `posts/.jupyter_cache/` - Jupyter cache (deleted after build)

The `posts/.gitignore` is configured to ignore all these files.
