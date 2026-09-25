import pandas as pd

metadata = pd.read_csv(
    "data/output/pubchem_assay_metadata_inactive.csv"
)

uniprots = (
    metadata["UniProtKB_ID"]
    .dropna()
    .drop_duplicates()
)

uniprots.to_csv(
    "data/output/unique_uniprots_inactive.txt",
    index=False,
    header=False
)

print(len(uniprots))