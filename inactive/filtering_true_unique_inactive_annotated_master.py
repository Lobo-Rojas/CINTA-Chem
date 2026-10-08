import pandas as pd

INPUT_FILE = "data/output/CINTA-Chem_Inactive_Annotated_Master.csv"
OUTPUT_FILE = "data/output/CINTA-Chem_Unique_Inactive_Annotated_Master.csv"

print("Loading inactive master observation table...")
df = pd.read_csv(INPUT_FILE, dtype=str, low_memory=False)
print(f"Initial observations: {len(df):,}")

# Unlike the active branch, inactive observations are NOT filtered out
# because of missing UniProt/KO annotations. Target metadata and target
# classification are added when available, while every explicitly INACTIVE
# observation is retained for the final inactive table.

before = len(df)
df = df.drop_duplicates()
print(f"Exact duplicated rows removed: {before - len(df):,}")

df = df.sort_values([
    "UniProtKB_ID",
    "PUBCHEM_CID",
    "PubChem_Standard_Type",
    "PubChem_Standard_Value_uM"
], na_position="last")

df.to_csv(OUTPUT_FILE, index=False)

print("\nInactive target-ready database")
print(f"Observations     : {len(df):,}")
print(f"Unique compounds : {df['PUBCHEM_CID'].nunique():,}")
print(f"Unique assays    : {df['PUBCHEM_AID'].nunique():,}")
print(f"Unique proteins  : {df['UniProtKB_ID'].nunique():,}")
print(f"Unique KO        : {df['KO'].nunique():,}")
print(f"Saved as         : {OUTPUT_FILE}")
