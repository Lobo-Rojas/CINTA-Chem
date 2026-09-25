# Public API request protection

The repository intentionally keeps request rates conservative.

## PubChem

`metadata_annotation_workers.py` uses a global lock and a 0.26-second minimum interval between requests. With four worker threads, the shared limiter keeps request submission below the nominal 5 requests/second PubChem policy and the script additionally reacts to `X-Throttling-Control` response headers. Warning and overload states trigger additional pauses.

The bulk PubChem BioAssay ZIP download is not an API-request loop; it uses `curl` against the public FTP/HTTP archive with retries and a 2-second post-download delay.

## KEGG

`KEGG_retrieving.py` waits 1 second between batches. `KEGG_KO_annotation.py` waits 0.4 seconds between requests, corresponding to a maximum theoretical rate of 2.5 requests/second and therefore remaining below KEGG's current recommendation of no more than 3 requests/second.

## UniProt

`uniprot_target_classification_2.py` retains the validated 0.2-second interval between individual accession requests. No additional concurrency was introduced.

The batch UniProt retrieval performed by `KEGG_retrieving.py` waits 1 second between batches.

## Important

These delays are part of the reproducibility/safety configuration. They should not be shortened merely to accelerate the workflow.
