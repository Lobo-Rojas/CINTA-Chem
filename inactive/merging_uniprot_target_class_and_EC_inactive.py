import pandas as pd

# ==========================================================
# FILES
# ==========================================================

MASTER_FILE = "data/output/pubchem_unique_inactive_annotated_master_clean.csv"

ANNOTATION_FILE = "data/output/uniprot_target_classification_assigned_inactive.csv"

OUTPUT_FILE = "data/final/master_observations_inactive_table.csv"


# ==========================================================
# LOAD MASTER TABLE
# ==========================================================

print("Loading master table...")

master = pd.read_csv(
    MASTER_FILE,
    low_memory=False
)

print(f"Master rows: {len(master):,}")


# ==========================================================
# LOAD UNIPROT ANNOTATION TABLE
# ==========================================================

print("Loading UniProt annotation table...")

annotation = pd.read_csv(
    ANNOTATION_FILE
)

print(f"Annotation rows: {len(annotation):,}")


# ==========================================================
# CHECK REQUIRED COLUMNS
# ==========================================================

if "UniProtKB_ID" not in master.columns:
    raise ValueError(
        "Column 'UniProtKB_ID' was not found in the master table."
    )

required_annotation_columns = [
    "UniProt_ID",
    "Protein_Family",
    "EC_Number",
    "Target_Class"
]

missing = [
    col
    for col in required_annotation_columns
    if col not in annotation.columns
]

if missing:
    raise ValueError(
        f"Missing columns in annotation table: {missing}"
    )


# ==========================================================
# CLEAN UNIPROT IDS
# ==========================================================

master["UniProtKB_ID"] = (
    master["UniProtKB_ID"]
    .astype("string")
    .str.strip()
)

annotation["UniProt_ID"] = (
    annotation["UniProt_ID"]
    .astype("string")
    .str.strip()
)


# ==========================================================
# CHECK FOR DUPLICATE UNIPROT IDS
# ==========================================================

duplicate_ids = annotation[
    annotation["UniProt_ID"].duplicated(
        keep=False
    )
]

if len(duplicate_ids) > 0:

    print(
        "\nWARNING:"
        f" {duplicate_ids['UniProt_ID'].nunique()} "
        "UniProt IDs appear more than once "
        "in the annotation table."
    )

    print(
        duplicate_ids[
            [
                "UniProt_ID",
                "Protein_Family",
                "EC_Number",
                "Target_Class"
            ]
        ].sort_values("UniProt_ID").head(20)
    )

    # Keep one annotation per UniProt ID
    annotation = (
        annotation
        .drop_duplicates(
            subset="UniProt_ID",
            keep="first"
        )
    )

    print(
        "Duplicate UniProt IDs removed before merging."
    )


# ==========================================================
# MERGE
# ==========================================================

print("\nMerging UniProt target annotations...")

master_annotated = master.merge(
    annotation[
        [
            "UniProt_ID",
            "Protein_Family",
            "EC_Number",
            "Target_Class"
        ]
    ],
    how="left",
    left_on="UniProtKB_ID",
    right_on="UniProt_ID",
    validate="many_to_one"
)


# ==========================================================
# REMOVE DUPLICATE KEY
# ==========================================================

master_annotated.drop(
    columns=["UniProt_ID"],
    inplace=True
)


# ==========================================================
# CHECK ROW COUNT
# ==========================================================

if len(master_annotated) != len(master):

    raise RuntimeError(
        "ERROR: Number of rows changed during merge!"
        f"\nOriginal: {len(master):,}"
        f"\nAfter merge: {len(master_annotated):,}"
    )

print(
    f"\nRow count preserved: {len(master_annotated):,}"
)


# ==========================================================
# ANNOTATION COVERAGE
# ==========================================================

annotated = (
    master_annotated["Target_Class"]
    .notna()
    .sum()
)

total = len(master_annotated)

coverage = (
    annotated / total * 100
    if total > 0
    else 0
)

print("\nAnnotation coverage:")
print(
    f"Annotated observations: {annotated:,}"
)

print(
    f"Unannotated observations: {total - annotated:,}"
)

print(
    f"Coverage: {coverage:.2f}%"
)


# ==========================================================
# TARGET CLASS DISTRIBUTION
# ==========================================================

print("\nTarget-class distribution:")

print(
    master_annotated[
        "Target_Class"
    ]
    .value_counts(
        dropna=False
    )
)


# ==========================================================
# COLUMN ORDER
# ==========================================================

COLUMN_ORDER = [
    "PUBCHEM_AID",
    "PUBCHEM_SID",
    "PUBCHEM_CID",
    "SMILES",
    "PUBCHEM_ACTIVITY_OUTCOME",
    "PUBCHEM_ASSAY_URL",
    "RESULT_IS_ACTIVE_CONCENTRATION",
    "PubChem_Standard_Value_uM",
    "pPotency",
    "PubChem_Standard_Type",
    "Assay_Name",
    "Target_Name",
    "UniProtKB_ID",
    "Gene_Symbol",
    "Organism",
    "KEGG_Gene_ID",
    "KO",
    "Protein_Family",
    "EC_Number",
    "Target_Class"
]

missing_final = [
    col
    for col in COLUMN_ORDER
    if col not in master_annotated.columns
]

if missing_final:
    raise ValueError(
        f"Missing final master columns: {missing_final}"
    )

master_annotated = master_annotated[COLUMN_ORDER]


# ==========================================================
# SAVE FINAL DATABASE
# ==========================================================

master_annotated.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nFinished.")
print(
    f"Final database saved as:\n{OUTPUT_FILE}"
)
