# QDArchive Metadata Acquisition - Phase 1

## Project Overview
This project is part of the **QDArchive** initiative, focusing on the automated discovery and metadata extraction of qualitative data research projects. In Phase 1, we implement a robust seeding pipeline to probe assigned repositories and establish a relational database structure based on the professor's official schema.

## Assigned Repositories
As per the project allocation, this implementation targets:
* **Repository ID 7:** Australian Data Archive (ADA)
* **Repository ID 16:** Open Data LSA (Uni-Halle)

## Technical Implementation
The system is built using **Python 3** and **SQLite3**, adhering to the following specifications:

### 1. Relational Database Schema
The database (`qdarchive_metadata.db`) implements the four-table relational model required:
* `PROJECTS`: Main table containing repository links, search queries, and discovery metadata.
* `FILES`: Placeholders for project-specific files (to be populated in Phase 2).
* `KEYWORDS`: Associated tags and query terms for each project.
* `PERSON_ROLE`: Identification of authors and providers involved in the research.

### 2. Data Standards & Types
* **Language:** Coded using the **BCP 47** standard (e.g., `en`).
* **Download Method:** Strictly set to `SCRAPING` as defined in `data_types.csv`.
* **Licenses:** The system intelligently probes for common licenses (e.g., **MIT**, **CC BY**, **CC0**). If not explicitly found on the summary page, it defaults to `NULL` to maintain data integrity for Phase 2.
* **Timestamps:** Automated recording of `download_date` to track acquisition history.

## How to Run
1.  **Install dependencies:**
    ```bash
    pip install pandas requests openpyxl
    ```
2.  **Execute the pipeline:**
    ```bash
    python main.py
    ```
3.  **Output:** * `qdarchive_metadata.db`: The SQLite database containing all relational data.
    * `Submission_Final.xlsx`: A multi-sheet Excel report for manual verification.

## Compliance Check
This implementation satisfies all **Required (r)** fields as specified in the `schema.csv`. **Optional (o)** fields such as `doi`, `upload_date`, and `license` are extracted where available or prepared as structural placeholders for deep crawling in subsequent phases.

---
**Author:** Sakineh Mohebi 
**Date:** March 2026
