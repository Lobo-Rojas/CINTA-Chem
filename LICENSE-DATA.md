# Data licensing and attribution

The software license in `LICENSE` applies to the pipeline source code and repository documentation. It does **not** automatically relicense the external data used to generate the database.

The generated database is derived from external resources, principally PubChem BioAssay and annotations retrieved from UniProtKB and KEGG. Those resources have their own terms, provenance, and licensing conditions.

PubChem currently states that most of its data are readily available for download while noting that exceptions can arise from contributor licensing agreements. PubChem also provides provenance information for data contributors and source records. Users redistributing a derived database should therefore retain upstream provenance and review the current source-specific licensing information.

KEGG currently states that its REST API is available for academic use and that non-academic use is subject to its licensing requirements.

Before distributing generated database tables outside the original research context, review the current terms of every upstream resource represented in the released data and retain appropriate attribution.

## Attribution checklist

For a fixed database release, retain at minimum:

- pipeline version;
- Git commit/tag;
- source retrieval dates;
- source URLs;
- relevant upstream citations;
- contributor/source provenance where available; and
- final-file SHA-256 checksums.
