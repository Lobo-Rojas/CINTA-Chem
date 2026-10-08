"""Pipeline orchestration.

The validated historical scripts are kept under ``legacy/`` and are executed
in their original dependency order.  The orchestration layer adds only:

* resumable download handling;
* stage-level checkpoints;
* a single entry point for the complete workflow.

The scientific filtering, annotation and API logic is intentionally delegated
to the validated scripts so that the v1.1 pipeline does not silently change the rules that produced the existing database.
"""
from __future__ import annotations

import subprocess
import time
from pathlib import Path

from .common import load_checkpoint, save_checkpoint

STEP_ORDER = [
    "download",
    "filter",
    "metadata",
    "unique_uniprots",
    "kegg",
    "ko",
    "target_annotation",
    "annotated_master",
    "unique_active",
    "clean_activity",
    "target_classification",
    "target_assignment",
    "target_class_merge",
    "polypharmacology",
    "promiscuity",
    "descriptors",
    "stat_summary",
    "validation",
    "uniprot_sequences",
]

# These are the validated production scripts from the supplied pipeline.
# Do not replace them with the pilot/alternative versions without validation.
COMMANDS = {
    "filter": ["python3", "legacy/pubchem_assay_filter.py"],
    "metadata": ["python3", "legacy/metadata_annotation_workers.py"],
    "unique_uniprots": ["python3", "legacy/unique_uniprotIDs_retrieving.py"],
    "kegg": ["python3", "legacy/KEGG_retrieving.py"],
    "ko": ["python3", "legacy/KEGG_KO_annotation.py"],
    "target_annotation": ["python3", "legacy/merging_pubchem_target_annotation.py"],
    "annotated_master": ["python3", "legacy/merging_pubchem_annotated_master.py"],
    "unique_active": ["python3", "legacy/filtering_true_unique_active_annotated_master.py"],
    "clean_activity": ["python3", "legacy/clean_higher_kd.py"],
    "target_classification": ["python3", "legacy/uniprot_target_classification_2.py"],
    "target_assignment": ["python3","legacy/target_classification_assigment.py"],
    "target_class_merge": ["python3", "legacy/merging_uniprot_target_class_and_EC.py"],
    "polypharmacology": ["python3", "legacy/polypharmacology_table_generator.py"],
    "promiscuity": ["python3", "legacy/target_promiscuity_table_generator.py"],
    "descriptors": ["python3", "legacy/molecular_descriptors_generator.py"],
    "stat_summary": ["python3", "legacy/data_quality_score_table.py"],
    "uniprot_sequences": ["python3", "legacy/retrieve_uniprot_sequences.py"]
}


def run_legacy(root: Path, step: str) -> None:
    cmd = COMMANDS[step]
    print(f"\n>>> {step}: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=root, check=True)


def _range_names(cfg: dict) -> list[str]:
    p = cfg["pubchem"]
    names: list[str] = []
    for start in range(p["start_aid"], p["end_aid"] + 1, p["range_size"]):
        end = min(start + p["range_size"] - 1, p["end_aid"])
        names.append(f"{start:07d}_{end:07d}.zip")
    return names


def run_download(root: Path, cfg: dict) -> None:
    """Resume the validated ``download_pubchem.sh`` behavior.

    Important behavior:
    - Existing valid ZIPs are never downloaded again.
    - The directory is scanned before the download loop.
    - The first missing/invalid range becomes the starting point of the
      download loop, so a user who already has ranges 1--3 sees range 4 as
      the first download rather than restarting at range 1.
    - curl retry, timeout and sleep values are retained from the supplied
      working shell script.
    - A JSON checkpoint is updated after every validated range.
    """
    p = cfg["pubchem"]
    raw = root / "data" / "raw_assays"
    raw.mkdir(parents=True, exist_ok=True)
    cp = load_checkpoint(root, "download")
    processed = set(cp.get("processed_files", []))
    skipped = set(cp.get("skipped_files", []))

    names = _range_names(cfg)
    first_missing = None

    # First pass: recognize all already-valid files and checkpoint them.
    for idx, name in enumerate(names):
        dest = raw / name
        valid = dest.is_file() and dest.stat().st_size > p["min_valid_zip_bytes"]
        if valid:
            processed.add(name)
        elif first_missing is None:
            first_missing = idx

    cp["processed_files"] = sorted(processed)
    cp["skipped_files"] = sorted(skipped)
    cp["existing_valid_files"] = len(processed)
    save_checkpoint(root, "download", cp)

    if first_missing is None:
        print(f"All {len(names)} PubChem ZIP ranges are already present and valid.")
        cp["status"] = "completed"
        cp["completed_ranges"] = len(names)
        save_checkpoint(root, "download", cp)
        return

    print(
        f"Resuming PubChem download at range {first_missing + 1}/{len(names)}: "
        f"{names[first_missing]}"
    )

    for name in names[first_missing:]:
        dest = raw / name

        # A later file may already exist even when an earlier one was missing;
        # honor it and continue without downloading it.
        if dest.is_file() and dest.stat().st_size > p["min_valid_zip_bytes"]:
            processed.add(name)
            cp["processed_files"] = sorted(processed)
            cp["skipped_files"] = sorted(skipped)
            cp["last_file"] = name
            save_checkpoint(root, "download", cp)
            print(f"Already exists, skipping: {name}")
            continue

        if dest.exists():
            print(f"Corrupted file detected, removing: {name}")
            dest.unlink()

        url = f'{p["base_url"]}/{name}'
        print("\n==================================================")
        print(f"Downloading {name}")
        print("==================================================")

        # This deliberately mirrors download_pubchem.sh.
        cmd = [
            "curl",
            "--retry", str(p["download_retry"]),
            "--retry-delay", str(p["download_retry_delay"]),
            "--connect-timeout", str(p["connect_timeout"]),
            "--max-time", str(p["max_time"]),
            "-L",
            "-o", str(dest),
            url,
        ]
        result = subprocess.run(cmd, cwd=root, check=False)

        if result.returncode != 0:
            message = (
                f"curl failed for {name} with exit code {result.returncode}. "
                "The file was removed and the pipeline will continue with the next range."
            )
            print(f"WARNING: {message}")
            dest.unlink(missing_ok=True)
            skipped.add(name)
            cp["processed_files"] = sorted(processed)
            cp["skipped_files"] = sorted(skipped)
            cp["last_skipped"] = name
            cp["last_skip_reason"] = message
            save_checkpoint(root, "download", cp)
            log_dir = root / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            with (log_dir / "download_errors.log").open("a", encoding="utf-8") as log:
                log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}\t{name}\t{message}\n")
            time.sleep(p["post_download_sleep"])
            continue

        if not dest.exists() or dest.stat().st_size <= p["min_valid_zip_bytes"]:
            actual_size = dest.stat().st_size if dest.exists() else 0
            message = (
                f"Invalid or unavailable PubChem response for {name}: "
                f"{actual_size} bytes. The file was removed and the pipeline "
                "will continue with the next range."
            )
            print(f"WARNING: {message}")
            dest.unlink(missing_ok=True)
            skipped.add(name)
            cp["processed_files"] = sorted(processed)
            cp["skipped_files"] = sorted(skipped)
            cp["last_skipped"] = name
            cp["last_skip_reason"] = message
            save_checkpoint(root, "download", cp)
            log_dir = root / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            with (log_dir / "download_errors.log").open("a", encoding="utf-8") as log:
                log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}\t{name}\t{message}\n")
            time.sleep(p["post_download_sleep"])
            continue

        size_mb = dest.stat().st_size / 1024 / 1024
        print(f"Download successful: {name}")
        print(f"Size: {size_mb:.1f} MB")

        processed.add(name)
        cp["processed_files"] = sorted(processed)
        cp["last_file"] = name
        cp["completed_ranges"] = len(processed)
        save_checkpoint(root, "download", cp)

        # Exact delay used by the validated shell script.
        time.sleep(p["post_download_sleep"])

    cp["status"] = "completed"
    cp["completed_ranges"] = len(processed)
    cp["skipped_ranges"] = len(skipped)
    save_checkpoint(root, "download", cp)
    print("\nDOWNLOAD COMPLETE")
