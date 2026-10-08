import numpy as np
import pandas as pd

# ==========================================================
# FILES
# ==========================================================

INPUT_FILE = "data/output/CINTA-Chem_Unique_Active_Annotated_Master.csv"

OUTPUT_FILE = "data/output/CINTA-Chem_Unique_Active_Annotated_Master_Clean.csv"

# ==========================================================
# PARAMETERS
# ==========================================================

MAX_POTENCY = 15.0

# ==========================================================
# LOAD
# ==========================================================

print("Loading database...")

df = pd.read_csv(INPUT_FILE)

print(f"Initial observations: {len(df):,}")

# ==========================================================
# CLEAN POTENCY COLUMN
# ==========================================================

df["PubChem_Standard_Value_uM"] = pd.to_numeric(
    df["PubChem_Standard_Value_uM"],
    errors="coerce"
)

df = df[
    df["PubChem_Standard_Value_uM"].notna()
]

df = df[
    df["PubChem_Standard_Value_uM"] > 0
]

print(f"After removing invalid concentrations: {len(df):,}")

# ==========================================================
# CONVERT uM -> M
# ==========================================================

df["Potency_M"] = (
    df["PubChem_Standard_Value_uM"] * 1e-6
)

# ==========================================================
# CALCULATE pPOTENCY
# ==========================================================

df["pPotency"] = -np.log10(
    df["Potency_M"]
)
# ==========================================================
# SAVE TABLE UNREALISTIC POTENCY OBSERVATIONS
# ==========================================================
outliers = df[df["pPotency"] > MAX_POTENCY]

outliers.to_csv(
    "data/output/CINTA-Chem_Removed_Unrealistic_Potencies.csv",
    index=False
)

# ==========================================================
# REMOVE UNREALISTIC VALUES
# ==========================================================

before = len(df)

df = df[
    df["pPotency"] <= MAX_POTENCY
]

removed = before - len(df)

print(f"Removed {removed:,} observations with pPotency > {MAX_POTENCY}")

# ==========================================================
# OPTIONAL
# Remove Potency_M column
# ==========================================================

df.drop(
    columns=["Potency_M"],
    inplace=True
)

# ==========================================================
# SAVE
# ==========================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print()

print("Finished successfully.")

print(f"Final observations: {len(df):,}")

print(f"Removed observations: {removed:,}")

print(f"Output written to:\n{OUTPUT_FILE}")

print()

print(df["pPotency"].describe())