import os
import re
import json
import time
import requests
import pandas as pd

# =====================================================
# CONFIG
# =====================================================

INPUT_FILE = "data/output/CINTA-Chem_Active_Compounds.csv"

OUTPUT_FILE = "data/output/CINTA-Chem_Assay_Metadata.csv"

CHECKPOINT_FILE = "data/output/CINTA-Chem_Assay_Metadata_Checkpoint.json"

BATCH_SIZE = 100

REQUEST_TIMEOUT = 30

SLEEP_BETWEEN_REQUESTS = 0.05

COLUMN_ORDER = [

    "PUBCHEM_AID",
    "Assay_Name",
    "Target_Name",
    "UniProtKB_ID",
    "Gene_Symbol",
    "Organism"

]

# =====================================================
# CHECKPOINT FUNCTIONS
# =====================================================

def load_checkpoint():

    if os.path.exists(
        CHECKPOINT_FILE
    ):

        with open(
            CHECKPOINT_FILE,
            "r"
        ) as f:

            return json.load(f)

    return {

        "processed_aids": []

    }


def save_checkpoint(
    checkpoint
):

    with open(
        CHECKPOINT_FILE,
        "w"
    ) as f:

        json.dump(
            checkpoint,
            f,
            indent=2
        )

# =====================================================
# PARSE PUBCHEM JSON
# =====================================================

def extract_target_metadata(
    record
):

    metadata = {

        "Assay_Name": record.get(
            "RecordTitle"
        ),

        "Target_Name": None,

        "UniProtKB_ID": None,

        "Gene_Symbol": None,

        "Organism": None

    }

    sections = record.get(
        "Section",
        []
    )

    for sec in sections:

        if sec.get(
            "TOCHeading"
        ) != "Target":

            continue

        for subsec in sec.get(
            "Section",
            []
        ):

            heading = subsec.get(
                "TOCHeading",
                ""
            )

            infos = subsec.get(
                "Information",
                []
            )

            if len(infos) == 0:

                continue

            info = infos[0]

            # =====================================
            # Protein Target
            # =====================================

            if heading == "Protein Target":

                try:

                    metadata[
                        "Target_Name"
                    ] = (

                        info["Value"]
                        ["StringWithMarkup"][0]
                        ["String"]

                    )

                except:

                    pass

                try:

                    url = info.get(
                        "URL",
                        ""
                    )

                    match = re.search(
                        r"/protein/([A-Z0-9]+)",
                        url
                    )

                    if match:

                        metadata[
                            "UniProtKB_ID"
                        ] = match.group(
                            1
                        )

                except:

                    pass

            # =====================================
            # Encoding Gene
            # =====================================

            elif heading == "Encoding Gene":

                try:

                    metadata[
                        "Gene_Symbol"
                    ] = (

                        info["Value"]
                        ["StringWithMarkup"][0]
                        ["String"]

                    )

                except:

                    pass

            # =====================================
            # Taxonomy
            # =====================================

            elif heading == "Taxonomy":

                try:

                    metadata[
                        "Organism"
                    ] = (

                        info["Value"]
                        ["StringWithMarkup"][0]
                        ["String"]

                    )

                except:

                    pass

    return metadata

# =====================================================
# RETRIEVE AID
# =====================================================

def get_aid_metadata(
    aid
):

    url = (

        "https://pubchem.ncbi.nlm.nih.gov/"
        f"rest/pug_view/data/assay/{aid}/JSON"

    )

    for attempt in range(5):

        try:

            r = requests.get(
                url,
                timeout=REQUEST_TIMEOUT
            )

            if r.status_code != 200:

                time.sleep(2)

                continue

            data = r.json()

            record = data.get(
                "Record"
            )

            if record is None:

                return None

            metadata = (
                extract_target_metadata(
                    record
                )
            )

            row = {

                "PUBCHEM_AID": aid,

                "Assay_Name":
                metadata[
                    "Assay_Name"
                ],

                "Target_Name":
                metadata[
                    "Target_Name"
                ],

                "UniProtKB_ID":
                metadata[
                    "UniProtKB_ID"
                ],

                "Gene_Symbol":
                metadata[
                    "Gene_Symbol"
                ],

                "Organism":
                metadata[
                    "Organism"
                ]

            }

            return row

        except Exception:

            time.sleep(2)

    return None

# =====================================================
# LOAD UNIQUE AIDs
# =====================================================

print(
    "Loading AIDs..."
)

aids = pd.read_csv(
    INPUT_FILE,
    usecols=[
        "PUBCHEM_AID"
    ]
)

unique_aids = sorted(

    aids[
        "PUBCHEM_AID"
    ]
    .dropna()
    .astype(int)
    .unique()

)

print(
    f"Total unique AIDs: "
    f"{len(unique_aids):,}"
)

# =====================================================
# CHECKPOINT
# =====================================================

checkpoint = (
    load_checkpoint()
)

processed = set(

    checkpoint[
        "processed_aids"
    ]

)

remaining = [

    aid

    for aid in unique_aids

    if aid not in processed

]

print(
    f"Remaining AIDs: "
    f"{len(remaining):,}"
)

# =====================================================
# CREATE OUTPUT FILE
# =====================================================

if not os.path.exists(
    OUTPUT_FILE
):

    pd.DataFrame(

        columns=COLUMN_ORDER

    ).to_csv(

        OUTPUT_FILE,

        index=False

    )

# =====================================================
# MAIN LOOP
# =====================================================

buffer = []

counter = 0

for aid in remaining:

    row = get_aid_metadata(
        aid
    )

    if row is not None:

        buffer.append(
            row
        )

    checkpoint[
        "processed_aids"
    ].append(
        int(aid)
    )

    counter += 1

    # =====================================
    # WRITE EVERY 100 ROWS
    # =====================================

    if len(buffer) >= BATCH_SIZE:

        pd.DataFrame(
            buffer
        )[COLUMN_ORDER].to_csv(

            OUTPUT_FILE,

            mode="a",

            index=False,

            header=False

        )

        buffer.clear()

        save_checkpoint(
            checkpoint
        )

        print(
            f"Processed "
            f"{counter:,} AIDs"
        )

    time.sleep(
        SLEEP_BETWEEN_REQUESTS
    )

# =====================================================
# FINAL WRITE
# =====================================================

if len(buffer) > 0:

    pd.DataFrame(
        buffer
    )[COLUMN_ORDER].to_csv(

        OUTPUT_FILE,

        mode="a",

        index=False,

        header=False

    )

save_checkpoint(
    checkpoint
)

print(
    "\nFinished."
)