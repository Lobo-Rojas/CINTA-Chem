import pandas as pd

# ==========================================================
# FILES
# ==========================================================

INPUT_FILE = "data/final/CINTA-Chem_Master_Observations.csv"

OUTPUT_FILE = "data/final/CINTA-Chem_Target_Promiscuity.csv"

# ==========================================================
# LOAD
# ==========================================================

print("Loading master table...")

df = pd.read_csv(INPUT_FILE)

# ==========================================================
# REQUIRED COLUMNS
# ==========================================================

required = [

    "UniProtKB_ID",
    "Gene_Symbol",
    "Organism",
    "KO",
    "PUBCHEM_CID",
    "PUBCHEM_AID",
    "pPotency"

]

df = df[required].copy()

# ==========================================================
# REMOVE MISSING TARGETS
# ==========================================================

df = df.dropna(subset=["UniProtKB_ID"])

# ==========================================================
# SORT BY TARGET
# ==========================================================

df = df.sort_values(
    ["UniProtKB_ID", "pPotency"],
    ascending=[True, False]
)

# ==========================================================
# BUILD TABLE
# ==========================================================

records = []

groups = df.groupby("UniProtKB_ID", sort=False)

total = len(groups)

for i, (uniprot, g) in enumerate(groups, start=1):

    if i % 250 == 0:

        print(f"{i:,}/{total:,}")

    gene = g["Gene_Symbol"].dropna()

    organism = g["Organism"].dropna()

    ko = g["KO"].dropna()

    cid_list = sorted(
        g["PUBCHEM_CID"]
        .astype(int)
        .unique()
    )

    aid_list = sorted(
        g["PUBCHEM_AID"]
        .astype(int)
        .unique()
    )

    potency = g["pPotency"].dropna()

    records.append({

        "UniProt": uniprot,

        "Gene":
        gene.iloc[0]
        if len(gene) else "",

        "Organism":
        organism.iloc[0]
        if len(organism) else "",

        "KO":
        ko.iloc[0]
        if len(ko) else "",

        "Number_of_compounds":
        len(cid_list),

        "Number_of_observations":
        len(g),

        "COMPOUND_CID_List":
        ";".join(map(str, cid_list)),

        "COMPOUND_AID_List":
        ";".join(map(str, aid_list)),

        "Median_activity":
        potency.median(),

        "Mean_activity":
        potency.mean(),

        "Best_activity":
        potency.max(),

        "Worst_activity":
        potency.min()

    })

# ==========================================================
# SAVE
# ==========================================================

out = pd.DataFrame(records)

out = out.sort_values(
    "Number_of_compounds",
    ascending=False
)

out.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("Finished.")
print(f"Targets: {len(out):,}")
print(f"Saved to: {OUTPUT_FILE}")