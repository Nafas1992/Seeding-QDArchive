QDArchive Phase 1 - Automated Data Acquisition (ID: 23542421)
This project implements the first phase of the QDArchive data pipeline, focusing on automated repository probing and metadata logging.

🎯 Final Task Assignment
Based on the official assignment, the following four sources were processed for ActiveID 23542421:

Assigned Repo 1 (ID 1): Zenodo

Assigned Repo 2 (ID 6): Dataverse.no

Assigned Repo 3 (ID 7): ADA (Australian Data Archive)

Assigned Repo 4 (ID 16): Open Data LSA (Martin Luther University Halle-Wittenberg)

🛠️ Implementation Details
Architecture: Python-based automated pipeline utilizing requests for scraping and sqlite3 for persistence.

Search Logic: Systematic querying using terms: qdpx, mqda, and interview study.

Relational Model: Strictly follows the official SQLite schema with 4 tables: PROJECTS, FILES, KEYWORDS, and PERSON_ROLE.

Persistence: Metadata is stored in a standardized SQLite database file named according to the course convention: 23542421-sq26.db.

Naming Convention: The output file follows the student_id-sq26.db format as requested by the chair.

🚀 Usage
Ensure requests and pandas are installed in your Python environment.

Run the automation script.

The script will automatically generate the SQLite database file: 23542421-sq26.db.

Verify the database content using any SQLite browser (e.g., sqliteviewer.app).

📂 Deliverables
23542421-sq26.db: The primary metadata database (located in the root folder).

*.py: The source code used for data acquisition.