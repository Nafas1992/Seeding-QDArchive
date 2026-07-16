# Seeding QDArchive: Automated Data Acquisition & Classification Pipeline
**Student:** Sakineh Mohebi
**Student ID:** 23542421
**Course:** Applied Software Engineering Project (10 ECTS) / Seminar (5 ECTS)
**Supervisor:** Prof. Dirk Riehle, FAU Erlangen-Nürnberg

---

## 🎯 What this script does
This repository contains a test-ready Python script named `Seeding-QDArchive.py`. It is designed so that anyone can clone the repository, install the required packages, and run the script without editing hard-coded system paths.

The script performs the full Part 2 (Classification) workflow described in the course slides:

* Collects real research project metadata from **three repositories**:
  * `dataverse-no` (Dataverse.no, via its REST API)
  * `ada` (Australian Data Archive, via headless-browser search + Dataverse API)
  * `uni-halle` (Uni Halle Open Data, DSpace, via browser-automated search)
* Downloads/extracts file listings, license, author, and keyword metadata for each project
* Classifies every project into a `PROJECT_TYPE` (`QDA_PROJECT`, `QD_PROJECT`, `OTHER_PROJECT`, `NOT_A_PROJECT`)
* Classifies every project against the **ISIC Rev.5** taxonomy (Section + Division, two hierarchical levels)
* Saves all metadata into a local SQLite database (`student_id-sq26-classification.db`)
* Generates a two-sheet Excel workbook (submission-ready table + a styled repository summary)
* Generates a fully vector-graphics PDF report (cover page, table of contents, executive overview, and one detailed section per repository)

---

## 📦 Prerequisites
The script requires **Python 3.8+** and the packages listed in `requirements.txt`.

Required Python packages for `Seeding-QDArchive.py`:

* `requests`
* `pandas`
* `openpyxl`
* `fpdf2`
* `beautifulsoup4`
* `playwright`

Install dependencies with:

```bash
pip install -r requirements.txt
```

**Playwright also needs its browser binary installed once** (this does not happen automatically via pip):

```bash
playwright install chromium
```

If you want to run it in a clean virtual environment:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

---

## ▶️ Running the script
From the folder that contains `Seeding-QDArchive.py`, run:

```bash
python Seeding-QDArchive.py
```

The script will ask:

```text
Enter full output folder path for DB/XLSX/PDF, or press Enter to use the current script folder:
>
```

Enter any valid folder path where you want outputs saved, or just press **Enter** to save everything next to the script.
For example:

* `C:\Users\YourName\Documents\QDArchiveOutput`
* `./output`

If the folder does not exist, the script creates it automatically.

> ⚠️ **Note on `uni-halle`:** this repository is scraped through a **visible** (non-headless) browser window, because the site occasionally shows an "I'm not a robot" verification. If a browser window pops up and shows a challenge, solve it manually in that window — the script will wait up to 3 minutes and then continue automatically.

---

## 📁 Output files
After execution, the script creates three files in the chosen output folder:

* **`23542421-sq26-classification.db`** — local SQLite metadata database (all tables: `PROJECTS`, `LICENSES`, `FILES`, `KEYWORDS`, `PERSON_ROLE`)
* **`Phase2_Classifications.xlsx`** — two-sheet Excel report:
  * `Classifications` — the exact 6-column table required for submission (`repository_id`, `project_type`, `project_title`, `primary_class`, `secondary_class`, `no_project_files`)
  * `Repository Summary` — a styled, human-readable per-repository overview (totals by project type, dominant class, share %)
* **`Phase2_Final_Report.pdf`** — the classification report, with:
  * A cover page (student name/ID, university, supervisor, date)
  * A table of contents with accurate page numbers
  * An Executive Overview page (overall project-type distribution + repository summary table)
  * One section per repository: colored title band, stat cards, a fully vector horizontal histogram of primary classes (full class names, count + share on each bar), a rank-ordered Top-20 class table, and a "Comments on Findings" box

---

## ✅ Notes for GitHub testers
* The script does not include personal file paths.
* It is designed to work on any machine that has Python, the required packages, and the Playwright Chromium browser installed.
* `ada` and `uni-halle` are collected via browser automation (Playwright), not plain HTTP requests — expect a Chromium window/process to launch during the run.
* Just clone the repo, install dependencies, install the Playwright browser, and run `python Seeding-QDArchive.py`.

---

## 🧩 Source file
The main runnable file is:

* `Seeding-QDArchive.py`

Keep `requirements.txt` alongside it to make testing easy for others.

### `requirements.txt` contents
```
requests
pandas
openpyxl
fpdf2
beautifulsoup4
playwright
```