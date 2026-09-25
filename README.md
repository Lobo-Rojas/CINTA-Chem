# PubChem Chemogenomics Pipeline v1.0

Reproducible workflow for constructing a PubChem-derived chemogenomics database from PubChem BioAssay observations and linked UniProt/KEGG target annotations.

**Release:** 1.0  
**Status:** reproducible release; validated production scripts are preserved unchanged.  
**Primary workflow:** active observations  
**Additional workflow:** inactive observations and balanced inactive-compound data

## What this repository contains

This repository contains the complete workflow used to generate the database, including:

- PubChem BioAssay bulk-data retrieval;
- active and inactive observation filtering;
- PubChem assay metadata retrieval;
- UniProt target identification and annotation;
- KEGG gene/KO annotation;
- protein-family and target-class assignment;
- compound-level polypharmacology summaries;
- target-level promiscuity summaries;
- RDKit molecular descriptors and Morgan fingerprints;
- compound-target data-quality summaries;
- resumable checkpoints and execution logs;
- documentation of data sources, schemas, rate limits, provenance, and reproducibility.

The repository intentionally separates the orchestration layer from the validated historical processing scripts. The files under `legacy/` and `inactive/` are treated as the production implementation for this release and have not been rewritten for v1.0.

## Version 1.0 and code-freeze policy

`VERSION` and `PIPELINE_VERSION` are the authoritative repository release identifiers and both contain `1.0`.

The v1.0 release does **not** change the scientific processing code. In particular, the Python and shell scripts supplied in the uploaded working package are preserved unchanged. Historical version strings that occur inside source-code comments/docstrings are retained as provenance and are not used as the authoritative release identifier.

For future releases, changes to filtering criteria, target-classification rules, output schemas, output filenames, or other scientific definitions must receive a new documented version rather than being silently changed under the same version.

## Quick start

### 1. Clone the repository

```bash
git clone <YOUR-GITHUB-REPOSITORY-URL>
cd pubchem_chemogenomics_pipeline
```

### 2. Create the environment

The recommended environment is documented in `environment.yml` and `docs/ENVIRONMENT.md`.

With Conda/Mamba:

```bash
conda env create -f environment.yml
conda activate pubchem-chemogenomics
```

Alternatively, with an existing Python 3.10 environment:

```bash
python -m pip install -r requirements.txt
```

The inactive balancing stage requires DuckDB; it is already included in `requirements.txt`. The provided Slurm inactive-pipeline script also checks for DuckDB and installs it into the active environment when it is absent.

### 3. Run the active database workflow

```bash
python3 run_pipeline.py
```

Inspect the available stages:

```bash
python3 run_pipeline.py --list-steps
```

Resume from a stage:

```bash
python3 run_pipeline.py --from-step metadata
```

Run a bounded section:

```bash
python3 run_pipeline.py --from-step descriptors --to-step validation
```

Re-run completed stages when required:

```bash
python3 run_pipeline.py --force
```

### 4. Run the inactive branch

```bash
python3 run_inactive_pipeline.py
```

List inactive stages:

```bash
python3 run_inactive_pipeline.py --list-steps
```

The inactive branch contains the explicit-INACTIVE extraction, annotation, cleaning, balancing, descriptor, and fingerprint workflow.

### 5. HPC / Slurm

Two submission templates are supplied:

```bash
sbatch submit_pipeline.sh
sbatch submit_pipeline_inactive.sh
```

These scripts are site-specific templates. Before use on another cluster, review the partition, Conda module, resource requests, email settings, and local scratch behavior. The scientific Python code does not depend on Slurm.

## Pipeline order

### Active branch

1. `download`
2. `filter`
3. `metadata`
4. `unique_uniprots`
5. `kegg`
6. `ko`
7. `target_annotation`
8. `annotated_master`
9. `unique_active`
10. `clean_activity`
11. `target_classification`
12. `target_assignment`
13. `target_class_merge`
14. `polypharmacology`
15. `promiscuity`
16. `descriptors`
17. `stat_summary`
18. `validation`

The final `validation` boundary is currently informational; the production outputs are generated before that boundary.

### Inactive branch

1. `download`
2. `inactive_filter`
3. `inactive_metadata`
4. `inactive_unique_uniprots`
5. `inactive_kegg`
6. `inactive_ko`
7. `inactive_target_annotation`
8. `inactive_annotated_master`
9. `inactive_unique`
10. `inactive_clean_activity`
11. `inactive_target_classification`
12. `inactive_target_assignment`
13. `inactive_target_class_merge`
14. `inactive_balanced_filter`
15. `inactive_descriptors`

## Scientific filtering rules

The v1.0 release preserves the filtering logic implemented in the supplied production scripts.

### Active observations

The active branch is based on PubChem observations that are not explicitly classified as `INACTIVE` and that satisfy the active-concentration logic implemented in `legacy/pubchem_assay_filter.py`. The low-value threshold used by the workflow is **10 µM**. The script also preserves active observations for which potency information is missing where required by its validated selection logic; missing potency must not be interpreted as inactivity.

The exact implementation in the production script is authoritative. Do not replace it with a simplified filter based only on a single potency column.

### Inactive observations

The inactive branch explicitly retains observations whose PubChem outcome is `INACTIVE`. Its selection and balancing logic is implemented in `inactive/pubchem_inactive_assay_filter.py` and `inactive/filtering_balanced_inactive_data.py` and is preserved unchanged in this release.

The inactive branch is therefore not simply the inverse of the active branch.

## PubChem download scope

The documented configuration covers BioAssay AIDs from:

- start AID: `2000001`
- end AID: `2283000`
- range size: `1000`

The source base URL is:

`https://ftp.ncbi.nlm.nih.gov/pubchem/Bioassay/CSV/Data`

The workflow stores downloaded ZIP ranges in `data/raw_assays/`. These large source files are intentionally excluded from Git because they are reproducible downloads and can occupy substantial storage.

The download stage is resumable. Existing valid ZIP files are reused. Invalid/unavailable responses are removed, recorded in `logs/download_errors.log`, and recorded in the download checkpoint rather than silently disappearing.

## External data sources

The workflow combines several public services/resources:

| Source | Role | Access used by pipeline |
|---|---|---|
| PubChem BioAssay | Primary assay observations and compound identifiers | Bulk BioAssay CSV archive |
| PubChem PUG/View services | Assay metadata | HTTP requests |
| UniProtKB | Protein identifiers, names, organism and related target metadata | UniProt REST services |
| KEGG | Gene/KO annotation | KEGG REST services |
| RDKit | Molecular descriptors, scaffolds and Morgan fingerprints | Local Python package |

See `docs/DATA_SOURCES.md` for source URLs, provenance expectations, retrieval dates, and licensing considerations.

Because external resources are live services, a rerun performed at a later date can legitimately produce differences caused by source-database updates. For a fixed historical database release, preserve the downloaded source files, retrieval dates, checkpoints, and final-output checksums together with the Git commit/tag.

## Rate limiting

The production workflow deliberately uses conservative request rates. See `docs/API_RATE_LIMITS.md` for the exact delays retained by the validated scripts.

The repository does not recommend increasing these rates. PubChem's current PUG REST documentation requests that users stay at or below 5 requests per second, and KEGG documents a maximum of 3 requests per second for its API. The workflow remains below those nominal limits and retains additional throttling behavior.

## Final outputs

### Active branch — `data/final/`

- `master_observations_table.csv`
- `pubchem_compound_polypharmacology_table.csv`
- `pubchem_target_promiscuity_table.csv`
- `molecular_descriptors.csv`
- `morgan_fingerprints.pkl`
- `data_quality_score_table.csv`

### Inactive branch — `data/final/`

- `master_observations_inactive_table.csv`
- `balanced_inactive_compounds.csv`
- `inactive_molecular_descriptors.csv`
- `inactive_morgan_fingerprints.pkl`

The repository distribution does **not** contain the large generated data tables by default. This GitHub repository contains the code and reproducibility framework needed to regenerate them. A Zenodo release should be used to archive the generated database tables and/or source-data snapshot when distribution of those large files is desired.

## Output schema

The authoritative schema documentation is `docs/OUTPUT_SCHEMA.md`.

The active master table contains 20 columns:

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

No production column names should be changed without a versioned schema change.

## Directory structure

```text
.
├── README.md
├── VERSION
├── PIPELINE_VERSION
├── config.yaml
├── requirements.txt
├── environment.yml
├── CITATION.cff
├── LICENSE
├── LICENSE-DATA.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── docs/
│   ├── API_RATE_LIMITS.md
│   ├── DATA_SOURCES.md
│   ├── ENVIRONMENT.md
│   ├── OUTPUT_SCHEMA.md
│   └── REPRODUCIBILITY.md
├── legacy/                 # validated active production scripts
├── inactive/               # validated inactive production scripts
├── src/                    # orchestration/checkpoint layer
├── tests/                  # lightweight repository tests
├── run_pipeline.py
├── run_inactive_pipeline.py
├── submit_pipeline.sh
└── submit_pipeline_inactive.sh
```

Generated runtime directories are ignored by Git:

- `data/raw_assays/`
- `data/intermediate/`
- `data/final/`
- `checkpoints/`
- `logs/`
- Python cache directories

## Reproducibility protocol

For a publication-quality database release, preserve the following together:

1. Git repository commit/tag for the pipeline.
2. `VERSION` and `PIPELINE_VERSION`.
3. `config.yaml`.
4. Python version and package versions.
5. RDKit version.
6. DuckDB version when the inactive balancing branch is used.
7. PubChem download range and retrieval date.
8. UniProt retrieval date.
9. KEGG retrieval date.
10. The generated output tables and their SHA-256 checksums.
11. Pipeline checkpoints and execution logs when available.
12. Any unavailable PubChem ranges recorded by the downloader.

See `docs/REPRODUCIBILITY.md` for a release checklist and `docs/ENVIRONMENT.md` for environment capture instructions.

## Validation

Run the lightweight repository tests with:

```bash
pytest -q
```

Also check shell-script syntax without executing the HPC jobs:

```bash
bash -n submit_pipeline.sh
bash -n submit_pipeline_inactive.sh
bash -n legacy/download_pubchem.sh
```

The included GitHub Actions workflow performs these non-destructive checks automatically.

## Provenance and licensing

This repository contains software plus a database derived from external resources. These components must not be treated as having identical licensing terms.

- The **pipeline source code and documentation** are released under the repository license in `LICENSE`.
- The **derived database** incorporates data obtained from PubChem and linked resources. Users must follow the licensing, attribution, and usage conditions applicable to the underlying sources. PubChem explicitly notes that data-source licensing can differ among contributors.
- KEGG access and reuse are subject to its stated usage conditions; its API is restricted to academic use and requests should remain within its published rate limit.

See `LICENSE-DATA.md` before redistributing generated database tables.

## Citation

When using this pipeline, cite the repository release and the underlying PubChem resource. PubChem provides a current primary citation recommendation on its citation page.

The machine-readable software citation is provided in `CITATION.cff`.

## Contact and contributions

Contribution and change-management rules are documented in `CONTRIBUTING.md`. Scientific changes should be accompanied by a version increment and an explicit description of how the generated database can differ from the preceding release.
