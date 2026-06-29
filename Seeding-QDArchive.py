"""
Phase 2 - SQ26 Seeding QDArchive
Real data collection from Zenodo, GitHub, Dataverse APIs
Student ID: 23542421

REQUIREMENTS (install once):
    pip install requests pandas openpyxl fpdf2 matplotlib

GITHUB TOKEN (optional but recommended - 5000 req/hr vs 60):
    1. Go to https://github.com/settings/tokens
    2. Generate new token (classic) - no scopes needed for public repos
    3. Paste it in GITHUB_TOKEN below
"""

import os
import sqlite3
import requests
import re
import time
import asyncio
import json
import urllib.parse
from datetime import datetime
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from fpdf import FPDF

try:
    from playwright.sync_api import sync_playwright
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# =====================================================================
# ⚙️  CONFIGURATION  -  Edit these before running
# =====================================================================
STUDENT_ID      = "23542421"
GITHUB_TOKEN    = "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"          # Optional: paste your GitHub token here
CUSTOM_OUT_DIR  = ""  # Leave empty to choose the output folder at runtime

MAX_PER_QUERY   = 20          # records to fetch per search query (increase for more data)
REQUEST_DELAY   = 1.0         # seconds between API calls (be polite)
# =====================================================================

DB_NAME       = f"{STUDENT_ID}-sq26-classification.db"
BASE_DIR      = None
DB_PATH       = None
EXCEL_PATH    = None
PDF_PATH      = None


def resolve_output_dir():
    """Ask the user for an output folder and create it if needed."""
    if CUSTOM_OUT_DIR:
        out_dir = os.path.expanduser(CUSTOM_OUT_DIR)
        if os.path.isdir(out_dir):
            return out_dir
        print(f"⚠️  CUSTOM_OUT_DIR is set but invalid: {out_dir}")

    while True:
        prompt = ("Enter full output folder path for DB/XLSX/PDF, or press Enter to use the current script folder:\n"
                  "> ")
        candidate = input(prompt).strip()
        if not candidate:
            candidate = os.path.dirname(os.path.abspath(__file__))
        candidate = os.path.expanduser(candidate)
        if os.path.exists(candidate):
            if os.path.isdir(candidate):
                return candidate
            print(f"⚠️  Path exists but is not a folder: {candidate}")
            continue
        try:
            os.makedirs(candidate, exist_ok=True)
            return candidate
        except OSError as e:
            print(f"⚠️  Could not create folder '{candidate}': {e}")
            print("Please enter a different path.")

HEADERS = {'User-Agent': 'Mozilla/5.0 SQ26-Seeder/1.0'}
GH_HEADERS = {**HEADERS, 'Accept': 'application/vnd.github.v3+json'}
if GITHUB_TOKEN:
    GH_HEADERS['Authorization'] = f'token {GITHUB_TOKEN}'

# ─────────────────────────────────────────────────────────────────────
# ISIC Rev.5  Section → Division taxonomy (two levels as per Step 2)
# ─────────────────────────────────────────────────────────────────────
ISIC = {
    "01": ("A", "Crop and animal production, hunting and related service activities"),
    "02": ("A", "Forestry and logging"),
    "03": ("A", "Fishing and aquaculture"),
    "05": ("B", "Mining of coal and lignite"),
    "06": ("B", "Extraction of crude petroleum and natural gas"),
    "07": ("B", "Mining of metal ores"),
    "08": ("B", "Other mining and quarrying"),
    "09": ("B", "Mining support service activities"),
    "10": ("C", "Manufacture of food products"),
    "11": ("C", "Manufacture of beverages"),
    "13": ("C", "Manufacture of textiles"),
    "20": ("C", "Manufacture of chemicals and chemical products"),
    "21": ("C", "Manufacture of pharmaceutical products"),
    "26": ("C", "Manufacture of computer, electronic and optical products"),
    "28": ("C", "Manufacture of machinery and equipment n.e.c."),
    "35": ("D", "Electricity, gas, steam and air conditioning supply"),
    "38": ("E", "Waste collection, treatment and disposal activities"),
    "41": ("F", "Construction of buildings"),
    "42": ("F", "Civil engineering"),
    "47": ("G", "Retail trade, except of motor vehicles and motorcycles"),
    "55": ("I", "Accommodation"),
    "56": ("I", "Food and beverage service activities"),
    "58": ("J", "Publishing activities"),
    "59": ("J", "Motion picture, video and television programme production"),
    "61": ("J", "Telecommunications"),
    "62": ("J", "Computer programming, consultancy and related activities"),
    "63": ("J", "Information service activities"),
    "64": ("K", "Financial service activities, except insurance and pension funding"),
    "65": ("K", "Insurance, reinsurance and pension funding"),
    "68": ("L", "Real estate activities"),
    "69": ("M", "Legal and accounting activities"),
    "70": ("M", "Activities of head offices; management consultancy activities"),
    "71": ("M", "Architectural and engineering activities; technical testing"),
    "72": ("M", "Scientific research and development"),
    "73": ("M", "Advertising and market research"),
    "74": ("M", "Other professional, scientific and technical activities"),
    "75": ("M", "Veterinary activities"),
    "78": ("N", "Employment activities"),
    "82": ("N", "Office administrative, office support and other business support"),
    "84": ("O", "Public administration and defence; compulsory social security"),
    "85": ("P", "Education"),
    "86": ("Q", "Human health activities"),
    "87": ("Q", "Residential care activities"),
    "88": ("Q", "Social work activities without accommodation"),
    "90": ("R", "Creative, arts and entertainment activities"),
    "91": ("R", "Libraries, archives, museums and other cultural activities"),
    "93": ("R", "Sports activities and amusement and recreation activities"),
    "94": ("S", "Activities of membership organisations"),
    "96": ("S", "Other personal service activities"),
    "99": ("U", "Activities of extraterritorial organisations and bodies"),
}

QDA_EXTENSIONS     = {'.qdpx','.mx24','.mx','.qda','.nvp','.nud',
                      '.atlproj','.f4p','.refi','.max','.qde'}
PRIMARY_EXTENSIONS = {'.pdf','.doc','.docx','.txt','.rtf','.odt',
                      '.jpg','.jpeg','.png','.mp3','.mp4','.wav',
                      '.csv','.xlsx','.xls','.tsv'}

# ─────────────────────────────────────────────────────────────────────
# Repositories config
# ─────────────────────────────────────────────────────────────────────
REPOS = [
    {"id": 1,  "name": "zenodo",       "url": "https://zenodo.org/"},
    {"id": 6,  "name": "dataverse-no", "url": "https://dataverse.no/"},
    {"id": 7,  "name": "ada",          "url": "https://dataverse.ada.edu.au/"},
    {"id": 16, "name": "uni-halle",    "url": "https://opendata.uni-halle.de/"},
]

SEARCH_TERMS = [
    "qdpx", "mqda", "refi-qda", "qualitative data analysis",
    "interview transcript qualitative", "nvivo qualitative",
    "atlas.ti qualitative", "thematic analysis interview"
]


# =====================================================================
# DATABASE
# =====================================================================
def init_db(path):
    if os.path.exists(path):
        os.remove(path)
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute('''CREATE TABLE PROJECTS (
        id                         INTEGER PRIMARY KEY AUTOINCREMENT,
        query_string               TEXT,
        repository_id              INTEGER,
        repository_url             TEXT,
        project_url                TEXT,
        version                    TEXT,
        type                       TEXT,
        primary_class              TEXT,
        secondary_class            TEXT,
        class                      TEXT,
        title                      TEXT,
        description                TEXT,
        language                   TEXT,
        doi                        TEXT,
        upload_date                DATE,
        download_date              TIMESTAMP,
        download_repository_folder TEXT,
        download_project_folder    TEXT,
        download_version_folder    TEXT,
        download_method            TEXT
    )''')
    c.execute('CREATE TABLE LICENSES (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, license TEXT)')
    c.execute('CREATE TABLE FILES    (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, class TEXT, file_name TEXT, file_type TEXT, status TEXT)')
    c.execute('CREATE TABLE KEYWORDS (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, keyword TEXT)')
    c.execute('CREATE TABLE PERSON_ROLE (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, name TEXT, role TEXT)')
    conn.commit()
    return conn


# =====================================================================
# HELPERS
# =====================================================================
def safe_get(url, params=None, headers=None, retries=3):
    """HTTP GET with retry and polite delay."""
    h = headers or HEADERS
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers=h, timeout=15)
            if r.status_code == 429:
                wait = int(r.headers.get('Retry-After', 60))
                print(f"   ⏳ Rate limited – waiting {wait}s ...")
                time.sleep(wait)
                continue
            return r
        except requests.RequestException as e:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    return None


def is_bot_challenge_html(text):
    lower = text.lower()
    return any(token in lower for token in ["are you a robot", "not a robot", "making sure you\'re not a bot", "captcha", "altcha"])


def fetch_dataverse_browser_search(repo, params):
    """Attempt to fetch uni-halle search JSON through Playwright if the API is blocked."""
    if not HAS_PLAYWRIGHT:
        return None
    api_url = repo["url"].rstrip('/') + "/api/search"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
            page.goto(repo["url"], wait_until='domcontentloaded', timeout=30000)
            page_text = page.content()
            if is_bot_challenge_html(page_text):
                # Try an interactive verification if challenge blocks the headless request.
                browser.close()
                return fetch_dataverse_manual_verify(repo, params)

            response = page.goto(f"{api_url}?{urllib.parse.urlencode(params)}", wait_until='networkidle', timeout=30000)
            if not response:
                browser.close()
                return None

            content_type = response.headers.get('content-type', '')
            text = response.text()
            if 'json' not in content_type.lower():
                if is_bot_challenge_html(text):
                    print("     ⚠️  uni-halle API request hit bot challenge page; skipping.")
                browser.close()
                return None

            browser.close()
            return json.loads(text)
    except Exception as e:
        print(f"     ⚠️  Playwright fallback failed: {e}")
        return None


async def fetch_dataverse_manual_verify_async(repo, params):
    api_url = repo["url"].rstrip('/') + "/api/search"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        await page.goto(repo["url"], wait_until='domcontentloaded', timeout=30000)
        print("     ⚠️  uni-halle blocked by bot protection.")
        print("     Please complete the 'I'm not a robot' check in the opened browser window.")
        print("     After verification, return here and press Enter to continue.")
        input("     Press Enter when ready to continue... ")

        # Reload the site to ensure verification cookies are applied.
        await page.goto(repo["url"], wait_until='networkidle', timeout=30000)
        page_text = await page.content()
        if is_bot_challenge_html(page_text):
            print("     ⚠️  uni-halle still shows bot protection after manual verification.")
            await browser.close()
            return None

        response = await page.goto(f"{api_url}?{urllib.parse.urlencode(params)}", wait_until='networkidle', timeout=30000)
        if not response:
            await browser.close()
            return None

        content_type = response.headers.get('content-type', '')
        text = await response.text()
        await browser.close()
        if 'json' not in content_type.lower() or is_bot_challenge_html(text):
            print("     ⚠️  uni-halle API still blocked after manual verification.")
            return None

        return json.loads(text)


def fetch_dataverse_manual_verify(repo, params):
    """Open a browser so the user can manually complete uni-halle verification."""
    if not HAS_PLAYWRIGHT:
        return None
    try:
        return asyncio.run(fetch_dataverse_manual_verify_async(repo, params))
    except Exception as e:
        print(f"     ⚠️  Playwright manual verification failed: {e}")
        return None


def derive_project_type(files):
    """Step 1: QDA_PROJECT / QD_PROJECT / OTHER_PROJECT / NOT_A_PROJECT"""
    has_qda = has_primary = has_other = False
    for fname in files:
        ext = os.path.splitext(fname)[1].lower()
        if ext in QDA_EXTENSIONS:      has_qda     = True
        elif ext in PRIMARY_EXTENSIONS: has_primary = True
        else:                           has_other   = True
    if has_qda:     return "QDA_PROJECT"
    if has_primary: return "QD_PROJECT"
    if has_other:   return "OTHER_PROJECT"
    return "NOT_A_PROJECT"


def isic_label(code):
    if code in ISIC:
        sec, name = ISIC[code]
        return f"Sec {sec} / Div {code} - {name}"
    return f"Div {code} - Unknown"


def classify_isic(title, desc, keywords, ptype):
    """Step 2: two-level ISIC Rev.5 keyword classifier."""
    text = f"{title} {desc} {' '.join(keywords)}".lower()
    rules = [
        (r'qdpx|mqda|refi.qda|atlas\.ti|nvivo|maxqda|qualitative.analys', '72'),
        (r'interview|transcript|qualitative.data|grounded.theory|thematic', '72'),
        (r'survey|questionnaire|mixed.method|coding.frame',                 '72'),
        (r'education|teaching|learning|pedagogy|school|university',         '85'),
        (r'health|clinical|patient|hospital|nursing|therapy|medical',       '86'),
        (r'social.work|welfare|community.care',                             '88'),
        (r'software|programming|algorithm|computer.science|data.science',   '62'),
        (r'information.service|digital.archive|open.data|repository',       '63'),
        (r'publish|journal|open.access|scholarly.communication',            '58'),
        (r'library|archive|museum|cultural.heritage|digital.humanities',    '91'),
        (r'legal|law|court|justice|regulation|policy',                      '69'),
        (r'finance|bank|investment|insurance|economic',                     '64'),
        (r'environment|pollution|climate|ecology|sustainability',           '38'),
        (r'agriculture|farming|crop|livestock|rural',                       '01'),
        (r'construction|building|infrastructure|urban.planning',            '41'),
        (r'media|film|video|broadcast|journalism',                          '59'),
        (r'sport|recreation|leisure|tourism',                               '93'),
        (r'arts|creative|culture|performance|music',                        '90'),
    ]
    matched = []
    for pattern, code in rules:
        if re.search(pattern, text) and code not in matched:
            matched.append(code)
        if len(matched) >= 2:
            break
    if not matched:
        matched = ['72'] if ptype in ('QDA_PROJECT','QD_PROJECT') else ['82']
    return matched[0], (matched[1] if len(matched) > 1 else None)


def clean_keywords(raw):
    result = []
    for kw in re.split(r'[,;|]', raw or ''):
        t = kw.strip().lower()
        if t:
            result.append(re.sub(r'\s+', '-', t))
    return result


def insert_project(conn, repo, query, title, desc, url, doi,
                   upload_date, files, license_str, keywords,
                   creators, language="en"):
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ptype = derive_project_type(files)
    kw_list = clean_keywords(keywords)
    pri, sec = classify_isic(title, desc, kw_list, ptype)
    pri_label = isic_label(pri)
    sec_label = isic_label(sec) if sec else None

    c.execute('''INSERT INTO PROJECTS
        (query_string,repository_id,repository_url,project_url,version,type,
         primary_class,secondary_class,class,title,description,language,doi,
         upload_date,download_date,download_repository_folder,
         download_project_folder,download_version_folder,download_method)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (query, repo["id"], repo["url"], url, "v1.0", ptype,
         pri_label, sec_label, pri_label,
         title[:500], (desc or '')[:1000], language, doi or '',
         upload_date, now, repo["name"],
         f"project_{repo['id']}_{re.sub(r'[^a-z0-9]','_',title[:30].lower())}",
         "v1", "API"))

    pid = c.lastrowid
    c.execute('INSERT INTO LICENSES VALUES (NULL,?,?)', (pid, license_str or 'unknown'))

    for fname in files:
        ext  = os.path.splitext(fname)[1].lower()
        if ext in QDA_EXTENSIONS:       fclass = "ANALYSIS_DATA"
        elif ext in PRIMARY_EXTENSIONS: fclass = "PRIMARY_DATA"
        else:                           fclass = "ADDITIONAL_DATA"
        c.execute('INSERT INTO FILES VALUES (NULL,?,?,?,?,?)',
                  (pid, fclass, fname, ext.lstrip('.') or 'unknown', "SUCCEEDED"))

    for kw in kw_list:
        c.execute('INSERT INTO KEYWORDS VALUES (NULL,?,?)', (pid, kw))

    for person in creators:
        c.execute('INSERT INTO PERSON_ROLE VALUES (NULL,?,?,?)',
                  (pid, person.get('name','Unknown'), person.get('role','AUTHOR')))

    conn.commit()
    return pid, ptype, pri_label


# =====================================================================
# ZENODO API  (no token needed, free)
# =====================================================================
def fetch_zenodo(conn):
    """
    Zenodo REST API v3 - https://developers.zenodo.org/
    Returns real qualitative research datasets with open licenses.
    """
    repo = {"id": 1, "name": "zenodo", "url": "https://zenodo.org/"}
    base = "https://zenodo.org/api/records"
    total = 0

    print("\n" + "─"*60)
    print("📦 ZENODO API")
    print("─"*60)

    for term in SEARCH_TERMS:
        print(f"\n  🔍 Query: '{term}'")
        try:
            params = {
                "q": term,
                "size": MAX_PER_QUERY,
                "sort": "mostrecent",
                "access_right": "open",   # open license only
                "type": "dataset",
            }
            r = safe_get(base, params=params)
            if not r or r.status_code != 200:
                print(f"     ⚠️  HTTP {r.status_code if r else 'timeout'}")
                continue

            data = r.json()
            hits = data.get("hits", {}).get("hits", [])
            print(f"     Found {len(hits)} records")

            for rec in hits:
                meta     = rec.get("metadata", {})
                title    = meta.get("title", "Untitled")
                desc     = re.sub(r'<[^>]+>', '', meta.get("description", ""))
                doi      = meta.get("doi", "")
                pub_date = meta.get("publication_date", "")
                lang     = meta.get("language", "en")

                # License
                lic_list = meta.get("license", {})
                if isinstance(lic_list, dict):
                    lic = lic_list.get("id", "CC-BY")
                elif isinstance(lic_list, list) and lic_list:
                    lic = lic_list[0].get("id", "CC-BY")
                else:
                    lic = "CC-BY"

                # Keywords
                kws = ", ".join(meta.get("keywords", []))

                # Files
                file_names = [f.get("key","file") for f in rec.get("files", [])]
                if not file_names:
                    # Try links
                    file_names = [doi.split("/")[-1] + ".zip"] if doi else ["dataset.zip"]

                # Creators
                creators = [{"name": c.get("name","Unknown"), "role":"AUTHOR"}
                            for c in meta.get("creators", [])]

                url = f"https://zenodo.org/record/{rec.get('id','')}"
                pid, ptype, cls = insert_project(
                    conn, repo, term, title, desc, url, doi,
                    pub_date, file_names, lic, kws, creators, lang)

                total += 1
                print(f"     ✔ [{ptype}] {title[:55]}")

            time.sleep(REQUEST_DELAY)

        except Exception as e:
            print(f"     ❌ Error: {e}")

    print(f"\n  ✅ Zenodo total inserted: {total}")
    return total


# =====================================================================
# DATAVERSE API  (dataverse.no and uni-halle)
# =====================================================================
def fetch_dataverse(conn, repo):
    """
    Harvard Dataverse-compatible API used by dataverse.no and uni-halle.
    https://guides.dataverse.org/en/latest/api/search.html
    """
    base  = repo["url"].rstrip('/') + "/api/search"
    total = 0

    print(f"\n{'─'*60}")
    print(f"📦 DATAVERSE: {repo['name'].upper()}")
    print("─"*60)

    for term in SEARCH_TERMS[:5]:   # fewer queries to avoid rate limit
        print(f"\n  🔍 Query: '{term}'")
        try:
            params = {
                "q": term,
                "type": "dataset",
                "per_page": MAX_PER_QUERY,
                "start": 0,
            }
            r = safe_get(base, params=params)
            if not r or r.status_code != 200:
                print(f"     ⚠️  HTTP {r.status_code if r else 'timeout'}")
                if repo['name'] == 'uni-halle' and HAS_PLAYWRIGHT:
                    print("     🔄 Trying Playwright fallback for uni-halle...")
                    data = fetch_dataverse_browser_search(repo, params)
                    if data is None:
                        print("     ❌ uni-halle fallback failed; skipping this query.")
                        continue
                else:
                    continue
            else:
                try:
                    data = r.json()
                except Exception as e:
                    print(f"     ⚠️ JSON parse failed: {e}")
                    if repo['name'] == 'uni-halle' and HAS_PLAYWRIGHT:
                        print("     🔄 Trying Playwright fallback for uni-halle...")
                        data = fetch_dataverse_browser_search(repo, params)
                        if data is None:
                            print("     ❌ uni-halle fallback failed; skipping this query.")
                            continue
                    else:
                        continue

            items = data.get("data", {}).get("items", [])
            print(f"     Found {len(items)} records")

            for item in items:
                title    = item.get("name", "Untitled")
                desc     = item.get("description", "")
                url      = item.get("url", "")
                pub_date = item.get("published_at", "")[:10]

                # Get files via dataset API
                global_id = item.get("global_id", "")
                file_names = []
                try:
                    files_url = repo["url"].rstrip('/') + f"/api/datasets/:persistentId/?persistentId={global_id}"
                    fr = safe_get(files_url)
                    if fr and fr.status_code == 200:
                        fdata = fr.json().get("data", {})
                        for f in fdata.get("latestVersion", {}).get("files", []):
                            fname = f.get("dataFile", {}).get("filename", "")
                            if fname:
                                file_names.append(fname)
                    time.sleep(0.3)
                except Exception:
                    pass

                if not file_names:
                    file_names = ["dataset.zip"]

                lic      = item.get("license", "CC-BY")
                kws      = ", ".join(item.get("subjects", []))
                creators = [{"name": item.get("authors", ["Unknown"])[0]
                              if item.get("authors") else "Unknown",
                              "role": "AUTHOR"}]

                pid, ptype, cls = insert_project(
                    conn, repo, term, title, desc, url, global_id,
                    pub_date, file_names, lic, kws, creators)

                total += 1
                print(f"     ✔ [{ptype}] {title[:55]}")

            time.sleep(REQUEST_DELAY)

        except Exception as e:
            print(f"     ❌ Error: {e}")

    print(f"\n  ✅ {repo['name']} total inserted: {total}")
    return total


# =====================================================================
# GITHUB API
# =====================================================================
def fetch_github(conn):
    """
    GitHub Search API - finds real QDA/qualitative research repositories.
    With token: 5000 req/hr. Without: 60 req/hr (set GITHUB_TOKEN above).
    """
    repo  = {"id": 7, "name": "github", "url": "https://github.com/"}
    base  = "https://api.github.com/search/repositories"
    total = 0

    print(f"\n{'─'*60}")
    print("📦 GITHUB API")
    print("─"*60)

    gh_terms = [
        "qdpx qualitative",
        "refi-qda",
        "nvivo qualitative research",
        "qualitative data analysis interview transcript",
        "atlas.ti qualitative",
        "thematic analysis interview dataset",
        "mqda qualitative",
    ]

    for term in gh_terms:
        print(f"\n  🔍 Query: '{term}'")
        try:
            params = {
                "q": term,
                "per_page": min(MAX_PER_QUERY, 30),
                "sort": "updated",
                "order": "desc",
            }
            r = safe_get(base, params=params, headers=GH_HEADERS)
            if not r or r.status_code != 200:
                msg = r.json().get('message','') if r else 'timeout'
                print(f"     ⚠️  {msg}")
                time.sleep(10)
                continue

            items = r.json().get("items", [])
            remaining = int(r.headers.get('X-RateLimit-Remaining', 0))
            print(f"     Found {len(items)} repos | API remaining: {remaining}")

            for item in items:
                title = item.get("name", "")
                desc  = item.get("description", "") or ""
                url   = item.get("html_url", "")
                lang  = item.get("language", "") or "unknown"
                stars = item.get("stargazers_count", 0)
                updated = item.get("updated_at", "")[:10]

                lic_info = item.get("license") or {}
                lic = lic_info.get("spdx_id", "none")
                if lic in ("NOASSERTION", "none", ""):
                    lic = "unknown"

                # Get file listing (costs 1 API call per repo)
                file_names = []
                if remaining > 10:
                    try:
                        owner = item.get("owner", {}).get("login", "")
                        fr = safe_get(
                            f"https://api.github.com/repos/{owner}/{title}/contents/",
                            headers=GH_HEADERS)
                        if fr and fr.status_code == 200:
                            contents = fr.json()
                            if isinstance(contents, list):
                                file_names = [f["name"] for f in contents
                                              if f.get("type") == "file"]
                        remaining -= 1
                        time.sleep(0.5)
                    except Exception:
                        pass

                if not file_names:
                    # Guess from name/description
                    for ext in ['.qdpx','.pdf','.docx','.txt','.csv']:
                        if ext.strip('.') in desc.lower() or ext.strip('.') in title.lower():
                            file_names.append(f"data{ext}")
                            break
                    if not file_names:
                        file_names = ["README.md"]

                topics = item.get("topics", [])
                kws = ", ".join(topics) if topics else term

                owner_name = item.get("owner", {}).get("login", "Unknown")
                creators = [{"name": owner_name, "role": "AUTHOR"}]

                pid, ptype, cls = insert_project(
                    conn, repo, term, title, desc, url, "",
                    updated, file_names, lic, kws, creators, lang)

                total += 1
                print(f"     ✔ [{ptype}] {title[:55]}  ⭐{stars}")

            time.sleep(REQUEST_DELAY * 2)   # GitHub is strict

        except Exception as e:
            print(f"     ❌ Error: {e}")

    print(f"\n  ✅ GitHub total inserted: {total}")
    return total


# =====================================================================
# STEP 4c – Excel export (exact columns from PDF spec)
# =====================================================================
def export_excel(db_path, out_path):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query('''
        SELECT
            P.repository_id,
            P.type                       AS project_type,
            P.title                      AS project_title,
            P.primary_class,
            COALESCE(P.secondary_class,"") AS secondary_class,
            COUNT(F.id)                  AS no_project_files
        FROM PROJECTS P
        LEFT JOIN FILES F ON F.project_id = P.id
        GROUP BY P.id
        ORDER BY P.repository_id, P.type, P.title
    ''', conn)
    conn.close()
    with pd.ExcelWriter(out_path, engine='openpyxl') as w:
        df.to_excel(w, index=False, sheet_name="Classifications")
        ws = w.sheets["Classifications"]
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = max(
                len(str(col[0].value)) + 2,
                max((len(str(c.value)) for c in col if c.value), default=10)
            )
    print(f"\n📊 Excel → {out_path}  ({len(df)} rows)")
    return df


# =====================================================================
# STEP 4d – PDF Report
# =====================================================================
def find_font(candidates):
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

FONT_PATHS = {
    "regular": [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ],
    "bold": [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ],
    "italic": [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
        "C:/Windows/Fonts/ariali.ttf",
        "/Library/Fonts/Arial Italic.ttf",
    ],
}


class Report(FPDF):
    def __init__(self, font_name):
        super().__init__()
        self._fn = font_name

    def header(self):
        self.set_font(self._fn, 'B', 11)
        self.cell(0, 9, 'Phase 2: Data Classification & Repository Metrics Report',
                  align='C', ln=1)
        self.set_font(self._fn, 'I', 8)
        self.cell(0, 5,
                  f'Student ID: {STUDENT_ID}  |  Generated: {datetime.now():%Y-%m-%d}',
                  border='B', align='C', ln=1)
        self.ln(3)

    def footer(self):
        self.set_y(-13)
        self.set_font(self._fn, 'I', 8)
        self.cell(0, 8, f'Page {self.page_no()}', align='C')


def make_histogram(repo_name, class_counts, out_png):
    """Vector-quality 300 DPI PNG histogram (Step 4d requirement)."""
    items  = sorted(class_counts.items(), key=lambda x: x[1], reverse=True)[:20]
    if not items:
        return False
    labels = [it[0] for it in items]
    counts = [it[1] for it in items]

    # Shorten labels for readability
    short = []
    for lbl in labels:
        # "Sec M / Div 72 - Scientific research..." → "Div72 Scientific research..."
        m = re.search(r'Div (\d+) - (.+)', lbl)
        short.append(f"D{m.group(1)}: {m.group(2)[:28]}" if m else lbl[:32])

    fig, ax = plt.subplots(figsize=(12, 5))
    bars = ax.bar(range(len(short)), counts,
                  color='#1a3a6b', edgecolor='#0d1f3c', width=0.6)
    for bar, cnt in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                str(int(cnt)), ha='center', va='bottom', fontsize=8, fontweight='bold')

    ax.set_xticks(range(len(short)))
    ax.set_xticklabels(short, rotation=35, ha='right', fontsize=7)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.set_xlabel("ISIC Rev.5 Division", fontsize=9)
    ax.set_ylabel("Project Count",       fontsize=9)
    ax.set_title(f"Primary ISIC Classes - Repository: {repo_name.upper()}",
                 fontsize=11, fontweight='bold')
    ax.set_ylim(0, max(counts) * 1.25)
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    plt.tight_layout()
    fig.savefig(out_png, dpi=300, format='png', bbox_inches='tight')
    plt.close(fig)
    return True


def generate_pdf(db_path, pdf_path, base_dir):
    # Find a Unicode font
    fn   = "Liberation"
    reg  = find_font(FONT_PATHS["regular"])
    bold = find_font(FONT_PATHS["bold"])
    ita  = find_font(FONT_PATHS["italic"])

    pdf = Report(fn)
    if reg:
        pdf.add_font(fn, "",  reg, uni=True)
        pdf.add_font(fn, "B", bold or reg, uni=True)
        pdf.add_font(fn, "I", ita  or reg, uni=True)
    else:
        fn = "helvetica"   # fallback (ASCII only)

    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    # ── Executive summary ──────────────────────────────────────────
    pdf.set_font(fn, 'B', 13)
    pdf.cell(0, 9, "1. Executive Summary", ln=1)
    pdf.set_font(fn, '', 10)
    cur.execute("SELECT COUNT(*) FROM PROJECTS")
    total_projects = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT repository_id) FROM PROJECTS")
    n_repos = cur.fetchone()[0]
    pdf.multi_cell(0, 6,
        f"This report presents Phase 2 classification results for {total_projects} "
        f"real research projects collected from {n_repos} repositories via live API calls. "
        "Projects are classified by PROJECT_TYPE (Step 1) and mapped to the UN ISIC Rev.5 "
        "standard at two hierarchical levels: Section and Division (Step 2).")
    pdf.ln(4)

    # ── Step 4b overview table ─────────────────────────────────────
    pdf.set_font(fn, 'B', 12)
    pdf.cell(0, 9, "2. Repository Overview - Project Type Distribution (Step 4b)",
             ln=1)

    cur.execute("""
        SELECT download_repository_folder, type, COUNT(*) c
        FROM PROJECTS GROUP BY download_repository_folder, type
        ORDER BY download_repository_folder, type
    """)
    rows = cur.fetchall()

    widths = [55, 50, 35, 40]
    pdf.set_font(fn, 'B', 9)
    for h, w in zip(["Repository","Project Type","Count","Dominant Class"], widths):
        pdf.cell(w, 7, h, border=1, align='C')
    pdf.ln()
    pdf.set_font(fn, '', 8)
    for rname, ptype, cnt in rows:
        cur.execute("""SELECT primary_class FROM PROJECTS
                       WHERE download_repository_folder=? AND type=?
                       GROUP BY primary_class ORDER BY COUNT(*) DESC LIMIT 1""",
                    (rname, ptype))
        dom = cur.fetchone()
        dom_label = (dom[0] or '')[:38] if dom else ''
        pdf.cell(widths[0], 6, str(rname),     border=1)
        pdf.cell(widths[1], 6, str(ptype),     border=1)
        pdf.cell(widths[2], 6, str(cnt),        border=1, align='C')
        pdf.cell(widths[3], 6, dom_label[:38], border=1)
        pdf.ln()
    pdf.ln(6)

    # ── Per-repository sections (Step 4d) ─────────────────────────
    pdf.set_font(fn, 'B', 12)
    pdf.cell(0, 9, "3. Per-Repository Classification Details (Step 4d)",
             ln=1)
    pdf.ln(2)

    cur.execute("SELECT DISTINCT repository_id, download_repository_folder FROM PROJECTS ORDER BY repository_id")
    repos = cur.fetchall()

    for repo_id, repo_folder in repos:
        cur.execute("""SELECT primary_class, COUNT(*) c FROM PROJECTS
                       WHERE repository_id=? GROUP BY primary_class ORDER BY c DESC""",
                    (repo_id,))
        class_rows = cur.fetchall()
        if not class_rows:
            continue
        class_counts = {r[0]: r[1] for r in class_rows}
        dominant     = class_rows[0][0]

        # Section header
        pdf.set_font(fn, 'B', 11)
        pdf.set_fill_color(220, 230, 245)
        pdf.cell(0, 8,
                 f"Repository: {repo_folder.upper()}  (ID: {repo_id})",
                 border=1, fill=True, ln=1)
        pdf.ln(2)

        # a) Histogram
        chart_path = os.path.join(base_dir, f"_tmp_hist_{repo_folder}.png")
        if make_histogram(repo_folder, class_counts, chart_path):
            pdf.image(chart_path, x=10, w=190)
            pdf.ln(2)
            os.remove(chart_path)

        # b) Top-20 rank-ordered table
        pdf.set_font(fn, 'B', 9)
        pdf.cell(10,  7, "#",     border=1, align='C')
        pdf.cell(148, 7, "ISIC Rev.5 Division (primary class)", border=1, align='C')
        pdf.cell(32,  7, "Count", border=1, align='C')
        pdf.ln()
        pdf.set_font(fn, '', 8)
        for rank, (cls, cnt) in enumerate(
                sorted(class_counts.items(), key=lambda x: x[1], reverse=True)[:20], 1):
            pdf.cell(10,  6, str(rank),      border=1, align='C')
            pdf.cell(148, 6, str(cls)[:98],  border=1)
            pdf.cell(32,  6, str(cnt),        border=1, align='C')
            pdf.ln()
        pdf.ln(3)

        # c) Comments
        total_r = sum(class_counts.values())
        pdf.set_font(fn, 'B', 9)
        pdf.cell(0, 5, "Comments on Findings:", ln=1)
        pdf.set_font(fn, 'I', 9)
        pdf.multi_cell(0, 5,
            f"Repository '{repo_folder.upper()}' contributed {total_r} classified project(s) "
            f"across {len(class_counts)} ISIC division(s). "
            f"Dominant class: {dominant}. "
            "Classification was performed at two ISIC Rev.5 levels (Section + Division) "
            "using keyword analysis on real metadata fetched from the live API. "
            "PROJECT_TYPE was derived from actual file extensions in each dataset.")
        pdf.ln(8)

    pdf.output(pdf_path)
    conn.close()
    print(f"📄 PDF  → {pdf_path}")


# =====================================================================
# MAIN
# =====================================================================
if __name__ == "__main__":
    print("\n" + "="*65)
    print(f"  SQ26 PHASE 2 - REAL DATA COLLECTOR  |  Student: {STUDENT_ID}")
    print("="*65)

    base_dir = resolve_output_dir()
    db_path = os.path.join(base_dir, DB_NAME)
    excel_path = os.path.join(base_dir, "Phase2_Classifications.xlsx")
    pdf_path = os.path.join(base_dir, "Phase2_Final_Report.pdf")

    conn = init_db(db_path)
    print(f"✅ DB initialised: {db_path}\n")

    grand_total = 0

    # ── Zenodo ──────────────────────────────────────────────────────
    grand_total += fetch_zenodo(conn)

    # ── Dataverse-NO ────────────────────────────────────────────────
    repo_dvno = {"id": 6, "name": "dataverse-no", "url": "https://dataverse.no/"}
    grand_total += fetch_dataverse(conn, repo_dvno)
    # ── ADA (Dataverse node) ──────────────────────────────────────────
    repo_ada = {"id": 7, "name": "ada", "url": "https://dataverse.ada.edu.au/"}
    grand_total += fetch_dataverse(conn, repo_ada)
    # ── Uni-Halle (interactive verification) ─────────────────────────
    repo_halle = {"id": 16, "name": "uni-halle", "url": "https://opendata.uni-halle.de/"}
    print("\n  ⚠️  Attempting uni-halle. If a browser window appears, please complete the 'I'm not a robot' check.")
    grand_total += fetch_dataverse(conn, repo_halle)

    conn.close()

    print(f"\n{'='*65}")
    print(f"  TOTAL REAL PROJECTS COLLECTED: {grand_total}")
    print(f"{'='*65}")

    # ── Excel (Step 4c) ─────────────────────────────────────────────
    export_excel(db_path, excel_path)

    # ── PDF (Step 4d) ───────────────────────────────────────────────
    generate_pdf(db_path, pdf_path, base_dir)

    print(f"""
╔{'═'*63}╗
║  DELIVERABLES READY                                           ║
╠{'═'*63}╣
║  DB   (GitHub / tag classification-results):                  ║
║    {db_path:<57} ║
║  XLSX (moo.uni1.de):                                          ║
║    {excel_path:<57} ║
║  PDF  (moo.uni1.de):                                          ║
║    {pdf_path:<57} ║
╚{'═'*63}╝
""")