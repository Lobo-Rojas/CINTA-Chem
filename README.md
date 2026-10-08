# PubChem Chemogenomics Pipeline v1.1

Reproducible workflow for constructing a PubChem-derived chemogenomics database from PubChem BioAssay observations and linked UniProtKB and KEGG target annotations.

**Release:** 1.1  
**Release date:** 2026-10-06  
**Status:** public reproducibility release; validated scientific processing logic is frozen.  
**Primary workflow:** active observations  
**Additional workflow:** inactive observations and balanced inactive-compound data

## Scope

This repository contains the orchestration layer, validated production scripts, environment specification, reproducibility documentation, and lightweight repository checks used to regenerate the database. Large PubChem source archives, intermediate tables, final database tables, checkpoints, and runtime logs are intentionally excluded from the public repository by default.

The repository has two related workflows:

- **Active branch:** filters and annotates active BioAssay observations, generates compound-level and target-level summaries, calculates molecular descriptors and Morgan fingerprints, produces data-quality summaries, and retrieves the final active-target protein sequences from UniProtKB.
- **Inactive branch:** retains explicitly `INACTIVE` observations, performs the inactive annotation/cleaning workflow, balances the inactive observations against the active dataset, and calculates descriptors and Morgan fingerprints for the balanced inactive set.

The inactive branch is not a simple inverse of the active branch. In particular, raw explicitly inactive observations are retained before the final balancing step.

## Frozen scientific-processing policy

The validated processing scripts under `legacy/` and `inactive/` are preserved as the production implementation for this release. No activity-filtering rule, target-annotation rule, target-classification rule, data-cleaning rule, descriptor/fingerprint setting, output schema, or biological selection criterion was changed as part of this documentation/reproducibility revision.

The authoritative release identifiers are `VERSION` and `PIPELINE_VERSION`. A small number of HTTP User-Agent strings inside preserved scripts contain `1.0`; those are implementation-level client identifiers and are intentionally not used as pipeline release identifiers.

The directory name `legacy/` indicates historical preservation of the validated implementation; it does **not** mean that these scripts are obsolete. The active orchestrator calls the validated scripts directly in a fixed dependency order.

Future scientific changes must receive a new documented release and must include an explicit description of how the generated database can differ from the preceding release.

## Repository layout

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
├── RELEASE_METADATA.md
├── docs/
│   ├── API_RATE_LIMITS.md
│   ├── DATA_SOURCES.md
│   ├── ENVIRONMENT.md
│   ├── OUTPUT_SCHEMA.md
│   ├── PRODUCTION_CODE_SHA256.txt
│   └── REPRODUCIBILITY.md
├── legacy/                     # validated active production scripts
├── inactive/                   # validated inactive production scripts
├── src/                        # orchestration and checkpoint layer
├── tests/                      # lightweight repository checks
├── run_active_pipeline.py      # active-branch entry point
├── run_inactive_pipeline.py    # inactive-branch entry point
├── submit_pipeline_active.sh   # Slurm template for the active branch
└── submit_pipeline_inactive.sh # Slurm template for the inactive branch
```

Generated runtime directories are ignored by Git, including:

- `data/raw_assays/`
- `data/intermediate/`
- `data/final/`
- `data/output/`
- `data/smiles_cache/`
- `checkpoints/`
- `logs/`
- Python cache directories

## Requirements and environment

The validated environment is specified for **Python 3.10**. The minimum dependency specification is in `requirements.txt`, and the Conda environment definition is in `environment.yml`.

Recommended setup:

```bash
conda env create -f environment.yml
conda activate pubchem-chemogenomics
```

Alternatively, in an existing Python 3.10 environment:

```bash
python -m pip install -r requirements.txt
```

The inactive balancing workflow uses DuckDB. It is listed in `requirements.txt`; the supplied inactive Slurm template also verifies that DuckDB is importable and installs it when it is missing from the active environment.

For exact reproduction of a released database, record the actual runtime environment used for the build, including Python, RDKit, DuckDB, pandas, requests, and other package versions. See `docs/ENVIRONMENT.md`.

## Quick start

### Active branch

List the stages:

```bash
python3 run_active_pipeline.py --list-steps
```

Run the complete active workflow:

```bash
python3 run_active_pipeline.py
```

Resume from a specific stage:

```bash
python3 run_active_pipeline.py --from-step metadata
```

Run only a bounded section:

```bash
python3 run_active_pipeline.py --from-step descriptors --to-step validation
```

Re-run completed stages when required:

```bash
python3 run_active_pipeline.py --force
```

### Final active-target sequence retrieval

The final active stage is `uniprot_sequences`. It reads the `UniProt` accessions from:

```text
data/final/pubchem_target_promiscuity_table.csv
```

and retrieves the corresponding protein sequences from the UniProtKB REST service using `legacy/retrieve_uniprot_sequences.py`. Requests are sequential, limited to batches of at most 25 accessions, separated by a conservative 3-second interval by default, and retried with backoff for transient failures. Retrieval status and missing accessions are written to separate tab-delimited reports.

Run only this final stage after the target-promiscuity table exists:

```bash
python3 run_active_pipeline.py --from-step uniprot_sequences --to-step uniprot_sequences
```

The principal sequence output is:

```text
data/final/UniProt_ID.fasta
```

No separate sequence-retrieval stage is included in the inactive branch. The inactive balancing workflow is explicitly matched to the active dataset, so the active target universe is the sequence reference used for the final database release.

### Inactive branch

List the inactive stages:

```bash
python3 run_inactive_pipeline.py --list-steps
```

Run the complete inactive workflow:

```bash
python3 run_inactive_pipeline.py
```

Run a bounded section:

```bash
python3 run_inactive_pipeline.py --from-step inactive_balanced_filter --to-step inactive_descriptors
```

### HPC / Slurm

The repository includes site-specific Slurm templates:

```bash
sbatch submit_pipeline_active.sh
sbatch submit_pipeline_inactive.sh
```

Before submission to another cluster, review the partition, Conda module, environment name, CPU/memory requests, walltime, notification settings, and node-local scratch behavior. The active Slurm template currently activates the site-specific environment name `pubchem_env`, whereas `environment.yml` defines the portable Conda environment name `pubchem-chemogenomics`. This difference is an HPC-site configuration detail and is not a scientific parameter. The scientific processing scripts do not require Slurm; Slurm is only a scheduling option.

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
19. `uniprot_sequences`

The `validation` stage is currently an orchestration boundary rather than a full independent production-validation module. The final sequence stage follows this boundary and produces `data/final/UniProt_ID.fasta`.

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

## Scientific processing definitions

### Active observations

The validated active filter selects records that satisfy all of the following conditions:

1. `PUBCHEM_ACTIVITY_OUTCOME` is not `INACTIVE`;
2. a numeric standardized activity value is available; and
3. the standardized value is **< 10 µM**.

No assay-type restriction is added by this filter. The downstream final output also requires a valid PubChem AID and CID and retains `RESULT_IS_ACTIVE_CONCENTRATION = True`.

The exact implementation in `legacy/pubchem_assay_filter.py` is authoritative. Do not replace it with a simplified filter based on a different column or a different activity threshold.

### Inactive observations

The inactive branch retains observations explicitly labelled `INACTIVE` without applying a potency threshold at the extraction stage. The inactive cleaning stage preserves those observations even when no usable concentration is available; `pPotency` is calculated only when a positive numeric concentration is present.

The final balancing stage uses the active observation table as the target for a nominal **1:1 inactive-to-active observation ratio** and prioritizes matching by exact `UniProtKB_ID`, followed by available fallback matching information such as `KO` and `Target_Class`. The exact implementation in `inactive/filtering_balanced_inactive_data.py` is authoritative.

### Molecular representations

The active and inactive descriptor generators use RDKit to calculate physicochemical and structural descriptors and Bemis-Murcko scaffolds. Morgan fingerprints use **radius = 2** and **2048 bits**.

## PubChem download scope

The active orchestrator uses the values in `config.yaml` as the download definition for the release:

- start AID: `2270000`
- end AID: `2283000`
- range size: `1000` AIDs
- inclusive range count: **14 PubChem ZIP ranges**

The bulk source is:

```text
https://ftp.ncbi.nlm.nih.gov/pubchem/Bioassay/CSV/Data
```

The orchestrator in `src/steps.py` uses these configuration values and a resumable download/checkpoint mechanism. Large ZIP files are stored under `data/raw_assays/`.

`legacy/download_pubchem.sh` is retained for historical provenance and standalone comparison. It is **not** the source of truth for the v1.1 orchestrated range and is not called by the active or inactive entry-point runners. The release definition is the configuration consumed by `src/steps.py`.

## External data sources and provenance

| Resource | Role in the pipeline | Access used |
|---|---|---|
| PubChem BioAssay | Primary assay observations, AIDs, SIDs, CIDs, outcomes, and standardized activity values | Bulk BioAssay CSV archive |
| PubChem PUG/View | Assay metadata | HTTP requests |
| UniProtKB | Protein identifiers and target metadata; final protein sequences | REST services |
| KEGG | Gene and KO annotation | KEGG REST services |
| RDKit | Molecular descriptors, Bemis-Murcko scaffolds, and Morgan fingerprints | Local package |

External resources are mutable. A rerun at a later date can legitimately differ from an archived release because upstream records and annotations can change. For a frozen release, preserve the exact source-data snapshot used, the retrieval dates, the pipeline Git commit/tag, the runtime environment, and the final-file SHA-256 checksums.

Detailed source information and current usage/licensing notes are documented in `docs/DATA_SOURCES.md` and `LICENSE-DATA.md`.

## Request-rate policy

The validated scripts use conservative request pacing and retry behavior. Do not shorten these delays merely to reduce walltime. The repository documents the settings actually present in the production scripts in `docs/API_RATE_LIMITS.md`.

PubChem's current programmatic-access policy asks clients to remain at or below 5 requests per second and notes that dynamic throttling can change server-side limits. KEGG's current API guidance asks clients to limit calls to no more than 3 per second. The repository's validated request schedules remain below these published limits.

## Final outputs

### Active branch — `data/final/`

- `master_observations_table.csv`
- `pubchem_compound_polypharmacology_table.csv`
- `pubchem_target_promiscuity_table.csv`
- `molecular_descriptors.csv`
- `morgan_fingerprints.pkl`
- `data_quality_score_table.csv`
- `UniProt_ID.fasta`
- `UniProt_ID_sequence_retrieval_status.tsv`
- `UniProt_ID_sequence_retrieval_missing.tsv`

### Inactive branch — `data/final/`

- `master_observations_inactive_table.csv`
- `balanced_inactive_compounds.csv`
- `inactive_molecular_descriptors.csv`
- `inactive_morgan_fingerprints.pkl`

The public repository distribution does not include these generated database files. Archive them separately, for example through Zenodo or another suitable data repository, and record their checksums.

## Output schema

The authoritative schema is documented in `docs/OUTPUT_SCHEMA.md`. Production column names and order are release-controlled and must not be changed silently.

## Reproducibility protocol

For a publication or database release, preserve the following together:

1. Git commit SHA and release tag.
2. `VERSION` and `PIPELINE_VERSION`.
3. `config.yaml`.
4. Exact Python and package versions.
5. PubChem retrieval date and source ZIP checksums.
6. UniProt retrieval date.
7. KEGG retrieval date.
8. The final generated tables and their SHA-256 checksums.
9. Pipeline checkpoints and execution logs, when available.
10. Any unavailable or skipped PubChem ranges.
11. Slurm job/resource information when the HPC templates are used.

The exact release checklist is in `docs/REPRODUCIBILITY.md`.

## Validation

Run the repository checks locally:

```bash
python -m compileall -q legacy inactive src run_active_pipeline.py run_inactive_pipeline.py tests
pytest -q
bash -n submit_pipeline_active.sh
bash -n submit_pipeline_inactive.sh
bash -n legacy/download_pubchem.sh
```

The GitHub Actions workflow in `.github/workflows/reproducibility.yml` performs the corresponding non-destructive checks on supported pushes and pull requests.

## Licensing and citation

The software and documentation are released under the license in `LICENSE`. The generated database is derived from external resources and does not automatically inherit the software license. Review `LICENSE-DATA.md` before redistributing generated database tables.

For PubChem data and services, follow the current PubChem citation guidance and retain attribution for upstream data contributors where provided.

The machine-readable software citation is supplied in `CITATION.cff`.

## Contribution and change management

See `CONTRIBUTING.md` for the release and change-management policy. Scientific changes must be versioned, documented, and accompanied by reproducibility checks that demonstrate the effect on the generated database.
