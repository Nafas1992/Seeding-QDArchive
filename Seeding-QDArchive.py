import os
import sqlite3
import requests
import pandas as pd
import re
from datetime import datetime
import time

# Specific settings according to your student number
STUDENT_ID = "23542421"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def create_db_tables(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # PROJECTS table - according to schema
    cursor.execute('''CREATE TABLE IF NOT EXISTS PROJECTS (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_string TEXT, repository_id INTEGER, repository_url TEXT, project_url TEXT,
        version TEXT, title TEXT, description TEXT, language TEXT, doi TEXT,
        license TEXT, upload_date DATE, download_date TIMESTAMP,
        download_repository_folder TEXT, download_project_folder TEXT, download_method TEXT
    )''')
    
    # FILES table with the addition of the status column (required according to the schema)
    cursor.execute('''CREATE TABLE IF NOT EXISTS FILES (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        project_id INTEGER, 
        file_name TEXT, 
        file_type TEXT, 
        status TEXT
    )''')
    
    cursor.execute('CREATE TABLE IF NOT EXISTS KEYWORDS (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, keyword TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS PERSON_ROLE (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, name TEXT, role TEXT)')
    conn.commit()
    return conn

def run_pipeline(conn):
    # List of 4 approved repositories
    repos = [
        {"id": 1, "name": "zenodo", "url": "https://zenodo.org/", "search": "https://zenodo.org/search?q="},
        {"id": 6, "name": "dataverse-no", "url": "https://dataverse.no/", "search": "https://dataverse.no/dataverse/root/?q="},
        {"id": 7, "name": "ada", "url": "https://ada.edu.au/", "search": "https://dataverse.ada.edu.au/dataverse/ada/?q="},
        {"id": 16, "name": "uni-halle", "url": "https://opendata.uni-halle.de/", "search": "https://opendata.uni-halle.de/simple-search?query="}
    ]
    terms = ["qdpx", "mqda", "interview study"]

    for repo in repos:
        for term in terms:
            try:
                formatted_term = term.replace(" ", "+")
                search_url = repo["search"] + formatted_term
                print(f"📡 Processing: {repo['name']} | Term: {term}")
                
                time.sleep(1) # Short delay for stability
                res = requests.get(search_url, headers=HEADERS, timeout=12)
                html = res.text
                
                # License extraction
                lic_match = re.search(r'(MIT|CC BY|CC0|Creative Commons|GPL)', html, re.IGNORECASE)
                found_license = lic_match.group(0) if lic_match else "UNKNOWN"
                
                # Extract date
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', html)
                found_date = date_match.group(0) if date_match else None
                
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                cursor = conn.cursor()
                cursor.execute('''INSERT INTO PROJECTS 
                    (query_string, repository_id, repository_url, project_url, title, description, 
                     language, license, upload_date, download_date, download_repository_folder, download_project_folder, download_method) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                    (term, repo["id"], repo["url"], search_url, f"Project {term}", "Phase 1: Metadata Extraction", 
                     "en", found_license, found_date, now, repo["name"], f"folder_{repo['id']}", "SCRAPING"))
                
                p_id = cursor.lastrowid
                cursor.execute('INSERT INTO KEYWORDS (project_id, keyword) VALUES (?, ?)', (p_id, term))
                conn.commit()
                print(f"✅ Saved successfully.")
            except Exception as e:
                print(f"❌ Error in {repo['name']}: {e}")

if __name__ == "__main__":
    target = input("📂 Path to save the database file: ")
    if not os.path.exists(target): os.makedirs(target)
    
    # Exact naming according to the format 12345678-sq26.db
    db_name = f"{STUDENT_ID}-sq26.db"
    db_file = os.path.join(target, db_name)
    
    c = create_db_tables(db_file)
    run_pipeline(c)
    c.close()
    
    print("\n" + "="*50)
    print(f"🎯 Done! Please upload ONLY this file to GitHub Root:")
    print(f"➡️ {db_name}")
    print("="*50)