#!/usr/bin/env python3
"""
Blog builder: renders .qmd files with Quarto, then converts markdown to HTML.

Usage:
    python build_blog.py              # Build all posts
    python build_blog.py --render     # Render .qmd files first, then build
    python build_blog.py --clean      # Clean temp files

Workflow:
1. .qmd files in posts/ contain executable code
2. Quarto renders .qmd -> .md with executed outputs
3. This script converts .md -> HTML using the site template
4. Generated figures are copied to docs/blog/figures/

Source files: posts/*.qmd and posts/*.md (hand-written)
Output files: docs/blog/*.html
"""

import argparse
import re
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

try:
    import markdown
except ImportError:
    print("Error: markdown package not found. Run: pixi add markdown")
    exit(1)

try:
    import yaml
except ImportError:
    print("Error: pyyaml package not found. Run: pixi add pyyaml")
    exit(1)


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} – John McLevey</title>
  <link rel="stylesheet" href="../styles.css">
  <!-- Highlight.js themes -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-light.min.css" id="hljs-light">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/nord.min.css" id="hljs-dark" disabled>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/python.min.js"></script>
</head>
<body>
  <header>
    <nav>
      <a href="../index.html" class="nav-home">JM.</a>
      <a href="../cv.html">CV</a>
      <a href="../research.html">Research</a>
      <a href="../teaching.html">Teaching & Supervision</a>
      <a href="../software-data.html">Software & Data</a>
      <a href="../blog.html" class="active">Blog</a>
      <button class="theme-toggle" onclick="toggleTheme()" aria-label="Toggle theme">
        <span class="icon-moon">☽</span>
        <span class="icon-sun">☼</span>
      </button>
    </nav>
  </header>
  <main>
    <div class="post-header">
      <div class="post-date">{date}</div>
      <h1>{title}</h1>
    </div>
    <div class="post-content">
{content}
    </div>
    <a href="../blog.html" class="back-link">← Back to blog</a>
  </main>

  <footer id="site-footer"></footer>
  <script>
    fetch('../footer.html')
      .then(response => response.text())
      .then(html => {{
        document.getElementById('site-footer').innerHTML = html;
      }});
  </script>

  <!-- Lightbox -->
  <div class="lightbox-overlay" id="lightbox">
    <span class="lightbox-close">&times;</span>
    <img src="" alt="" id="lightbox-img">
  </div>

  <script>
    // Initialize highlight.js
    hljs.highlightAll();

    // Theme toggle with highlight.js theme switching
    function updateHljsTheme(theme) {{
      const lightTheme = document.getElementById('hljs-light');
      const darkTheme = document.getElementById('hljs-dark');
      if (theme === 'dark') {{
        lightTheme.disabled = true;
        darkTheme.disabled = false;
      }} else {{
        lightTheme.disabled = false;
        darkTheme.disabled = true;
      }}
    }}

    function toggleTheme() {{
      const html = document.documentElement;
      const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
      updateHljsTheme(next);
    }}

    const saved = localStorage.getItem('theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    if (saved === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
    updateHljsTheme(saved);

    // Lightbox
    const lightbox = document.getElementById('lightbox');
    const lightboxImg = document.getElementById('lightbox-img');

    document.querySelectorAll('.post-content img').forEach(img => {{
      img.addEventListener('click', () => {{
        lightboxImg.src = img.src;
        lightboxImg.alt = img.alt;
        lightbox.classList.add('active');
      }});
    }});

    lightbox.addEventListener('click', () => {{
      lightbox.classList.remove('active');
    }});

    document.addEventListener('keydown', (e) => {{
      if (e.key === 'Escape') lightbox.classList.remove('active');
    }});
  </script>
</body>
</html>
"""

BLOG_INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Blog – John McLevey</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header>
    <nav>
      <a href="index.html" class="nav-home">JM.</a>
      <a href="cv.html">CV</a>
      <a href="research.html">Research</a>
      <a href="teaching.html">Teaching & Supervision</a>
      <a href="software-data.html">Software & Data</a>
      <a href="blog.html" class="active">Blog</a>
      <button class="theme-toggle" onclick="toggleTheme()" aria-label="Toggle theme">
        <span class="icon-moon">☽</span>
        <span class="icon-sun">☼</span>
      </button>
    </nav>
  </header>

  <main>
    <h1>Blog</h1>
    <p class="intro">Notes on methods, tutorials, and updates.</p>

    <div class="cards">
{posts}
    </div>
  </main>

  <footer id="site-footer"></footer>
  <script>
    fetch('footer.html')
      .then(response => response.text())
      .then(html => {{
        document.getElementById('site-footer').innerHTML = html;
      }});
  </script>

  <script>
    function toggleTheme() {{
      const html = document.documentElement;
      const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
    }}
    const saved = localStorage.getItem('theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    if (saved === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
  </script>
</body>
</html>
"""

POST_ENTRY_TEMPLATE = """      <a href="blog/{slug}.html" class="card">
        <div class="meta">{date}</div>
        <h3>{title}</h3>
        <p>{excerpt}</p>
      </a>
"""


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from markdown content."""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1])
            body = parts[2].strip()
            return frontmatter, body
    return {}, content


def get_excerpt(html_content: str, max_length: int = 200) -> str:
    """Extract first paragraph as excerpt."""
    text = re.sub(r"<[^>]+>", "", html_content)
    text = " ".join(text.split())
    if len(text) > max_length:
        text = text[:max_length].rsplit(" ", 1)[0] + "..."
    return text


def clean_quarto_body(body: str, title: str, date: str) -> str:
    """Remove Quarto-generated title/author/date lines from body."""
    lines = body.split("\n")
    cleaned = []
    skip_next_blank = False

    # Date patterns to skip (YYYY-MM-DD format)
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    for i, line in enumerate(lines):
        stripped = line.strip()
        # Skip redundant title (Quarto adds # Title at top)
        if stripped == f"# {title}":
            skip_next_blank = True
            continue
        # Skip author line and "Invalid Date" that Quarto adds
        if stripped in ["Invalid Date", "John McLevey", "John McLevey Invalid Date"]:
            skip_next_blank = True
            continue
        # Skip standalone date lines (Quarto adds these)
        if date_pattern.match(stripped):
            skip_next_blank = True
            continue
        # Skip blank lines after removed content
        if skip_next_blank and stripped == "":
            skip_next_blank = False
            continue
        skip_next_blank = False
        cleaned.append(line)

    return "\n".join(cleaned)


def fix_image_paths(body: str) -> str:
    """Fix image paths for the output location."""
    # Convert ../img/ to ../images/ (source to output path)
    body = re.sub(r'\.\./img/', '../images/', body)
    # Convert relative figure paths from Quarto output
    # e.g., 2026-02-03-nsbm-1_files/figure-gfm/... -> figures/...
    body = re.sub(r'(\S+)_files/figure-gfm/', 'figures/', body)
    return body


def format_code_output(body: str) -> str:
    """Format code output blocks properly - combine consecutive output lines."""
    lines = body.split("\n")
    result = []
    in_code_block = False
    output_buffer = []

    def flush_output():
        """Flush buffered output lines into a single pre block."""
        if output_buffer:
            result.append('<pre class="code-output">' + "\n".join(output_buffer) + '</pre>')
            output_buffer.clear()

    for line in lines:
        # Track code blocks
        if line.strip().startswith("```"):
            flush_output()
            in_code_block = not in_code_block
            result.append(line)
            continue

        # Convert indented output (4 spaces) to output block if not in code block
        if not in_code_block and line.startswith("    "):
            # This is likely code output - buffer it
            output_buffer.append(line[4:])  # Strip the 4-space indent
        else:
            flush_output()
            result.append(line)

    flush_output()  # Don't forget any trailing output
    return "\n".join(result)


def render_qmd_files(posts_dir: Path) -> list[Path]:
    """Render all .qmd files with Quarto and return list of generated .md files."""
    qmd_files = list(posts_dir.glob("*.qmd"))
    if not qmd_files:
        print("No .qmd files found to render")
        return []

    print(f"Rendering {len(qmd_files)} .qmd files with Quarto...")

    # Run quarto render on the posts directory
    result = subprocess.run(
        ["quarto", "render", str(posts_dir), "--to", "gfm"],
        capture_output=True,
        text=True,
        cwd=posts_dir.parent
    )

    if result.returncode != 0:
        print(f"Quarto render failed:\n{result.stderr}")
        return []

    print(result.stdout)

    # Find the generated .md files (same name as .qmd)
    generated = []
    for qmd in qmd_files:
        md_file = qmd.with_suffix(".md")
        if md_file.exists():
            generated.append(md_file)
            print(f"  Generated: {md_file.name}")

    return generated


def copy_figures(posts_dir: Path, output_dir: Path):
    """Copy generated figure directories to output."""
    figures_output = output_dir / "figures"
    figures_output.mkdir(exist_ok=True)

    # Find and copy figure directories
    for fig_dir in posts_dir.glob("*_files/figure-gfm"):
        if fig_dir.is_dir():
            for fig_file in fig_dir.glob("*"):
                dest = figures_output / fig_file.name
                shutil.copy2(fig_file, dest)
                print(f"  Copied figure: {fig_file.name}")


def clean_temp_files(posts_dir: Path):
    """Clean up temporary files generated by Quarto."""
    # Remove -gfm.md files (we use the .md output)
    for gfm_file in posts_dir.glob("*-gfm.md"):
        gfm_file.unlink()
        print(f"  Removed: {gfm_file.name}")

    # Remove figure directories (after copying)
    for fig_dir in posts_dir.glob("*_files"):
        if fig_dir.is_dir():
            shutil.rmtree(fig_dir)
            print(f"  Removed: {fig_dir.name}/")

    # Optionally remove .quarto directory
    quarto_dir = posts_dir / ".quarto"
    if quarto_dir.exists():
        shutil.rmtree(quarto_dir)
        print("  Removed: .quarto/")


def get_source_md_files(posts_dir: Path) -> list[Path]:
    """Get markdown files to process, excluding Quarto intermediates."""
    all_md = list(posts_dir.glob("*.md"))
    # Exclude -gfm.md variants (Quarto duplicates)
    return [f for f in all_md if not f.stem.endswith("-gfm")]


def build_blog(render: bool = False, clean: bool = False):
    base_dir = Path(__file__).resolve().parent.parent
    posts_dir = base_dir / "posts"
    output_dir = base_dir / "docs" / "blog"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Optionally render .qmd files first
    if render:
        render_qmd_files(posts_dir)
        copy_figures(posts_dir, output_dir)

    md = markdown.Markdown(extensions=["fenced_code", "tables", "attr_list"])

    posts = []

    # Get source markdown files (excluding -gfm variants)
    md_files = get_source_md_files(posts_dir)

    for md_file in sorted(md_files, reverse=True):
        # Skip files that have a corresponding .qmd and haven't been rendered
        qmd_file = md_file.with_suffix(".qmd")
        if qmd_file.exists() and not render:
            # If there's a .qmd source, skip the .md unless we just rendered
            print(f"Skipping {md_file.name} (has .qmd source, use --render)")
            continue

        print(f"Processing: {md_file.name}")

        content = md_file.read_text()
        frontmatter, body = parse_frontmatter(content)

        title = frontmatter.get("title", md_file.stem.replace("-", " ").title())

        # Handle date - extract from filename if not in frontmatter or invalid
        date = frontmatter.get("date")
        if date is None or date == "\\today" or str(date) == "\\today":
            # Try to extract from filename (YYYY-MM-DD-title.md)
            match = re.match(r"(\d{4}-\d{2}-\d{2})", md_file.stem)
            if match:
                date = match.group(1)
            else:
                date = datetime.now().strftime("%Y-%m-%d")
        elif isinstance(date, datetime):
            date = date.strftime("%Y-%m-%d")
        else:
            date = str(date)

        # Clean up Quarto-generated artifacts
        body = clean_quarto_body(body, title, date)
        body = fix_image_paths(body)
        body = format_code_output(body)

        md.reset()
        html_content = md.convert(body)

        slug = md_file.stem

        html = TEMPLATE.format(title=title, date=date, content=html_content)

        output_file = output_dir / f"{slug}.html"
        output_file.write_text(html)
        print(f"  → {output_file.relative_to(base_dir)}")

        posts.append(
            {
                "title": title,
                "date": date,
                "slug": slug,
                "excerpt": frontmatter.get("excerpt", get_excerpt(html_content)),
            }
        )

    # Clean temp files if requested
    if clean:
        print("\nCleaning temporary files...")
        clean_temp_files(posts_dir)

    # Sort posts by date
    posts.sort(key=lambda p: p["date"], reverse=True)

    # Generate blog index
    posts_html = "\n".join(POST_ENTRY_TEMPLATE.format(**post) for post in posts)

    blog_index = BLOG_INDEX_TEMPLATE.format(posts=posts_html)
    blog_index_file = base_dir / "docs" / "blog.html"
    blog_index_file.write_text(blog_index)
    print(f"  → {blog_index_file.relative_to(base_dir)}")

    print(f"\nBuilt {len(posts)} posts")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build blog from markdown/qmd files")
    parser.add_argument("--render", action="store_true",
                        help="Render .qmd files with Quarto first")
    parser.add_argument("--clean", action="store_true",
                        help="Clean temporary files after build")
    args = parser.parse_args()

    build_blog(render=args.render, clean=args.clean)
