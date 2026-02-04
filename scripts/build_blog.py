#!/usr/bin/env python3
"""
Blog Builder: Renders Quarto notebooks to HTML for the site.

WORKFLOW:
    1. Source files: posts/*.qmd (Quarto notebooks with executable code)
    2. Quarto renders: .qmd → .md (markdown with executed code outputs)
    3. This script converts: .md → HTML (using site template)
    4. Cleanup: intermediate .md files are removed

USAGE:
    pixi run update-blog     # Full build: render .qmd files and convert to HTML

    # Or run directly:
    python scripts/build_blog.py

OUTPUT:
    docs/blog/*.html         # Individual post pages
    docs/blog.html           # Blog index page
    docs/blog/figures/       # Any generated figures from code execution
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


# HTML template for individual blog posts
POST_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} – John McLevey</title>
  <link rel="stylesheet" href="../styles.css">
  <!-- Highlight.js for syntax highlighting -->
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

  <!-- Lightbox for images -->
  <div class="lightbox-overlay" id="lightbox">
    <span class="lightbox-close">&times;</span>
    <img src="" alt="" id="lightbox-img">
  </div>

  <script>
    hljs.highlightAll();

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

# HTML template for blog index page
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

# Template for each post entry on the blog index
POST_CARD_TEMPLATE = """      <a href="blog/{slug}.html" class="card">
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
    """Extract plain text excerpt from HTML content."""
    text = re.sub(r"<[^>]+>", "", html_content)
    text = " ".join(text.split())
    if len(text) > max_length:
        text = text[:max_length].rsplit(" ", 1)[0] + "..."
    return text


def clean_quarto_artifacts(body: str, title: str) -> str:
    """
    Remove Quarto-generated artifacts from the markdown body.

    Quarto adds redundant title, author, and date lines at the top of the
    rendered markdown which we don't need (we get these from frontmatter).
    """
    lines = body.split("\n")
    cleaned = []
    skip_next_blank = False
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    for line in lines:
        stripped = line.strip()

        # Skip redundant title (Quarto adds "# Title" at top)
        if stripped == f"# {title}":
            skip_next_blank = True
            continue

        # Skip author line
        if stripped in ["John McLevey", "Invalid Date", "John McLevey Invalid Date"]:
            skip_next_blank = True
            continue

        # Skip standalone date lines
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


def format_code_output(body: str) -> str:
    """
    Format code output blocks with proper HTML.

    Quarto renders code output as 4-space indented text. We wrap these
    in <pre class="code-output"> blocks for styling.
    """
    lines = body.split("\n")
    result = []
    in_code_block = False
    output_buffer = []

    def flush_output():
        if output_buffer:
            result.append('<pre class="code-output">' + "\n".join(output_buffer) + '</pre>')
            output_buffer.clear()

    for line in lines:
        # Track fenced code blocks
        if line.strip().startswith("```"):
            flush_output()
            in_code_block = not in_code_block
            result.append(line)
            continue

        # 4-space indented lines outside code blocks are output
        if not in_code_block and line.startswith("    "):
            output_buffer.append(line[4:])  # Strip the 4-space indent
        else:
            flush_output()
            result.append(line)

    flush_output()
    return "\n".join(result)


def fix_image_paths(body: str, slug: str) -> str:
    """
    Fix image paths for the output location.

    - Converts relative figure paths from Quarto (slug_files/figure-gfm/...)
      to the output location (figures/...)
    """
    # Fix Quarto figure paths: slug_files/figure-gfm/image.png -> figures/image.png
    body = re.sub(rf'{re.escape(slug)}_files/figure-gfm/', 'figures/', body)
    return body


def render_qmd_to_md(qmd_file: Path, posts_dir: Path) -> Path | None:
    """
    Render a single .qmd file to markdown using Quarto.

    Returns the path to the generated .md file, or None if rendering failed.
    """
    print(f"  Rendering: {qmd_file.name}")

    result = subprocess.run(
        ["quarto", "render", str(qmd_file), "--to", "gfm"],
        capture_output=True,
        text=True,
        cwd=posts_dir
    )

    if result.returncode != 0:
        print(f"    ERROR: Quarto render failed")
        print(f"    {result.stderr}")
        return None

    # Quarto outputs to same name with .md extension
    md_file = qmd_file.with_suffix(".md")
    if md_file.exists():
        return md_file

    # Sometimes Quarto adds -gfm suffix, check for that
    gfm_file = posts_dir / f"{qmd_file.stem}-gfm.md"
    if gfm_file.exists():
        # Rename to expected name
        gfm_file.rename(md_file)
        return md_file

    print(f"    ERROR: Expected output {md_file.name} not found")
    return None


def copy_figures(posts_dir: Path, output_dir: Path, slug: str):
    """Copy generated figures to the output directory."""
    figures_src = posts_dir / f"{slug}_files" / "figure-gfm"
    if not figures_src.exists():
        return

    figures_dest = output_dir / "figures"
    figures_dest.mkdir(exist_ok=True)

    for fig_file in figures_src.glob("*"):
        dest = figures_dest / fig_file.name
        shutil.copy2(fig_file, dest)
        print(f"    Copied figure: {fig_file.name}")


def cleanup_intermediate_files(posts_dir: Path, slug: str):
    """Remove intermediate files generated during build."""
    # Remove the generated .md file
    md_file = posts_dir / f"{slug}.md"
    if md_file.exists():
        md_file.unlink()

    # Remove any -gfm.md variant
    gfm_file = posts_dir / f"{slug}-gfm.md"
    if gfm_file.exists():
        gfm_file.unlink()

    # Remove figure directory
    fig_dir = posts_dir / f"{slug}_files"
    if fig_dir.exists():
        shutil.rmtree(fig_dir)


def cleanup_quarto_cache(posts_dir: Path):
    """Remove Quarto cache directories."""
    for cache_dir in [".quarto", "_freeze", ".jupyter_cache"]:
        cache_path = posts_dir / cache_dir
        if cache_path.exists():
            shutil.rmtree(cache_path)
            print(f"  Removed cache: {cache_dir}/")


def update_index_latest_posts(base_dir: Path, posts: list):
    """
    Update the 'Latest Posts' section on the index page with the two most recent posts.
    """
    index_file = base_dir / "docs" / "index.html"
    if not index_file.exists():
        print("  Warning: index.html not found, skipping latest posts update")
        return

    content = index_file.read_text()

    # Find and replace the Latest Posts section
    # Pattern: from <h2>Latest Posts</h2> through the closing </div> of the cards
    pattern = r'(<h2>Latest Posts</h2>\s*<div class="cards">).*?(</div>\s*</main>)'

    if not re.search(pattern, content, re.DOTALL):
        print("  Warning: Could not find Latest Posts section in index.html")
        return

    # Build the new cards HTML (top 2 posts)
    latest_posts = posts[:2]
    cards_html = "\n".join(
        f'''      <a href="blog/{post['slug']}.html" class="card">
        <div class="meta">{post['date']}</div>
        <h3>{post['title']}</h3>
        <p>{post['excerpt']}</p>
      </a>'''
        for post in latest_posts
    )

    replacement = f'\\1\n{cards_html}\n    \\2'
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    index_file.write_text(new_content)
    print("Updated index.html with latest posts")


def build_blog():
    """
    Main build function.

    1. Find all .qmd files in posts/
    2. Render each to markdown with Quarto (executes code)
    3. Convert markdown to HTML with site template
    4. Clean up intermediate files
    5. Generate blog index
    6. Update index.html with latest posts
    """
    base_dir = Path(__file__).resolve().parent.parent
    posts_dir = base_dir / "posts"
    output_dir = base_dir / "docs" / "blog"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all .qmd source files
    qmd_files = sorted(posts_dir.glob("*.qmd"), reverse=True)

    if not qmd_files:
        print("No .qmd files found in posts/")
        return

    print(f"Found {len(qmd_files)} .qmd files\n")

    # Markdown converter
    md_converter = markdown.Markdown(extensions=["fenced_code", "tables", "attr_list"])

    posts = []

    for qmd_file in qmd_files:
        slug = qmd_file.stem
        print(f"Processing: {qmd_file.name}")

        # Step 1: Render .qmd to .md with Quarto
        md_file = render_qmd_to_md(qmd_file, posts_dir)
        if md_file is None:
            print(f"  Skipping due to render error\n")
            continue

        # Step 2: Copy any generated figures
        copy_figures(posts_dir, output_dir, slug)

        # Step 3: Read and parse the rendered markdown
        content = md_file.read_text()
        frontmatter, body = parse_frontmatter(content)

        title = frontmatter.get("title", slug.replace("-", " ").title())

        # Extract date from frontmatter or filename
        date = frontmatter.get("date")
        if date is None or str(date) == "\\today":
            # Try to extract from filename (YYYY-MM-DD-title.qmd)
            match = re.match(r"(\d{4}-\d{2}-\d{2})", slug)
            if match:
                date = match.group(1)
            else:
                date = datetime.now().strftime("%Y-%m-%d")
        elif isinstance(date, datetime):
            date = date.strftime("%Y-%m-%d")
        else:
            # Handle ISO format with timezone
            date = str(date).split("T")[0]

        # Step 4: Clean up and convert to HTML
        body = clean_quarto_artifacts(body, title)
        body = fix_image_paths(body, slug)
        body = format_code_output(body)

        md_converter.reset()
        html_content = md_converter.convert(body)

        # Step 5: Apply template and write HTML
        html = POST_TEMPLATE.format(title=title, date=date, content=html_content)

        output_file = output_dir / f"{slug}.html"
        output_file.write_text(html)
        print(f"  → docs/blog/{slug}.html")

        # Collect post metadata for index
        posts.append({
            "title": title,
            "date": date,
            "slug": slug,
            "excerpt": frontmatter.get("excerpt", get_excerpt(html_content)),
        })

        # Step 6: Clean up intermediate files
        cleanup_intermediate_files(posts_dir, slug)
        print()

    # Clean up Quarto cache
    cleanup_quarto_cache(posts_dir)

    # Generate blog index page
    posts.sort(key=lambda p: p["date"], reverse=True)
    posts_html = "\n".join(POST_CARD_TEMPLATE.format(**post) for post in posts)

    blog_index = BLOG_INDEX_TEMPLATE.format(posts=posts_html)
    blog_index_file = base_dir / "docs" / "blog.html"
    blog_index_file.write_text(blog_index)
    print(f"Generated blog index: docs/blog.html")

    # Update index.html with latest posts
    update_index_latest_posts(base_dir, posts)

    print(f"\nBuilt {len(posts)} posts successfully")


if __name__ == "__main__":
    build_blog()
