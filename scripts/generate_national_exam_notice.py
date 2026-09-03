#!/usr/bin/env python3
import csv, html
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
HEAD = (SCRIPT_DIR / "_head.html").read_text(encoding="utf-8")
CREST = (SCRIPT_DIR / "_crestdefs.html").read_text(encoding="utf-8")

SCHOOL_NAME = "TENDER CARE COMPREHENSIVE COLLEGE"
SCHOOL_ADDRESS = "Kamalo Labori Sagamu Road, Gbaga, Ogun State."
SCHOOL_PHONE = "Tel: 08149135960; 08085042982"

EXAM_BY_CLASS = {
    "JSS3A": ("BECE", "Basic Education Certificate Examination"),
    "JSS3B": ("BECE", "Basic Education Certificate Examination"),
    "SS3 Science": ("WASSCE", "West African Senior School Certificate Examination"),
    "SS3 Actuarial": ("WASSCE", "West African Senior School Certificate Examination"),
}

BODY_TEMPLATE = """<body>
{crest_defs}
<div class="page-wrap">
    <header class="archive-header">
        <div class="ah-left">
            <svg class="ah-crest"><use href="#crest-symbol" xlink:href="#crest-symbol"/></svg>
            <div>
                <h1>{name} &middot; Academic Record</h1>
                <div class="ah-sub">Tendercare Comprehensive College &nbsp;&middot;&nbsp; Student ID {student_id} &nbsp;&middot;&nbsp; 2025/2026</div>
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
                        <span class="tb-value">THIRD TERM &middot; 2025/2026</span>
                    </div>
                </div>
                <div class="student-info">
                    <div><span class="label">Student</span><span class="value">{name}</span></div>
                    <div><span class="label">Student ID</span><span class="value">{student_id}</span></div>
                    <div><span class="label">Class</span><span class="value">{klass}</span></div>
                    <div><span class="label">Term</span><span class="value">Third</span></div>
                </div>
                <div class="placeholder-notice">
                    <div class="placeholder-icon">&#127891;</div>
                    <div class="placeholder-text">
                        <strong>Wrote {exam_short} &mdash; National Examination</strong>
                        <span>{klass} does not sit an internal Third Term examination. Students at this level proceed directly to {exam_full} ({exam_short}), the national examination for this class, in place of a school-set Third Term result.</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
</body>
"""


def main():
    with open("/home/claude/pending_gen/missing.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    outdir = SCRIPT_DIR / "out"
    outdir.mkdir(exist_ok=True)

    for row in rows:
        student_id = row["StudentID"].strip()
        name = row["StudentName"].strip()
        klass = row["ClassID"].strip()
        exam_short, exam_full = EXAM_BY_CLASS[klass]

        title = "Academic Record &ndash; " + html.escape(name) + " &ndash; Tendercare Comprehensive College"
        head = HEAD.replace("__PAGE_TITLE__", title)

        body = BODY_TEMPLATE.format(
            crest_defs=CREST,
            name=html.escape(name),
            student_id=html.escape(student_id),
            klass=html.escape(klass),
            school_name=SCHOOL_NAME,
            school_address=SCHOOL_ADDRESS,
            school_phone=SCHOOL_PHONE,
            exam_short=exam_short,
            exam_full=exam_full,
        )

        page = (
            head + "\n" + body + "\n</html>\n"
            + f"<!-- {klass} sits a national examination, not an internal Third Term result -->\n"
        )
        (outdir / f"{student_id}.html").write_text(page, encoding="utf-8")

    print(f"wrote {len(rows)} files to {outdir}")


if __name__ == "__main__":
    main()
