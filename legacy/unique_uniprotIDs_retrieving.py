import pandas as pd

metadata = pd.read_csv(
    "data/output/pubchem_assay_metadata.csv"
)

uniprots = (
    metadata["UniProtKB_ID"]
    .dropna()
    .drop_duplicates()
)

uniprots.to_csv(
    "data/output/unique_uniprots.txt",
    index=False,
    header=False
)

print(len(uniprots))