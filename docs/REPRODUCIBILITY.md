# Reproducibility and release checklist

This document defines the minimum information that should accompany a public v1.0 database release.

## A. Repository identity

- [ ] Git repository URL recorded.
- [ ] Git commit SHA recorded.
- [ ] Release tag recorded as `v1.0`.
- [ ] `VERSION` contains `1.0`.
- [ ] `PIPELINE_VERSION` contains `1.0`.
- [ ] `config.yaml` archived with the database.

## B. Runtime environment

Record:

```bash
python --version
python -m pip freeze
python -c "import rdkit; print(rdkit.__version__)"
python -c "import duckdb; print(duckdb.__version__)"
```

Also record OS, CPU architecture, and whether execution was local or under Slurm.

## C. External input snapshot

Record:

- PubChem AID range;
- PubChem retrieval date;
- names and SHA-256 checksums of source ZIP files;
- unavailable/skipped ranges;
- UniProt retrieval date;
- KEGG retrieval date;
- any source-version identifiers exposed by the services.

For a truly frozen release, archive the source ZIP files or an equivalent immutable source snapshot.

## D. Execution record

Preserve:

- pipeline checkpoints;
- standard output/error logs;
- Slurm job ID when applicable;
- start/end timestamps;
- any warnings concerning unavailable source ranges;
- resource usage when available.

## E. Output validation

At minimum, verify:

```bash
pytest -q
bash -n submit_pipeline.sh
bash -n submit_pipeline_inactive.sh
bash -n legacy/download_pubchem.sh
```

Then calculate checksums of every released data table:

```bash
sha256sum data/final/* > data-final-sha256.txt
```

For large binary files, the same SHA-256 procedure should be used.

## F. Database-level validation

Record at least:

- number of rows in each final table;
- number of unique PubChem CIDs;
- number of unique UniProtKB IDs;
- number of unique assays;
- number of unique targets;
- number of protein families;
- number of target classes;
- descriptor/fingerprint row counts;
- inactive-source and balanced-inactive row counts where applicable.

The values above are release metadata and should be generated from the actual final files rather than hard-coded into the repository documentation.

## G. Reproducing an archived release

1. Checkout the exact Git tag/commit.
2. Create the documented Python environment.
3. Restore the archived source-data snapshot.
4. Restore any required checkpoints if reproducing an interrupted run.
5. Run the active and/or inactive pipeline.
6. Compare final-table schemas against `docs/OUTPUT_SCHEMA.md`.
7. Compare row counts and unique-ID counts against the release record.
8. Compare SHA-256 checksums when byte-identical reproduction is expected.

If checksums differ while schemas and biological counts are consistent, investigate source-data version changes, service updates, dependency versions, and CSV serialization differences before interpreting the result as a scientific discrepancy.
