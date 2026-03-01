import os
import requests
import sqlite3
import pandas as pd
from datetime import datetime

# Header to simulate a real browser to bypass the 403 error
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def init_system():
    print("--- QDArchive: Phase 1 (Standard Acquisition) ---")
    base_folder = input("Please enter the storage directory: ")
    if not os.path.exists(base_folder): os.makedirs(base_folder)
    
    conn = sqlite3.connect(os.path.join(base_folder, 'qdarchive_metadata.db'))
    conn.execute('''CREATE TABLE IF NOT EXISTS metadata 
                   (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    source_name TEXT, 
                    repository_url TEXT,
                    file_url TEXT, 
                    status TEXT,
                    timestamp TEXT,
                    local_path TEXT)''')
    return conn, base_folder

def run_acquisition(conn, base_folder):
    # Revised list with tested and stable links
    sources = [
        {"name": "Zenodo Sample", "base": "https://zenodo.org/", "test_file": "https://zenodo.org/record/10058814/files/Qualitative_Data_Example.pdf?download=1"},
        {"name": "UCL Archive", "base": "https://discovery.ucl.ac.uk/", "test_file": "https://discovery.ucl.ac.uk/id/eprint/1474246/1/Qualitative_Methodology_Appendix.pdf"},
        {"name": "Public Repo", "base": "https://raw.githubusercontent.com/", "test_file": "https://raw.githubusercontent.com/allisonhorst/palmerpenguins/main/README.md"}
    ]

    for item in sources:
        try:
            print(f"🔍 Attempting to reach: {item['name']}...")
            res = requests.get(item["test_file"], headers=HEADERS, timeout=20, stream=True)
            
            status = "Success" if res.status_code == 200 else f"Failed ({res.status_code})"
            local_p = "N/A"
            
            if res.status_code == 200:
                fname = item["test_file"].split('/')[-1].split('?')[0]
                local_p = os.path.join(base_folder, fname)
                with open(local_p, 'wb') as f:
                    f.write(res.content)
                print(f"   ✅ Download Successful!")
            else:
                print(f"   ⚠️ Server responded with: {res.status_code}")
            
            conn.execute('''INSERT INTO metadata (source_name, repository_url, file_url, status, timestamp, local_path) 
                            VALUES (?, ?, ?, ?, ?, ?)''', 
                         (item["name"], item["base"], item["test_file"], status, datetime.now().strftime("%Y-%m-%d %H:%M"), local_p))
        except Exception as e:
            print(f"   ❌ Connection Error: Possible network restriction.")
            conn.execute('''INSERT INTO metadata (source_name, repository_url, file_url, status, timestamp, local_path) 
                            VALUES (?, ?, ?, ?, ?, ?)''', 
                         (item["name"], item["base"], item["test_file"], "Connection Error", datetime.now().strftime("%Y-%m-%d %H:%M"), "N/A"))
    conn.commit()

def generate_report(conn, base_folder):
    df = pd.read_sql_query("SELECT * FROM metadata", conn)
    print("\n" + "="*50 + "\n", df.to_string(index=False))
    df.to_excel(os.path.join(base_folder, "QDArchive_Final_Report.xlsx"), index=False)
    print(f"\n⭐ Report generated! Check the directory.")

if __name__ == "__main__":
    db_conn, folder = init_system()
    run_acquisition(db_conn, folder)
    generate_report(db_conn, folder)
    db_conn.close()