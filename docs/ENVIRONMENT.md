# Reproducible environment

## Supported baseline

The v1.1 workflow is specified for **Python 3.10**. The minimum dependency specification is `requirements.txt`, and the Conda environment definition is `environment.yml`.

Create the recommended environment with:

```bash
conda env create -f environment.yml
conda activate cinta-chem
```

Or, in an existing Python 3.10 environment:

```bash
python -m pip install -r requirements.txt
```

## Dependency policy

`requirements.txt` intentionally provides minimum compatible package versions rather than a complete lockfile. This makes the repository easier to install across systems but means that an exact database release must archive the environment that was actually used.

RDKit is a key scientific dependency. If platform-specific installation problems occur, use a Conda/Mamba environment and install a compatible RDKit build rather than modifying the production scripts to work around environment differences.

The inactive balancing stage uses DuckDB. DuckDB is included in `requirements.txt` and is explicitly checked by `submit_pipeline_inactive.sh`.

## Capture an exact runtime environment

Before or immediately after a release build, record:

```bash
python --version
python -m pip freeze > pip-freeze.txt
python -c "import rdkit; print('RDKit', rdkit.__version__)"
python -c "import duckdb; print('DuckDB', duckdb.__version__)"
```

Also record:

- operating system and architecture;
- CPU and memory resources;
- Slurm version and job information when HPC execution is used;
- the Git commit/tag; and
- retrieval dates for PubChem, UniProtKB, and KEGG.

Do not commit `pip-freeze.txt` by default; archive it with the generated database release when exact environment reconstruction is required.

## Reproducibility versus portability

Recreating the named Conda environment is sufficient to reproduce the documented software stack at a baseline level. Byte-identical regeneration additionally requires the same package versions, the same upstream input snapshots, the same pipeline commit, and compatible serialization behavior.

## Hardware and storage

The active workflow can be memory-intensive because several stages load and merge large CSV tables. The inactive balancing stage can require substantially more temporary disk space because it processes the large inactive observation table with DuckDB.

For HPC execution, use node-local scratch space when available for temporary files, while keeping final outputs and release artifacts on persistent storage. The supplied Slurm templates currently activate the site-specific Conda environment `pubchem_env`; this is intentionally distinct from the portable environment name `cinta-chem` defined in `environment.yml`. Record the actual environment name and package set used for the database build.
