# Reproducible environment

## Supported baseline

The v1.0 workflow is specified for **Python 3.10**. The dependency list is in `requirements.txt`; the Conda environment definition is in `environment.yml`.

Create the recommended environment with:

```bash
conda env create -f environment.yml
conda activate pubchem-chemogenomics
```

Or with an existing Python 3.10 environment:

```bash
python -m pip install -r requirements.txt
```

## Why both files are provided

`requirements.txt` is the authoritative Python dependency list used by the workflow. `environment.yml` supplies a named Python 3.10 environment and delegates package installation to that requirements file.

RDKit is a key scientific dependency. If a platform has difficulty installing the requested RDKit build from PyPI, use a Conda/Mamba environment and install RDKit from the appropriate Conda channel before installing the remaining requirements. Do not alter the production scripts to work around an environment-specific installation problem.

## Capture an exact runtime environment

For a publication or database release, record the exact environment actually used:

```bash
python --version
python -m pip freeze > pip-freeze.txt
python -c "import rdkit; print('RDKit', rdkit.__version__)"
python -c "import duckdb; print('DuckDB', duckdb.__version__)"
```

Also record the operating system, architecture, Git commit, and retrieval dates of the external resources.

`pip-freeze.txt` is intentionally not committed by default because it is environment-specific. Archive it with the generated database release when exact environment reconstruction is required.

## Inactive branch

The inactive balancing stage uses DuckDB for large-table processing. Confirm that it is importable before starting that branch:

```bash
python -c "import duckdb; print(duckdb.__version__)"
```

The supplied Slurm script `submit_pipeline_inactive.sh` performs this check and installs DuckDB if necessary.

## Hardware and storage

The active workflow can be memory-intensive because several stages load or merge large CSV tables. The inactive balancing stage can require substantially more temporary disk space because it processes the large inactive observation table with DuckDB.

For HPC execution, use node-local scratch space when available and ensure that the final output directory remains on persistent storage.
