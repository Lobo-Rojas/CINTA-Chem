# Legacy scripts

These scripts are preserved from the validated database-construction workflow. They are intentionally kept as separate scripts because their behavior was validated during the original database build.

`run_pipeline.py` calls the production scripts in this directory in the documented dependency order.

The following are retained only for historical comparison/provenance and are not called by the orchestrator:

- `metadata_annotation.py`
- `metadata_annotation_pilot.py`

The production metadata implementation is:

- `metadata_annotation_workers.py`

It contains the validated rate-limiting and dynamic-throttling behavior used for PubChem requests.
