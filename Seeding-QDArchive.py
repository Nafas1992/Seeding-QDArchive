import os
import sqlite3
import requests
import pandas as pd
import re
from datetime import datetime

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def create_db_tables(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # PROJECTS table with all r and o columns
    cursor.execute('''CREATE TABLE IF NOT EXISTS PROJECTS (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_string TEXT, repository_id INTEGER, repository_url TEXT, project_url TEXT,
        version TEXT, title TEXT, description TEXT, language TEXT, doi TEXT,
        license TEXT, upload_date DATE, download_date TIMESTAMP,
        download_repository_folder TEXT, download_project_folder TEXT, download_method TEXT
    )''')
    # Three other tables requested by the professor
    cursor.execute('CREATE TABLE IF NOT EXISTS FILES (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, file_name TEXT, file_type TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS KEYWORDS (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, keyword TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS PERSON_ROLE (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, name TEXT, role TEXT)')
    conn.commit()
    return conn

def run_pipeline(conn):
    # Tanks 7 and 16
    repos = [
        {"id": 7, "name": "ada", "url": "https://ada.edu.au/", "search": "https://dataverse.ada.edu.au/dataverse/ada/?q="},
        {"id": 16, "name": "uni-halle", "url": "https://opendata.uni-halle.de/", "search": "https://opendata.uni-halle.de/simple-search?query="}
    ]
    terms = ["qdpx", "mqda", "interview study"]

    for repo in repos:
        for term in terms:
            try:
                res = requests.get(repo["search"] + term, headers=HEADERS, timeout=10)
                html = res.text
                
                # License extraction (including MIT, CC BY, etc.)
                lic_match = re.search(r'(MIT|CC BY|CC0|Creative Commons|GPL)', html, re.IGNORECASE)
                found_license = lic_match.group(0) if lic_match else None
                
                # Date extraction
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', html)
                found_date = date_match.group(0) if date_match else None
                
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                cursor = conn.cursor()
                cursor.execute('''INSERT INTO PROJECTS 
                    (query_string, repository_id, repository_url, project_url, title, description, 
                     language, license, upload_date, download_date, download_repository_folder, download_project_folder, download_method) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                    (term, repo["id"], repo["url"], repo["search"]+term, f"Project {term}", "Phase 1: Metadata Extraction", 
                     "en", found_license, found_date, now, repo["name"], f"folder_{term}", "SCRAPING"))
                
                p_id = cursor.lastrowid
                cursor.execute('INSERT INTO KEYWORDS (project_id, keyword) VALUES (?, ?)', (p_id, term))
                conn.commit()
            except: pass

def export_final(db_path, excel_path):
    conn = sqlite3.connect(db_path)
    with pd.ExcelWriter(excel_path) as writer:
        for t_name in ['PROJECTS', 'FILES', 'KEYWORDS', 'PERSON_ROLE']:
            pd.read_sql_query(f"SELECT * FROM {t_name}", conn).to_excel(writer, sheet_name=t_name, index=False)
    conn.close()

if __name__ == "__main__":
    target = input("📂 File storage path: ")
    if not os.path.exists(target): os.makedirs(target)
    
    db_file = os.path.join(target, 'qdarchive_metadata.db')
    excel_file = os.path.join(target, 'Submission_Final.xlsx')
    
    c = create_db_tables(db_file)
    run_pipeline(c)
    export_final(db_file, excel_file)
    print(f"✅ The program has ended.")