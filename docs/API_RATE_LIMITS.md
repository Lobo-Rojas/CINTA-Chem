# Public API request protection

The repository intentionally uses conservative request pacing. The delays and retry settings documented below describe the validated production scripts; they are part of the reproducibility record and should not be shortened merely to reduce runtime.

## PubChem

The validated metadata script `legacy/metadata_annotation_workers.py` uses a global lock and a minimum **0.26-second interval** between requests. In v1.1 it runs with **one worker**, so requests are serialized. The script also inspects PubChem throttling headers and adds longer pauses when warning or overload states are returned.

The active/inactive bulk download is a file download rather than a PUG REST request loop. The orchestrator uses the PubChem archive configured in `config.yaml` and retains retry, timeout, and post-download delays from the validated workflow.

PubChem's current programmatic-access policy asks users not to exceed **5 requests per second**. PubChem also documents dynamic throttling and notes that requests can be rejected when demand is excessive.

Official current references:

- `https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest`
- `https://pubchem.ncbi.nlm.nih.gov/docs/dynamic-request-throttling`

## KEGG

`legacy/KEGG_retrieving.py` waits **1 second between batches**. `legacy/KEGG_KO_annotation.py` waits **0.4 seconds between requests**, corresponding to a maximum theoretical rate of 2.5 requests per second. These settings remain below KEGG's current published maximum of three API calls per second.

Official current reference:

`https://www.kegg.jp/kegg/rest/`

## UniProtKB

The historical target-classification stage `legacy/uniprot_target_classification_2.py` retains its validated **0.2-second interval** between accession requests.

The final v1.1 sequence stage `legacy/retrieve_uniprot_sequences.py` uses a deliberately separate and more conservative schedule:

- sequential requests only;
- default batch size: **25 accessions**;
- default interval between successful batch requests: **3 seconds**;
- retry handling for HTTP 429 and transient 5xx responses;
- `Retry-After` is honored when available; and
- network failures and incomplete reads use exponential backoff.

No additional concurrency is introduced by the final sequence stage.

## Important

The documented rates are intentionally conservative and should not be increased simply to accelerate the workflow. When a public service reports throttling or overload, the appropriate response is to reduce request pressure and retry later.
