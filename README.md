# johnmclevey.com

Personal website served via GitHub Pages from the `docs/` directory.

## Prerequisites

- [Pixi](https://pixi.sh) for Python environment management and easily running common commands (e.g., `pixi run blog-update`)
- Run `pixi install` to set up dependencies

## Site Structure

```
.
├── docs/           # Built site (served by GitHub Pages)
│   ├── blog/       # Generated blog post HTML
│   ├── books/      # Book pages (manual HTML)
│   ├── images/     # All images (profile, book covers, blog images)
│   ├── pdfs/       # PDF files (cv.pdf, publications, etc.)
│   ├── teaching/   # Teaching materials (e.g., course and workshop pages) (manual HTML)
│   └── *.html      # Main site pages
├── posts/          # Blog post sources (Markdown)
├── records/        # CV data source
│   └── cv.md       # CV content in YAML frontmatter
└── scripts/        # Build scripts
    ├── build_blog.py
    └── build_cv.py
```

## Updating Content

### CV Updates

The CV is generated from `records/cv.md`. This file uses YAML frontmatter to store all CV data.

1. **Edit the source:** Open `records/cv.md` and update the YAML frontmatter
2. **Rebuild:** Run `pixi run update-cv`
3. **Preview:** Run `pixi run preview` and open http://localhost:8080/cv.html
4. **Update PDF:** Replace `docs/pdfs/cv.pdf` with an updated version

Example CV entry in `records/cv.md`:

```yaml
---
name: John McLevey (he/him)
email: john.mclevey@uwaterloo.ca

education:
  - year: 2013
    subject: PhD, Sociology
    institute: McMaster University
    city: Hamilton, ON, Canada

articles:
  - year: 2022
    authors: John McLevey, Tyler Crick, Pierson Browne
    title: "Article Title Here"
    journal: Canadian Review of Sociology
    volume: 59
    issue: 2
    pages: 228-250
---
```

### Blog Posts

Blog posts are Markdown files in `posts/` with YAML frontmatter.

1. **Create a new post:** Add a file named `YYYY-MM-DD-slug.md` in `posts/`
2. **Add frontmatter:**

   ```yaml
   ---
   title: Your Post Title
   date: 2024-12-01
   excerpt: A brief description for the blog index.
   ---
   Your markdown content here...
   ```

3. **Rebuild:** Run `pixi run update-blog`
4. **Preview:** Run `pixi run preview` and open http://localhost:8080/blog.html

Images for posts should go in `docs/images/` and be referenced as `../images/image.png` in your markdown.

### Static Pages

Pages like `index.html`, `research.html`, `teaching.html`, etc. are edited directly in `docs/`. These are not auto-generated.

To edit:

1. Open the file in `docs/`
2. Make changes
3. Preview with `pixi run preview`

### Book Pages

Book pages in `docs/books/` are manual HTML files. Edit them directly.

## Pixi Commands

| Command                | Description                                 |
| ---------------------- | ------------------------------------------- |
| `pixi run preview`     | Start local server at http://localhost:8080 |
| `pixi run update-cv`   | Rebuild CV from `records/cv.md`             |
| `pixi run update-blog` | Rebuild blog from `posts/*.md`              |

## Deployment

The site deploys automatically when you push to the `master` branch. GitHub Pages serves the `docs/` directory.

```bash
git add .
git commit -m "Update site"
git push
```

The custom domain `www.johnmclevey.com` is configured via `docs/CNAME`.

## File Reference

| File               | Purpose         | How to Update                        |
| ------------------ | --------------- | ------------------------------------ |
| `records/cv.md`    | CV data         | Edit YAML, run `update-cv`           |
| `posts/*.md`       | Blog posts      | Edit/add Markdown, run `update-blog` |
| `docs/pdfs/cv.pdf` | Downloadable CV | Replace file manually                |
| `docs/*.html`      | Static pages    | Edit directly                        |
| `docs/styles.css`  | Site styles     | Edit directly                        |
| `docs/footer.html` | Shared footer   | Edit directly                        |
