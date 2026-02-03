#!/usr/bin/env python3
"""
CV builder: converts YAML metadata from cv.md to HTML for the website.

Usage:
    python build_cv.py

Reads cv.md and outputs site/cv.html.
"""

import re
import urllib.request
import urllib.error
import json
import os
from pathlib import Path
from datetime import datetime, timezone

LEADING_WS = "&nbsp;&nbsp;&nbsp;&nbsp;"

# Global for tracking GitHub fetch statistics
_github_stats = {"fresh": 0, "cached": 0}

# Global for tracking TOC entries
_toc_entries = []


def slugify(text):
    """Convert heading text to a URL-friendly ID."""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Convert to lowercase
    text = text.lower()
    # Replace spaces and non-alphanumeric chars with hyphens
    text = re.sub(r"[^a-z0-9]+", "-", text)
    # Remove leading/trailing hyphens
    text = text.strip("-")
    return text


def add_heading_ids(html_content):
    """Add IDs to h2 and h3 tags and track them for TOC."""
    global _toc_entries
    _toc_entries = []

    def replace_heading(match):
        tag = match.group(1)  # h2 or h3
        content = match.group(2)
        slug = slugify(content)

        # Make slugs unique if needed
        base_slug = slug
        counter = 1
        existing_slugs = [e["id"] for e in _toc_entries]
        while slug in existing_slugs:
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Track for TOC
        level = int(tag[1])  # 2 or 3
        _toc_entries.append(
            {
                "id": slug,
                "text": re.sub(r"<[^>]+>", "", content),  # Strip HTML for TOC text
                "level": level,
            }
        )

        return f'<{tag} id="{slug}">{content}</{tag}>'

    # Match h2 and h3 tags
    pattern = r"<(h[23])>([^<]+)</\1>"
    return re.sub(pattern, replace_heading, html_content)


def generate_toc_html():
    """Generate the table of contents HTML from tracked headings."""
    if not _toc_entries:
        return ""

    toc_items = []
    for entry in _toc_entries:
        level_class = f"toc-h{entry['level']}"
        toc_items.append(
            f'<li class="{level_class}">'
            f'<a href="#{entry["id"]}">{entry["text"]}</a>'
            f"</li>"
        )

    return f"""<aside class="toc-sidebar">
    <div class="toc-title">On this page</div>
    <nav>
        <ul>
{chr(10).join("            " + item for item in toc_items)}
        </ul>
    </nav>
</aside>"""


# Cache file path
CACHE_FILE = Path(__file__).resolve().parent.parent / "records" / "github_cache.json"

# Default cache max age in minutes
CACHE_MAX_AGE_MINUTES = 15

# Show placeholder text (XX.XX, XXXXXXX) when data is missing
# Set to True to debug/identify missing data
SHOW_MISSING_SOURCE_DATA = False


# GitHub API headers (with optional token for higher rate limits)
def get_github_headers():
    """Get headers for GitHub API requests, including auth token if available."""
    headers = {"User-Agent": "CV-Builder"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def format_date_long(date_str):
    """Format YYYY-MM-DD date string as 'Feb 3, 2026' (no leading zero)."""
    if not date_str or date_str == "XXXX-XX-XX":
        return date_str
    try:
        dt = datetime.fromisoformat(date_str)
        return f"{dt.strftime('%b')} {dt.day}, {dt.year}"
    except ValueError:
        return date_str


def load_github_cache():
    """Load cache file, return empty dict if doesn't exist."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"  ⚠ Warning: Could not load cache file: {e}")
    return {}


def save_github_cache(cache):
    """Save cache to file with pretty formatting."""
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2, sort_keys=True)
    except IOError as e:
        print(f"  ⚠ Warning: Could not save cache file: {e}")


def is_cache_fresh(cache_entry, max_age_minutes=CACHE_MAX_AGE_MINUTES):
    """Check if cache entry is fresh (within max_age_minutes)."""
    if not cache_entry or "last_fetched" not in cache_entry:
        return False, 0

    try:
        last_fetched = datetime.fromisoformat(
            cache_entry["last_fetched"].replace("Z", "+00:00")
        )
        now = datetime.now(timezone.utc)
        age_minutes = (now - last_fetched).total_seconds() / 60
        return age_minutes <= max_age_minutes, age_minutes
    except (ValueError, KeyError):
        return False, 0


def check_rate_limit():
    """Check GitHub API rate limit status. Returns (remaining, limit) or None on error."""
    try:
        url = "https://api.github.com/rate_limit"
        req = urllib.request.Request(url, headers=get_github_headers())
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            core = data.get("resources", {}).get("core", {})
            return core.get("remaining", 0), core.get("limit", 60)
    except Exception:
        return None, None


def make_github_request(url):
    """
    Make a GitHub API request with proper error handling.
    Returns (data, headers, error_type) where error_type is None on success,
    'rate_limit' if rate limited, 'not_found' for 404, or 'error' for other errors.
    """
    try:
        req = urllib.request.Request(url, headers=get_github_headers())
        with urllib.request.urlopen(req, timeout=10) as response:
            headers = dict(response.headers)
            data = json.loads(response.read().decode())
            return data, headers, None
    except urllib.error.HTTPError as e:
        if e.code == 403:
            # Check if rate limited
            body = e.read().decode() if e.fp else ""
            if "rate limit" in body.lower():
                return None, None, "rate_limit"
        elif e.code == 404:
            return None, None, "not_found"
        return None, None, "error"
    except Exception:
        return None, None, "error"


def fetch_repo_info(owner, repo):
    """Fetch basic repository info from /repos endpoint."""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    data, headers, error = make_github_request(url)

    if error:
        return None, error

    return {
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "open_issues": data.get("open_issues_count", 0),
        "description": data.get("description", ""),
        "topics": data.get("topics", []),
        "license_spdx": (data.get("license") or {}).get("spdx_id", ""),
        "created_at": (data.get("created_at") or "")[:10],  # Just the date part
        "updated_at": (data.get("updated_at") or "")[:10],
    }, None


def fetch_version_info(owner, repo):
    """Fetch version from releases or tags."""
    # Try releases first
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    data, headers, error = make_github_request(url)

    if not error and data:
        return data.get("tag_name", ""), None

    if error == "rate_limit":
        return None, "rate_limit"

    # Try tags as fallback
    url = f"https://api.github.com/repos/{owner}/{repo}/tags"
    data, headers, error = make_github_request(url)

    if not error and data and len(data) > 0:
        return data[0].get("name", ""), None

    return "", error


def fetch_commits_info(owner, repo):
    """Fetch commit info: latest commit and total count."""
    result = {
        "last_commit_date": "",
        "last_commit_sha": "",
        "first_commit_date": "",
        "total_commits": 0,
    }

    # Fetch latest commit
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=1"
    data, headers, error = make_github_request(url)

    if error == "rate_limit":
        return None, "rate_limit"

    if not error and data and len(data) > 0:
        commit = data[0]
        result["last_commit_sha"] = commit["sha"][:7]
        date_str = commit["commit"]["committer"]["date"]
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            result["last_commit_date"] = dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

        # Try to get total commit count from Link header
        if headers:
            link = headers.get("Link", "")
            # Parse the last page number from Link header
            # Format: <url>; rel="last"
            import re as re_module

            match = re_module.search(r'page=(\d+)>; rel="last"', link)
            if match:
                result["total_commits"] = int(match.group(1))
            else:
                # If no pagination, it's just 1 commit
                result["total_commits"] = 1

    # Try to get first commit (oldest)
    # This requires getting the last page of commits
    if result["total_commits"] > 1:
        last_page = result["total_commits"]
        url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=1&page={last_page}"
        data, _, error = make_github_request(url)
        if not error and data and len(data) > 0:
            commit = data[0]
            date_str = commit["commit"]["committer"]["date"]
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                result["first_commit_date"] = dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

    return result, None


def fetch_contributors(owner, repo):
    """Fetch contributor list."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contributors?per_page=100"
    data, headers, error = make_github_request(url)

    if error == "rate_limit":
        return None, "rate_limit"

    if not error and data:
        contributors = [c.get("login", "") for c in data if c.get("login")]
        return {
            "contributors": contributors,
            "contributor_count": len(contributors),
        }, None

    return {"contributors": [], "contributor_count": 0}, None


def fetch_github_info(github_url, yaml_data=None, force_refresh=False):
    """
    Fetch version and commit info from GitHub API with caching.
    Falls back to cached data, then YAML data, then to placeholders.

    Returns dict with:
    - version, last_commit_date, last_commit_sha (basic info)
    - first_commit_date, total_commits (commit history)
    - contributors, contributor_count (team info)
    - stars, forks, open_issues (popularity)
    - description, topics, license_spdx (metadata)
    - created_at, updated_at (dates)
    - from_cache, cache_age_minutes (cache status)
    """
    global _github_stats

    if yaml_data is None:
        yaml_data = {}

    # Default result with placeholders
    result = {
        "version": yaml_data.get("version", "XX.XX"),
        "last_commit_date": yaml_data.get("last_commit", "XXXX-XX-XX"),
        "last_commit_sha": yaml_data.get("commit_id", "XXXXXXX"),
        "first_commit_date": "",
        "total_commits": 0,
        "contributors": [],
        "contributor_count": 0,
        "open_issues": 0,
        "stars": 0,
        "forks": 0,
        "description": yaml_data.get("description", ""),
        "topics": [],
        "license_spdx": "",
        "created_at": "",
        "updated_at": "",
        "from_cache": False,
        "cache_age_minutes": 0,
    }

    if not github_url:
        print(f"    ⚠ No GitHub URL provided")
        return result

    # Parse owner/repo from GitHub URL
    github_url = github_url.strip().rstrip("/")
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?$", github_url)
    if not match:
        print(f"    ⚠ Could not parse GitHub URL: {github_url}")
        return result

    owner, repo = match.groups()
    cache_key = f"{owner}/{repo}"

    # Load cache
    cache = load_github_cache()
    cached_entry = cache.get(cache_key, {})

    # Check if we should use cache
    is_fresh, age_minutes = is_cache_fresh(cached_entry)

    # Check for force-api-call flag in YAML
    if yaml_data.get("force-api-call"):
        force_refresh = True

    if is_fresh and not force_refresh:
        # Use cached data
        print(f"    ✓ Using cached data ({age_minutes:.0f} min old)")
        result.update(
            {
                "version": cached_entry.get("version", result["version"]),
                "last_commit_date": cached_entry.get(
                    "last_commit_date", result["last_commit_date"]
                ),
                "last_commit_sha": cached_entry.get(
                    "last_commit_sha", result["last_commit_sha"]
                ),
                "first_commit_date": cached_entry.get("first_commit_date", ""),
                "total_commits": cached_entry.get("total_commits", 0),
                "contributors": cached_entry.get("contributors", []),
                "contributor_count": cached_entry.get("contributor_count", 0),
                "open_issues": cached_entry.get("open_issues", 0),
                "stars": cached_entry.get("stars", 0),
                "forks": cached_entry.get("forks", 0),
                "description": cached_entry.get("description", ""),
                "topics": cached_entry.get("topics", []),
                "license_spdx": cached_entry.get("license_spdx", ""),
                "created_at": cached_entry.get("created_at", ""),
                "updated_at": cached_entry.get("updated_at", ""),
                "from_cache": True,
                "cache_age_minutes": age_minutes,
            }
        )
        _github_stats["cached"] += 1
        return result

    # Fetch fresh data
    print(f"    → Fetching fresh data from API...")
    rate_limited = False
    new_data = {"last_fetched": datetime.now(timezone.utc).isoformat()}

    # Fetch repo info
    repo_info, error = fetch_repo_info(owner, repo)
    if error == "rate_limit":
        rate_limited = True
        print(f"    ⚠ Rate limited")
    elif repo_info:
        new_data.update(repo_info)
        result.update(repo_info)

    # Fetch version
    if not rate_limited:
        version, error = fetch_version_info(owner, repo)
        if error == "rate_limit":
            rate_limited = True
            print(f"    ⚠ Rate limited")
        elif version:
            new_data["version"] = version
            result["version"] = version

    # Fetch commits info
    if not rate_limited:
        commits_info, error = fetch_commits_info(owner, repo)
        if error == "rate_limit":
            rate_limited = True
            print(f"    ⚠ Rate limited")
        elif commits_info:
            new_data.update(commits_info)
            result.update(commits_info)

    # Fetch contributors
    if not rate_limited:
        contrib_info, error = fetch_contributors(owner, repo)
        if error == "rate_limit":
            rate_limited = True
            print(f"    ⚠ Rate limited")
        elif contrib_info:
            new_data.update(contrib_info)
            result.update(contrib_info)

    # Handle rate limiting: fall back to cache
    if rate_limited and cached_entry:
        print(f"    ⚠ Rate limited - using cached data as fallback")
        result.update(
            {
                "version": cached_entry.get("version", result["version"]),
                "last_commit_date": cached_entry.get(
                    "last_commit_date", result["last_commit_date"]
                ),
                "last_commit_sha": cached_entry.get(
                    "last_commit_sha", result["last_commit_sha"]
                ),
                "first_commit_date": cached_entry.get("first_commit_date", ""),
                "total_commits": cached_entry.get("total_commits", 0),
                "contributors": cached_entry.get("contributors", []),
                "contributor_count": cached_entry.get("contributor_count", 0),
                "open_issues": cached_entry.get("open_issues", 0),
                "stars": cached_entry.get("stars", 0),
                "forks": cached_entry.get("forks", 0),
                "description": cached_entry.get("description", ""),
                "topics": cached_entry.get("topics", []),
                "license_spdx": cached_entry.get("license_spdx", ""),
                "created_at": cached_entry.get("created_at", ""),
                "updated_at": cached_entry.get("updated_at", ""),
                "from_cache": True,
                "cache_age_minutes": age_minutes if cached_entry else 0,
            }
        )
        _github_stats["cached"] += 1
        return result

    # Save to cache if we got any new data
    if not rate_limited and new_data.get("last_fetched"):
        cache[cache_key] = new_data
        save_github_cache(cache)
        _github_stats["fresh"] += 1

    result["from_cache"] = False
    result["cache_age_minutes"] = 0

    return result


def md_to_html(text):
    """Convert common markdown syntax to HTML."""
    if not text:
        return ""
    text = str(text)
    # Convert markdown links [text](url) to <a href="url">text</a>
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    # Convert inline code `code` to <code>code</code>
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def md_links_to_html(text):
    """Legacy wrapper - use md_to_html instead."""
    return md_to_html(text)


try:
    import yaml
except ImportError:
    print("Error: pyyaml package not found. Run: pixi add pyyaml")
    exit(1)


def parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from markdown content."""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return yaml.safe_load(parts[1])
    return {}


def clean_text(text: str) -> str:
    """Clean LaTeX and special formatting from text, convert markdown to HTML."""
    if not text:
        return ""
    text = str(text)
    # Remove LaTeX newlines and formatting
    text = re.sub(r"\\newline", "", text)
    text = re.sub(r"\\footnotesize", "", text)
    text = re.sub(r"\\vspace\{[^}]*\}", "", text)
    text = re.sub(r"\\ind\s*", "", text)
    # Handle superscripts like 21^st^
    text = re.sub(r"\^(\w+)\^", r"<sup>\1</sup>", text)
    # Handle bold marked with double asterisks (must come before italics)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    # Handle italics marked with single asterisks
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    # Convert markdown syntax to HTML (links, inline code)
    text = md_to_html(text)
    return text.strip()


def format_pages(pages):
    """Format page numbers."""
    if not pages:
        return ""
    return f": {pages}"


def format_volume_issue(volume, issue):
    """Format volume and issue."""
    if not volume:
        return ""
    if issue:
        return f" {volume}({issue})"
    return f" {volume}"


def build_cv():
    base_dir = Path(__file__).resolve().parent.parent
    cv_file = base_dir / "records" / "cv.md"
    output_file = base_dir / "docs" / "cv.html"

    print(f"Reading: {cv_file}")
    content = cv_file.read_text()
    data = parse_frontmatter(content)

    # Build HTML sections
    sections = []

    # Contact Info
    name = clean_text(data.get("name", ""))
    # Clean up the name further
    name = re.sub(r"\s+", " ", name).strip()
    if "Dr." in name:
        name = name.replace("Dr. ", "")
    # sections.append(f"<h1>{name}</h1>")

    address = data.get("address", [])
    address = "<br>".join(address)
    email = data.get("email", "")
    phone = data.get("phone", "")
    urls = data.get("urls", [])
    urls = "<br>".join(urls)

    contact_html = "<h2>Contact Information</h2>\n"
    if len(address) > 0:
        contact_html += f"<p>{address}</p>\n"

    contact_html += "<p>\n"
    if len(email) > 0:
        contact_html += f'<a href="mailto:{email}">{email}</a>\n'
    if len(phone) > 0:
        contact_html += f"<br>\n{phone}\n"
    contact_html += "</p>\n"

    if len(urls) > 0:
        contact_html += f"<p>{urls}</p>\n"

    sections.append(contact_html)

    # Areas
    if data.get("areas"):
        sections.append(
            f"""
<h2>Research Areas</h2>
<p>{clean_text(" ⋅ ".join(data["areas"]))}</p>
"""
        )

    # Education
    if data.get("education"):
        edu_items = []
        for edu in data["education"]:
            edu_items.append(
                f'<p>{edu.get("year", "")} | <strong>{clean_text(edu.get("subject", ""))}</strong><br>{LEADING_WS}{clean_text(edu.get("institute", ""))}, {clean_text(edu.get("city", ""))}</p>'
            )

        sections.append(
            f"""
<h2>Education</h2>
{"\n".join(edu_items)}
"""
        )

    # Appointments
    if data.get("appointments"):
        appt_items = []
        for appt in data["appointments"]:
            appointment_str = f"""
<p>{appt.get("years", "")} | <strong>{clean_text(appt.get("job", ""))}</strong><br>
"""

            if appt.get("notes"):
                appointment_str += f"{LEADING_WS}{appt.get("notes")}<br>"

            appointment_str += f"""
{LEADING_WS}{clean_text(appt.get("department", ""))}, {clean_text(appt.get("faculty", ""))}<br>
"""

            if appt.get("cross"):
                appointment_str += f"{LEADING_WS}{appt.get("cross")}<br>"

            appointment_str += f"{LEADING_WS}{clean_text(appt.get("employer", ""))}"

            appointment_str += "</p>"
            appt_items.append(appointment_str)

        sections.append(
            f"""
<h2>Academic Appointments</h2>
{"\n".join(appt_items)}
""".replace(
                "--", " to "
            )
        )

    # leaves
    if data.get("leaves"):
        leave_items = []
        for leave in data["leaves"]:
            leave_items.append(
                f'<p>{leave.get("years", "")} | <strong>{clean_text(leave.get("type", ""))}</strong><br>'
                f"{LEADING_WS}{leave.get("employer", "")}</p>"
            )
        sections.append(
            f"""
<h3>Leaves</h3>
{"\n".join(leave_items)}
""".replace(
                "--", " to "
            )
        )

    # Affiliations
    if data.get("affiliations"):
        aff_items = []
        for aff in data["affiliations"]:
            aff_str = f'<p>{aff.get("years", "")} | <strong>{clean_text(aff.get("role", ""))}</strong><br>'
            aff_str += f'{LEADING_WS}{clean_text(aff.get("organization", ""))}'.replace(
                ": ", f"<br>{LEADING_WS}"
            )
            if aff.get("notes"):
                aff_str += f"<br>{LEADING_WS}"
                aff_str += f"{aff.get("notes")}"
            aff_str += "</p>"

            aff_items.append(aff_str)
        sections.append(
            f"""
<h3>Affiliations</h3>
{"\n".join(aff_items)}
""".replace(
                "--", " to "
            )
        )

    # Books
    if data.get("books"):
        book_items = []
        for book in data["books"]:
            link = (
                f' <a href="{book.get("ilink", "")}">[link]</a>'
                if book.get("ilink")
                else ""
            )
            book_items.append(
                f'<li>{clean_text(book.get("authors", ""))}. {book.get("year", "")}. <em>{clean_text(book.get("title", ""))}</em>. {clean_text(book.get("press", ""))}: {clean_text(book.get("city", ""))}.</li>'
            )
        sections.append(
            f"""
<h2>Books</h2>
<ol reversed>
{"\n".join(book_items)}
</ol>
"""
        )

    # Articles
    if data.get("articles"):
        article_items = []
        for art in data["articles"]:
            vol_issue = format_volume_issue(art.get("volume"), art.get("issue"))
            pages = format_pages(art.get("pages"))
            article_items.append(
                f'<li>{clean_text(art.get("authors", ""))}. {art.get("year", "")}. '
                f'"{clean_text(art.get("title", ""))}." '
                f'<em>{clean_text(art.get("journal", ""))}</em>{vol_issue}{pages}.</li>'
            )
        sections.append(
            f"""
<h2>Peer-Reviewed Articles</h2>
<ol reversed>
{"\n".join(article_items)}
</ol>
"""
        )

    # Chapters
    if data.get("chapters"):
        chap_items = []
        for chap in data["chapters"]:
            oa_link = (
                f' <a href="{chap.get("oa", "")}">[open access]</a>'
                if chap.get("oa")
                else ""
            )
            chap_items.append(
                f'<li>{clean_text(chap.get("authors", ""))}. {chap.get("year", "")}. '
                f'"{clean_text(chap.get("title", ""))}." '
                f'In {clean_text(chap.get("editors", ""))} (Eds.), '
                f'<em>{clean_text(chap.get("book", ""))}</em>. '
                f'{clean_text(chap.get("press", ""))}: {clean_text(chap.get("city", ""))}.{oa_link}</li>'
            )
        sections.append(
            f"""
<h2>Book Chapters</h2>
<ol reversed>
{"\n".join(chap_items)}
</ol>
"""
        )

    # Special Issues
    if data.get("issues"):
        issue_items = []
        for iss in data["issues"]:
            issue_items.append(
                f'<li>{clean_text(iss.get("editors", ""))} (Eds.). {iss.get("year", "")}. '
                f'"{clean_text(iss.get("theme", ""))}." '
                f'<em>{clean_text(iss.get("journal", ""))}</em>.</li>'
            )
        sections.append(
            f"""
<h2>Edited Special Issues</h2>
<ol reversed>
{"\n".join(issue_items)}
</ol>
"""
        )

    # Reports
    if data.get("reports"):
        report_items = []
        for rep in data["reports"]:
            report_items.append(
                f'<li>{clean_text(rep.get("authors", ""))}. {rep.get("year", "")}. '
                f'"{clean_text(rep.get("report", ""))}." '
                f'{clean_text(rep.get("client", ""))}.</li>'
            )
        sections.append(
            f"""
<h2>Research Reports</h2>
<ol reversed>
{"\n".join(report_items)}
</ol>
"""
        )

    # Publication Supplements and Replication Kits
    if data.get("publication_supplements_and_replication_kits"):
        supp_items = []
        for item in data["publication_supplements_and_replication_kits"]:
            supp_items.append(f"<li>{clean_text(item)}</li>")
        sections.append(
            f"""
<h2>Replication Kits & Supplements</h2>
<ol reversed>
{chr(10).join(supp_items)}
</ol>
"""
        )

    # Manuscripts in Progress
    manuscripts = []
    if data.get("article-manuscripts"):
        for ms in data["article-manuscripts"]:
            manuscripts.append(
                f'<li>{clean_text(ms.get("authors", ""))}. '
                f'"{clean_text(ms.get("title", ""))}." '
                f'{ms.get("status", "In Progress")}.</li>'
            )
    if data.get("book-manuscripts"):
        for ms in data["book-manuscripts"]:
            manuscripts.append(
                f'<li>{clean_text(ms.get("authors", ""))}. '
                f'<em>{clean_text(ms.get("title", ""))}</em>. '
                f'{ms.get("status", "In Progress")}.</li>'
            )
    if manuscripts:
        sections.append(
            f"""
<h2>Manuscripts in Progress</h2>
<ol reversed>
{"\n".join(manuscripts)}
</ol>
"""
        )

    # Miscellaneous Publications
    if data.get("misc"):
        misc_items = []
        for m in data["misc"]:
            misc_items.append(
                f'<li>{clean_text(m.get("authors", ""))}. {m.get("year", "")}. '
                f'"{clean_text(m.get("title", ""))}." '
                f'{clean_text(m.get("details", ""))}</li>'
            )
        sections.append(
            f"""
<h2>Other Publications</h2>
<ol reversed>
{"\n".join(misc_items)}
</ol>
"""
        )

    # Grants
    if data.get("grants"):
        grant_items = []
        for g in data["grants"]:
            years = str(g.get("years", "")).replace("--", " to ")
            grant_string = f'<li>{clean_text(g.get("title", ""))}<br>'
            grant_string += f'{clean_text(g.get("pi", ""))} (PI). {years}. {clean_text(g.get("grant", ""))}. {g.get("amount", "")}<br>'

            if g.get("ci"):
                grant_string += f"CI: {g.get("ci")}.<br>"
            if g.get("collaborators"):
                grant_string += f"CO: {g.get("collaborators")}."
            grant_string += "</li>"

            grant_items.append(grant_string)
        sections.append(
            f"""
<h2>Research Grants</h2>
<ol reversed>
{"\n".join(grant_items)}
</ol>
"""
        )

    # Teaching Grants
    if data.get("teachinggrants"):
        tg_items = []
        for tg in data["teachinggrants"]:
            years = str(tg.get("years", "")).replace("--", " to ")
            tg_items.append(
                f'<li>{years}. "{clean_text(tg.get("title", ""))}." '
                f'{clean_text(tg.get("grant", ""))}. {tg.get("amount", "")}.</li>'
            )
        sections.append(
            f"""
<h2>Teaching Grants</h2>
<ol reversed>
{"\n".join(tg_items)}
</ol>
"""
        )

    # Awards
    if data.get("awards"):
        award_items = []
        for a in data["awards"]:
            org = clean_text(a.get("organization", ""))
            org = md_links_to_html(org)

            award = clean_text(a.get("award", ""))
            award = md_links_to_html(award)

            award_items.append(
                f'<li>{a.get("year", "")}. {award}.<br>'
                f'{org} {a.get("amount", "")}</li>'.replace("--", " to ")
            )
        sections.append(
            f"""
<h2>Awards and Scholarships</h2>
<ol reversed>
{"\n".join(award_items)}
</ol>
"""
        )

    # Contracts
    if data.get("contracts"):
        contract_items = []
        for c in data["contracts"]:
            years = str(c.get("years", "")).replace("--", " to ")
            org = md_links_to_html(clean_text(c.get("organization", "")))
            contract_items.append(
                f'<li>{c.get("contracted", "")}. {years}. "{clean_text(c.get("title", ""))}." '
                f"{org}.</li>"
            )
        sections.append(
            f"""
<h2>Research Contracts</h2>
<ol reversed>
{"\n".join(contract_items)}
</ol>
"""
        )

    # License badge mapping
    LICENSE_BADGES = {
        "MIT License": "https://img.shields.io/badge/License-MIT-yellow.svg",
        "MIT": "https://img.shields.io/badge/License-MIT-yellow.svg",
        "GNU GPL2": "https://img.shields.io/badge/License-GPL_v2-blue.svg",
        "GNU GPL3": "https://img.shields.io/badge/License-GPLv3-blue.svg",
        "Apache 2.0": "https://img.shields.io/badge/License-Apache_2.0-yellowgreen.svg",
        "BSD 3-Clause": "https://img.shields.io/badge/License-BSD_3--Clause-orange.svg",
    }

    # GitHub badge
    GITHUB_BADGE = "https://img.shields.io/badge/github-%23121011.svg?style=flat&logo=github&logoColor=white"
    # Language and tool badges
    LANGUAGE_BADGES = {
        # Languages
        "Python": "https://img.shields.io/badge/python-3670A0?style=flat&logo=python&logoColor=ffdd54",
        "R": "https://img.shields.io/badge/r-%23276DC3.svg?style=flat&logo=r&logoColor=white",
        "Julia": "https://img.shields.io/badge/-Julia-9558B2?style=flat&logo=julia&logoColor=white",
        "Bash": "https://img.shields.io/badge/bash-%23121011.svg?style=flat&logo=gnu-bash&logoColor=white",
        "Shell": "https://img.shields.io/badge/shell-%23121011.svg?style=flat&logo=gnu-bash&logoColor=white",
        # ML/NLP tools
        "HuggingFace": "https://img.shields.io/badge/HuggingFace-%23FFD21E.svg?style=flat&logo=huggingface&logoColor=black",
        "Transformers": "https://img.shields.io/badge/Transformers-%23FFD21E.svg?style=flat&logo=huggingface&logoColor=black",
        "spaCy": "https://img.shields.io/badge/spaCy-09A3D5?style=flat&logo=spacy&logoColor=white",
        # Network analysis
        "graph-tool": "https://img.shields.io/badge/graph--tool-7B68EE?style=flat",
        # Bibliometric databases
        "OpenAlex": "https://img.shields.io/badge/OpenAlex-A6CE39?style=flat",
        "Web of Science": "https://img.shields.io/badge/Web_of_Science-5C5C5C?style=flat",
        "Scopus": "https://img.shields.io/badge/Scopus-E9711C?style=flat",
    }

    # Software
    if data.get("software"):
        # Group software by status
        sw_by_status = {}
        # Define the order of status groups
        status_order = [
            "Active Development",
            "Maintained, Occasional Updates",
            "Archived",
        ]

        print("\nFetching GitHub info for software packages...")

        # Check and display rate limit status
        remaining, limit = check_rate_limit()
        has_token = os.environ.get("GITHUB_TOKEN") is not None
        auth_status = (
            "(authenticated)"
            if has_token
            else "(unauthenticated - set GITHUB_TOKEN for higher limits)"
        )
        if remaining is not None:
            print(f"  GitHub API: {remaining}/{limit} requests remaining {auth_status}")
        else:
            print(f"  GitHub API: Could not check rate limit {auth_status}")

        for sw in data["software"]:
            package = clean_text(sw.get("package", ""))
            language = sw.get("language", "")
            status = sw.get("status", "Other")
            description = clean_text(sw.get("description", ""))
            license_text = sw.get("license", "")
            github_url = sw.get("github", "")
            team = clean_text(sw.get("development", ""))
            documentation_url = sw.get("documentation", "")
            citation = sw.get("citation", "")
            learn_more = clean_text(sw.get("learn-more", ""))

            # Fetch GitHub info (version, commit, and more)
            print(f"  → {package}...")
            gh_info = fetch_github_info(github_url, sw)

            # All available variables from GitHub API / cache:
            version = gh_info["version"]
            last_commit_date = gh_info["last_commit_date"]
            last_commit_sha = gh_info["last_commit_sha"]

            # Get language badge
            language_badge = LANGUAGE_BADGES.get(language)
            if language_badge:
                language_html = f'<img src="{language_badge}" alt="{language}">'
            else:
                language_html = ""

            badge_url = LICENSE_BADGES.get(license_text)
            if badge_url:
                license_html = f'<img src="{badge_url}" alt="{license_text}">'
            else:
                license_html = license_text

            # Helper to check if a value is a placeholder/missing
            def is_missing(val):
                if not val:
                    return True
                missing_markers = [
                    "XX.XX",
                    "XXXX-XX-XX",
                    "XXXXXXX",
                    "add documentation website here",
                    "add citation here",
                ]
                return str(val).strip() in missing_markers

            # GitHub badge with link
            if github_url:
                github_html = (
                    f'<a href="{github_url}">'
                    f'<img src="{GITHUB_BADGE}" alt="GitHub"></a>'
                )
                # Package name links to GitHub, include version if available
                if is_missing(version) and not SHOW_MISSING_SOURCE_DATA:
                    package_html = (
                        f'<a href="{github_url}"><strong>{package}</strong></a>'
                    )
                else:
                    package_html = (
                        f'<a href="{github_url}"><strong>{package}</strong></a> '
                        f"(v{version})"
                    )
            else:
                github_html = ""
                package_html = f"<strong>{package}</strong>"

            # Format date for display (e.g., "Feb 3, 2026")
            formatted_date = format_date_long(last_commit_date)

            # Build last commit display, hide if missing
            has_commit_info = not is_missing(last_commit_date) or not is_missing(
                last_commit_sha
            )
            if has_commit_info or SHOW_MISSING_SOURCE_DATA:
                if is_missing(last_commit_date) and is_missing(last_commit_sha):
                    last_commit_line = "Last commit: (no data)<br>\n"
                elif is_missing(last_commit_sha):
                    last_commit_line = f"Last commit: {formatted_date}<br>\n"
                elif is_missing(last_commit_date):
                    last_commit_line = f"Last commit: (commit: {last_commit_sha})<br>\n"
                else:
                    last_commit_line = (
                        f"<code>Last commit ({last_commit_sha}): "
                        f"{formatted_date}</code><br>\n"
                    )
            else:
                last_commit_line = ""

            # Build documentation line
            if not is_missing(documentation_url):
                doc_line = f'Documentation: <a href="{documentation_url}">{documentation_url}</a><br>\n'
            elif SHOW_MISSING_SOURCE_DATA:
                doc_line = "Documentation: (no link)<br>\n"
            else:
                doc_line = ""

            # # Build citation line (bibtex format)
            # if not is_missing(citation):
            #     citation_line = f"Citation:<br>\n<pre><code>{citation}</code></pre>\n"
            # elif SHOW_MISSING_SOURCE_DATA:
            #     citation_line = "Citation: (no citation)<br>\n"
            # else:
            #     citation_line = ""

            # Build learn more line
            # if learn_more:
            #     learn_more_line = f"{learn_more}<br>\n"
            # else:
            #     learn_more_line = ""

            software_str = "<li>\n"
            software_str += f'{package_html} | {description}. Developed by {team}. <a href="{github_url}">{github_url}</a><br>\n'
            # {doc_line}
            software_str += f"{language_html} {license_html} {github_html}<br>\n"
            software_str += f"{last_commit_line}"
            software_str += "</li>"

            # Add to appropriate status group
            if status not in sw_by_status:
                sw_by_status[status] = []
            sw_by_status[status].append(software_str.replace("..", "."))

        # Print summary
        print(
            f"\n  GitHub data: {_github_stats['fresh']} packages fetched fresh, "
            f"{_github_stats['cached']} from cache"
        )

        # Build software section with H3 subsections for each status
        software_html = "\n<h2>Scientific Software</h2>\n"

        # Output in defined order, then any remaining statuses
        all_statuses = status_order + [
            s for s in sw_by_status.keys() if s not in status_order
        ]

        for status in all_statuses:
            if status in sw_by_status and sw_by_status[status]:
                software_html += f"<h3>{status}</h3>\n"
                software_html += "<ol reversed>\n"
                software_html += "\n".join(sw_by_status[status])
                software_html += "\n</ol>\n"

        sections.append(software_html)

    # Conference Presentations
    if data.get("conferences"):
        conf_items = []
        for c in sorted(
            data["conferences"], key=lambda x: str(x.get("year", "")), reverse=True
        ):
            conf_items.append(
                f'<li>{clean_text(c.get("authors", ""))}. {str(c.get("year", ""))[:7]}. '
                f'"{clean_text(c.get("title", ""))}." '
                f'{clean_text(c.get("conference", ""))}. {clean_text(c.get("location", ""))}.</li>'
            )
        sections.append(
            f"""
<h2>Conference Presentations</h2>
<ol reversed>
{"\n".join(conf_items)}
</ol>
""".replace(
                "..", "."
            ).replace(
                "?.", "?"
            )
        )

    # Invited Talks
    if data.get("invited"):
        inv_items = []
        for i in sorted(
            data["invited"], key=lambda x: str(x.get("year", "")), reverse=True
        ):
            inv_items.append(
                f'<li>{clean_text(i.get("authors", ""))}. {str(i.get("year", ""))[:7]}. '
                f'"{clean_text(i.get("title", ""))}." '
                f'{clean_text(i.get("conference", ""))}. {clean_text(i.get("location", ""))}.</li>'
            )
        sections.append(
            f"""
<h2>Invited Talks</h2>
<ol reversed>
{"\n".join(inv_items)}
</ol>
"""
        )

    # Courses Taught
    teaching_file = base_dir / "records" / "teaching.yml"
    if teaching_file.exists():
        import pandas as pd

        with open(teaching_file, "r") as f:
            teaching_data = yaml.safe_load(f)

        courses = teaching_data.get("courses", [])
        df_courses = pd.DataFrame(courses)
        teaching = teaching_data.get("teaching", [])
        df_teaching = pd.DataFrame(teaching)

        # Lookup dicts
        lookup_course_id_to_number = dict(zip(df_courses["id"], df_courses["number"]))
        lookup_course_id_to_name = dict(zip(df_courses["id"], df_courses["name"]))

        course_strings = []

        # Group by 'id'
        for course_id, group in df_teaching.groupby("id"):
            # Sort by 'term-code'
            group_sorted = group.sort_values(
                by="term-code", key=lambda col: pd.to_numeric(col, errors="coerce")
            )
            # Sum total enrollment (treat NaN as 0)
            total_enrollment = group_sorted["enrollment"].fillna(0).astype(int).sum()
            # Create ordered list of semester-year values
            semester_years = group_sorted["semester-year"].tolist()
            offering_list = ", ".join(semester_years)
            # Get course number and name
            course_number = lookup_course_id_to_number.get(course_id, course_id)
            course_name = lookup_course_id_to_name.get(course_id, "")

            # Format string
            section_string = (
                f"<p>{course_number} | <strong>{course_name}</strong><br>\n"
            )
            if total_enrollment > 0:
                section_string += (
                    f"{LEADING_WS}{total_enrollment} total enrolments from "
                    f"{len(semester_years)} sections:<br>\n"
                    f"{LEADING_WS}{offering_list}\n"
                ).replace("1 sections:", "1 section:")
            else:
                section_string += f"{LEADING_WS}Scheduled for {offering_list}\n"
            section_string += "</p>\n"

            course_strings.append(section_string)

        if course_strings:
            sections.append(
                f"""
<h2>Courses Taught</h2>
{chr(10).join(course_strings)}
"""
            )

    # Reading Courses
    if data.get("reading"):
        read_items = []
        for r in data["reading"]:
            who = f' ({clean_text(r.get("who", ""))})' if r.get("who") else ""
            read_items.append(
                f'<li>{r.get("year", "")}. {clean_text(r.get("name", ""))} ({r.get("level", "")}){who}.</li>'
            )
        sections.append(
            f"""
<h2>Directed Reading Courses</h2>
<ol reversed>
{"\n".join(read_items)}
</ol>
"""
        )

    # PhD Supervision
    if data.get("phd"):
        phd_active = []
        phd_completed = []
        for p in data["phd"]:
            status_val = p.get("status", "")
            # Check if completed: status is a year (int or string that's a 4-digit number)
            is_completed = isinstance(status_val, int) or (
                isinstance(status_val, str) and status_val.isdigit()
            )
            role = (
                "Supervisor"
                if p.get("supervisor") == "John McLevey"
                else "Committee Member"
            )
            if is_completed:
                phd_completed.append(
                    f"<li>{role} for "
                    f'<strong>{clean_text(p.get("student", ""))} ({status_val})</strong><br>'
                    f'{LEADING_WS}{clean_text(p.get("department", ""))}<br>'
                    f'{LEADING_WS}Supervisor: {p.get("supervisor", "")}<br>'
                    f'{LEADING_WS}Committee: {p.get("committee", "")}</li>'
                )
            else:
                # Only show status if it's "ABD", otherwise hide it
                status_str = " (ABD)" if status_val == "ABD" else ""
                phd_active.append(
                    f"<p>{role} for "
                    f'<strong>{clean_text(p.get("student", ""))}{status_str}</strong><br>'
                    f'{LEADING_WS}{clean_text(p.get("department", ""))}<br>'
                    f'{LEADING_WS}Supervisor: {p.get("supervisor", "")}<br>'
                    f'{LEADING_WS}Committee: {p.get("committee", "")}</p>'
                )
        phd_section = "\n<h2>PhD Students</h2>\n"
        if phd_active:
            phd_section += "<h3>Active</h3>\n"
            phd_section += "\n".join(phd_active) + "\n"
        if phd_completed:
            phd_section += "<h3>Completed</h3>\n<ol reversed>\n"
            phd_section += "\n".join(phd_completed)
            phd_section += "\n</ol>\n"
        sections.append(phd_section)

    # Masters Supervision
    if data.get("masters"):
        ma_active = []
        ma_completed = []
        for m in data["masters"]:
            status_val = m.get("status", "")
            is_completed = isinstance(status_val, int) or (
                isinstance(status_val, str) and status_val.isdigit()
            )
            if is_completed:
                ma_completed.append(
                    f'<li>{m.get("role", "")} for <strong>{clean_text(m.get("student", ""))} ({status_val})</strong><br>'
                    f'{m.get("degree", "")}, {clean_text(m.get("department", ""))}.'
                    "</li>"
                )
            else:
                status_str = f" ({status_val})" if status_val else ""
                ma_active.append(
                    f'<p>{clean_text(m.get("student", ""))}{status_str}. '
                    f'{m.get("degree", "")}, {clean_text(m.get("department", ""))}. '
                    f'Role: {m.get("role", "")}</p>'
                )
        ma_section = "\n<h2>Masters Students</h2>\n"
        if ma_active:
            ma_section += "<h3>Active</h3>\n"
            ma_section += "\n".join(ma_active) + "\n"
        if ma_completed:
            ma_section += "<h3>Completed</h3>\n<ol reversed>\n"
            ma_section += "\n".join(ma_completed)
            ma_section += "\n</ol>\n"
        sections.append(ma_section)

    # HQP
    if data.get("hqp"):
        hqp_items = []
        for h in data["hqp"]:
            gra = (
                f' Graduate RAs: {clean_text(h.get("gra", ""))}.'
                if h.get("gra")
                else ""
            )
            ura = (
                f' Undergraduate RAs: {clean_text(h.get("ura", ""))}.'
                if h.get("ura")
                else ""
            )
            hqp_items.append(f'<li>{h.get("year", "")}.{gra}{ura}</li>')
        sections.append(
            f"""
<h2>Research Assistants (HQP)</h2>
<ol reversed>
{"\n".join(hqp_items)}
</ol>
"""
        )

    # Other Graduate Training
    if data.get("othergrad"):
        og_items = []
        for og in data["othergrad"]:
            og_items.append(
                f'<li>{og.get("who", "")}. {og.get("year", "")}. <strong>{clean_text(og.get("training", ""))}</strong>. {clean_text(og.get("details", ""))}. {clean_text(og.get("length", ""))}.</li>'
            )
        sections.append(
            f"""
<h2>Methods & Scientific Computing Workshops</h2>
<ol reversed>
{"\n".join(og_items)}
</ol>
""".replace(
                "..", "."
            )
        )

    # Undergraduate Supervision
    if data.get("undergraduate"):
        ug_items = []
        for ug in data["undergraduate"]:
            ug_items.append(
                f'<li>{clean_text(ug.get("student", ""))} ({ug.get("year", "")})<br>{clean_text(ug.get("department", ""))}</li>'
            )
        sections.append(
            f"""
<h2>Undergraduate Thesis Supervision</h2>
<ol reversed>
{"\n".join(ug_items)}
</ol>
"""
        )

    # Professional Service (year-marker format)
    if data.get("profession"):
        prof_items = []
        for p in data["profession"]:
            years = str(p.get("year", "")).replace("--", "-")
            role = clean_text(p.get("role", ""))
            prof_items.append(
                f'<li><span class="year">{years}</span>'
                f'<span class="content">{role}</span></li>'
            )
        sections.append(
            f"""
<h2>Professional Service</h2>
<ul class="cv-year-list">
{chr(10).join(prof_items)}
</ul>
"""
        )

    # Sessions Organized (year-marker format)
    if data.get("sessions"):
        sess_items = []
        for s in data["sessions"]:
            year = s.get("year", "")
            session = clean_text(s.get("session", ""))
            panelists = (
                f' Panelists: {clean_text(s.get("panelists", ""))}.'
                if s.get("panelists")
                else ""
            )
            sess_items.append(
                f'<li><span class="year">{year}</span>'
                f'<span class="content">{session}.{panelists}</span></li>'
            )
        sections.append(
            f"""
<h2>Conference Sessions Organized</h2>
<ul class="cv-year-list">
{chr(10).join(sess_items)}
</ul>
"""
        )

    # Peer Review (separate subsections)
    pr_section = ""
    if data.get("prarticles"):
        journals = [
            f"<li><em>{clean_text(j.get('journal', ''))}</em></li>"
            for j in data["prarticles"]
        ]
        pr_section += f"""
<h3>Peer Reviewing - Academic Journals</h3>
<ul>
{chr(10).join(journals)}
</ul>
"""
    if data.get("prbooks"):
        books = [
            f"<li>{clean_text(prb.get('book', ''))}</li>" for prb in data["prbooks"]
        ]
        pr_section += f"""
<h3>Peer Reviewing - Books</h3>
<ul>
{chr(10).join(books)}
</ul>
"""
    if data.get("prgrants"):
        grant_items = []
        for prg in data["prgrants"]:
            year = prg.get("year", "")
            grant = clean_text(prg.get("grant", ""))
            grant_items.append(
                f'<li><span class="year">{year}</span>'
                f'<span class="content">{grant}</span></li>'
            )
        pr_section += f"""
<h3>Peer Reviewing / Evaluation - Grants</h3>
<ul class="cv-year-list">
{chr(10).join(grant_items)}
</ul>
"""
    if pr_section:
        sections.append(f"\n<h2>Peer Review</h2>\n{pr_section}")

    # University Service - Memorial (year-marker format)
    if data.get("smemorial"):
        mem_items = []
        for mem in data["smemorial"]:
            years = str(mem.get("year", "")).replace("--", "-")
            role = clean_text(mem.get("role", ""))
            mem_items.append(
                f'<li><span class="year">{years}</span>'
                f'<span class="content">{role}</span></li>'
            )
        sections.append(
            f"""
<h2>University Service</h2>
<h3>Memorial University</h3>
<ul class="cv-year-list">
{chr(10).join(mem_items)}
</ul>
"""
        )

    # University Service - Waterloo (year-marker format)
    if data.get("suwaterloo"):
        uw_items = []
        for uw in data["suwaterloo"]:
            years = str(uw.get("year", "")).replace("--", "-")
            role = clean_text(uw.get("role", ""))
            uw_items.append(
                f'<li><span class="year">{years}</span>'
                f'<span class="content">{role}</span></li>'
            )
        sections.append(
            f"""
<h3>University of Waterloo</h3>
<ul class="cv-year-list">
{chr(10).join(uw_items)}
</ul>
"""
        )

    # University Service - McMaster (year-marker format)
    if data.get("mcmaster"):
        mc_items = []
        for mc in data["mcmaster"]:
            years = str(mc.get("year", "")).replace("--", "-")
            role = clean_text(mc.get("role", ""))
            mc_items.append(
                f'<li><span class="year">{years}</span>'
                f'<span class="content">{role}</span></li>'
            )
        sections.append(
            f"""
<h3>McMaster University</h3>
<ul class="cv-year-list">
{chr(10).join(mc_items)}
</ul>
"""
        )

    # Professional Training (year-marker format)
    if data.get("training"):
        tr_items = []
        for tr in data["training"]:
            year = str(tr.get("year", "")).replace("--", "-")
            training = clean_text(tr.get("training", ""))
            tr_items.append(
                f'<li><span class="year">{year}</span>'
                f'<span class="content">{training}</span></li>'
            )
        sections.append(
            f"""
<h2>Professional Development</h2>
<ul class="cv-year-list">
{chr(10).join(tr_items)}
</ul>
"""
        )

    # RA/TA Experience (year-marker format)
    if data.get("rata"):
        rata_items = []
        for r in data["rata"]:
            year = str(r.get("year", "")).replace("--", "-")
            position = clean_text(r.get("position", ""))
            rata_items.append(
                f'<li><span class="year">{year}</span>'
                f'<span class="content">{position}</span></li>'
            )
        sections.append(
            f"""
<h2>Research and Teaching Assistantships</h2>
<ul class="cv-year-list">
{chr(10).join(rata_items)}
</ul>
"""
        )

    # Memberships
    if data.get("memberships"):
        sections.append(
            f"""
<h2>Professional Memberships</h2>
<p>{clean_text(" ⋅ ".join(data["memberships"]))}</p>
"""
        )

    # Build sections content and add heading IDs
    sections_html = add_heading_ids("".join(sections))

    # Generate TOC from tracked headings
    toc_html = generate_toc_html()

    # Build final HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CV – John McLevey</title>
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
            <a href="blog.html">Blog</a>
            <a href="cv.html" class="active">CV</a>
            <button class="theme-toggle" onclick="toggleTheme()" aria-label="Toggle theme">◐</button>
        </nav>
    </header>

{toc_html}

    <main>
        <!--
        <p><a href="pdfs/cv.pdf" download class="pdf-button">
            <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
                <path fill="currentColor"
                    d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2l5 5h-5V4zM6 20V4h5v7h7v9H6zm2-6h8v2H8v-2zm0 3h8v2H8v-2z" />
            </svg>
            Download my CV (PDF)
        </a></p>
        -->
        <div class="post-header">
            <h1>Professor John McLevey</h1>
            <p class="meta">he/him</p>
        </div>
        <div class="cv-content">
{sections_html}
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

    <!-- Scroll spy for TOC -->
    <script>
        (function() {{
            const tocLinks = document.querySelectorAll('.toc-sidebar a');
            const headings = [];

            // Collect all headings that have IDs
            tocLinks.forEach(link => {{
                const id = link.getAttribute('href').slice(1);
                const heading = document.getElementById(id);
                if (heading) {{
                    headings.push({{ id, element: heading, link }});
                }}
            }});

            if (headings.length === 0) return;

            function updateActiveLink() {{
                const scrollPos = window.scrollY + 120; // Offset for better UX

                // Find the current section
                let current = headings[0];
                for (const heading of headings) {{
                    if (heading.element.offsetTop <= scrollPos) {{
                        current = heading;
                    }} else {{
                        break;
                    }}
                }}

                // Update active class
                tocLinks.forEach(link => link.classList.remove('active'));
                if (current) {{
                    current.link.classList.add('active');
                }}
            }}

            // Throttle scroll events
            let ticking = false;
            window.addEventListener('scroll', () => {{
                if (!ticking) {{
                    requestAnimationFrame(() => {{
                        updateActiveLink();
                        ticking = false;
                    }});
                    ticking = true;
                }}
            }});

            // Initial update
            updateActiveLink();

            // Smooth scroll for TOC links
            tocLinks.forEach(link => {{
                link.addEventListener('click', (e) => {{
                    e.preventDefault();
                    const id = link.getAttribute('href').slice(1);
                    const target = document.getElementById(id);
                    if (target) {{
                        const offset = 80;
                        const targetPosition = target.offsetTop - offset;
                        window.scrollTo({{
                            top: targetPosition,
                            behavior: 'smooth'
                        }});
                    }}
                }});
            }});
        }})();
    </script>
</body>
</html>
"""

    output_file.write_text(html)
    print(f"  → {output_file.relative_to(base_dir)}")
    print(f"\nBuilt CV with {len(sections)} sections")


if __name__ == "__main__":
    build_cv()
