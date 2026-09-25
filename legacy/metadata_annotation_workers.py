import os
import re
import json
import time
import requests
import pandas as pd

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)
# =====================================================
# STRICT RATE LIMIT (MAX ~3.8 REQ/SEC)
# =====================================================
from threading import Lock

RATE_LOCK = Lock()
LAST_REQUEST = [0.0]

def wait_rate_limit():
    """
    Guarantees a minimum 0.26-second interval between HTTP requests.
    Keeps the workflow safely below the 5 requests/s limit.
    """
    with RATE_LOCK:
        now = time.time()
        elapsed = now - LAST_REQUEST[0]
        if elapsed < 0.26:
            time.sleep(0.26 - elapsed)
        LAST_REQUEST[0] = time.time()

def handle_dynamic_throttling(headers):
    """
    Checks PubChem responses and proactively slows the script when the service reports a warning (Yellow) or overload (Red) state.
    """
    throttle = headers.get("X-Throttling-Control", "")
    if "Yellow" in throttle:
        print("\n[!] PubChem warning (Yellow): reducing request rate. Waiting 5 seconds...")
        time.sleep(5)
    elif "Red" in throttle:
        print("\nCritical PubChem warning (Red): server overloaded. Emergency 20-second pause...")
        time.sleep(20)

# =====================================================
# CONFIG
# =====================================================
INPUT_FILE = "data/output/pubchem_active_compounds.csv"
OUTPUT_FILE = "data/output/pubchem_assay_metadata.csv"
CHECKPOINT_FILE = "data/output/pubchem_assay_checkpoint.json"

BATCH_SIZE = 100
REQUEST_TIMEOUT = 30
MAX_WORKERS = 1
COLUMN_ORDER = [
    "PUBCHEM_AID",
    "Assay_Name",
    "Target_Name",
    "UniProtKB_ID",
    "Gene_Symbol",
    "Organism"
]

# =====================================================
# GLOBAL SESSION
# =====================================================
session = requests.Session()
session.headers.update({
    "User-Agent": "PubChem-Metadata-Annotation/1.0 (Defensive HPC client)"
})

# =====================================================
# CHECKPOINT FUNCTIONS
# =====================================================
def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {"processed_aids": []}

def save_checkpoint(checkpoint):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(checkpoint, f, indent=2)

# =====================================================
# PARSE PUBCHEM JSON
# =====================================================
def extract_target_metadata(record):
    metadata = {
        "Assay_Name": record.get("RecordTitle"),
        "Target_Name": None,
        "UniProtKB_ID": None,
        "Gene_Symbol": None,
        "Organism": None
    }

    sections = record.get("Section", [])
    for sec in sections:
        if sec.get("TOCHeading") != "Target":
            continue

        for subsec in sec.get("Section", []):
            heading = subsec.get("TOCHeading", "")
            infos = subsec.get("Information", [])
            if len(infos) == 0:
                continue

            info = infos[0]

            # INDEXING FIX: replaced the nested access pattern with direct dictionary access 
            # due to the direct dictionary structure, avoiding accidental KeyErrors.
            if heading == "Protein Target":
                try:
                    val_data = info.get("Value", {}).get("StringWithMarkup", [])
                    if val_data:
                        metadata["Target_Name"] = val_data[0].get("String")
                except:
                    pass

                try:
                    url = info.get("URL", "")
                    match = re.search(r"/protein/([A-Z0-9]+)", url)
                    if match:
                        metadata["UniProtKB_ID"] = match.group(1)
                except:
                    pass

            elif heading == "Encoding Gene":
                try:
                    val_data = info.get("Value", {}).get("StringWithMarkup", [])
                    if val_data:
                        metadata["Gene_Symbol"] = val_data[0].get("String")
                except:
                    pass

            elif heading == "Taxonomy":
                try:
                    val_data = info.get("Value", {}).get("StringWithMarkup", [])
                    if val_data:
                        metadata["Organism"] = val_data[0].get("String")
                except:
                    pass

    return metadata

# =====================================================
# RETRIEVE AID
# =====================================================
def get_aid_metadata(aid):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/assay/{aid}/JSON"

    for attempt in range(5):
        try:
            wait_rate_limit()
            r = session.get(url, timeout=REQUEST_TIMEOUT)

            # Operational response-header inspection
            handle_dynamic_throttling(r.headers)

            if r.status_code in (429, 503):
                time.sleep(5 * (attempt + 1))
                continue

            if r.status_code == 404:
                # Return an empty row marked so deleted AIDs are not retried
                return {
                    "PUBCHEM_AID": aid, "Assay_Name": "Not Found", "Target_Name": None,
                    "UniProtKB_ID": None, "Gene_Symbol": None, "Organism": None
                }

            if r.status_code != 200:
                time.sleep(2)
                continue

            data = r.json()
            record = data.get("Record")
            if record is None:
                return None

            metadata = extract_target_metadata(record)
            return {
                "PUBCHEM_AID": aid,
                "Assay_Name": metadata["Assay_Name"],
                "Target_Name": metadata["Target_Name"],
                "UniProtKB_ID": metadata["UniProtKB_ID"],
                "Gene_Symbol": metadata["Gene_Symbol"],
                "Organism": metadata["Organism"]
            }

        except Exception:
            time.sleep(3 * (attempt + 1))

    return None

# =====================================================
# LOAD UNIQUE AIDs
# =====================================================
print("Loading AIDs...")
aids = pd.read_csv(INPUT_FILE, usecols=["PUBCHEM_AID"])
unique_aids = sorted(aids["PUBCHEM_AID"].dropna().astype(int).unique())
print(f"Total unique AIDs: {len(unique_aids):,}")

# =====================================================
# CHECKPOINT
# =====================================================
checkpoint = load_checkpoint()
processed = set(checkpoint["processed_aids"])
remaining = [aid for aid in unique_aids if aid not in processed]
print(f"Remaining AIDs: {len(remaining):,}")

# =====================================================
# CREATE OUTPUT FILE
# =====================================================
if not os.path.exists(OUTPUT_FILE):
    pd.DataFrame(columns=COLUMN_ORDER).to_csv(OUTPUT_FILE, index=False)

# =====================================================
# MAIN
# =====================================================
buffer = []
counter = 0

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {
        executor.submit(get_aid_metadata, aid): aid
        for aid in remaining
    }

    for future in as_completed(futures):
        aid = futures[future]
        try:
            row = future.result()
            if row is not None:
                buffer.append(row)
        except Exception:
            pass

        checkpoint["processed_aids"].append(int(aid))
        counter += 1

        if len(buffer) >= BATCH_SIZE:
            pd.DataFrame(buffer)[COLUMN_ORDER].to_csv(
                OUTPUT_FILE,
                mode="a",
                index=False,
                header=False
            )
            buffer.clear()
            save_checkpoint(checkpoint)
            print(f"Processed {counter:,} AIDs / {len(remaining):,}")

# =====================================================
# FINAL WRITE
# =====================================================
if len(buffer) > 0:
    pd.DataFrame(buffer)[COLUMN_ORDER].to_csv(
        OUTPUT_FILE,
        mode="a",
        index=False,
        header=False
    )
save_checkpoint(checkpoint)
print("\nFinished.")
