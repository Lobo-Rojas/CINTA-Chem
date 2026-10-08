#!/usr/bin/env python3
"""Run the inactive-compound branch of PubChem Chemogenomics Pipeline v1.1."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

from src.common import ensure_dirs, load_config, load_checkpoint, save_checkpoint
from src.steps import run_download

STEP_ORDER = [
    "download",
    "inactive_filter",
    "inactive_metadata",
    "inactive_unique_uniprots",
    "inactive_kegg",
    "inactive_ko",
    "inactive_target_annotation",
    "inactive_annotated_master",
    "inactive_unique",
    "inactive_clean_activity",
    "inactive_target_classification",
    "inactive_target_assignment",
    "inactive_target_class_merge",
    "inactive_balanced_filter",
    "inactive_descriptors",
]

COMMANDS = {
    "inactive_filter": ["python3", "inactive/pubchem_inactive_assay_filter.py"],
    "inactive_metadata": ["python3", "inactive/metadata_annotation_workers_inactive.py"],
    "inactive_unique_uniprots": ["python3", "inactive/unique_uniprotIDs_retrieving_inactive.py"],
    "inactive_kegg": ["python3", "inactive/KEGG_retrieving_inactive.py"],
    "inactive_ko": ["python3", "inactive/KEGG_KO_annotation_inactive.py"],
    "inactive_target_annotation": ["python3", "inactive/merging_pubchem_target_annotation_inactive.py"],
    "inactive_annotated_master": ["python3", "inactive/merging_pubchem_annotated_master_inactive.py"],
    "inactive_unique": ["python3", "inactive/filtering_true_unique_inactive_annotated_master.py"],
    "inactive_clean_activity": ["python3", "inactive/clean_higher_kd_inactive.py"],
    "inactive_target_classification": ["python3", "inactive/uniprot_target_classification_inactive.py"],
    "inactive_target_assignment": ["python3", "inactive/target_classification_assigment_inactive.py"],
    "inactive_target_class_merge": ["python3", "inactive/merging_uniprot_target_class_and_EC_inactive.py"],
    "inactive_balanced_filter": ["python3", "inactive/filtering_balanced_inactive_data.py"],
    "inactive_descriptors": ["python3", "inactive/molecular_descriptors_generator_inactive.py"],
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-step", choices=STEP_ORDER, default="download")
    parser.add_argument("--to-step", choices=STEP_ORDER, default="inactive_descriptors")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--list-steps", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    cfg = load_config(root / "config.yaml")
    ensure_dirs(root)

    if args.list_steps:
        for i, step in enumerate(STEP_ORDER, 1):
            print(f"{i:02d}  {step}")
        return

    start = STEP_ORDER.index(args.from_step)
    end = STEP_ORDER.index(args.to_step)
    if end < start:
        raise SystemExit("--to-step must not precede --from-step")

    for step in STEP_ORDER[start:end + 1]:
        cp = load_checkpoint(root, step)

        if step != "download" and cp.get("status") == "completed" and not args.force:
            print(f"\n=== {step}: already completed; skipping ===")
            continue

        print(f"\n========== INACTIVE PIPELINE STEP: {step} ==========")

        if step == "download":
            run_download(root, cfg)
        else:
            subprocess.run(COMMANDS[step], cwd=root, check=True)

        cp = load_checkpoint(root, step)
        cp["status"] = "completed"
        save_checkpoint(root, step, cp)

    print("\nINACTIVE PIPELINE FINISHED")
    print("\nFinal inactive outputs:")
    print("  data/final/master_observations_inactive_table.csv")
    print("  data/final/inactive_molecular_descriptors.csv")
    print("  data/final/inactive_morgan_fingerprints.pkl")

if __name__ == "__main__":
    main()
