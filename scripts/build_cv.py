#!/usr/bin/env python3
"""
CV builder: converts YAML metadata from cv.md to HTML for the website.

Usage:
    python build_cv.py

Reads cv.md and outputs site/cv.html.
"""

import re
from pathlib import Path

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
    """Clean LaTeX and special formatting from text."""
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
    # Handle italics marked with asterisks (student names)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
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
    base_dir = Path(__file__).parent.parent
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

    contact_html = '<div class="cv-contact">'
    contact_html += f'<p><strong>Email:</strong> <a href="mailto:{data.get("email", "")}">{data.get("email", "")}</a></p>'
    contact_html += f'<p><strong>Phone:</strong> {data.get("phone", "")}</p>'
    if data.get("urls"):
        urls_html = ", ".join([f'<a href="https://{u}">{u}</a>' for u in data["urls"]])
        contact_html += f"<p><strong>Web:</strong> {urls_html}</p>"
    if data.get("address"):
        addr = " | ".join(data["address"])
        contact_html += f"<p><strong>Address:</strong> {addr}</p>"
    contact_html += "</div>"
    sections.append(contact_html)

    # Areas
    if data.get("areas"):
        sections.append(
            f"""
<h2>Research Areas</h2>
<p>{clean_text(data["areas"])}</p>
"""
        )

    # Education
    if data.get("education"):
        edu_items = []
        for edu in data["education"]:
            edu_items.append(
                f'<li><strong>{edu.get("year", "")}</strong> — {clean_text(edu.get("subject", ""))}, {clean_text(edu.get("institute", ""))}, {clean_text(edu.get("city", ""))}</li>'
            )
        sections.append(
            f"""
<h2>Education</h2>
<ul>
{"".join(edu_items)}
</ul>
"""
        )

    # Appointments
    if data.get("appointments"):
        appt_items = []
        for appt in data["appointments"]:
            notes = (
                f' <em>{clean_text(appt.get("notes", ""))}</em>'
                if appt.get("notes")
                else ""
            )
            cross = (
                f'<br>Cross-appointed: {clean_text(appt.get("cross", ""))}'
                if appt.get("cross")
                else ""
            )
            appt_items.append(
                f"""<li><strong>{appt.get("years", "")}</strong> — {clean_text(appt.get("job", ""))}, {clean_text(appt.get("department", ""))}, {clean_text(appt.get("employer", ""))}{cross}{notes}</li>"""
            )
        sections.append(
            f"""
<h2>Academic Appointments</h2>
<ul>
{"".join(appt_items)}
</ul>
"""
        )

    # Affiliations
    if data.get("affiliations"):
        aff_items = []
        for aff in data["affiliations"]:
            notes = f' ({clean_text(aff.get("notes", ""))})' if aff.get("notes") else ""
            aff_items.append(
                f'<li><strong>{aff.get("years", "")}</strong> — {clean_text(aff.get("role", ""))}, {clean_text(aff.get("organization", ""))}{notes}</li>'
            )
        sections.append(
            f"""
<h2>Affiliations</h2>
<ul>
{"".join(aff_items)}
</ul>
"""
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
                f'<li><strong>{book.get("year", "")}</strong> — {clean_text(book.get("authors", ""))}. <em>{clean_text(book.get("title", ""))}</em>. {clean_text(book.get("city", ""))}: {clean_text(book.get("press", ""))}.{link}</li>'
            )
        sections.append(
            f"""
<h2>Books</h2>
<ul>
{"".join(book_items)}
</ul>
"""
        )

    # Articles
    if data.get("articles"):
        article_items = []
        for art in data["articles"]:
            vol_issue = format_volume_issue(art.get("volume"), art.get("issue"))
            pages = format_pages(art.get("pages"))
            article_items.append(
                f'<li><strong>{art.get("year", "")}</strong> — {clean_text(art.get("authors", ""))}. "{clean_text(art.get("title", ""))}." <em>{clean_text(art.get("journal", ""))}</em>{vol_issue}{pages}.</li>'
            )
        sections.append(
            f"""
<h2>Peer-Reviewed Articles</h2>
<ul>
{"".join(article_items)}
</ul>
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
                f'<li><strong>{chap.get("year", "")}</strong> — {clean_text(chap.get("authors", ""))}. "{clean_text(chap.get("title", ""))}." In {clean_text(chap.get("editors", ""))} (Eds.), <em>{clean_text(chap.get("book", ""))}</em>. {clean_text(chap.get("city", ""))}: {clean_text(chap.get("press", ""))}.{oa_link}</li>'
            )
        sections.append(
            f"""
<h2>Book Chapters</h2>
<ul>
{"".join(chap_items)}
</ul>
"""
        )

    # Special Issues
    if data.get("issues"):
        issue_items = []
        for iss in data["issues"]:
            issue_items.append(
                f'<li><strong>{iss.get("year", "")}</strong> — {clean_text(iss.get("editors", ""))} (Eds.). Special Issue: "{clean_text(iss.get("theme", ""))}." <em>{clean_text(iss.get("journal", ""))}</em>.</li>'
            )
        sections.append(
            f"""
<h2>Edited Special Issues</h2>
<ul>
{"".join(issue_items)}
</ul>
"""
        )

    # Reports
    if data.get("reports"):
        report_items = []
        for rep in data["reports"]:
            report_items.append(
                f'<li><strong>{rep.get("year", "")}</strong> — {clean_text(rep.get("authors", ""))}. "{clean_text(rep.get("report", ""))}." {clean_text(rep.get("client", ""))}.</li>'
            )
        sections.append(
            f"""
<h2>Research Reports</h2>
<ul>
{"".join(report_items)}
</ul>
"""
        )

    # Manuscripts in Progress
    manuscripts = []
    if data.get("article-manuscripts"):
        for ms in data["article-manuscripts"]:
            manuscripts.append(
                f'<li>{clean_text(ms.get("authors", ""))}. "{clean_text(ms.get("title", ""))}." <em>{ms.get("status", "In Progress")}</em>.</li>'
            )
    if data.get("book-manuscripts"):
        for ms in data["book-manuscripts"]:
            manuscripts.append(
                f'<li>{clean_text(ms.get("authors", ""))}. <em>{clean_text(ms.get("title", ""))}</em>. {ms.get("status", "In Progress")}.</li>'
            )
    if manuscripts:
        sections.append(
            f"""
<h2>Manuscripts in Progress</h2>
<ul>
{"".join(manuscripts)}
</ul>
"""
        )

    # Miscellaneous Publications
    if data.get("misc"):
        misc_items = []
        for m in data["misc"]:
            misc_items.append(
                f'<li><strong>{m.get("year", "")}</strong> — {clean_text(m.get("authors", ""))}. "{clean_text(m.get("title", ""))}." {clean_text(m.get("details", ""))}</li>'
            )
        sections.append(
            f"""
<h2>Other Publications</h2>
<ul>
{"".join(misc_items)}
</ul>
"""
        )

    # Grants
    if data.get("grants"):
        grant_items = []
        for g in data["grants"]:
            ci = (
                f', Co-Investigators: {clean_text(g.get("ci", ""))}'
                if g.get("ci")
                else ""
            )
            collab = (
                f', Collaborators: {clean_text(g.get("collaborators", ""))}'
                if g.get("collaborators")
                else ""
            )
            grant_items.append(
                f'<li><strong>{g.get("years", "")}</strong> — "{clean_text(g.get("title", ""))}." {clean_text(g.get("grant", ""))}. PI: {clean_text(g.get("pi", ""))}{ci}{collab}. {g.get("amount", "")}.</li>'
            )
        sections.append(
            f"""
<h2>Research Grants</h2>
<ul>
{"".join(grant_items)}
</ul>
"""
        )

    # Teaching Grants
    if data.get("teachinggrants"):
        tg_items = []
        for tg in data["teachinggrants"]:
            tg_items.append(
                f'<li><strong>{tg.get("years", "")}</strong> — "{clean_text(tg.get("title", ""))}." {clean_text(tg.get("grant", ""))}. {tg.get("amount", "")}.</li>'
            )
        sections.append(
            f"""
<h2>Teaching Grants</h2>
<ul>
{"".join(tg_items)}
</ul>
"""
        )

    # Awards
    if data.get("awards"):
        award_items = []
        for a in data["awards"]:
            amount = f' ({a.get("amount", "")})' if a.get("amount") else ""
            award_items.append(
                f'<li><strong>{a.get("year", "")}</strong> — {clean_text(a.get("award", ""))}, {clean_text(a.get("organization", ""))}{amount}</li>'
            )
        sections.append(
            f"""
<h2>Awards and Scholarships</h2>
<ul>
{"".join(award_items)}
</ul>
"""
        )

    # Contracts
    if data.get("contracts"):
        contract_items = []
        for c in data["contracts"]:
            contract_items.append(
                f'<li><strong>{c.get("years", "")}</strong> — "{clean_text(c.get("title", ""))}." {clean_text(c.get("organization", ""))}.</li>'
            )
        sections.append(
            f"""
<h2>Research Contracts</h2>
<ul>
{"".join(contract_items)}
</ul>
"""
        )

    # Software
    if data.get("software"):
        sw_items = []
        for sw in data["software"]:
            sw_items.append(
                f'<li><strong>{sw.get("package", "")}</strong> — {clean_text(sw.get("description", ""))} <em>License: {sw.get("license", "")}. Development: {clean_text(sw.get("development", ""))}</em></li>'
            )
        sections.append(
            f"""
<h2>Software</h2>
<ul>
{"".join(sw_items)}
</ul>
"""
        )

    # Other Software
    if data.get("othersoftware"):
        osw_items = []
        for osw in data["othersoftware"]:
            osw_items.append(
                f'<li><strong>{osw.get("package", "")}</strong> — {clean_text(osw.get("description", ""))}</li>'
            )
        sections.append(
            f"""
<h2>Software Contributions</h2>
<ul>
{"".join(osw_items)}
</ul>
"""
        )

    # Conference Presentations
    if data.get("conferences"):
        conf_items = []
        for c in sorted(
            data["conferences"], key=lambda x: str(x.get("year", "")), reverse=True
        ):
            conf_items.append(
                f'<li><strong>{str(c.get("year", ""))[:7]}</strong> — {clean_text(c.get("authors", ""))}. "{clean_text(c.get("title", ""))}." {clean_text(c.get("conference", ""))}. {clean_text(c.get("location", ""))}.</li>'
            )
        sections.append(
            f"""
<h2>Conference Presentations</h2>
<ul>
{"".join(conf_items)}
</ul>
"""
        )

    # Invited Talks
    if data.get("invited"):
        inv_items = []
        for i in sorted(
            data["invited"], key=lambda x: str(x.get("year", "")), reverse=True
        ):
            inv_items.append(
                f'<li><strong>{str(i.get("year", ""))[:7]}</strong> — {clean_text(i.get("authors", ""))}. "{clean_text(i.get("title", ""))}." {clean_text(i.get("conference", ""))}. {clean_text(i.get("location", ""))}.</li>'
            )
        sections.append(
            f"""
<h2>Invited Talks</h2>
<ul>
{"".join(inv_items)}
</ul>
"""
        )

    # Courses Taught
    if data.get("courses"):
        course_items = []
        for c in data["courses"]:
            course_items.append(
                f'<li><strong>{c.get("year", "")}</strong> — {c.get("id", "")}: {clean_text(c.get("name", ""))} ({c.get("level", "")})</li>'
            )
        sections.append(
            f"""
<h2>Courses Taught</h2>
<ul>
{"".join(course_items)}
</ul>
"""
        )

    # Reading Courses
    if data.get("reading"):
        read_items = []
        for r in data["reading"]:
            who = f' — {clean_text(r.get("who", ""))}' if r.get("who") else ""
            read_items.append(
                f'<li><strong>{r.get("year", "")}</strong> — {clean_text(r.get("name", ""))} ({r.get("level", "")}){who}</li>'
            )
        sections.append(
            f"""
<h2>Directed Reading Courses</h2>
<ul>
{"".join(read_items)}
</ul>
"""
        )

    # PhD Supervision
    if data.get("phd"):
        phd_items = []
        for p in data["phd"]:
            status = f' — {p.get("status", "")}' if p.get("status") else ""
            diss = (
                f'<br><em>Dissertation: {clean_text(p.get("dissertation", ""))}</em>'
                if p.get("dissertation")
                else ""
            )
            role = (
                "Supervisor"
                if p.get("supervisor") == "John McLevey"
                else f'Committee Member (Supervisor: {clean_text(p.get("supervisor", ""))})'
            )
            phd_items.append(
                f'<li><strong>{clean_text(p.get("student", ""))}</strong>{status}<br>{clean_text(p.get("department", ""))} — {role}<br>Committee: {clean_text(p.get("committee", ""))}{diss}</li>'
            )
        sections.append(
            f"""
<h2>PhD Supervision</h2>
<ul>
{"".join(phd_items)}
</ul>
"""
        )

    # Masters Supervision
    if data.get("masters"):
        ma_items = []
        for m in data["masters"]:
            thesis = (
                f'<br><em>{clean_text(m.get("thesis", ""))}</em>'
                if m.get("thesis")
                else ""
            )
            ma_items.append(
                f'<li><strong>{clean_text(m.get("student", ""))}</strong> ({m.get("status", "")}) — {m.get("degree", "")}, {clean_text(m.get("department", ""))}. {m.get("role", "")}.{thesis}</li>'
            )
        sections.append(
            f"""
<h2>Masters Supervision</h2>
<ul>
{"".join(ma_items)}
</ul>
"""
        )

    # HQP
    if data.get("hqp"):
        hqp_items = []
        for h in data["hqp"]:
            gra = (
                f'<br>Graduate RAs: {clean_text(h.get("gra", ""))}'
                if h.get("gra")
                else ""
            )
            ura = (
                f'<br>Undergraduate RAs: {clean_text(h.get("ura", ""))}'
                if h.get("ura")
                else ""
            )
            hqp_items.append(f'<li><strong>{h.get("year", "")}</strong>{gra}{ura}</li>')
        sections.append(
            f"""
<h2>Research Assistants (HQP)</h2>
<ul>
{"".join(hqp_items)}
</ul>
"""
        )

    # Other Graduate Training
    if data.get("othergrad"):
        og_items = []
        for og in data["othergrad"]:
            og_items.append(
                f'<li><strong>{og.get("year", "")}</strong> — {clean_text(og.get("training", ""))}</li>'
            )
        sections.append(
            f"""
<h2>Graduate Training and Workshops</h2>
<ul>
{"".join(og_items)}
</ul>
"""
        )

    # Undergraduate Supervision
    if data.get("undergraduate"):
        ug_items = []
        for ug in data["undergraduate"]:
            ug_items.append(
                f'<li><strong>{ug.get("year", "")}</strong> — {clean_text(ug.get("student", ""))}, {clean_text(ug.get("department", ""))}. "{clean_text(ug.get("thesis", ""))}"</li>'
            )
        sections.append(
            f"""
<h2>Undergraduate Thesis Supervision</h2>
<ul>
{"".join(ug_items)}
</ul>
"""
        )

    # Professional Service
    prof_service = []
    if data.get("profession"):
        for p in data["profession"]:
            prof_service.append(
                f'<li><strong>{p.get("year", "")}</strong> — {clean_text(p.get("role", ""))}</li>'
            )
    if prof_service:
        sections.append(
            f"""
<h2>Professional Service</h2>
<ul>
{"".join(prof_service)}
</ul>
"""
        )

    # Sessions Organized
    if data.get("sessions"):
        sess_items = []
        for s in data["sessions"]:
            panelists = (
                f' Panelists: {clean_text(s.get("panelists", ""))}'
                if s.get("panelists")
                else ""
            )
            sess_items.append(
                f'<li><strong>{s.get("year", "")}</strong> — {clean_text(s.get("session", ""))}{panelists}</li>'
            )
        sections.append(
            f"""
<h2>Conference Sessions Organized</h2>
<ul>
{"".join(sess_items)}
</ul>
"""
        )

    # Peer Review
    pr_items = []
    if data.get("prarticles"):
        journals = ", ".join(
            [clean_text(j.get("journal", "")) for j in data["prarticles"]]
        )
        pr_items.append(f"<li><strong>Journal Articles:</strong> {journals}</li>")
    if data.get("prbooks"):
        for prb in data["prbooks"]:
            pr_items.append(
                f'<li><strong>{prb.get("year", "")}</strong> — {clean_text(prb.get("book", ""))}</li>'
            )
    if data.get("prgrants"):
        for prg in data["prgrants"]:
            pr_items.append(
                f'<li><strong>{prg.get("year", "")}</strong> — {clean_text(prg.get("grant", ""))}</li>'
            )
    if pr_items:
        sections.append(
            f"""
<h2>Peer Review</h2>
<ul>
{"".join(pr_items)}
</ul>
"""
        )

    # University Service - Waterloo
    if data.get("suwaterloo"):
        uw_items = []
        for uw in data["suwaterloo"]:
            uw_items.append(
                f'<li><strong>{uw.get("year", "")}</strong> — {clean_text(uw.get("role", ""))}</li>'
            )
        sections.append(
            f"""
<h2>University Service (Waterloo)</h2>
<ul>
{"".join(uw_items)}
</ul>
"""
        )

    # University Service - McMaster
    if data.get("mcmaster"):
        mc_items = []
        for mc in data["mcmaster"]:
            mc_items.append(
                f'<li><strong>{mc.get("year", "")}</strong> — {clean_text(mc.get("role", ""))}</li>'
            )
        sections.append(
            f"""
<h2>University Service (McMaster)</h2>
<ul>
{"".join(mc_items)}
</ul>
"""
        )

    # Professional Training
    if data.get("training"):
        tr_items = []
        for tr in data["training"]:
            tr_items.append(
                f'<li><strong>{tr.get("year", "")}</strong> — {clean_text(tr.get("training", ""))}</li>'
            )
        sections.append(
            f"""
<h2>Professional Development</h2>
<ul>
{"".join(tr_items)}
</ul>
"""
        )

    # RA/TA Experience
    if data.get("rata"):
        rata_items = []
        for r in data["rata"]:
            rata_items.append(
                f'<li><strong>{r.get("year", "")}</strong> — {clean_text(r.get("position", ""))}</li>'
            )
        sections.append(
            f"""
<h2>Research and Teaching Assistantships</h2>
<ul>
{"".join(rata_items)}
</ul>
"""
        )

    # Memberships
    if data.get("memberships"):
        sections.append(
            f"""
<h2>Professional Memberships</h2>
<p>{clean_text(data["memberships"])}</p>
"""
        )

    # Build final HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CV – John McLevey</title>
    <link rel="stylesheet" href="styles.css">
    <style>
        .cv-contact {{ margin-bottom: 2rem; }}
        .cv-contact p {{ margin-bottom: 0.5rem; }}
        .post-content h2 {{ margin-top: 2.5rem; }}
        .post-content ul {{ margin-bottom: 1.5rem; }}
        .post-content li {{ margin-bottom: 0.75rem; line-height: 1.5; }}
    </style>
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

    <main>
        <div class="post-header">
            <h1>Curriculum Vitae</h1>
            <p class="meta">John McLevey, PhD</p>
        </div>
        <p><a href="pdfs/cv.pdf" download class="pdf-button">
            <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
                <path fill="currentColor"
                    d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2l5 5h-5V4zM6 20V4h5v7h7v9H6zm2-6h8v2H8v-2zm0 3h8v2H8v-2z" />
            </svg>
            Download PDF
        </a></p>
        <div class="post-content">
{"".join(sections)}
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

    output_file.write_text(html)
    print(f"  → {output_file.relative_to(base_dir)}")
    print(f"\nBuilt CV with {len(sections)} sections")


if __name__ == "__main__":
    build_cv()
