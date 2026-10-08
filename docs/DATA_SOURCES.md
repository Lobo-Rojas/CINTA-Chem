# Data sources and provenance

**Documentation review date:** 2026-10-06

This repository combines public experimental and biological resources with local cheminformatics calculations. Because several upstream resources are mutable, the date and version/snapshot of each external resource used for a database build must be recorded separately from the GitHub repository version.

## 1. PubChem BioAssay

**Role:** primary source of BioAssay observations, assay identifiers (AIDs), substance identifiers (SIDs), compound identifiers (CIDs), activity outcomes, standardized activity values, and associated structure information used by the filtering stage.

**Bulk archive:**

`https://ftp.ncbi.nlm.nih.gov/pubchem/Bioassay/CSV/Data`

**Configured v1.1 range:** `2270000–2283000` AIDs, using ranges of 1000 AIDs.

The v1.1 orchestrator reads this range from `config.yaml`. The historical standalone downloader `legacy/download_pubchem.sh` is preserved for provenance and is not used by the entry-point runners.

PubChem states that most data are readily available for download but that exceptions can exist because of contributor licensing agreements. PubChem also emphasizes that provenance and licensing can depend on the individual data contributor associated with a record. The current PubChem Downloads and Citation Guidelines should therefore be consulted when distributing derived data.

Current official documentation reviewed for this release:

- PubChem Downloads: `https://pubchem.ncbi.nlm.nih.gov/docs/downloads`
- PubChem Citation Guidelines: `https://pubchem.ncbi.nlm.nih.gov/docs/citation-guidelines`
- PubChem PUG REST: `https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest`

## 2. PubChem PUG/View

**Role:** retrieval of structured assay metadata used to annotate assay records.

**Endpoint used by the metadata stage:**

`https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/assay/{aid}/JSON`

PubChem's programmatic services are subject to a shared-server usage policy and dynamic throttling. The validated request schedule used by the repository is documented in `docs/API_RATE_LIMITS.md`.

## 3. UniProtKB

**Role:** UniProt accession identifiers, protein/target metadata used during annotation and classification, and final active-target protein sequences.

**Search endpoint used by the historical target-annotation scripts:**

`https://rest.uniprot.org/uniprotkb/search`

**Entry endpoint used by the historical target-annotation scripts:**

`https://rest.uniprot.org/uniprotkb/{}.json`

**Sequence-stream endpoint used by the v1.1 final sequence stage:**

`https://rest.uniprot.org/uniprotkb/stream`

The sequence output is generated from the `UniProt` accessions present in the active target-promiscuity table. For an archived release, record the retrieval date and the UniProt release information available at the time of retrieval.

## 4. KEGG

**Role:** KEGG gene identifiers and KO annotations linked to UniProt targets.

**REST base:**

`https://rest.kegg.jp/`

The current KEGG API documentation states that the REST API is available for academic use and asks clients to limit API calls to no more than three per second. The production scripts use slower request schedules.

Current official documentation reviewed for this release:

`https://www.kegg.jp/kegg/rest/`

## 5. RDKit

**Role:** local calculation of molecular descriptors, Bemis-Murcko scaffolds, and Morgan fingerprints.

RDKit is not an external annotation service in this workflow; its calculations are performed locally from the SMILES strings present in the generated database tables. The fingerprint settings used by the production descriptor generators are radius 2 and 2048 bits.

## 6. Source-data volatility and release provenance

A GitHub checkout alone does not freeze PubChem, UniProtKB, or KEGG. A later rerun can therefore differ from an archived database even when the same Git commit is used.

For a database release supporting a publication, archive or otherwise immutably record:

- Git commit/tag;
- `VERSION` and `PIPELINE_VERSION`;
- `config.yaml`;
- PubChem source ZIP names and SHA-256 checksums;
- PubChem retrieval date;
- UniProt retrieval date/release;
- KEGG retrieval date/release information when available;
- exact Python package versions;
- final database files and SHA-256 checksums; and
- execution logs/checkpoints when needed to reconstruct the run.
