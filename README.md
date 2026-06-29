# Seeding QDArchive: Automated Data Acquisition & Classification Pipeline
**Student ID:** 23542421  
**Course:** Applied Software Engineering Project (10 ECTS) / Seminar (5 ECTS)

---

## 🎯 What this script does
This repository contains a test-ready Python script named `Seeding-QDArchive.py`. It is designed so that anyone can clone the repository, install the required packages, and run the script without editing hard-coded system paths.

The script performs a simple acquisition workflow:
* prompts the user for a storage folder
* downloads test files from public repositories
* saves metadata into a local SQLite database
* writes a final Excel report using `pandas`

---

## 📦 Prerequisites
The script requires Python 3.8+ and the packages listed in `requirements.txt`.

Required Python packages for `Seeding-QDArchive.py`:

* `requests`
* `pandas`
* `openpyxl`

Install dependencies with:

```bash
pip install -r requirements.txt
```

If you want to run it in a clean virtual environment:

```bash
python -m venv .venv
# Windows
.venد\Scripts\activate
# macOS / Linux
source .venv/bin/activate
pip install -r requirements.txt
```

---

## ▶️ Running the script
From the folder that contains `Seeding-QDArchive.py`, run:

```bash
python Seeding-QDArchive.py
```

The script will ask:

```text
Please enter the storage directory:
```

Enter any valid folder path where you want outputs saved.
For example:

* `C:\Users\YourName\Documents\QDArchiveOutput`
* `./output`

If the folder does not exist, the script creates it automatically.

---

## 📁 Output files
After execution, the script creates:

* `qdarchive_metadata.db` — local SQLite metadata database
* `QDArchive_Final_Report.xlsx` — Excel report with the acquired metadata

> Note: `Seeding-QDArchive.py` does not generate a PDF file.

---

## ✅ Notes for GitHub testers
* The script does not include personal file paths.
* It is designed to work on any machine that has Python and the required packages installed.
* Just clone the repo, install dependencies, and run `python Seeding-QDArchive.py`.

---

## 🧩 Source file
The main runnable file is:

* `Seeding-QDArchive.py`

Keep `requirements.txt` alongside it to make testing easy for others.