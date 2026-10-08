import pandas as pd
import re


# ==========================================================
# FILES
# ==========================================================

INPUT_FILE = "data/output/CINTA-Chem_Inactive_UniProt_Target_Classification.csv"
OUTPUT_FILE = "data/output/CINTA-Chem_Inactive_UniProt_Target_Classification_Assigned.csv"


# ==========================================================
# TARGET CLASSIFICATION
# ==========================================================

def classify_target(protein_family, ec_number):

    family = str(protein_family).lower() if pd.notna(protein_family) else ""
    ec = str(ec_number).lower() if pd.notna(ec_number) else ""

    # ------------------------------------------------------
    # 1. KINASE
    # ------------------------------------------------------

    # Protein-family evidence has priority.
    if (
        "kinase" in family
        or "protein kinase" in family
        or "phosphokinase" in family
    ):
        return "Kinase"

    # EC 2.7 = Transferring phosphorus-containing groups
    # However, not every EC 2.7 enzyme should automatically
    # be considered a biological kinase target.
    #
    # We therefore use EC 2.7 only when the family also
    # suggests kinase/phosphorylation activity.

    if "2.7." in ec and (
        "phosphoryl" in family
        or "kinase" in family
    ):
        return "Kinase"


    # ------------------------------------------------------
    # 2. GPCR
    # ------------------------------------------------------

    if (
        "g-protein coupled receptor" in family
        or "g protein-coupled receptor" in family
        or "g-protein coupled" in family
        or "gpcr" in family
    ):
        return "GPCR"


    # ------------------------------------------------------
    # 3. ION CHANNEL
    # ------------------------------------------------------

    if (
        "ion channel" in family
        or "voltage-gated channel" in family
        or "ligand-gated channel" in family
        or "cation channel" in family
        or "anion channel" in family
        or "potassium channel" in family
        or "sodium channel" in family
        or "calcium channel" in family
        or "chloride channel" in family
        or "ion-conducting" in family
    ):
        return "Ion channel"


    # ------------------------------------------------------
    # 4. PROTEASE
    # ------------------------------------------------------

    if (
        "protease" in family
        or "peptidase" in family
        or "proteinase" in family
        or "endopeptidase" in family
        or "exopeptidase" in family
    ):
        return "Protease"

    # EC 3.4 = Acting on peptide bonds
    if "3.4." in ec:
        return "Protease"


    # ------------------------------------------------------
    # 5. OXIDOREDUCTASE
    # ------------------------------------------------------

    # EC 1 = oxidoreductases
    if re.search(r"(^|;\s*)1\.", ec):
        return "Oxidoreductase"

    if (
        "oxidoreductase" in family
        or "dehydrogenase" in family
        or "reductase" in family
        or "oxidase" in family
        or "peroxidase" in family
        or "oxygenase" in family
        or "dioxygenase" in family
        or "monooxygenase" in family
    ):
        return "Oxidoreductase"


    # ------------------------------------------------------
    # 6. TRANSFERASE
    # ------------------------------------------------------

    # EC 2 = transferases
    if re.search(r"(^|;\s*)2\.", ec):
        return "Transferase"

    if (
        "transferase" in family
        or "transaminase" in family
        or "aminotransferase" in family
        or "glycosyltransferase" in family
        or "acetyltransferase" in family
        or "methyltransferase" in family
    ):
        return "Transferase"


    # ------------------------------------------------------
    # 7. HYDROLASE
    # ------------------------------------------------------

    # EC 3 = hydrolases
    if re.search(r"(^|;\s*)3\.", ec):
        return "Hydrolase"

    if (
        "hydrolase" in family
        or "phosphatase" in family
        or "esterase" in family
        or "lipase" in family
        or "amidase" in family
        or "glycosidase" in family
        or "nuclease" in family
    ):
        return "Hydrolase"


    # ------------------------------------------------------
    # 8. LYASE
    # ------------------------------------------------------

    # EC 4 = lyases
    if re.search(r"(^|;\s*)4\.", ec):
        return "Lyase"

    if (
        "lyase" in family
        or "decarboxylase" in family
        or "aldolase" in family
        or "dehydratase" in family
        or "hydratase" in family
    ):
        return "Lyase"


    # ------------------------------------------------------
    # 9. ISOMERASE
    # ------------------------------------------------------

    # EC 5 = isomerases
    if re.search(r"(^|;\s*)5\.", ec):
        return "Isomerase"

    if (
        "isomerase" in family
        or "epimerase" in family
        or "racemase" in family
        or "mutase" in family
    ):
        return "Isomerase"


    # ------------------------------------------------------
    # 10. LIGASE
    # ------------------------------------------------------

    # EC 6 = ligases
    if re.search(r"(^|;\s*)6\.", ec):
        return "Ligase"

    if (
        "ligase" in family
        or "synthetase" in family
        or "carboxylase" in family
    ):
        return "Ligase"


    # ------------------------------------------------------
    # 11. TRANSPORTER
    # ------------------------------------------------------

    # Transporters generally do not have EC numbers.
    # Therefore family/name annotation is essential.

    if (
        "transporter" in family
        or "transport protein" in family
        or "transporting atpase" in family
        or "abc transporter" in family
        or "solute carrier" in family
        or "carrier protein" in family
        or "permease" in family
        or "antiporter" in family
        or "symporter" in family
        or "exchanger" in family
    ):
        return "Transporter"


    # ------------------------------------------------------
    # 12. NUCLEAR RECEPTOR
    # ------------------------------------------------------

    if (
        "nuclear receptor" in family
        or "steroid receptor" in family
        or "hormone receptor" in family
    ):
        return "Nuclear receptor"


    # ------------------------------------------------------
    # 13. TRANSCRIPTION FACTOR
    # ------------------------------------------------------

    if (
        "transcription factor" in family
        or "transcriptional factor" in family
        or "transcription regulator" in family
        or "transcriptional regulator" in family
        or "dna-binding protein" in family
        or "dna binding protein" in family
    ):
        return "Transcription factor"


    # ------------------------------------------------------
    # 14. STRUCTURAL PROTEIN
    # ------------------------------------------------------

    if (
        "structural protein" in family
        or "cytoskeletal protein" in family
        or "actin" in family
        or "tubulin" in family
        or "collagen" in family
        or "keratin" in family
        or "intermediate filament" in family
    ):
        return "Structural protein"


    # ------------------------------------------------------
    # 15. OTHER
    # ------------------------------------------------------

    return "Other"


# ==========================================================
# LOAD ANNOTATION TABLE
# ==========================================================

df = pd.read_csv(INPUT_FILE)


# ==========================================================
# CHECK REQUIRED COLUMNS
# ==========================================================

required_columns = [
    "UniProt_ID",
    "Protein_Family",
    "EC_Number"
]

missing = [
    col
    for col in required_columns
    if col not in df.columns
]

if missing:
    raise ValueError(
        f"Missing required columns: {missing}"
    )


# ==========================================================
# ASSIGN TARGET CLASS
# ==========================================================

df["Target_Class"] = df.apply(
    lambda row: classify_target(
        row["Protein_Family"],
        row["EC_Number"]
    ),
    axis=1
)


# ==========================================================
# SAVE
# ==========================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nFinished.")
print(f"Saved: {OUTPUT_FILE}")


# ==========================================================
# SUMMARY
# ==========================================================

print("\nTarget class distribution:")
print(
    df["Target_Class"]
    .value_counts(dropna=False)
)