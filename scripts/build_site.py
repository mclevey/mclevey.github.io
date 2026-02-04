#!/usr/bin/env python3
"""
Unified Site Builder

Builds the entire site from content files using Jinja2 templates.

CONTENT SOURCES:
    content/*.md             → docs/*.html (static pages)
    content/books/*.md       → docs/books/*.html (book pages)
    content/teaching/*.md    → docs/teaching/*.html (course pages)
    content/posts/*.qmd      → docs/blog/*.html (blog posts via Quarto)
    records/cv.md            → docs/cv.html (CV from YAML)

TEMPLATES:
    templates/base.html       - Common page structure
    templates/page.html       - Generic content page
    templates/index.html      - Home page with profile
    templates/blog_post.html  - Blog post with syntax highlighting
    templates/blog_index.html - Blog listing
    templates/book.html       - Book page
    templates/course.html     - Course page
    templates/cv.html         - CV with TOC sidebar

USAGE:
    pixi run build           # Build everything
    pixi run build-pages     # Build static pages only
    pixi run build-blog      # Build blog only
    pixi run build-cv        # Build CV only
"""

import re
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

try:
    import yaml
except ImportError:
    print("Error: pyyaml not found. Run: pixi install")
    exit(1)

try:
    import markdown
except ImportError:
    print("Error: markdown not found. Run: pixi install")
    exit(1)

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    print("Error: jinja2 not found. Run: pixi install")
    exit(1)


# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
CONTENT_DIR = BASE_DIR / "content"
POSTS_DIR = CONTENT_DIR / "posts"
RECORDS_DIR = BASE_DIR / "records"
OUTPUT_DIR = BASE_DIR / "docs"

# Initialize Jinja2 environment
env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(['html', 'xml'])
)

# Markdown converter
md_converter = markdown.Markdown(extensions=["fenced_code", "tables", "attr_list"])


# ============================================================================
# UTILITIES
# ============================================================================

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from content."""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1])
            body = parts[2].strip()
            return frontmatter or {}, body
    return {}, content


def get_excerpt(html_content: str, max_length: int = 200) -> str:
    """Extract plain text excerpt from HTML."""
    text = re.sub(r"<[^>]+>", "", html_content)
    text = " ".join(text.split())
    if len(text) > max_length:
        text = text[:max_length].rsplit(" ", 1)[0] + "..."
    return text


# ============================================================================
# PAGE BUILDERS
# ============================================================================

def build_page(content_file: Path, output_file: Path, base_path: str = ""):
    """Build a single page from markdown content."""
    content = content_file.read_text()
    frontmatter, body = parse_frontmatter(content)

    template_name = frontmatter.get("template", "page") + ".html"
    template = env.get_template(template_name)

    # Convert markdown body to HTML (but preserve raw HTML)
    md_converter.reset()
    html_content = md_converter.convert(body)

    html = template.render(
        base_path=base_path,
        content=html_content,
        **frontmatter
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html)
    return frontmatter


def build_static_pages():
    """Build all static pages from content/*.md"""
    print("Building static pages...")

    # Build top-level pages
    for md_file in CONTENT_DIR.glob("*.md"):
        output_name = md_file.stem + ".html"
        output_file = OUTPUT_DIR / output_name
        frontmatter = build_page(md_file, output_file, base_path="")
        print(f"  → {output_file.relative_to(BASE_DIR)}")

    # Build book pages
    books_dir = CONTENT_DIR / "books"
    if books_dir.exists():
        for md_file in books_dir.glob("*.md"):
            output_name = md_file.stem + ".html"
            output_file = OUTPUT_DIR / "books" / output_name
            frontmatter = build_page(md_file, output_file, base_path="../")
            print(f"  → {output_file.relative_to(BASE_DIR)}")

    # Build teaching pages
    teaching_dir = CONTENT_DIR / "teaching"
    if teaching_dir.exists():
        for md_file in teaching_dir.glob("*.md"):
            output_name = md_file.stem + ".html"
            output_file = OUTPUT_DIR / "teaching" / output_name
            frontmatter = build_page(md_file, output_file, base_path="../")
            print(f"  → {output_file.relative_to(BASE_DIR)}")


# ============================================================================
# BLOG BUILDER
# ============================================================================

def clean_quarto_artifacts(body: str, title: str) -> str:
    """Remove Quarto-generated artifacts from markdown."""
    lines = body.split("\n")
    cleaned = []
    skip_next_blank = False
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    for line in lines:
        stripped = line.strip()
        if stripped == f"# {title}":
            skip_next_blank = True
            continue
        if stripped in ["John McLevey", "Invalid Date", "John McLevey Invalid Date"]:
            skip_next_blank = True
            continue
        if date_pattern.match(stripped):
            skip_next_blank = True
            continue
        if skip_next_blank and stripped == "":
            skip_next_blank = False
            continue
        skip_next_blank = False
        cleaned.append(line)

    return "\n".join(cleaned)


def format_code_output(body: str) -> str:
    """Format code output blocks with proper HTML."""
    lines = body.split("\n")
    result = []
    in_code_block = False
    output_buffer = []

    def flush_output():
        if output_buffer:
            result.append('<pre class="code-output">' + "\n".join(output_buffer) + '</pre>')
            output_buffer.clear()

    for line in lines:
        if line.strip().startswith("```"):
            flush_output()
            in_code_block = not in_code_block
            result.append(line)
            continue

        if not in_code_block and line.startswith("    "):
            output_buffer.append(line[4:])
        else:
            flush_output()
            result.append(line)

    flush_output()
    return "\n".join(result)


def render_qmd_to_md(qmd_file: Path) -> Path | None:
    """Render a .qmd file to markdown using Quarto."""
    result = subprocess.run(
        ["quarto", "render", str(qmd_file), "--to", "gfm"],
        capture_output=True,
        text=True,
        cwd=POSTS_DIR
    )

    if result.returncode != 0:
        print(f"    ERROR: Quarto render failed: {result.stderr}")
        return None

    md_file = qmd_file.with_suffix(".md")
    if md_file.exists():
        return md_file

    gfm_file = POSTS_DIR / f"{qmd_file.stem}-gfm.md"
    if gfm_file.exists():
        gfm_file.rename(md_file)
        return md_file

    return None


def copy_figures(slug: str):
    """Copy generated figures to output."""
    figures_src = POSTS_DIR / f"{slug}_files" / "figure-gfm"
    if not figures_src.exists():
        return

    figures_dest = OUTPUT_DIR / "blog" / "figures"
    figures_dest.mkdir(exist_ok=True)

    for fig_file in figures_src.glob("*"):
        dest = figures_dest / fig_file.name
        shutil.copy2(fig_file, dest)
        print(f"    Copied: {fig_file.name}")


def cleanup_post_files(slug: str):
    """Remove intermediate files for a post."""
    md_file = POSTS_DIR / f"{slug}.md"
    if md_file.exists():
        md_file.unlink()

    gfm_file = POSTS_DIR / f"{slug}-gfm.md"
    if gfm_file.exists():
        gfm_file.unlink()

    fig_dir = POSTS_DIR / f"{slug}_files"
    if fig_dir.exists():
        shutil.rmtree(fig_dir)


def cleanup_quarto_cache():
    """Remove Quarto cache directories."""
    for cache_dir in [".quarto", "_freeze", ".jupyter_cache"]:
        cache_path = POSTS_DIR / cache_dir
        if cache_path.exists():
            shutil.rmtree(cache_path)
            print(f"  Removed cache: {cache_dir}/")


def build_blog():
    """Build all blog posts from posts/*.qmd"""
    print("Building blog...")

    qmd_files = sorted(POSTS_DIR.glob("*.qmd"), reverse=True)
    if not qmd_files:
        print("  No .qmd files found")
        return []

    template = env.get_template("blog_post.html")
    posts = []

    for qmd_file in qmd_files:
        slug = qmd_file.stem
        print(f"  Processing: {qmd_file.name}")

        # Render with Quarto
        md_file = render_qmd_to_md(qmd_file)
        if md_file is None:
            continue

        # Copy figures
        copy_figures(slug)

        # Parse content
        content = md_file.read_text()
        frontmatter, body = parse_frontmatter(content)

        title = frontmatter.get("title", slug.replace("-", " ").title())

        # Extract date
        date = frontmatter.get("date")
        if date is None or str(date) == "\\today":
            match = re.match(r"(\d{4}-\d{2}-\d{2})", slug)
            if match:
                date = match.group(1)
            else:
                date = datetime.now().strftime("%Y-%m-%d")
        elif isinstance(date, datetime):
            date = date.strftime("%Y-%m-%d")
        else:
            date = str(date).split("T")[0]

        # Extract author (default to John McLevey)
        author = frontmatter.get("author", "John McLevey")

        # Clean and convert
        body = clean_quarto_artifacts(body, title)
        body = re.sub(rf'{re.escape(slug)}_files/figure-gfm/', 'figures/', body)
        body = format_code_output(body)

        md_converter.reset()
        html_content = md_converter.convert(body)

        # Render template
        html = template.render(
            base_path="../",
            title=title,
            date=date,
            author=author,
            content=html_content,
            active="blog"
        )

        output_file = OUTPUT_DIR / "blog" / f"{slug}.html"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(html)
        print(f"    → docs/blog/{slug}.html")

        posts.append({
            "title": title,
            "date": date,
            "slug": slug,
            "excerpt": frontmatter.get("excerpt", get_excerpt(html_content)),
        })

        # Cleanup
        cleanup_post_files(slug)

    cleanup_quarto_cache()

    # Sort by date
    posts.sort(key=lambda p: p["date"], reverse=True)

    # Build blog index
    index_template = env.get_template("blog_index.html")
    html = index_template.render(
        base_path="",
        posts=posts,
        active="blog"
    )
    (OUTPUT_DIR / "blog.html").write_text(html)
    print(f"  → docs/blog.html")

    return posts


def update_index_with_posts(posts: list):
    """Update index.html with latest posts."""
    if not posts:
        return

    # Re-render index page with posts
    index_content = (CONTENT_DIR / "index.md").read_text()
    frontmatter, body = parse_frontmatter(index_content)

    template = env.get_template("index.html")
    md_converter.reset()
    html_content = md_converter.convert(body)

    html = template.render(
        base_path="",
        content=html_content,
        latest_posts=posts[:2],
        **frontmatter
    )

    (OUTPUT_DIR / "index.html").write_text(html)
    print("  Updated index.html with latest posts")


# ============================================================================
# CV BUILDER (imports from existing build_cv.py)
# ============================================================================

def build_cv():
    """Build CV from records/cv.md - delegates to existing script."""
    print("Building CV...")
    # Import and run the existing CV builder
    import importlib.util
    spec = importlib.util.spec_from_file_location("build_cv", BASE_DIR / "scripts" / "build_cv.py")
    build_cv_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build_cv_module)
    build_cv_module.build_cv()


# ============================================================================
# MAIN
# ============================================================================

def build_all():
    """Build entire site."""
    print("=" * 60)
    print("BUILDING SITE")
    print("=" * 60 + "\n")

    build_static_pages()
    print()

    posts = build_blog()
    print()

    update_index_with_posts(posts)
    print()

    build_cv()
    print()

    print("=" * 60)
    print("BUILD COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "pages":
            build_static_pages()
        elif cmd == "blog":
            posts = build_blog()
            update_index_with_posts(posts)
        elif cmd == "cv":
            build_cv()
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: build_site.py [pages|blog|cv]")
            exit(1)
    else:
        build_all()
