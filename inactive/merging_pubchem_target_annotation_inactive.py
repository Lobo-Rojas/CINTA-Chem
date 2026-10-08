import pandas as pd

# =====================================================
# FILES
# =====================================================

ASSAY_FILE = "data/output/CINTA-Chem_Inactive_Assay_Metadata.csv"

UNIPROT_FILE = "data/output/CINTA-Chem_Inactive_UniProt_Target_Metadata.csv"

KO_FILE = "data/output/CINTA-Chem_Inactive_KEGG_KO_Annotation.csv"

OUTPUT_FILE = "data/output/CINTA-Chem_Inactive_Target_Annotation.csv"

# =====================================================
# LOAD TABLES
# =====================================================

print("Loading files...")

assays = pd.read_csv(
    ASSAY_FILE,
    dtype=str
)

uniprot = pd.read_csv(
    UNIPROT_FILE,
    dtype=str
)

ko = pd.read_csv(
    KO_FILE,
    dtype=str
)

# =====================================================
# CLEAN UNIPROT TABLE
# =====================================================

print("Cleaning UniProt table...")

uniprot = uniprot.rename(

    columns={

        "Entry":"UniProtKB_ID",

        "Gene Names (primary)":"Gene_Symbol",

        "KEGG":"KEGG"

    }

)

uniprot["KEGG"] = (

    uniprot["KEGG"]
    .fillna("")
    .str.rstrip(";")
)

# =====================================================
# CLEAN KO TABLE
# =====================================================

print("Cleaning KO table...")

ko["KEGG"] = (

    ko["KEGG"]
    .fillna("")
    .str.rstrip(";")
)

ko["KO"] = (

    ko["KO"]
    .fillna("")
    .str.replace(
        "ko:",
        "",
        regex=False
    )
)

# =====================================================
# MERGE 1
# UniProt annotation
# =====================================================

print("Merging UniProt...")

merged = assays.merge(

    uniprot[

        [

            "UniProtKB_ID",

            "Gene_Symbol",

            "Organism",

            "KEGG"

        ]

    ],

    on="UniProtKB_ID",

    how="left",

    suffixes=("", "_new")

)

# Prefer UniProt annotation whenever available

for col in [

    "Gene_Symbol",

    "Organism"

]:

    merged[col] = (

        merged[col + "_new"]

        .combine_first(

            merged[col]

        )

    )

merged.drop(

    columns=[

        "Gene_Symbol_new",

        "Organism_new"

    ],

    inplace=True

)

# =====================================================
# MERGE 2
# KEGG -> KO
# =====================================================

print("Merging KO annotation...")

merged = merged.merge(

    ko,

    on="KEGG",

    how="left"

)

# =====================================================
# COLUMN ORDER
# =====================================================

merged = merged[

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
# REMOVE DUPLICATES
# =====================================================

merged = merged.drop_duplicates()

# =====================================================
# SAVE
# =====================================================

merged.to_csv(

    OUTPUT_FILE,

    index=False

)

# =====================================================
# SUMMARY
# =====================================================

print()

print("Finished.")

print()

print(f"Rows              : {len(merged):,}")

print(f"Unique AIDs       : {merged['PUBCHEM_AID'].nunique():,}")

print(f"UniProt IDs       : {merged['UniProtKB_ID'].notna().sum():,}")

print(f"Gene symbols      : {merged['Gene_Symbol'].notna().sum():,}")

print(f"Organisms         : {merged['Organism'].notna().sum():,}")

print(f"KEGG IDs          : {merged['KEGG'].notna().sum():,}")

print(f"KO numbers        : {merged['KO'].notna().sum():,}")

print()

print(f"Saved to: {OUTPUT_FILE}")