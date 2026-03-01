# QDArchive - Seeding Project (Phase 1)

This repository contains the **Data Acquisition Pipeline** for the QDArchive project.

## Features
- **Automated Downloads**: Fetches qualitative data from open repositories.
- **Robustness**: Handles 404 and 403 errors without crashing.
- **Metadata Logging**: Saves all transaction details in an SQLite database.
- **Excel Reporting**: Automatically generates a summary report for evaluation.

## Installation
Run the following command to install dependencies:
```bash
pip install -r requirements.txt

python Seeding-QDArchive.py