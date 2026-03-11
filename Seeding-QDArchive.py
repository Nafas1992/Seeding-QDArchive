import os
import requests
import sqlite3
import pandas as pd
from datetime import datetime

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def init_system():
    print("\n" + "="*50)
    print("🚀 QDArchive Intelligence: Assigned Repos 7 (ADA) & 16 (Halle)")
    print("="*50)
    
    base_folder = input("📂 Please enter the storage directory: ")
    if not os.path.exists(base_folder): os.makedirs(base_folder)
    
    db_path = os.path.join(base_folder, 'qdarchive_metadata.db')
    conn = sqlite3.connect(db_path)
    
    conn.execute('''CREATE TABLE IF NOT EXISTS metadata 
                   (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    repo_id INTEGER,
                    source_name TEXT, 
                    endpoint_url TEXT,
                    status_code TEXT,
                    usability_note TEXT,
                    timestamp TEXT)''')
    return conn, base_folder

def run_assigned_pipeline(conn, base_folder):
    # Adjusted based on your final approval (7 and 16)
    assigned_sources = [
        {"id": 7, "name": "ADA (Australian Data Archive)", "url": "https://ada.edu.au/"},
        {"id": 16, "name": "Open Data LSA (Uni-Halle)", "url": "https://opendata.uni-halle.de/"}
    ]

    print("\n🔍 Probing Assigned Repositories...")
    for item in assigned_sources:
        try:
            print(f"📡 Connecting to Repo {item['id']}: {item['name']}...")
            res = requests.get(item["url"], headers=HEADERS, timeout=15)
            
            if res.status_code == 200:
                note = "Accessible. Operational for automated probing."
            elif res.status_code == 403:
                note = "Access Restricted (403). Possible IP block or API needed."
            else:
                note = f"Status {res.status_code}. Manual check required."

            conn.execute('''INSERT INTO metadata (repo_id, source_name, endpoint_url, status_code, usability_note, timestamp) 
                            VALUES (?, ?, ?, ?, ?, ?)''', 
                         (item["id"], item["name"], item["url"], str(res.status_code), note, datetime.now().strftime("%Y-%m-%d %H:%M")))
            print(f"   ✅ Logged: {note}")
        except:
            print(f"   ❌ Connection failed for {item['name']}")
    
    conn.commit()

def generate_report(conn, base_folder):
    df = pd.read_sql_query("SELECT * FROM metadata", conn)
    report_file = os.path.join(base_folder, "QDArchive_Final_Report.xlsx")
    df.to_excel(report_file, index=False)
    print("\n" + "="*60 + "\n", df[['repo_id', 'source_name', 'status_code', 'usability_note']])
    print(f"\n⭐ Final Report for Repos 7 & 16 generated: {report_file}")

if __name__ == "__main__":
    db_conn, target_folder = init_system()
    run_assigned_pipeline(db_conn, target_folder)
    generate_report(db_conn, target_folder)
    db_conn.close()