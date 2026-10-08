# Changelog

## v1.1 — 2026-10-06

Public v1.1 release of CINTA-Chem (Curated Interaction Network and Target Atlas for Chemogenomics).

### Active workflow

- Added the final `uniprot_sequences` stage to the active pipeline.
- Added `legacy/retrieve_uniprot_sequences.py` as the validated sequence-retrieval implementation.
- The final stage reads the `UniProt` column from `data/final/CINTA-Chem_Target_Promiscuity.csv`.
- UniProt requests are sequential, batched, conservatively paced, checkpointed, and retried with `Retry-After` and exponential backoff for transient failures.
- Added `data/final/CINTA-Chem_Target_Sequences.fasta` plus retrieval-status and missing-accession reports.

### Inactive workflow

- No independent inactive sequence stage is included. The inactive balancing workflow remains matched to the active dataset, so the active target universe is the final sequence reference.

### Documentation and reproducibility hardening

- Synchronized the repository documentation with the authoritative v1.1 version files.
- Corrected active-runner and Slurm command references to the actual repository filenames.
- Corrected the documented PubChem AID range to match `config.yaml` as consumed by the orchestration layer.
- Expanded the release, environment, source-provenance, API-rate, output-schema, licensing, and reproducibility documentation.
- Refreshed the production-file SHA-256 manifest.
- Removed generated runtime logs and Python bytecode from the upload package.
- Corrected non-English comments/annotations in the Slurm template so repository-facing annotations are consistently written in English.

### Database naming alignment

- Standardized the public resource identity to **CINTA-Chem (Curated Interaction Network and Target Atlas for Chemogenomics)**.
- Renamed CINTA-Chem-generated active, inactive, intermediate, final, checkpoint, cache, and retrieval-report filenames with the `CINTA-Chem_` prefix.
- Updated repository documentation, citation metadata, environment naming, Slurm job/log names, and the GitHub remote to use the CINTA-Chem identity.
- External PubChem source ZIP filenames remain unchanged to preserve upstream provenance.

### Scientific-processing policy

No activity-filtering, target-annotation, classification, balancing, descriptor, fingerprint, or output-schema rule was changed during the documentation/reproducibility hardening pass.

## v1.0 — 2026-09-23

Initial public reproducibility release.

### Repository/reproducibility layer

- Promoted the repository release identifier from `0.6.3` to `1.0` in the authoritative version files.
- Preserved the validated production Python and shell scripts.
- Expanded the main README for public GitHub use.
- Added a Conda environment definition for Python 3.10.
- Added explicit data-source and provenance documentation.
- Added an environment and exact-runtime capture guide.
- Added a database-release reproducibility checklist.
- Added machine-readable citation metadata.
- Added separate software and derived-data licensing guidance.
- Added contribution and change-management guidance.
- Added automated non-destructive repository checks.
- Added a release manifest documenting the production-file hashes.

### Scientific processing

No scientific filtering, annotation, classification, output-column, or production-script logic was intentionally changed for v1.0.
