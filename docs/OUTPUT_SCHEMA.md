# Output schema

This document describes the generated final files without renaming any production columns or files.

## master_observations_table.csv

```text
PUBCHEM_AID
PUBCHEM_SID
PUBCHEM_CID
SMILES
PUBCHEM_ACTIVITY_OUTCOME
PUBCHEM_ASSAY_URL
RESULT_IS_ACTIVE_CONCENTRATION
PubChem_Standard_Value_uM
pPotency
PubChem_Standard_Type
Assay_Name
Target_Name
UniProtKB_ID
Gene_Symbol
Organism
KEGG_Gene_ID
KO
Protein_Family
EC_Number
Target_Class
```

## pubchem_compound_polypharmacology_table.csv

The compound-level table summarizes the number of observed targets and assays and summarizes best, median, and worst pPotency values. The existing list-valued columns are retained exactly as produced by the validated script.

## pubchem_target_promiscuity_table.csv

The target-level table summarizes the number of active compounds and observations associated with each UniProt target and summarizes the pPotency distribution. Existing list-valued columns are retained exactly as produced by the validated script.

## molecular_descriptors.csv

The descriptor table contains one row per unique PubChem CID with SMILES validity, physicochemical descriptors, structural counts, and Bemis-Murcko scaffold information.

## morgan_fingerprints.pkl

The fingerprint file stores Morgan fingerprints for the same unique compounds used in the descriptor calculation, using radius 2 and 2048 bits.

## data_quality_score_table.csv

The quality table summarizes replicate observations at the compound-target level.


## Inactive final outputs

`master_observations_inactive_table.csv` uses the same final observation schema as `master_observations_table.csv`, but contains the inactive branch. All explicitly `INACTIVE` observations retained by the filter are preserved through the potency-cleaning step, including rows with missing `PubChem_Standard_Value_uM`; `pPotency` is populated only when a positive numeric concentration is available.

`inactive_molecular_descriptors.csv` and `inactive_morgan_fingerprints.pkl` use the same RDKit descriptor and Morgan fingerprint settings as the active branch.
