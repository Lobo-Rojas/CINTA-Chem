import pandas as pd

# ==========================================================
# FILES
# ==========================================================

INPUT_FILE = "data/final/CINTA-Chem_Master_Observations.csv"

OUTPUT_FILE = "data/final/CINTA-Chem_Polypharmacology.csv"

# ==========================================================
# LOAD
# ==========================================================

print("Loading master table...")

df = pd.read_csv(INPUT_FILE)

print(f"Observations: {len(df):,}")

# ==========================================================
# REQUIRED COLUMNS
# ==========================================================

required = [
    "PUBCHEM_CID",
    "SMILES",
    "Target_Name",
    "Gene_Symbol",
    "UniProtKB_ID",
    "KO",
    "PUBCHEM_AID",
    "PubChem_Standard_Type",
    "pPotency"
]

df = df[required].copy()

# ==========================================================
# GROUP BY COMPOUND
# ==========================================================

rows = []

total = df["PUBCHEM_CID"].nunique()

print(f"Unique compounds: {total:,}")

for i, (cid, group) in enumerate(df.groupby("PUBCHEM_CID"), start=1):

    if i % 5000 == 0:
        print(f"{i:,}/{total:,}")

    smiles = group[
        "SMILES"
    ].iloc[0]

    target_list = sorted(
        group["Target_Name"]
        .dropna()
        .astype(str)
        .unique()
    )

    gene_list = sorted(
        group["Gene_Symbol"]
        .dropna()
        .astype(str)
        .unique()
    )

    uniprot_list = sorted(
        group["UniProtKB_ID"]
        .dropna()
        .astype(str)
        .unique()
    )

    ko_list = sorted(
        group["KO"]
        .dropna()
        .astype(str)
        .unique()
    )

    aid_list = sorted(
        group["PUBCHEM_AID"]
        .astype(int)
        .astype(str)
        .unique()
    )

    activity_types = sorted(
        group["PubChem_Standard_Type"]
        .dropna()
        .astype(str)
        .unique()
    )

    potency = pd.to_numeric(
        group["pPotency"],
        errors="coerce"
    ).dropna()

    rows.append({

        "PUBCHEM_CID": cid,

        "SMILES": smiles,

        "Number_of_Targets": len(uniprot_list),

        "Target_Name_List":
            ";".join(target_list),

        "Gene_List":
            ";".join(gene_list),

        "UniProt_ID_List":
            ";".join(uniprot_list),

        "KO_List":
            ";".join(ko_list),

        "AID_List":
            ";".join(aid_list),

        "Activity_Types":
            ";".join(activity_types),

        "Number_of_Assays":
            len(group),

        "Best_pPotency":
            potency.max(),

        "Median_pPotency":
            potency.median(),

        "Worst_pPotency":
            potency.min()

    })

# ==========================================================
# SAVE
# ==========================================================

poly = pd.DataFrame(rows)

poly.sort_values(

    by=[
        "Number_of_Targets",
        "Best_pPotency"
    ],

    ascending=[
        False,
        False
    ],

    inplace=True

)

poly.to_csv(
    OUTPUT_FILE,
    index=False
)

# ==========================================================
# SUMMARY
# ==========================================================

print("\nFinished.\n")

print(f"Compounds: {len(poly):,}")

print(f"Output: {OUTPUT_FILE}")

print("\nSummary:")

print(poly[
    [
        "Number_of_Targets",
        "Best_pPotency",
        "Median_pPotency",
        "Worst_pPotency"
    ]
].describe())