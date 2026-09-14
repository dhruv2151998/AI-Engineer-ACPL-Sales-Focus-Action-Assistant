"""Read all 6 files in DataSet/documents/, store as {filename: full_text}
in data/documents.json with relevance notes.
"""

import json
from pathlib import Path

from docx import Document

DOCUMENTS_DIR = Path("DataSet/documents")
OUTPUT_PATH = Path("data/documents.json")

# Relevance assessment per docs/data_profile.md
RELEVANCE_NOTES = {
    "distributor_note_west.docx": (
        "Relevant — corroborates stock-out data for West distributors D032/D033 "
        "on Beverages 1L, supports playbook rules R-01/R-04/R-08."
    ),
    "escalation_sop.docx": (
        "Relevant — defines the PENDING_APPROVAL gating rule and the 'never "
        "invent a cause' principle."
    ),
    "hr_circular.docx": (
        "Noise — HR leave calendar, unrelated to sales performance or actions."
    ),
    "promo_circular_h2fy26.docx": (
        "Relevant — confirms approved H2 promotion mechanics; supports "
        "R-02/R-07 promo-effectiveness evaluation."
    ),
    "visit_note_north_feb2026.docx": (
        "Relevant — documents competitor-driven CremeDelight miss in North "
        "(Feb 2026), providing context for R-03/R-06 manual-review handling."
    ),
    "weekly_summary_w32.docx": (
        "Noise — routine roll-up with no exceptions or actionable findings."
    ),
}


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    documents = {}
    for fpath in sorted(DOCUMENTS_DIR.iterdir()):
        if not fpath.is_file():
            continue
        doc = Document(str(fpath))
        text = "\n".join(p.text for p in doc.paragraphs)
        note = RELEVANCE_NOTES.get(fpath.name, "Unknown relevance.")
        documents[fpath.name] = {
            "text": text,
            "relevance_note": note,
        }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(documents, f, indent=2)

    print(f"Documents loaded: {len(documents)} files written to {OUTPUT_PATH}")
    for fname, info in documents.items():
        print(f"  {fname}: {info['relevance_note']}")


if __name__ == "__main__":
    main()