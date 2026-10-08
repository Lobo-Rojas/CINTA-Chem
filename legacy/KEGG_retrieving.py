import pandas as pd
import requests
import time

# ==========================================
# CONFIG
# ==========================================

INPUT_FILE = "data/output/CINTA-Chem_Unique_UniProt_IDs.txt"

OUTPUT_FILE = "data/output/CINTA-Chem_UniProt_Target_Metadata.csv"

BATCH_SIZE = 25

# ==========================================
# LOAD IDS
# ==========================================

with open(INPUT_FILE) as f:

    ids = [
        line.strip()
        for line in f
        if line.strip()
    ]

print(
    f"Total UniProt IDs: {len(ids):,}"
)
print (ids)
# ==========================================
# QUERY FUNCTION
# ==========================================

def query_uniprot(batch):

    accessions = " OR ".join(

        f"accession:{x}"

        for x in batch

    )

    url = (
        "https://rest.uniprot.org/uniprotkb/search"
    )

    params = {

        "query": accessions,

        "format": "tsv",

        "fields":
            "accession,"
            "gene_primary,"
            "organism_name,"
            "xref_kegg"

    }

    r = requests.get(
        url,
        params=params,
        timeout=60
    )
    print(r.status_code)

    if r.status_code != 200:

        print(
            "Failed:",
            r.status_code
        )

        return None

    from io import StringIO

    return pd.read_csv(
        StringIO(r.text),
        sep="\t"
    )

# ==========================================
# MAIN
# ==========================================

header_written = False

for i in range(
    0,
    len(ids),
    BATCH_SIZE
):

    batch = ids[
        i:i+BATCH_SIZE
    ]

    print(
        f"{i+1:,}"
        f"/{len(ids):,}"
    )

    df = query_uniprot(
        batch
    )

    if df is None:

        continue
    df["KEGG"] = (
    df["KEGG"]
    .str.rstrip(";")
    )
    df.to_csv(

        OUTPUT_FILE,

        mode="a",

        index=False,

        header=not header_written

    )

    header_written = True

    time.sleep(1)

print("Finished")