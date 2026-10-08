import pandas as pd

# =====================================================
# FILES
# =====================================================

INPUT_FILE = "data/output/CINTA-Chem_Active_Annotated_Master.csv"

OUTPUT_FILE = "data/output/CINTA-Chem_Unique_Active_Annotated_Master.csv"

# =====================================================
# LOAD
# =====================================================

print("Loading master observation table...")

df = pd.read_csv(
    INPUT_FILE,
    dtype=str,
    low_memory=False
)

print(f"Initial observations: {len(df):,}")

# =====================================================
# KEEP ONLY PROTEIN TARGETS
# =====================================================

df = df[

    df["UniProtKB_ID"].notna()

]

print(f"After UniProt filter: {len(df):,}")

# =====================================================
# KEEP ONLY KEGG ORTHOLOGY
# =====================================================

df = df[

    df["KO"].notna()

]

print(f"After KO filter: {len(df):,}")


# =====================================================
# KEEP ONLY NUMERIC VALUES
# =====================================================

df["PubChem_Standard_Value_uM"] = pd.to_numeric(

    df["PubChem_Standard_Value_uM"],

    errors="coerce"

)

df = df[

    df["PubChem_Standard_Value_uM"].notna()

]

print(f"After numeric value filter: {len(df):,}")

# =====================================================
# REMOVE ONLY TRUE DUPLICATES
# =====================================================

before = len(df)

df = df.drop_duplicates()

removed = before - len(df)

print(f"Exact duplicated rows removed: {removed:,}")

# =====================================================
# SORT
# =====================================================

df = df.sort_values(

    [

        "UniProtKB_ID",

        "PUBCHEM_CID",

        "PubChem_Standard_Type",

        "PubChem_Standard_Value_uM"

    ]

)

# =====================================================
# SAVE
# =====================================================

df.to_csv(

    OUTPUT_FILE,

    index=False

)

# =====================================================
# SUMMARY
# =====================================================

print("\n==============================")
print("FINAL DATABASE")
print("==============================")

print(f"Observations          : {len(df):,}")

print(f"Unique compounds      : {df['PUBCHEM_CID'].nunique():,}")

print(f"Unique assays         : {df['PUBCHEM_AID'].nunique():,}")

print(f"Unique proteins       : {df['UniProtKB_ID'].nunique():,}")

print(f"Unique KO             : {df['KO'].nunique():,}")

print(f"Activity types")

print(

    df["PubChem_Standard_Type"]

    .value_counts()

)

print(f"\nSaved as:\n{OUTPUT_FILE}")