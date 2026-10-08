import pandas as pd
import requests
import time

INPUT = "data/output/CINTA-Chem_Inactive_UniProt_Target_Metadata.csv"
OUTPUT = "data/output/CINTA-Chem_Inactive_KEGG_KO_Annotation.csv"

BATCH_SIZE = 25
SLEEP = 0.3

df = pd.read_csv(INPUT)

genes = (
    df["KEGG"]
    .dropna()
    .astype(str)
    .str.rstrip(";")
    .unique()
)

print(f"KEGG genes: {len(genes):,}")

rows = []

for i in range(0, len(genes), BATCH_SIZE):

    batch = genes[i:i+BATCH_SIZE]

    print(f"{i+1:,}/{len(genes):,}")

    url = (
        "https://rest.kegg.jp/link/ko/"
        + "+".join(batch)
    )

    try:

        r = requests.get(url, timeout=30)

        if r.status_code != 200:

            print("Failed", r.status_code)
            continue

        for line in r.text.splitlines():

            gene, ko = line.split("\t")

            rows.append({

                "KEGG": gene,
                "KO": ko.replace("ko:", "")

            })

    except Exception as e:

        print(e)

    time.sleep(SLEEP)

pd.DataFrame(rows).to_csv(
    OUTPUT,
    index=False
)

print("Finished")