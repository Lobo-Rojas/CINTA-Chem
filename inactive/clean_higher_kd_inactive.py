import numpy as np
import pandas as pd

INPUT_FILE = "data/output/pubchem_unique_inactive_annotated_master.csv"
OUTPUT_FILE = "data/output/pubchem_unique_inactive_annotated_master_clean.csv"

print("Loading inactive database...")
df = pd.read_csv(INPUT_FILE, low_memory=False)
print(f"Initial observations: {len(df):,}")

# IMPORTANT: all INACTIVE observations are retained regardless of whether
# a potency/value exists. pPotency is calculated only where a positive
# numeric concentration is available.
value = pd.to_numeric(df["PubChem_Standard_Value_uM"], errors="coerce")
valid = value.gt(0)

df["pPotency"] = np.nan
df.loc[valid, "pPotency"] = -np.log10(value.loc[valid] * 1e-6)

print(f"Observations retained: {len(df):,}")
print(f"With numeric positive potency: {valid.sum():,}")
print(f"Without usable potency value: {(~valid).sum():,}")

# No pPotency threshold is applied here: this is deliberate so that
# every observation labelled INACTIVE remains in the final database.
df.to_csv(OUTPUT_FILE, index=False)

print(f"Output written to: {OUTPUT_FILE}")
