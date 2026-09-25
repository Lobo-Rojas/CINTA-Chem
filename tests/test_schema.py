from pathlib import Path

EXPECTED_MASTER = [
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
    "Target_Class",
]


def test_repository_exists():
    root = Path(__file__).resolve().parents[1]
    assert (root / "run_pipeline.py").exists()
    assert (root / "config.yaml").exists()


def test_expected_master_schema_is_documented():
    assert len(EXPECTED_MASTER) == 20
    assert EXPECTED_MASTER[8] == "pPotency"
