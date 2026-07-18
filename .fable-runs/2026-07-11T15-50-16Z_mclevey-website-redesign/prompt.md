# Build the John McLevey website redesign

You are the implementation agent. Work directly in the repository sandbox that
contains this prompt. Build the redesigned website, do not merely report on it.

## Objective

Rebuild the site to match the approved design references in `docs-redesign/`,
especially these final page designs:

- `docs-redesign/Home.dc.html`
- `docs-redesign/Research.dc.html`
- `docs-redesign/Teaching.dc.html`
- `docs-redesign/Code and Data.dc.html`
- `docs-redesign/Blog.dc.html`

`docs-redesign/Homepage Options.dc.html` records discarded or exploratory
homepage directions. Treat the five page-specific files above as the source of
truth. Reproduce their visual language and layout faithfully while making the
implementation production-quality and responsive.

## Architecture constraint

Prefer retaining the existing build system: Markdown content, Jinja2 templates,
the Python builder, and static output in `docs/`. Update all templates, styling,
assets, and any small builder details needed to make that system produce the new
site. Change the build architecture only if the existing system genuinely blocks
the design, and explain any such decision in the final response.

Do not replace real content with mock copy from the design references. Preserve
the current content model, book detail pages, course pages, CV, Quarto blog
posts, CNAME, and GitHub Pages output contract. Where the design shows a real
page or asset, wire it to the corresponding local page or asset. Remove `#`
placeholder links when a real local or known external target is available.

## Required implementation quality

- Create shared, maintainable template structure and CSS. Do not paste the
  prototype's inline styles across every page.
- Match the reference palette, typography, spacing, borders, book layouts,
  compact navigation, footer, and restrained interaction style.
- Add a responsive mobile navigation and responsive layouts for home, research,
  teaching, code/data, blog, blog posts, book pages, course pages, and CV.
- Preserve accessible semantic HTML, keyboard navigation, visible focus states,
  descriptive alt text, and sensible contrast.
- Keep page-relative links and asset paths correct at top level and in nested
  `books/`, `teaching/`, and `blog/` output.
- Preserve or improve syntax highlighting, blog images/lightbox behaviour, and
  the CV table of contents where they remain appropriate.
- If you modify Python, use Python 3.11+ type annotations throughout changed
  functions, `pathlib.Path`, clear errors, and Google-style docstrings for new
  utilities. Do not hide failures.
- Do not use em dashes in newly written prose.

## Verification

1. Inspect the current repo and all five final design reference files before
   editing.
2. Run the existing full build, preferably `pixi run build`.
3. Fix all build failures and inspect the generated `docs/` tree.
4. Check internal HTML links and referenced local assets across generated pages.
5. Verify the output at desktop and narrow/mobile widths. If browser tooling is
   unavailable, perform rigorous static responsive checks and state that limit.
6. Leave the sandbox with the complete implementation and generated `docs/`
   output ready to copy back to the source Mac.

Do not commit, push, publish, or alter any remote repository. Do not edit
`docs-redesign/`; it is reference input. Do not stop after a plan. Implement,
build, validate, and then give a concise final summary with exact files changed,
commands run, outcomes, and any remaining limitations.
