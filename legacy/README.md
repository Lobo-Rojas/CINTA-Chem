# Legacy scripts

These scripts are preserved from the validated database-construction workflow. They are intentionally kept as separate scripts because their behavior was validated during the original database build.

`run_active_pipeline.py` calls the production scripts in this directory in the documented dependency order. The directory name `legacy/` denotes historical preservation of validated implementations; it does not mean that the scripts are unused or obsolete.

The following scripts are retained for historical comparison/provenance and are not called by the active orchestrator:

- `metadata_annotation.py`
- `metadata_annotation_pilot.py`

The production metadata implementation is:

- `metadata_annotation_workers.py`

It contains the validated rate-limiting and dynamic-throttling behavior used for PubChem metadata requests.
