import pandas as pd
import pickle
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit.Chem import Crippen
from rdkit.Chem import Lipinski
from rdkit.Chem import rdMolDescriptors
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit.Chem import AllChem

# ==========================================================
# FILES
# ==========================================================

INPUT_FILE = "data/final/CINTA-Chem_Master_Observations.csv"

OUTPUT_FILE = "data/final/CINTA-Chem_Molecular_Descriptors.csv"

FINGERPRINT_FILE = "data/final/CINTA-Chem_Molecular_Fingerprints.pkl"

# ==========================================================
# LOAD UNIQUE COMPOUNDS
# ==========================================================

print("Loading database...")

df = pd.read_csv(
    INPUT_FILE,
    usecols=[
        "PUBCHEM_CID",
        "SMILES"
    ]
)

df = (
    df
    .drop_duplicates("PUBCHEM_CID")
    .reset_index(drop=True)
)

print(f"Unique compounds: {len(df):,}")

# ==========================================================
# FIRST PASS
# Compute descriptors
# ==========================================================

records = []

fingerprints = {}

all_scaffolds = set()

for i, row in df.iterrows():

    if (i + 1) % 10000 == 0:

        print(f"{i+1:,}/{len(df):,}")

    cid = row["PUBCHEM_CID"]

    smiles = row["SMILES"]

    mol = Chem.MolFromSmiles(smiles)

    if mol is None:

        records.append({

            "PUBCHEM_CID": cid,

            "SMILES": smiles,

            "Valid_SMILES": False,

            "Molecular_Weight": None,

            "Exact_Molecular_Weight": None,

            "cLogP": None,

            "TPSA": None,

            "HBD": None,

            "HBA": None,

            "Rotatable_Bonds": None,

            "Fraction_CSP3": None,

            "Heavy_Atom_Count": None,

            "Ring_Count": None,

            "Aromatic_Ring_Count": None,

            "Murcko_Scaffold": None

        })

        continue

    scaffold = MurckoScaffold.MurckoScaffoldSmiles(
        mol=mol
    )

    all_scaffolds.add(scaffold)

    records.append({

        "PUBCHEM_CID": cid,

        "SMILES": smiles,

        "Valid_SMILES": True,

        "Molecular_Weight":
        Descriptors.MolWt(mol),

        "Exact_Molecular_Weight":
        Descriptors.ExactMolWt(mol),

        "cLogP":
        Crippen.MolLogP(mol),

        "TPSA":
        rdMolDescriptors.CalcTPSA(mol),

        "HBD":
        Lipinski.NumHDonors(mol),

        "HBA":
        Lipinski.NumHAcceptors(mol),

        "Rotatable_Bonds":
        Lipinski.NumRotatableBonds(mol),

        "Fraction_CSP3":
        rdMolDescriptors.CalcFractionCSP3(mol),

        "Heavy_Atom_Count":
        mol.GetNumHeavyAtoms(),

        "Ring_Count":
        rdMolDescriptors.CalcNumRings(mol),

        "Aromatic_Ring_Count":
        rdMolDescriptors.CalcNumAromaticRings(mol),

        "Murcko_Scaffold":
        scaffold

    })

    fingerprints[cid] = AllChem.GetMorganFingerprintAsBitVect(
        mol,
        radius=2,
        nBits=2048
    )

# ==========================================================
# DETERMINISTIC SCAFFOLD IDS
# ==========================================================

print("Assigning scaffold IDs...")

scaffold_dict = {

    scaffold: idx + 1

    for idx, scaffold in enumerate(

        sorted(

            s for s in all_scaffolds

            if s != ""

        )

    )

}

# ==========================================================
# BUILD DATAFRAME
# ==========================================================

desc = pd.DataFrame(records)

desc["Murcko_Scaffold_ID"] = (

    desc["Murcko_Scaffold"]

    .map(scaffold_dict)

)

# ==========================================================
# SAVE DESCRIPTORS
# ==========================================================

desc.to_csv(
    OUTPUT_FILE,
    index=False
)

print()

print(
    f"Descriptors saved to {OUTPUT_FILE}"
)

# ==========================================================
# SAVE FINGERPRINTS
# ==========================================================

with open(
    FINGERPRINT_FILE,
    "wb"
) as f:

    pickle.dump(
        fingerprints,
        f,
        protocol=pickle.HIGHEST_PROTOCOL
    )

print(
    f"Morgan fingerprints saved to {FINGERPRINT_FILE}"
)

print("Finished.")