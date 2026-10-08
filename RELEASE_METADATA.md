# CINTA-Chem v1.1 release metadata

- **Release:** `1.1`
- **Database name:** `CINTA-Chem`
- **Full name:** *Curated Interaction Network and Target Atlas for Chemogenomics*
- **Release date:** `2026-10-06`
- **Pipeline scope:** active and inactive PubChem chemogenomics workflows
- **Scientific processing status:** validated production logic frozen for this release
- **Primary source:** PubChem BioAssay bulk archive
- **Configured PubChem AID range:** `2270000–2283000`
- **Range size:** `1000` AIDs
- **Configured range count:** `14`
- **Active final master:** `data/final/CINTA-Chem_Master_Observations.csv`
- **Active target sequence output:** `data/final/CINTA-Chem_Target_Sequences.fasta`
- **Inactive final master:** `data/final/CINTA-Chem_Inactive_Master_Observations.csv`
- **Balanced inactive output:** `data/final/CINTA-Chem_Balanced_Inactive_Compounds.csv`
- **Environment baseline:** Python `3.10`
- **Fingerprint settings:** Morgan radius `2`, `2048` bits

## Release integrity

The authoritative repository version identifiers are stored in `VERSION` and `PIPELINE_VERSION`. The production Python and shell file checksums are recorded in `docs/PRODUCTION_CODE_SHA256.txt`.

The GitHub repository does not contain the large generated database tables or PubChem source archives. For the database release associated with a publication, archive those files separately and record their SHA-256 checksums together with the pipeline commit/tag, retrieval dates, exact runtime environment, and source-data snapshot.

## v1.1 sequence stage

The final active sequence stage uses `legacy/retrieve_uniprot_sequences.py`. It reads the `UniProt` column from `data/final/CINTA-Chem_Target_Promiscuity.csv`, retrieves sequences in sequential batches, applies conservative request pacing, honors `Retry-After` when supplied, uses exponential backoff for transient failures, and checkpoints both the sequence cache and retrieval status after each successful batch.
