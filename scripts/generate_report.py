#!/usr/bin/env python3
"""
generate_report.py

Generates Tender Care Comprehensive College result-page HTML (and optionally
PDF) files from a teacher-supplied broadsheet CSV, in the exact visual format
of the canonical reference (Werksharp/print/TCH-2025-091.html) -- minus the
JS password gate, which is being replaced by a real auth provider elsewhere
in the stack. This script only produces the report content; whatever serves
these files is responsible for access control.

Ships with two sibling files that must stay next to this script:
    _head.html        -- the <!DOCTYPE ...>...<head>...</head> block (fonts +
                          full CSS, including the print rules), with the
                          title tag holding a swappable __PAGE_TITLE__ token.
    _crestdefs.html    -- the inline SVG <symbol> definition for the crest,
                          reused via <use> for the watermark/corner-logo/
                          header-logo/gate-logo.

CSV FORMAT (one row per student, one row = one term's result for one student):
    Required columns:
        StudentID, StudentName, Class, Term, Session
    Subject columns, in pairs, one pair per subject the class takes:
        "<Subject Name>_CA1", "<Subject Name>_CA2"
    e.g. "Mathematics_CA1", "Mathematics_CA2", "English_CA1", "English_CA2", ...
    Subjects are auto-detected from the header -- no fixed subject list, so a
    class with a different subject mix just needs different column names.

    Optional columns (omit to leave the printed placeholder text):
        TeacherRemark, TeacherName, PrincipalRemark

USAGE:
    python3 generate_report.py --csv j2b.csv --outdir out/
    python3 generate_report.py --csv j2b.csv --outdir out/ --pdf
        (--pdf additionally calls a headless Chrome/Chromium binary, if one
        is found on PATH, to export each HTML file straight to PDF)

OUTPUT:
    One <StudentID>.html per student in --outdir (matching the
    TCH-2025-091.html naming convention), and matching .pdf files alongside
    them if --pdf was passed and a Chromium binary was found.
"""
import argparse
import csv
import html
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

SCHOOL_NAME = "TENDER CARE COMPREHENSIVE COLLEGE"
SCHOOL_ADDRESS = "Kamalo Labori Sagamu Road, Gbaga, Ogun State."
SCHOOL_PHONE = "Tel: 08149135960; 08085042982"

# (low, high, code, css-class) -- exactly the boundaries printed in the
# reference file's grade key, verified against its own worked example.
GRADE_BANDS = [
    (75, 9999, "A1", "ga1"),
    (70, 74, "B2", "gb2"),
    (65, 69, "B3", "gb3"),
    (60, 64, "C4", "gc4"),
    (55, 59, "C5", "gc5"),
    (50, 54, "C6", "gc6"),
    (45, 49, "D7", "gd7"),
    (40, 44, "E8", "ge8"),
    (0, 39, "F9", "gf9"),
]


def grade_for(score):
    for low, high, code, css in GRADE_BANDS:
        if low <= score <= high:
            return code, css
    return "F9", "gf9"


def load_assets():
    head = (SCRIPT_DIR / "_head.html").read_text(encoding="utf-8")
    crest = (SCRIPT_DIR / "_crestdefs.html").read_text(encoding="utf-8")
    return head, crest


def detect_subjects(fieldnames):
    subjects = []
    for name in fieldnames:
        if name.endswith("_CA1"):
            subj = name[: -len("_CA1")]
            if f"{subj}_CA2" in fieldnames:
                subjects.append(subj)
    return subjects


def render_subject_rows(row, subjects):
    rows = []
    subject_total = 0
    for subj in subjects:
        ca1 = int(row[f"{subj}_CA1"])
        ca2 = int(row[f"{subj}_CA2"])
        total = ca1 + ca2
        subject_total += total
        code, css = grade_for(total)
        rows.append(
            "<tr>"
            '<td class="subject-name">' + html.escape(subj) + "</td>"
            '<td class="score-cell">' + str(ca1) + "</td>"
            '<td class="score-cell">' + str(ca2) + "</td>"
            '<td class="score-cell total-score">' + str(total) + "</td>"
            '<td><span class="gdot ' + css + '">' + code + "</span></td>"
            "</tr>"
        )
    return "\n".join(rows), subject_total


BODY_TEMPLATE = """<body>
{crest_defs}
<div class="page-wrap">
    <header class="archive-header">
        <div class="ah-left">
            <svg class="ah-crest"><use href="#crest-symbol" xlink:href="#crest-symbol"/></svg>
            <div>
                <h1>{name} &middot; Academic Record</h1>
                <div class="ah-sub">Tendercare Comprehensive College &nbsp;&middot;&nbsp; Student ID {student_id} &nbsp;&middot;&nbsp; {session}</div>
            </div>
        </div>
    </header>
    <div class="panel-viewport">
        <div class="term-panel">
            <div class="card-inner">
                <svg class="watermark-crest"><use href="#crest-symbol" xlink:href="#crest-symbol"/></svg>
                <svg class="corner-logo"><use href="#crest-symbol" xlink:href="#crest-symbol"/></svg>
                <div class="school-header">
                    <svg class="header-logo"><use href="#crest-symbol" xlink:href="#crest-symbol"/></svg>
                    <div class="school-name">{school_name}</div>
                    <div class="school-address">{school_address}</div>
                    <div class="school-phone">{school_phone}</div>
                </div>
                <div class="term-badge">
                    <div class="term-badge-inner">
                        <span class="tb-label">Session</span>
                        <span class="tb-value">{term_upper} TERM &middot; {session}</span>
                    </div>
                </div>
                <div class="student-info">
                    <div><span class="label">Student</span><span class="value">{name}</span></div>
                    <div><span class="label">Student ID</span><span class="value">{student_id}</span></div>
                    <div><span class="label">Class</span><span class="value">{klass}</span></div>
                    <div><span class="label">Term</span><span class="value">{term}</span></div>
                </div>
                <table class="report-table">
                    <thead>
                        <tr>
                            <th style="width:38%;">Subject</th>
                            <th style="width:18%;">CA1</th>
                            <th style="width:18%;">CA2</th>
                            <th style="width:16%;">Total (100)</th>
                            <th style="width:10%;">Grade</th>
                        </tr>
                    </thead>
                    <tbody>
{subject_rows}
                        <tr class="total-row" style="font-weight:700; background:#e6edf5;">
                            <td style="text-align:right; padding-right:15px; font-size:14px;">TOTALS</td>
                            <td>&mdash;</td><td>&mdash;</td>
                            <td style="font-family:var(--fd); font-size:1.4rem; color:var(--pd);">{total_score}</td>
                            <td style="font-size:10px; color:var(--ash);">/{max_total}</td>
                        </tr>
                    </tbody>
                </table>
                <div class="summary-band">
                    <div class="sb-item"><span class="sb-label">Total Score</span><span class="sb-value">{total_score}<span class="sb-unit">/{max_total}</span></span></div>
                    <div class="sb-item"><span class="sb-label">Average</span><span class="sb-value">{average}<span class="sb-unit">/100</span></span></div>
                    <div class="sb-item"><span class="sb-label">Subjects</span><span class="sb-value">{n}</span></div>
                    <div class="sb-item"><span class="sb-label">Overall Grade</span><span class="sb-value">{overall_code}</span></div>
                </div>
                <div class="remarks">
                    <div class="remark-box teacher">
                        <div class="remark-label">Class Teacher&rsquo;s Comment</div>
                        <div class="remark-content">{teacher_remark}</div>
                        <div class="remark-line"></div>
                        <div class="remark-signature">Signature: ___________________________<br>
                        <span style="font-size:9px;opacity:0.7;">{teacher_sub}</span></div>
                    </div>
                    <div class="remark-box principal">
                        <div class="remark-label">Principal&rsquo;s Comment</div>
                        <div class="remark-content">{principal_remark}</div>
                        <div class="remark-line"></div>
                        <div class="remark-signature">Signature &amp; Stamp: ________________<br>
                        <span style="font-size:9px;opacity:0.7;">Principal &middot; Tendercare Comprehensive College</span></div>
                    </div>
                </div>
                <div class="footer-note">
                    <div class="grade-key">
                        <span>A1 &ge;75</span><span>B2 70&ndash;74</span><span>B3 65&ndash;69</span>
                        <span>C4 60&ndash;64</span><span>C5 55&ndash;59</span><span>C6 50&ndash;54</span>
                        <span>D7 45&ndash;49</span><span>E8 40&ndash;44</span><span>F9 &lt;40</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
</body>
"""


def render_student_page(row, subjects, head_block, crest_defs):
    student_id = row["StudentID"].strip()
    name = row["StudentName"].strip()
    klass = row["Class"].strip()
    term = row["Term"].strip()
    session = row["Session"].strip()

    subject_rows_html, total_score = render_subject_rows(row, subjects)
    n = len(subjects)
    max_total = n * 100
    average = total_score / n if n else 0
    overall_code, _ = grade_for(round(average))

    teacher_remark = html.escape(row.get("TeacherRemark", "").strip()) or "&mdash; comment pending &mdash;"
    teacher_name = html.escape(row.get("TeacherName", "").strip())
    principal_remark = html.escape(row.get("PrincipalRemark", "").strip()) or "&mdash; comment pending &mdash;"
    teacher_sub = teacher_name if teacher_name else ("Class Teacher &middot; " + html.escape(klass))

    title = "Academic Record &ndash; " + html.escape(name) + " &ndash; Tendercare Comprehensive College"
    head = head_block.replace("__PAGE_TITLE__", title)

    body = BODY_TEMPLATE.format(
        crest_defs=crest_defs,
        name=html.escape(name),
        student_id=html.escape(student_id),
        session=html.escape(session),
        school_name=SCHOOL_NAME,
        school_address=SCHOOL_ADDRESS,
        school_phone=SCHOOL_PHONE,
        term_upper=html.escape(term.upper()),
        klass=html.escape(klass),
        term=html.escape(term),
        subject_rows=subject_rows_html,
        total_score=total_score,
        max_total=max_total,
        average=f"{average:.2f}",
        n=n,
        overall_code=overall_code,
        teacher_remark=teacher_remark,
        teacher_sub=teacher_sub,
        principal_remark=principal_remark,
    )

    page = (
        head
        + "\n"
        + body
        + "\n</html>\n"
        + "<!-- generated by generate_report.py from teacher-supplied broadsheet CSV; no auth gate (handled upstream) -->\n"
    )
    return student_id, page


def find_chromium():
    for name in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        path = shutil.which(name)
        if path:
            return path
    return None


def main():
    parser = argparse.ArgumentParser(description="Generate TCC result-page HTML/PDF from a broadsheet CSV.")
    parser.add_argument("--csv", required=True, help="Path to the teacher-supplied broadsheet CSV")
    parser.add_argument("--outdir", required=True, help="Directory to write generated files into")
    parser.add_argument("--pdf", action="store_true", help="Also export each page to PDF via a headless Chromium/Chrome, if found")
    args = parser.parse_args()

    head_block, crest_defs = load_assets()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    with open(args.csv, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        subjects = detect_subjects(reader.fieldnames)
        if not subjects:
            sys.exit("No subject columns detected -- expected pairs like 'Mathematics_CA1' / 'Mathematics_CA2' in the CSV header.")
        rows = list(reader)

    if not rows:
        sys.exit("CSV had no data rows.")

    chromium = find_chromium() if args.pdf else None
    if args.pdf and not chromium:
        print("--pdf requested but no Chrome/Chromium binary found on PATH; writing HTML only.", file=sys.stderr)

    for row in rows:
        student_id, page_html = render_student_page(row, subjects, head_block, crest_defs)
        out_path = outdir / f"{student_id}.html"
        out_path.write_text(page_html, encoding="utf-8")
        print(f"wrote {out_path}")

        if chromium:
            pdf_path = outdir / f"{student_id}.pdf"
            cmd = [chromium, "--headless", "--disable-gpu", f"--print-to-pdf={pdf_path}", out_path.resolve().as_uri()]
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                print(f"wrote {pdf_path}")
            except subprocess.CalledProcessError as e:
                print(f"PDF export failed for {student_id}: {e.stderr.decode(errors='ignore')}", file=sys.stderr)


if __name__ == "__main__":
    main()
