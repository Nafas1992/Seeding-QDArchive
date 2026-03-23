# QDArchive Phase 1 - Automated Data Acquisition (ID: 23542421)

This project implements the first phase of the QDArchive data pipeline, focusing on automated repository probing and metadata logging.

## 🎯 Final Task Assignment
Based on the provided assignment table and the **Qualitative Data Repositories.xlsx** reference, the following four sources were processed for **ActiveID 123542421**:

1. **Assigned Repo 1 (ID 1):** Zenodo (General-purpose repository)
2. **Assigned Repo 2 (ID 6):** Dataverse.no (Norwegian Open Research Data)
3. **Assigned Repo 3 (ID 7):** ADA (Australian Data Archive)
4. **Assigned Repo 4 (ID 16):** Open Data LSA (Martin Luther University Halle-Wittenberg)

## 🛠️ Implementation Details
- **Architecture:** Python-based automated pipeline utilizing `requests` and `sqlite3`.
- **Search Logic:** Multi-term querying (qdpx, mqda, interview study) across all assigned platforms.
- **Relational Model:** Data is structured into 4 tables (`PROJECTS`, `FILES`, `KEYWORDS`, `PERSON_ROLE`) to follow the official QDArchive schema.
- **Persistence:** Metadata is stored in a relational SQLite database (`qdarchive_metadata.db`).
- **Reporting:** Automated multi-sheet Excel report generation for academic review.

## 🚀 Usage
1. Ensure `pandas`, `requests`, and `openpyxl` are installed.
2. Run the Python script.
3. Enter the target storage directory path.
4. Review `Submission_Final.xlsx` for the complete acquisition status across all 4 repositories.