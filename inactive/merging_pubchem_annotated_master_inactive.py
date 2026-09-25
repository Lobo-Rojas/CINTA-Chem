import pandas as pd

# =====================================================
# FILES
# =====================================================

COMPOUND_FILE = "data/output/pubchem_inactive_compounds.csv"

TARGET_FILE = "data/output/pubchem_target_annotation_inactive.csv"

OUTPUT_FILE = "data/output/pubchem_inactive_annotated_master.csv"

# =====================================================
# LOAD TABLES
# =====================================================

print("Loading files...")

compounds = pd.read_csv(
    COMPOUND_FILE,
    dtype=str,
    low_memory=False
)

targets = pd.read_csv(
    TARGET_FILE,
    dtype=str,
    low_memory=False
)

print(f"Compound observations : {len(compounds):,}")
print(f"Target annotations    : {len(targets):,}")

# =====================================================
# CLEAN TARGET TABLE
# =====================================================

# Remove duplicated AIDs if present

targets = (

    targets
    .drop_duplicates(
        subset="PUBCHEM_AID"
    )

)

# Standardize KEGG column

if "KEGG" in targets.columns:

    targets["KEGG"] = (

        targets["KEGG"]
        .fillna("")
        .str.rstrip(";")

    )

# =====================================================
# KEEP ONLY NECESSARY COLUMNS
# =====================================================

targets = targets[

    [

        "PUBCHEM_AID",

        "Assay_Name",

        "Target_Name",

        "UniProtKB_ID",

        "Gene_Symbol",

        "Organism",

        "KEGG",

        "KO"

    ]

]

# =====================================================
# RENAME NEW COLUMNS
# =====================================================

targets = targets.rename(

    columns={

        "KEGG":"KEGG_Gene_ID"

    }

)

# =====================================================
# MERGE
# =====================================================

print("Merging annotation...")

master = compounds.merge(

    targets,

    on="PUBCHEM_AID",

    how="left"

)

# =====================================================
# COLUMN ORDER
# =====================================================

COLUMN_ORDER = [

    # ---------------------------------------------
    # Original columns
    # ---------------------------------------------

    "PUBCHEM_AID",

    "PUBCHEM_SID",

    "PUBCHEM_CID",

    "SMILES",

    "PUBCHEM_ACTIVITY_OUTCOME",

    "PUBCHEM_ASSAY_URL",

    "RESULT_IS_ACTIVE_CONCENTRATION",

    "PubChem_Standard_Value_uM",

    "PubChem_Standard_Type",

    # ---------------------------------------------
    # Annotation columns
    # ---------------------------------------------

    "Assay_Name",

    "Target_Name",

    "UniProtKB_ID",

    "Gene_Symbol",

    "Organism",

    "KEGG_Gene_ID",

    "KO"

]

master = master[COLUMN_ORDER]

# =====================================================
# SAVE
# =====================================================

master.to_csv(

    OUTPUT_FILE,

    index=False

)

# =====================================================
# SUMMARY
# =====================================================

print("\nFinished.")

print(f"\nTotal observations : {len(master):,}")

print(f"Unique compounds   : {master['PUBCHEM_CID'].nunique():,}")

print(f"Unique assays      : {master['PUBCHEM_AID'].nunique():,}")

print(f"Annotated assays   : {master['UniProtKB_ID'].notna().sum():,}")

print(f"Unique proteins    : {master['UniProtKB_ID'].dropna().nunique():,}")

print(f"Unique KO numbers  : {master['KO'].dropna().nunique():,}")

print(f"\nSaved as:\n{OUTPUT_FILE}")