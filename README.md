# QDArchive Phase 1 - Automated Data Acquisition (ID: 235**421)

This project implements the first phase of the QDArchive data pipeline, focusing on automated repository probing and metadata logging.

## 🎯 Final Task Assignment
Based on the provided assignment table and the **Qualitative Data Repositories.xlsx** reference, the following sources were processed for **ActiveID 235**421:
- **Assigned Repo 1 (ID 7):** ADA (Australian Data Archive)
- **Assigned Repo 2 (ID 16):** Open Data LSA (Martin Luther University Halle-Wittenberg)

## 🛠️ Implementation Details
- **Architecture:** Python-based automated pipeline.
- **Diagnostics:** Analysis of repository accessibility (How and Why) recorded in the `usability_note` column.
- **Persistence:** Metadata is stored in an SQLite database (`qdarchive_metadata.db`).
- **Reporting:** Automated Excel report generation for academic review.

## 🚀 Usage
1. Run `Seeding-QDArchive.py`
2. Enter the storage directory path.
3. Review `QDArchive_Final_Report.xlsx` for acquisition status.
