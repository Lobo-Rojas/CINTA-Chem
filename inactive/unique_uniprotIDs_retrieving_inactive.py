import pandas as pd

metadata = pd.read_csv(
    "data/output/CINTA-Chem_Inactive_Assay_Metadata.csv"
)

uniprots = (
    metadata["UniProtKB_ID"]
    .dropna()
    .drop_duplicates()
)

uniprots.to_csv(
    "data/output/CINTA-Chem_Inactive_Unique_UniProt_IDs.txt",
    index=False,
    header=False
)

print(len(uniprots))