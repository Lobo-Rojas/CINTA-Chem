# Contributing

## Project principle

This project is a reproducible scientific database pipeline. Every change must be reviewable, traceable, and distinguish clearly between scientific-processing changes and repository/documentation maintenance.

## Validated production logic

The Python and shell scripts under `legacy/` and `inactive/` are preserved as the validated production implementation. Do not modify their scientific behavior merely for style, optimization, or convenience.

Changes to any of the following require an explicit version change and documentation in `CHANGELOG.md`:

- activity-filtering rules;
- inactive balancing rules;
- target annotation rules;
- protein-family or target-class definitions;
- data-cleaning rules;
- descriptor/fingerprint settings;
- output filenames;
- output column names or order;
- source-data ranges; or
- external-service endpoints used as scientific inputs.

Documentation, comments, release metadata, and reproducibility infrastructure may be updated without changing scientific processing behavior, but such changes should still be described in the release record when they affect how users run or audit the repository.

## Reproducibility checks

Before creating a release or pull request, run:

```bash
python -m compileall -q legacy inactive src run_active_pipeline.py run_inactive_pipeline.py tests
pytest -q
bash -n submit_pipeline_active.sh
bash -n submit_pipeline_inactive.sh
bash -n legacy/download_pubchem.sh
```

If scientific processing changes, provide before/after row counts, unique-ID counts, and schema comparisons for affected outputs, together with an updated SHA-256 manifest.

## Generated data

Do not commit large PubChem source archives, intermediate tables, checkpoints, runtime logs, or generated final database files unless a release specifically requires them. Archive large release artifacts separately and record their checksums.

## Release integrity

The release-level production-file checksum manifest is maintained in `docs/PRODUCTION_CODE_SHA256.txt`. When any production/orchestration Python or shell file changes, regenerate the manifest and document the reason for the change.
