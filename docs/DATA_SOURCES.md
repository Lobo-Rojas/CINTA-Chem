# Data sources and provenance

## Primary sources

### PubChem BioAssay

**Role:** primary source of BioAssay observations, assay identifiers, substance identifiers, compound identifiers, activity outcomes, and standardized activity values used by the filtering stage.

**Bulk archive used by the v1.0 configuration:**

`https://ftp.ncbi.nlm.nih.gov/pubchem/Bioassay/CSV/Data`

**AID range configured in v1.0:** `2000001–2283000`, in ranges of 1000 AIDs.

PubChem recommends citing the PubChem resource and, where appropriate, the original data contributor associated with individual records. PubChem also notes that licensing can differ among contributing data sources. See the current PubChem download and data-source documentation before redistributing derived data.

### PubChem PUG/View services

Used by the assay metadata stage to retrieve structured assay information.

`https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/assay/{aid}/JSON`

### UniProtKB

Used for target metadata and target classification inputs.

`https://rest.uniprot.org/uniprotkb/search`

`https://rest.uniprot.org/uniprotkb/{}.json`

Record the UniProt retrieval date for each released database snapshot because protein annotations can change over time.

### KEGG

Used for KEGG gene identifiers and KO annotations.

`https://rest.kegg.jp/link/ko/`

KEGG states that its REST API is available for academic use and requests that API clients limit calls to no more than three per second. The production scripts retain a slower validated request schedule. Review KEGG's current legal/usage terms before non-academic redistribution or service use.

## Provenance requirements for a database release

A release intended to support a publication should archive:

- Git tag/commit of the pipeline;
- `VERSION` and `PIPELINE_VERSION`;
- `config.yaml`;
- source retrieval dates;
- PubChem AID range;
- list of downloaded PubChem ZIP files;
- list of unavailable/skipped ranges, if any;
- exact Python package versions;
- final-table SHA-256 checksums;
- execution logs and checkpoints when available.

## Source-data volatility

This pipeline accesses live external resources. A rerun in a later month or year is not guaranteed to reproduce an earlier database byte-for-byte because source records, annotations, and service responses can change.

For a frozen database release, preserve the downloaded source archive or an independently archived source-data snapshot. The GitHub repository alone is the reproducibility recipe; it is not a substitute for archiving mutable external inputs.
