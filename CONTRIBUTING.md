# Contributing

## Principle

This project is a reproducible scientific database pipeline. Changes must be reviewable and traceable to a specific version.

## Do not modify validated production logic casually

The scripts under `legacy/` and `inactive/` are the validated production implementations for v1.0. Do not change them merely for style, optimization, or convenience without demonstrating that the scientific outputs remain equivalent.

Changes to any of the following require an explicit version change and documentation in `CHANGELOG.md`:

- activity filtering rules;
- inactive balancing rules;
- target annotation rules;
- protein-family or target-class definitions;
- data cleaning rules;
- descriptor/fingerprint settings;
- output filenames;
- output column names/order;
- source-data ranges.

## Reproducibility checks

Before opening a pull request:

```bash
pytest -q
bash -n submit_pipeline.sh
bash -n submit_pipeline_inactive.sh
bash -n legacy/download_pubchem.sh
```

If scientific processing changes, provide before/after row counts, unique-ID counts, and schema comparisons for the affected outputs.

## Generated data

Do not commit the large PubChem source archives, intermediate tables, checkpoints, or generated final database files unless a release specifically requires them. Archive large release artifacts separately, for example through Zenodo, and record their checksums.
