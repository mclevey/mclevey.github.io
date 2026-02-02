#!/usr/bin/env python3
"""
Simple blog builder: converts markdown files to HTML using the site template.

Usage:
    python build_blog.py

Reads markdown files from posts/ and outputs HTML to docs/blog/.
Each markdown file should have YAML frontmatter with title and date.
"""

import re
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
</head>
<body>
  <header>
    <nav>
      <a href="../index.html" class="nav-home">JM.</a>
      <a href="../research.html">Research</a>
      <a href="../teaching.html">Teaching</a>
      <a href="../supervision.html">Supervision</a>
      <a href="../software.html">Software</a>
      <a href="../data.html">Data</a>
      <a href="../blog.html" class="active">Blog</a>
      <a href="../cv.html">CV</a>
      <button class="theme-toggle" onclick="toggleTheme()" aria-label="Toggle theme">◐</button>
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
    // Theme toggle
    function toggleTheme() {{
      const html = document.documentElement;
      const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
    }}
    const saved = localStorage.getItem('theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    if (saved === 'dark') document.documentElement.setAttribute('data-theme', 'dark');

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
      <a href="research.html">Research</a>
      <a href="teaching.html">Teaching</a>
      <a href="supervision.html">Supervision</a>
      <a href="software.html">Software</a>
      <a href="data.html">Data</a>
      <a href="blog.html" class="active">Blog</a>
      <a href="cv.html">CV</a>
      <button class="theme-toggle" onclick="toggleTheme()" aria-label="Toggle theme">◐</button>
    </nav>
  </header>

  <main>
    <h1>Blog</h1>
    <p class="intro">Notes on methods, tutorials, and updates.</p>

    <div class="posts">
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

POST_ENTRY_TEMPLATE = """      <article class="post">
        <div class="post-date">{date}</div>
        <a href="blog/{slug}.html" class="post-title">{title}</a>
        <p class="post-excerpt">{excerpt}</p>
      </article>
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


def build_blog():
    base_dir = Path(__file__).parent.parent
    posts_dir = base_dir / "posts"
    output_dir = base_dir / "docs" / "blog"

    output_dir.mkdir(parents=True, exist_ok=True)

    md = markdown.Markdown(extensions=["fenced_code", "tables"])

    posts = []

    for md_file in sorted(posts_dir.glob("*.md"), reverse=True):
        print(f"Processing: {md_file.name}")

        content = md_file.read_text()
        frontmatter, body = parse_frontmatter(content)

        title = frontmatter.get("title", md_file.stem.replace("-", " ").title())
        date = frontmatter.get("date", datetime.now().strftime("%Y-%m-%d"))
        if isinstance(date, datetime):
            date = date.strftime("%Y-%m-%d")

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

    posts.sort(key=lambda p: p["date"], reverse=True)

    posts_html = "\n".join(POST_ENTRY_TEMPLATE.format(**post) for post in posts)

    blog_index = BLOG_INDEX_TEMPLATE.format(posts=posts_html)
    blog_index_file = base_dir / "docs" / "blog.html"
    blog_index_file.write_text(blog_index)
    print(f"  → {blog_index_file.relative_to(base_dir)}")

    print(f"\nBuilt {len(posts)} posts")


if __name__ == "__main__":
    build_blog()
