# Reproducibility and release checklist

This document defines the minimum information that should accompany a public v1.1 database release generated with this repository. The GitHub repository is the reproducibility recipe; it is not, by itself, a frozen copy of mutable upstream databases or the generated database tables.

## 1. Repository identity

Record:

- Git repository URL;
- Git commit SHA;
- release tag, for example `v1.1`;
- contents of `VERSION` and `PIPELINE_VERSION`;
- `config.yaml`; and
- the SHA-256 manifest in `docs/PRODUCTION_CODE_SHA256.txt`.

The release identifiers for v1.1 are: `VERSION = 1.1` and `PIPELINE_VERSION = 1.1`.

HTTP User-Agent strings preserved inside historical production scripts are not authoritative release identifiers and are intentionally unchanged when they contain an implementation version such as `1.0`.

## 2. Runtime environment

Record the environment actually used to generate the database:

```bash
python --version
python -m pip freeze > pip-freeze.txt
python -c "import rdkit; print('RDKit', rdkit.__version__)"
python -c "import duckdb; print('DuckDB', duckdb.__version__)"
```

Also record the operating system, CPU architecture, execution mode (local or Slurm), and relevant scheduler resource information.

Do not treat the unpinned minimum versions in `requirements.txt` as an exact environment snapshot. For a released database, archive the actual package-resolution record.

## 3. External input snapshot

Record the exact upstream inputs used for the release:

### PubChem

- configured AID range: `2270000–2283000`;
- range size: 1000 AIDs;
- retrieval date;
- list of downloaded ZIP ranges;
- SHA-256 checksum of each source ZIP;
- unavailable/skipped ranges and reasons.

### UniProtKB

- retrieval date;
- source endpoint(s);
- sequence-retrieval status and missing-accession reports;
- UniProt release information when available from the service or archive used for the build.

### KEGG

- retrieval date;
- source endpoint(s);
- any service-version or database-release information available at build time.

For a genuinely frozen release, archive the source-data snapshot or an equivalent immutable record.

## 4. Execution record

Preserve, when available:

- stage checkpoints under `checkpoints/`;
- stdout/stderr logs;
- Slurm job ID;
- start and end timestamps;
- unavailable source ranges; and
- CPU, memory, and temporary-storage information.

The repository intentionally excludes generated runtime logs and checkpoints from version control by default. Archive them with the database release when exact reconstruction is required.

## 5. Validation commands

Run the following without executing the full production pipeline:

```bash
python -m compileall -q legacy inactive src run_active_pipeline.py run_inactive_pipeline.py tests
pytest -q
bash -n submit_pipeline_active.sh
bash -n submit_pipeline_inactive.sh
bash -n legacy/download_pubchem.sh
```

For the v1.1 repository package prepared for publication, these checks should pass before the corresponding Git tag is created.

## 6. Output validation

For every generated release table, record:

- row count;
- column names and order;
- SHA-256 checksum;
- number of unique PubChem CIDs;
- number of unique UniProtKB IDs;
- number of unique PubChem AIDs;
- number of unique target classes;
- number of protein families;
- descriptor and fingerprint row counts; and
- inactive-source and balanced-inactive counts where applicable.

Generate release-specific values from the actual files rather than hard-coding them into the generic repository documentation.

A simple checksum command is:

```bash
sha256sum data/final/* > data-final-sha256.txt
```

For large binary outputs such as `.pkl` files, use the same SHA-256 procedure.

## 7. Reproducing an archived release

1. Checkout the exact Git tag/commit.
2. Recreate the documented Python environment.
3. Restore the archived PubChem source snapshot.
4. Restore other external-source snapshots or retrieval records when available.
5. Run the active and/or inactive branch.
6. Compare output schemas against `docs/OUTPUT_SCHEMA.md`.
7. Compare row counts and unique-ID counts against the archived release record.
8. Compare SHA-256 checksums when byte-identical reproduction is expected.

Byte-identical reproduction is only a realistic expectation when the same source snapshot, software environment, pipeline commit, and serialization behavior are preserved. Live-source reruns may legitimately differ.

## 8. Release integrity

The production-file SHA-256 manifest in `docs/PRODUCTION_CODE_SHA256.txt` provides a file-level integrity record for the Python and shell production/orchestration scripts included in the release. Any change to these files must be accompanied by a new manifest and documented release record.
