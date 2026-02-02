#!/usr/bin/env python3
"""
CV builder: converts YAML metadata from cv.md to HTML for the website.

Usage:
    python build_cv.py

Reads cv.md and outputs site/cv.html.
"""

import re
from pathlib import Path

LEADING_WS = "&nbsp;&nbsp;&nbsp;&nbsp;"


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
<h2>Affiliations</h2>
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
            grant_string = f'<li><strong>{clean_text(g.get("title", ""))}</strong> <br>'
            grant_string += f'{years}. PI: {clean_text(g.get("pi", ""))}. {clean_text(g.get("grant", ""))}. {g.get("amount", "")}<br>'

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
            amount = f' ({a.get("amount", "")})' if a.get("amount") else ""
            award_items.append(
                f'<li>{a.get("year", "")}. {clean_text(a.get("award", ""))}. '
                f'{clean_text(a.get("organization", ""))}{amount}.</li>'.replace(
                    "--", " to "
                )
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
            contract_items.append(
                f'<li>{years}. "{clean_text(c.get("title", ""))}." '
                f'{clean_text(c.get("organization", ""))}.</li>'
            )
        sections.append(
            f"""
<h2>Research Contracts</h2>
<ol reversed>
{"\n".join(contract_items)}
</ol>
"""
        )

    # Software
    if data.get("software"):
        sw_items = []
        for sw in data["software"]:
            sw_items.append(
                f'<li><strong>{sw.get("package", "")}</strong>. {clean_text(sw.get("description", ""))}. '
                f'License: {sw.get("license", "")}. Development: {clean_text(sw.get("development", ""))}.</li>'
            )
        sections.append(
            f"""
<h2>Software</h2>
<ol reversed>
{"\n".join(sw_items)}
</ol>
"""
        )

    # Other Software
    if data.get("othersoftware"):
        osw_items = []
        for osw in data["othersoftware"]:
            osw_items.append(
                f'<li><strong>{osw.get("package", "")}</strong>. {clean_text(osw.get("description", ""))}.</li>'
            )
        sections.append(
            f"""
<h2>Software Contributions</h2>
<ol reversed>
{"\n".join(osw_items)}
</ol>
"""
        )

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
"""
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
    if data.get("courses"):
        course_items = []
        for c in data["courses"]:
            course_items.append(
                f'<li>{c.get("year", "")}. {c.get("id", "")}: '
                f'{clean_text(c.get("name", ""))} ({c.get("level", "")}).</li>'
            )
        sections.append(
            f"""
<h2>Courses Taught</h2>
<ol reversed>
{"\n".join(course_items)}
</ol>
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
        phd_items = []
        for p in data["phd"]:
            status = f' ({p.get("status", "")})' if p.get("status") else ""
            diss = (
                f' Dissertation: "{clean_text(p.get("dissertation", ""))}".'
                if p.get("dissertation")
                else ""
            )
            role = (
                "Supervisor"
                if p.get("supervisor") == "John McLevey"
                else f'Committee Member (Supervisor: {clean_text(p.get("supervisor", ""))})'
            )
            phd_items.append(
                f'<li>{clean_text(p.get("student", ""))}{status}. '
                f'{clean_text(p.get("department", ""))}. {role}. '
                f'Committee: {clean_text(p.get("committee", ""))}.{diss}</li>'
            )
        sections.append(
            f"""
<h2>PhD Supervision</h2>
<ol reversed>
{"\n".join(phd_items)}
</ol>
"""
        )

    # Masters Supervision
    if data.get("masters"):
        ma_items = []
        for m in data["masters"]:
            thesis = f' "{clean_text(m.get("thesis", ""))}".' if m.get("thesis") else ""
            ma_items.append(
                f'<li>{clean_text(m.get("student", ""))} ({m.get("status", "")}). '
                f'{m.get("degree", "")}, {clean_text(m.get("department", ""))}. '
                f'{m.get("role", "")}.{thesis}</li>'
            )
        sections.append(
            f"""
<h2>Masters Supervision</h2>
<ol reversed>
{"\n".join(ma_items)}
</ol>
"""
        )

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
                f'<li>{og.get("year", "")}. {clean_text(og.get("training", ""))}.</li>'
            )
        sections.append(
            f"""
<h2>Graduate Training and Workshops</h2>
<ol reversed>
{"\n".join(og_items)}
</ol>
"""
        )

    # Undergraduate Supervision
    if data.get("undergraduate"):
        ug_items = []
        for ug in data["undergraduate"]:
            ug_items.append(
                f'<li>{ug.get("year", "")}. {clean_text(ug.get("student", ""))}. '
                f'{clean_text(ug.get("department", ""))}. "{clean_text(ug.get("thesis", ""))}".</li>'
            )
        sections.append(
            f"""
<h2>Undergraduate Thesis Supervision</h2>
<ol reversed>
{"\n".join(ug_items)}
</ol>
"""
        )

    # Professional Service
    prof_service = []
    if data.get("profession"):
        for p in data["profession"]:
            years = str(p.get("year", "")).replace("--", " to ")
            prof_service.append(f'<li>{years}. {clean_text(p.get("role", ""))}.</li>')
    if prof_service:
        sections.append(
            f"""
<h2>Professional Service</h2>
<ol reversed>
{"\n".join(prof_service)}
</ol>
"""
        )

    # Sessions Organized
    if data.get("sessions"):
        sess_items = []
        for s in data["sessions"]:
            panelists = (
                f' Panelists: {clean_text(s.get("panelists", ""))}.'
                if s.get("panelists")
                else ""
            )
            sess_items.append(
                f'<li>{s.get("year", "")}. {clean_text(s.get("session", ""))}.{panelists}</li>'
            )
        sections.append(
            f"""
<h2>Conference Sessions Organized</h2>
<ol reversed>
{"\n".join(sess_items)}
</ol>
"""
        )

    # Peer Review
    pr_items = []
    if data.get("prarticles"):
        journals = ", ".join(
            [clean_text(j.get("journal", "")) for j in data["prarticles"]]
        )
        pr_items.append(f"<li>Journal Articles: {journals}.</li>")
    if data.get("prbooks"):
        for prb in data["prbooks"]:
            pr_items.append(
                f'<li>{prb.get("year", "")}. {clean_text(prb.get("book", ""))}.</li>'
            )
    if data.get("prgrants"):
        for prg in data["prgrants"]:
            pr_items.append(
                f'<li>{prg.get("year", "")}. {clean_text(prg.get("grant", ""))}.</li>'
            )
    if pr_items:
        sections.append(
            f"""
<h2>Peer Review</h2>
<ol reversed>
{"\n".join(pr_items)}
</ol>
"""
        )

    # University Service - Waterloo
    if data.get("suwaterloo"):
        uw_items = []
        for uw in data["suwaterloo"]:
            years = str(uw.get("year", "")).replace("--", " to ")
            uw_items.append(f'<li>{years}. {clean_text(uw.get("role", ""))}.</li>')
        sections.append(
            f"""
<h2>University Service (Waterloo)</h2>
<ol reversed>
{"\n".join(uw_items)}
</ol>
"""
        )

    # University Service - McMaster
    if data.get("mcmaster"):
        mc_items = []
        for mc in data["mcmaster"]:
            years = str(mc.get("year", "")).replace("--", " to ")
            mc_items.append(f'<li>{years}. {clean_text(mc.get("role", ""))}.</li>')
        sections.append(
            f"""
<h2>University Service (McMaster)</h2>
<ol reversed>
{"\n".join(mc_items)}
</ol>
"""
        )

    # Professional Training
    if data.get("training"):
        tr_items = []
        for tr in data["training"]:
            tr_items.append(
                f'<li>{tr.get("year", "")}. {clean_text(tr.get("training", ""))}.</li>'
            )
        sections.append(
            f"""
<h2>Professional Development</h2>
<ol reversed>
{"\n".join(tr_items)}
</ol>
"""
        )

    # RA/TA Experience
    if data.get("rata"):
        rata_items = []
        for r in data["rata"]:
            rata_items.append(
                f'<li>{r.get("year", "")}. {clean_text(r.get("position", ""))}.</li>'
            )
        sections.append(
            f"""
<h2>Research and Teaching Assistantships</h2>
<ol reversed>
{"\n".join(rata_items)}
</ol>
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
