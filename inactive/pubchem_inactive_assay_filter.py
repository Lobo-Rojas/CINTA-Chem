import os
import json
import zipfile
import gzip
import pandas as pd

from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed

RAW_DIR = "data/raw_assays"
OUTPUT_DIR = "data/output"
CACHE_DIR = "data/smiles_cache"

OUTPUT_FILE = os.path.join(OUTPUT_DIR, "pubchem_inactive_compounds.csv")
CHECKPOINT_FILE = os.path.join(OUTPUT_DIR, "inactive_checkpoint.json")
CID_CACHE_FILE = os.path.join(CACHE_DIR, "cid_smiles_cache.csv")
MISSING_CIDS_FILE = os.path.join(OUTPUT_DIR, "inactive_missing_cids.txt")

CHUNKSIZE = 50000
MAX_WORKERS = os.cpu_count() or 1
TEMP_DIR = os.path.join(OUTPUT_DIR, "_inactive_parallel_tmp")

for directory in [OUTPUT_DIR, CACHE_DIR, TEMP_DIR]:
    Path(directory).mkdir(parents=True, exist_ok=True)

CHECKPOINT_VERSION = "inactive_all_v1"

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            checkpoint = json.load(f)
        if checkpoint.get("selection_rule_version") == CHECKPOINT_VERSION:
            return checkpoint
    return {"processed_files": [], "selection_rule_version": CHECKPOINT_VERSION}

def save_checkpoint(checkpoint):
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)

def load_cid_cache():
    if not os.path.exists(CID_CACHE_FILE):
        return {}
    try:
        cache_df = pd.read_csv(CID_CACHE_FILE, dtype=str)
        if not {"PUBCHEM_CID", "SMILES"}.issubset(cache_df.columns):
            return {}
        return dict(zip(cache_df["PUBCHEM_CID"], cache_df["SMILES"]))
    except Exception:
        return {}

GLOBAL_CACHE = load_cid_cache()

def clean_cid(value):
    try:
        if pd.isna(value):
            return None
        cid = str(int(float(str(value))))
        return None if cid == "0" else cid
    except Exception:
        return None

def clean_aid(value):
    try:
        if pd.isna(value):
            return None
        return str(int(float(str(value))))
    except Exception:
        return None

def extract_smiles_cascade(row, missing_set):
    cid = row["PUBCHEM_CID"]
    native_smiles = row.get("SMILES")
    if native_smiles is not None and not pd.isna(native_smiles) and str(native_smiles).strip():
        return str(native_smiles).strip()
    cached_smiles = GLOBAL_CACHE.get(cid)
    if cached_smiles is not None and not pd.isna(cached_smiles) and str(cached_smiles).strip():
        return str(cached_smiles).strip()
    missing_set.add(cid)
    return None

def process_zip_local(zip_path, worker_id):
    rows_saved = 0
    worker_missing_cids = set()
    temp_file = os.path.join(TEMP_DIR, f"inactive_{worker_id}_{zip_path.stem}.csv")
    if os.path.exists(temp_file):
        os.remove(temp_file)

    with zipfile.ZipFile(zip_path, "r") as archive:
        gz_files = [x for x in archive.namelist() if x.endswith(".csv.gz")]

        for gz_file in gz_files:
            try:
                aid = clean_aid(Path(gz_file).stem.replace(".csv", ""))
                if aid is None:
                    continue

                with archive.open(gz_file) as zipped:
                    with gzip.open(zipped, mode="rt", encoding="utf-8", errors="ignore") as input_file:
                        for chunk in pd.read_csv(input_file, chunksize=CHUNKSIZE, low_memory=False, dtype=str):
                            chunk.columns = [column.strip().upper() for column in chunk.columns]

                            if not {"PUBCHEM_ACTIVITY_OUTCOME", "PUBCHEM_CID"}.issubset(chunk.columns):
                                continue

                            standard_value_column = next(
                                (c for c in chunk.columns if "PUBCHEM STANDARD VALUE" in c), None
                            )
                            standard_type_column = next(
                                (c for c in chunk.columns if "STANDARD TYPE" in c), None
                            )
                            smiles_column = next((c for c in chunk.columns if "SMILES" in c), None)

                            if standard_value_column is not None:
                                standard_value = pd.to_numeric(chunk[standard_value_column], errors="coerce")
                            else:
                                standard_value = pd.Series([None] * len(chunk), index=chunk.index, dtype="float64")

                            if standard_type_column is not None:
                                standard_type = chunk[standard_type_column].astype("string").str.strip().replace({"nan": pd.NA, "": pd.NA})
                            else:
                                standard_type = pd.Series([pd.NA] * len(chunk), index=chunk.index, dtype="string")

                            outcome = chunk["PUBCHEM_ACTIVITY_OUTCOME"].astype("string").str.upper().str.strip()

                            if smiles_column is not None and smiles_column != "SMILES":
                                chunk["SMILES"] = chunk[smiles_column]
                            elif smiles_column is None:
                                chunk["SMILES"] = pd.NA

                            # ALL records explicitly labelled INACTIVE are retained.
                            # No potency/value filter, no balancing against active observations,
                            # no sampling, and no duplicate-by-CID reduction.
                            inactive_mask = outcome.eq("INACTIVE")
                            if not inactive_mask.any():
                                continue

                            inactive_chunk = chunk[inactive_mask].copy()
                            inactive_chunk["_STANDARD_VALUE_NUMERIC"] = standard_value[inactive_mask].to_numpy()
                            inactive_chunk["_STANDARD_TYPE_CLEAN"] = standard_type[inactive_mask].to_numpy()
                            inactive_chunk["PUBCHEM_CID"] = inactive_chunk["PUBCHEM_CID"].apply(clean_cid)
                            inactive_chunk = inactive_chunk[inactive_chunk["PUBCHEM_CID"].notna()]
                            if len(inactive_chunk) == 0:
                                continue

                            inactive_chunk["FINAL_SMILES"] = inactive_chunk.apply(
                                lambda row: extract_smiles_cascade(row, worker_missing_cids), axis=1
                            )
                            inactive_chunk["PUBCHEM_AID"] = aid

                            out = pd.DataFrame({
                                "PUBCHEM_AID": inactive_chunk["PUBCHEM_AID"],
                                "PUBCHEM_SID": inactive_chunk.get("PUBCHEM_SID"),
                                "PUBCHEM_CID": inactive_chunk["PUBCHEM_CID"],
                                "PUBCHEM_ACTIVITY_OUTCOME": inactive_chunk["PUBCHEM_ACTIVITY_OUTCOME"],
                                "PUBCHEM_ASSAY_URL": (
                                    "https://pubchem.ncbi.nlm.nih.gov/bioassay/"
                                    + inactive_chunk["PUBCHEM_AID"].astype(str)
                                ),
                                "RESULT_IS_ACTIVE_CONCENTRATION": inactive_chunk["_STANDARD_VALUE_NUMERIC"].notna(),
                                "PubChem_Standard_Value_uM": inactive_chunk["_STANDARD_VALUE_NUMERIC"],
                                "PubChem_Standard_Type": inactive_chunk["_STANDARD_TYPE_CLEAN"],
                                "SMILES": inactive_chunk["FINAL_SMILES"],
                            })

                            out = out[
                                out["PUBCHEM_AID"].notna()
                                & out["PUBCHEM_CID"].notna()
                            ]
                            if len(out):
                                out.to_csv(temp_file, mode="a", index=False, header=not os.path.exists(temp_file))
                                rows_saved += len(out)

            except Exception as exc:
                print(f"Error processing {gz_file}: {exc}")

    return str(zip_path), temp_file, list(worker_missing_cids), rows_saved

def append_temp_file(temp_file):
    if not os.path.exists(temp_file) or os.path.getsize(temp_file) == 0:
        return 0
    df = pd.read_csv(temp_file, dtype=str)
    if len(df) == 0:
        return 0
    df.to_csv(OUTPUT_FILE, mode="a", index=False, header=not os.path.exists(OUTPUT_FILE))
    return len(df)

if __name__ == "__main__":
    old_checkpoint = None
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                old_checkpoint = json.load(f)
        except Exception:
            old_checkpoint = None

    if old_checkpoint is None or old_checkpoint.get("selection_rule_version") != CHECKPOINT_VERSION:
        # Start the all-INACTIVE selection rule from a clean inactive output.
        if os.path.exists(OUTPUT_FILE):
            os.remove(OUTPUT_FILE)
        checkpoint = {"processed_files": [], "selection_rule_version": CHECKPOINT_VERSION}
        save_checkpoint(checkpoint)
    else:
        checkpoint = old_checkpoint

    zip_files = sorted(Path(RAW_DIR).glob("*.zip"))
    processed_files = set(checkpoint.get("processed_files", []))
    files_to_process = [f for f in zip_files if str(f) not in processed_files]

    print(f"\nLocal CPU workers: {MAX_WORKERS}")
    print(f"ZIP files queued for inactive processing: {len(files_to_process)}")

    global_missing_cids = set()

    if files_to_process:
        worker_count = min(MAX_WORKERS, len(files_to_process))
        with ProcessPoolExecutor(max_workers=worker_count) as executor:
            futures = {
                executor.submit(process_zip_local, file, index): file
                for index, file in enumerate(files_to_process)
            }
            for future in tqdm(as_completed(futures), total=len(futures), desc="Parsing inactive observations"):
                file = futures[future]
                try:
                    file_path, temp_file, missing, count = future.result()
                    global_missing_cids.update(missing)
                    append_temp_file(temp_file)
                    processed_files.add(str(file))
                    checkpoint["processed_files"] = sorted(processed_files)
                    checkpoint["last_file"] = str(file)
                    checkpoint["last_rows_saved"] = count
                    save_checkpoint(checkpoint)
                    print(f"Processed: {file.name} | inactive observations: {count:,}")
                except Exception as exc:
                    print(f"Worker failed for {file}: {exc}")

    if global_missing_cids:
        with open(MISSING_CIDS_FILE, "a", encoding="utf-8") as f:
            for cid in sorted(global_missing_cids):
                f.write(f"{cid}\n")

    checkpoint["status"] = "completed"
    checkpoint["processed_files"] = sorted(processed_files)
    save_checkpoint(checkpoint)

    if os.path.exists(OUTPUT_FILE):
        try:
            total = len(pd.read_csv(OUTPUT_FILE, usecols=["PUBCHEM_CID"]))
        except Exception:
            total = 0
    else:
        total = 0

    print(f"\nInactive filtering complete. Total rows written: {total:,}")
    print(f"Output: {OUTPUT_FILE}")
