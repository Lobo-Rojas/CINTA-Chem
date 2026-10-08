import os
import json
import zipfile
import gzip
import pandas as pd

from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed


# ==========================================================
# CONFIGURATION
# ==========================================================

RAW_DIR = "data/raw_assays"
OUTPUT_DIR = "data/output"
CACHE_DIR = "data/smiles_cache"

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "CINTA-Chem_Active_Compounds.csv"
)

INACTIVE_OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "CINTA-Chem_Inactive_Compounds_Active_Branch.csv"
)

CHECKPOINT_FILE = os.path.join(
    OUTPUT_DIR,
    "CINTA-Chem_Activity_Filter_Checkpoint.json"
)

CID_CACHE_FILE = os.path.join(
    CACHE_DIR,
    "CINTA-Chem_CID_SMILES_Cache.csv"
)

MISSING_CIDS_FILE = os.path.join(
    OUTPUT_DIR,
    "CINTA-Chem_Missing_CIDs.txt"
)

CHUNKSIZE = 50000
LOW_VALUE_THRESHOLD_UM = 10.0

# Use all locally available CPU cores.
# This step performs no network requests.
MAX_WORKERS = os.cpu_count() or 1

TEMP_DIR = os.path.join(
    OUTPUT_DIR,
    "_parallel_tmp"
)


# ==========================================================
# CREATE DIRECTORIES
# ==========================================================

for directory in [
    OUTPUT_DIR,
    CACHE_DIR,
    TEMP_DIR
]:
    Path(directory).mkdir(
        parents=True,
        exist_ok=True
    )


# ==========================================================
# CHECKPOINT
# ==========================================================

def load_checkpoint():
    """Load the filtering checkpoint."""

    if os.path.exists(CHECKPOINT_FILE):

        with open(
            CHECKPOINT_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    return {
        "processed_files": []
    }


def save_checkpoint(checkpoint):
    """Save the filtering checkpoint."""

    with open(
        CHECKPOINT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            checkpoint,
            f,
            indent=2
        )


# ==========================================================
# LOCAL CID/SMILES CACHE
# ==========================================================

def load_cid_cache():
    """
    Load the existing local CID/SMILES cache.

    No network access is performed.
    """

    if not os.path.exists(CID_CACHE_FILE):
        return {}

    try:

        cache_df = pd.read_csv(
            CID_CACHE_FILE,
            dtype=str
        )

        required_columns = {
            "PUBCHEM_CID",
            "SMILES"
        }

        if not required_columns.issubset(
            cache_df.columns
        ):
            print(
                "Warning: local SMILES cache does not contain "
                "the required columns. Cache will be ignored."
            )
            return {}

        print(
            "Loaded local SMILES cache: "
            f"{len(cache_df):,} CIDs"
        )

        return dict(
            zip(
                cache_df["PUBCHEM_CID"],
                cache_df["SMILES"]
            )
        )

    except Exception as exc:

        print(
            "Warning: could not read the local SMILES cache: "
            f"{exc}"
        )

        return {}


# Static local cache shared with worker processes.
GLOBAL_CACHE = load_cid_cache()


# ==========================================================
# CLEANERS
# ==========================================================

def clean_cid(value):
    """Normalize a PubChem CID."""

    try:

        if pd.isna(value):
            return None

        cid = str(
            int(
                float(
                    str(value)
                )
            )
        )

        if cid == "0":
            return None

        return cid

    except Exception:
        return None


def clean_aid(value):
    """Normalize a PubChem AID."""

    try:

        if pd.isna(value):
            return None

        return str(
            int(
                float(
                    str(value)
                )
            )
        )

    except Exception:
        return None


# ==========================================================
# OFFLINE SMILES RESOLUTION
# ==========================================================

def extract_smiles_cascade(
    row,
    missing_set
):
    """
    Resolve SMILES without any network request.

    Priority:
    1. SMILES contained directly in the current PubChem CSV.
    2. SMILES in the local CID cache.
    3. Missing value, with the CID recorded in CINTA-Chem_Missing_CIDs.txt.
    """

    cid = row["PUBCHEM_CID"]

    # Priority 1: native SMILES in the currently processed CSV.
    native_smiles = row.get(
        "SMILES"
    )

    if (
        native_smiles is not None
        and not pd.isna(native_smiles)
        and str(native_smiles).strip() != ""
    ):
        return str(native_smiles).strip()

    # Priority 2: local cache only.
    cached_smiles = GLOBAL_CACHE.get(
        cid
    )

    if (
        cached_smiles is not None
        and not pd.isna(cached_smiles)
        and str(cached_smiles).strip() != ""
    ):
        return str(cached_smiles).strip()

    # Priority 3: no structure available offline.
    missing_set.add(cid)

    return None


# ==========================================================
# PROCESS ONE PUBCHEM ZIP
# ==========================================================

def process_zip_local(
    zip_path,
    worker_id
):
    """
    Process one PubChem ZIP archive locally.

    No web/API requests are performed by this function.
    """

    rows_saved = 0
    inactive_rows_saved = 0

    worker_missing_cids = set()

    active_temp_file = os.path.join(
        TEMP_DIR,
        f"active_{worker_id}_{zip_path.stem}.csv"
    )

    inactive_temp_file = os.path.join(
        TEMP_DIR,
        f"inactive_{worker_id}_{zip_path.stem}.csv"
    )

    for temporary_file in [
        active_temp_file,
        inactive_temp_file
    ]:

        if os.path.exists(temporary_file):
            os.remove(temporary_file)

    with zipfile.ZipFile(
        zip_path,
        "r"
    ) as archive:

        gz_files = [
            filename
            for filename in archive.namelist()
            if filename.endswith(".csv.gz")
        ]

        for gz_file in gz_files:

            try:

                aid = clean_aid(
                    Path(gz_file)
                    .stem
                    .replace(".csv", "")
                )

                if aid is None:
                    continue

                active_candidates = []
                inactive_candidates = []

                with archive.open(
                    gz_file
                ) as zipped:

                    with gzip.open(
                        zipped,
                        mode="rt",
                        encoding="utf-8",
                        errors="ignore"
                    ) as input_file:

                        for chunk in pd.read_csv(
                            input_file,
                            chunksize=CHUNKSIZE,
                            low_memory=False,
                            dtype=str
                        ):

                            chunk.columns = [
                                column.strip().upper()
                                for column in chunk.columns
                            ]

                            if not {
                                "PUBCHEM_ACTIVITY_OUTCOME",
                                "PUBCHEM_CID"
                            }.issubset(
                                chunk.columns
                            ):
                                continue

                            standard_value_column = next(
                                (
                                    column
                                    for column in chunk.columns
                                    if "PUBCHEM STANDARD VALUE"
                                    in column
                                ),
                                None
                            )

                            standard_type_column = next(
                                (
                                    column
                                    for column in chunk.columns
                                    if "STANDARD TYPE"
                                    in column
                                ),
                                None
                            )

                            smiles_column = next(
                                (
                                    column
                                    for column in chunk.columns
                                    if "SMILES" in column
                                ),
                                None
                            )

                            if standard_value_column is not None:

                                standard_value = pd.to_numeric(
                                    chunk[
                                        standard_value_column
                                    ],
                                    errors="coerce"
                                )

                            else:

                                standard_value = pd.Series(
                                    [None] * len(chunk),
                                    index=chunk.index,
                                    dtype="float64"
                                )

                            if standard_type_column is not None:

                                standard_type = (
                                    chunk[
                                        standard_type_column
                                    ]
                                    .astype("string")
                                    .str.strip()
                                    .replace({
                                        "nan": pd.NA,
                                        "": pd.NA
                                    })
                                )

                            else:

                                standard_type = pd.Series(
                                    [pd.NA] * len(chunk),
                                    index=chunk.index,
                                    dtype="string"
                                )

                            outcome = (
                                chunk[
                                    "PUBCHEM_ACTIVITY_OUTCOME"
                                ]
                                .astype("string")
                                .str.upper()
                                .str.strip()
                            )

                            # Preserve the native SMILES field when present.
                            if (
                                smiles_column is not None
                                and smiles_column != "SMILES"
                            ):

                                chunk["SMILES"] = chunk[
                                    smiles_column
                                ]

                            elif smiles_column is None:

                                chunk["SMILES"] = pd.NA

                            # --------------------------------------------------
                            # ACTIVE SELECTION
                            #
                            # Preserve the supplied rule:
                            #   outcome != INACTIVE
                            #   standardized value is available
                            #   standardized value < 10 uM
                            #
                            # No assay-type restriction is applied here.
                            # --------------------------------------------------

                            active_mask = (
                                outcome.ne("INACTIVE")
                                & standard_value.notna()
                                & standard_value.lt(
                                    LOW_VALUE_THRESHOLD_UM
                                )
                            )

                            active_chunk = chunk[
                                active_mask
                            ].copy()

                            if len(active_chunk) > 0:

                                active_chunk[
                                    "_STANDARD_VALUE_NUMERIC"
                                ] = standard_value[
                                    active_mask
                                ].to_numpy()

                                active_chunk[
                                    "_STANDARD_TYPE_CLEAN"
                                ] = standard_type[
                                    active_mask
                                ].to_numpy()

                                active_chunk[
                                    "PUBCHEM_CID"
                                ] = active_chunk[
                                    "PUBCHEM_CID"
                                ].apply(
                                    clean_cid
                                )

                                active_chunk = active_chunk[
                                    active_chunk[
                                        "PUBCHEM_CID"
                                    ].notna()
                                ]

                                if len(active_chunk) > 0:

                                    active_candidates.append(
                                        active_chunk[
                                            [
                                                "PUBCHEM_CID",
                                                "_STANDARD_VALUE_NUMERIC",
                                                "_STANDARD_TYPE_CLEAN",
                                                "PUBCHEM_SID",
                                                "PUBCHEM_ACTIVITY_OUTCOME",
                                                "SMILES"
                                            ]
                                        ]
                                    )

                            # --------------------------------------------------
                            # INACTIVE CANDIDATES
                            #
                            # Preserve the supplied inactive-selection logic.
                            # --------------------------------------------------

                            inactive_mask = outcome.eq(
                                "INACTIVE"
                            )

                            if inactive_mask.any():

                                inactive_chunk = chunk[
                                    inactive_mask
                                ].copy()

                                inactive_chunk[
                                    "_STANDARD_VALUE_NUMERIC"
                                ] = standard_value[
                                    inactive_mask
                                ].to_numpy()

                                inactive_chunk[
                                    "_STANDARD_TYPE_CLEAN"
                                ] = standard_type[
                                    inactive_mask
                                ].to_numpy()

                                inactive_chunk[
                                    "PUBCHEM_CID"
                                ] = inactive_chunk[
                                    "PUBCHEM_CID"
                                ].apply(
                                    clean_cid
                                )

                                inactive_chunk = inactive_chunk[
                                    inactive_chunk[
                                        "PUBCHEM_CID"
                                    ].notna()
                                ]

                                if len(inactive_chunk) > 0:

                                    inactive_candidates.append(
                                        inactive_chunk[
                                            [
                                                "PUBCHEM_CID",
                                                "_STANDARD_VALUE_NUMERIC",
                                                "_STANDARD_TYPE_CLEAN",
                                                "PUBCHEM_SID",
                                                "PUBCHEM_ACTIVITY_OUTCOME",
                                                "SMILES"
                                            ]
                                        ]
                                    )

                if len(active_candidates) == 0:
                    continue

                active_pool = pd.concat(
                    active_candidates,
                    ignore_index=True
                )

                active_observation_count = len(
                    active_pool
                )

                # Offline-only SMILES resolution.
                active_pool[
                    "FINAL_SMILES"
                ] = active_pool.apply(
                    lambda row: extract_smiles_cascade(
                        row,
                        worker_missing_cids
                    ),
                    axis=1
                )

                if len(active_pool) > 0:

                    active_pool[
                        "PUBCHEM_AID"
                    ] = aid

                    out_active = pd.DataFrame({

                        "PUBCHEM_AID":
                            active_pool[
                                "PUBCHEM_AID"
                            ],

                        "PUBCHEM_SID":
                            active_pool.get(
                                "PUBCHEM_SID"
                            ),

                        "PUBCHEM_CID":
                            active_pool[
                                "PUBCHEM_CID"
                            ],

                        "PUBCHEM_ACTIVITY_OUTCOME":
                            active_pool.get(
                                "PUBCHEM_ACTIVITY_OUTCOME"
                            ),

                        "PUBCHEM_ASSAY_URL":
                            (
                                "https://pubchem.ncbi.nlm.nih.gov/"
                                "bioassay/"
                                + active_pool[
                                    "PUBCHEM_AID"
                                ].astype(str)
                            ),

                        "RESULT_IS_ACTIVE_CONCENTRATION":
                            active_pool[
                                "_STANDARD_VALUE_NUMERIC"
                            ].notna(),

                        "PubChem_Standard_Value_uM":
                            active_pool[
                                "_STANDARD_VALUE_NUMERIC"
                            ],

                        "PubChem_Standard_Type":
                            active_pool[
                                "_STANDARD_TYPE_CLEAN"
                            ],

                        "SMILES":
                            active_pool[
                                "FINAL_SMILES"
                            ]
                    })

                    # Preserve the supplied biological filters.
                    # Missing SMILES are not excluded here.
                    out_active = out_active[
                        out_active[
                            "PUBCHEM_AID"
                        ].notna()
                        &
                        out_active[
                            "PUBCHEM_CID"
                        ].notna()
                        &
                        out_active[
                            "PUBCHEM_ACTIVITY_OUTCOME"
                        ]
                        .astype("string")
                        .str.upper()
                        .ne("INACTIVE")
                        &
                        out_active[
                            "RESULT_IS_ACTIVE_CONCENTRATION"
                        ].eq(True)
                        &
                        pd.to_numeric(
                            out_active[
                                "PubChem_Standard_Value_uM"
                            ],
                            errors="coerce"
                        ).lt(
                            LOW_VALUE_THRESHOLD_UM
                        )
                    ]

                    if len(out_active) > 0:

                        out_active.to_csv(
                            active_temp_file,
                            mode="a",
                            index=False,
                            header=not os.path.exists(
                                active_temp_file
                            )
                        )

                        rows_saved += len(
                            out_active
                        )

                # --------------------------------------------------------------
                # SELECT AND BALANCE INACTIVES
                #
                # Priority:
                # 1. Inactive records without concentration.
                # 2. If none exist, inactive records with concentration > 10 uM.
                # 3. Sample at most the number of active observations.
                # --------------------------------------------------------------

                if (
                    active_observation_count > 0
                    and len(inactive_candidates) > 0
                ):

                    inactive_pool = pd.concat(
                        inactive_candidates,
                        ignore_index=True
                    ).drop_duplicates(
                        subset=["PUBCHEM_CID"]
                    )

                    inactive_without_concentration = (
                        inactive_pool[
                            inactive_pool[
                                "_STANDARD_VALUE_NUMERIC"
                            ].isna()
                        ]
                    )

                    if len(
                        inactive_without_concentration
                    ) > 0:

                        inactive_pool = (
                            inactive_without_concentration
                        )

                    else:

                        inactive_pool = inactive_pool[
                            inactive_pool[
                                "_STANDARD_VALUE_NUMERIC"
                            ].notna()
                            &
                            inactive_pool[
                                "_STANDARD_VALUE_NUMERIC"
                            ].gt(
                                LOW_VALUE_THRESHOLD_UM
                            )
                        ]

                    if len(inactive_pool) > 0:

                        number_to_select = min(
                            active_observation_count,
                            len(inactive_pool)
                        )

                        inactive_selected = (
                            inactive_pool
                            .sample(
                                n=number_to_select,
                                replace=False,
                                random_state=42
                            )
                            .reset_index(drop=True)
                        )

                        # Offline-only SMILES resolution.
                        inactive_selected[
                            "FINAL_SMILES"
                        ] = inactive_selected.apply(
                            lambda row:
                            extract_smiles_cascade(
                                row,
                                worker_missing_cids
                            ),
                            axis=1
                        )

                        inactive_selected[
                            "PUBCHEM_AID"
                        ] = aid

                        out_inactive = pd.DataFrame({

                            "PUBCHEM_AID":
                                inactive_selected[
                                    "PUBCHEM_AID"
                                ],

                            "PUBCHEM_SID":
                                inactive_selected.get(
                                    "PUBCHEM_SID"
                                ),

                            "PUBCHEM_CID":
                                inactive_selected[
                                    "PUBCHEM_CID"
                                ],

                            "PUBCHEM_ACTIVITY_OUTCOME":
                                inactive_selected.get(
                                    "PUBCHEM_ACTIVITY_OUTCOME"
                                ),

                            "PUBCHEM_ASSAY_URL":
                                (
                                    "https://pubchem.ncbi.nlm.nih.gov/"
                                    "bioassay/"
                                    + inactive_selected[
                                        "PUBCHEM_AID"
                                    ].astype(str)
                                ),

                            "RESULT_IS_ACTIVE_CONCENTRATION":
                                inactive_selected[
                                    "_STANDARD_VALUE_NUMERIC"
                                ].notna(),

                            "PubChem_Standard_Value_uM":
                                inactive_selected[
                                    "_STANDARD_VALUE_NUMERIC"
                                ],

                            "PubChem_Standard_Type":
                                inactive_selected[
                                    "_STANDARD_TYPE_CLEAN"
                                ],

                            "SMILES":
                                inactive_selected[
                                    "FINAL_SMILES"
                                ]
                        })

                        out_inactive = out_inactive[
                            out_inactive[
                                "PUBCHEM_AID"
                            ].notna()
                            &
                            out_inactive[
                                "PUBCHEM_CID"
                            ].notna()
                        ]

                        if len(out_inactive) > 0:

                            out_inactive.to_csv(
                                inactive_temp_file,
                                mode="a",
                                index=False,
                                header=not os.path.exists(
                                    inactive_temp_file
                                )
                            )

                            inactive_rows_saved += len(
                                out_inactive
                            )

            except Exception as exc:

                print(
                    f"Error processing internal file "
                    f"{gz_file}: {exc}"
                )

    return (
        str(zip_path),
        active_temp_file,
        inactive_temp_file,
        list(worker_missing_cids),
        rows_saved,
        inactive_rows_saved
    )


# ==========================================================
# APPEND TEMPORARY FILE TO FINAL OUTPUT
# ==========================================================

def append_temp_file(
    temp_file,
    output_file
):
    """Append a worker temporary file to a final CSV."""

    if (
        not os.path.exists(temp_file)
        or os.path.getsize(temp_file) == 0
    ):
        return 0

    df = pd.read_csv(
        temp_file,
        dtype=str
    )

    if len(df) == 0:
        return 0

    df.to_csv(
        output_file,
        mode="a",
        index=False,
        header=not os.path.exists(
            output_file
        )
    )

    return len(df)


# ==========================================================
# MAIN LOCAL HPC ORCHESTRATOR
# ==========================================================

if __name__ == "__main__":

    checkpoint = load_checkpoint()

    zip_files = sorted(
        Path(RAW_DIR).glob("*.zip")
    )

    processed_files = set(
        checkpoint.get(
            "processed_files",
            []
        )
    )

    files_to_process = [
        file
        for file in zip_files
        if str(file) not in processed_files
    ]

    print(
        "\nLocal CPU workers: "
        f"{MAX_WORKERS}"
    )

    print(
        "ZIP files queued for processing: "
        f"{len(files_to_process)}"
    )

    global_missing_cids = set()

    if len(files_to_process) > 0:

        worker_count = min(
            MAX_WORKERS,
            len(files_to_process)
        )

        with ProcessPoolExecutor(
            max_workers=worker_count
        ) as executor:

            futures = {
                executor.submit(
                    process_zip_local,
                    file,
                    index
                ): file
                for index, file
                in enumerate(files_to_process)
            }

            for future in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="Parsing compressed archives"
            ):

                file = futures[future]

                try:

                    (
                        file_path,
                        active_temp_file,
                        inactive_temp_file,
                        worker_missing_cids,
                        active_count,
                        inactive_count
                    ) = future.result()

                    global_missing_cids.update(
                        worker_missing_cids
                    )

                    append_temp_file(
                        active_temp_file,
                        OUTPUT_FILE
                    )

                    append_temp_file(
                        inactive_temp_file,
                        INACTIVE_OUTPUT_FILE
                    )

                    checkpoint[
                        "processed_files"
                    ].append(
                        file_path
                    )

                    save_checkpoint(
                        checkpoint
                    )

                    for temporary_file in [
                        active_temp_file,
                        inactive_temp_file
                    ]:

                        if os.path.exists(
                            temporary_file
                        ):
                            os.remove(
                                temporary_file
                            )

                except Exception as exc:

                    print(
                        "\n[PROCESS FAILURE] "
                        f"Critical exception while processing "
                        f"{file.name}: {exc}"
                    )

    # ======================================================
    # SAVE MISSING CID LIST
    # ======================================================

    if global_missing_cids:

        existing_missing_cids = set()

        if os.path.exists(
            MISSING_CIDS_FILE
        ):

            with open(
                MISSING_CIDS_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                existing_missing_cids = {
                    line.strip()
                    for line in f
                    if line.strip()
                }

        global_missing_cids.update(
            existing_missing_cids
        )

        with open(
            MISSING_CIDS_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            for cid in sorted(
                global_missing_cids,
                key=int
            ):

                f.write(
                    f"{cid}\n"
                )

        print(
            "\n[PROCESS COMPLETED] "
            f"{len(global_missing_cids):,} orphan CIDs "
            f"were written to: {MISSING_CIDS_FILE}"
        )

    else:

        print(
            "\n[PROCESS COMPLETED] "
            "All processed compounds had a native or locally "
            "cached SMILES representation."
        )
