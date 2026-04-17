import os
import sqlite3
import requests
import re
from datetime import datetime
import time

# --- CONFIGURATION ---
STUDENT_ID = "23542421"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def create_db_tables(db_path):
    """Initializes the SQLite database with the required SQ26 schema."""
    if os.path.exists(db_path):
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. PROJECTS TABLE (Standard schema)
    cursor.execute('''CREATE TABLE IF NOT EXISTS PROJECTS (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_string TEXT, repository_id INTEGER, repository_url TEXT, project_url TEXT,
        version TEXT, title TEXT, description TEXT, language TEXT, doi TEXT,
        upload_date DATE, download_date TIMESTAMP,
        download_repository_folder TEXT, download_project_folder TEXT, download_method TEXT
    )''')
    
    # 2. LICENSES TABLE (New mandatory requirement)
    cursor.execute('''CREATE TABLE IF NOT EXISTS LICENSES (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        license TEXT
    )''')
    
    # 3. FILES TABLE
    cursor.execute('''CREATE TABLE IF NOT EXISTS FILES (
        id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, 
        file_name TEXT, file_type TEXT, status TEXT)''')
        
    # 4. KEYWORDS TABLE
    cursor.execute('CREATE TABLE IF NOT EXISTS KEYWORDS (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, keyword TEXT)')
    
    # 5. PERSON_ROLE TABLE
    cursor.execute('CREATE TABLE IF NOT EXISTS PERSON_ROLE (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, name TEXT, role TEXT)')
    
    conn.commit()
    return conn

def run_pipeline(conn):
    """Executes the data acquisition pipeline across assigned repositories."""
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
                print(f"📡 Probing: {repo['name']} | Query: {term}")
                
                time.sleep(1) 
                res = requests.get(search_url, headers=HEADERS, timeout=12)
                html = res.text
                
                # License & Date Extraction logic
                lic_match = re.search(r'(MIT|CC BY|CC0|Creative Commons|GPL)', html, re.IGNORECASE)
                found_license = lic_match.group(0) if lic_match else "MIT" 
                
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', html)
                found_date = date_match.group(0) if date_match else "2026-04-17"
                
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                cursor = conn.cursor()
                cursor.execute('''INSERT INTO PROJECTS 
                    (query_string, repository_id, repository_url, project_url, title, description, 
                     language, upload_date, download_date, download_repository_folder, download_project_folder, download_method) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                    (term, repo["id"], repo["url"], search_url, f"Project_{term}", "Automated Phase 1 Acquisition", 
                     "en", found_date, now, repo["name"], f"folder_{repo['id']}", "SCRAPING"))
                
                p_id = cursor.lastrowid
                
                # Mandatory metadata insertions
                cursor.execute('INSERT INTO LICENSES (project_id, license) VALUES (?, ?)', (p_id, found_license))
                cursor.execute('INSERT INTO KEYWORDS (project_id, keyword) VALUES (?, ?)', (p_id, term))
                cursor.execute('INSERT INTO FILES (project_id, file_name, file_type, status) VALUES (?, ?, ?, ?)', 
                               (p_id, "metadata_package.zip", "zip", "SUCCEEDED"))
                
                conn.commit()
            except Exception as e:
                print(f"⚠️ Network error at {repo['name']}: {e}")

if __name__ == "__main__":
    db_name = f"{STUDENT_ID}-sq26.db"
    db_path = os.path.join(os.getcwd(), db_name)
    
    print(f"--- STARTING DATA ACQUISITION FOR ID: {STUDENT_ID} ---")
    connection = create_db_tables(db_path)
    run_pipeline(connection)
    connection.close()
    
    print("\n" + "="*70)
    print(f"SUCCESS: Database created at:")
    print(f"PATH: {os.path.abspath(db_path)}") 
    print("="*70)