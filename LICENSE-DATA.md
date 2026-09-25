# Data licensing and attribution

The software license in `LICENSE` applies to the pipeline source code and repository documentation. It does **not** automatically relicense the external data used to generate the database.

The generated database is derived from external resources, principally PubChem BioAssay and annotations retrieved from UniProtKB and KEGG. Those resources have their own terms, provenance, and licensing conditions.

PubChem states that it is free to use and that most data are readily available for download, while also noting that exceptions can exist and that licensing may depend on individual data contributors. Users redistributing a derived database should therefore retain provenance and review the current source-specific licensing information.

KEGG states that its API is available for academic use and that non-academic use is subject to licensing requirements.

Before distributing a generated database outside the original research context, review the current terms of every upstream resource represented in the released tables.

## Attribution

For PubChem data and services, follow the current PubChem citation guidance and cite the original source of individual data where attribution is available.

For a fixed release, include:

- the pipeline version;
- Git commit/tag;
- source retrieval dates;
- source URLs;
- upstream citations where applicable;
- final-file SHA-256 checksums.
