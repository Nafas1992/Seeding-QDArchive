# Seeding QDArchive: Automated Data Acquisition & Classification Pipeline
**Student ID:** 23542421  
**Course:** Applied Software Engineering Project (10 ECTS) / Seminar (5 ECTS)

---

## 🎯 Project Overview
This repository contains the full end-to-end automated pipeline developed for the **Seeding QDArchive** course. The project addresses the "chicken-and-egg" problem of attracting researchers to the new QDArchive prototype by building a robust metadata acquisition, homogenization, and industry-standard classification engine using open-source qualitative research data.

The system is fully developed across two distinct academic phases:
1. **Phase 1 (Data Acquisition):** Programmatic repository probing, scraping, and relational metadata logging.
2. **Phase 2 (Data Classification & Reporting):** Keyword standardization and smart industry mapping under the official **United Nations ISIC Rev 5** classification guidelines, followed by automated generation of computational deliverables.

---

## 🏛️ Assigned Repositories & Search Logic
Based on the official assignment for **StudentID 23542421**, the following four scientific sources are target-probed:
* **Repo 1 (ID 1):** Zenodo (`https://zenodo.org/`)
* **Repo 2 (ID 6):** Dataverse.no (`https://dataverse.no/`)
* **Repo 3 (ID 7):** ADA - Australian Data Archive (`https://ada.edu.au/`)
* **Repo 4 (ID 16):** Open Data LSA - Martin Luther University Halle-Wittenberg (`https://opendata.uni-halle.de/`)

### Systematic Search Terms:
The crawler automatically filters metadata packages across all assigned repositories using the required qualitative search queries:
1. `qdpx` (REFI-QDA Standard format)
2. `mqda` (MAXQDA Project format)
3. `interview study` (Qualitative transcript studies)

---

## 🛠️ Implementation & Technical Features

### 1. Relational Database Model (Phase 1 & 2 Constraints)
The pipeline strictly enforces the official SQLite relational database architecture. Metadata is dynamically structured into the following target tables:
* `PROJECTS`: Primary project meta, source URLs, timestamps, download methods, and assigned ISIC Rev 5 industrial classes.
* `LICENSES`: Accurate project-specific licensing strings parsed via descriptive Regex mapping.
* `FILES`: Asset tracking records (`PRIMARY_DATA` or `PROJECT_METADATA`) verifying dataset completeness with status outcomes.
* `KEYWORDS`: Tokenized key-terms assigned by authors.
* `PERSON_ROLE`: Participant role associations (e.g., mapping author configurations).

### 2. Phase 2 Advanced Refinements
* **Keyword Homogenization:** Automatically refines raw metadata tags by splitting comma/semicolon delimiters, shifting text to lowercase, trimming padding spaces, and replacing internal spaces with standard hyphens to ensure uniform index queries.
* **UN ISIC Rev 5 Classification Mapping:** Programmatically analyzes data profiles to allocate appropriate global industrial division classes (e.g., *Q85 - Education*, *N72 - Scientific research and development*, and *O82 - Office administrative support*).

---

## 📦 Prerequisites & Installation

The pipeline is written in Python 3.8+ and utilizes standard engineering packages alongside specialized reporting engines. Install all required dependencies using `pip`:

```bash
pip install pandas openpyxl matplotlib requests fpdf2