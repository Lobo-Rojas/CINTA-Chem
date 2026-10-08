#!/usr/bin/env python3
"""Single entry point for the reproducible CINTA-Chem pipeline."""
from __future__ import annotations

import argparse
from pathlib import Path

from src.common import ensure_dirs, load_config, load_checkpoint, save_checkpoint
from src.steps import STEP_ORDER, run_download, run_legacy


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reproducible CINTA-Chem pipeline v1.1"
    )
    parser.add_argument("--from-step", choices=STEP_ORDER, default=STEP_ORDER[0])
    parser.add_argument("--to-step", choices=STEP_ORDER)
    parser.add_argument("--list-steps", action="store_true")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run completed pipeline stages. Individual historical scripts still honor their own checkpoints.",
    )
    args = parser.parse_args()

    if args.list_steps:
        for i, step in enumerate(STEP_ORDER, 1):
            print(f"{i:02d}  {step}")
        return

    root = Path(__file__).resolve().parent
    cfg = load_config(root / "config.yaml")
    ensure_dirs(root)

    start = STEP_ORDER.index(args.from_step)
    end = STEP_ORDER.index(args.to_step) if args.to_step else len(STEP_ORDER) - 1
    if end < start:
        raise SystemExit("--to-step must not precede --from-step")

    for step in STEP_ORDER[start:end + 1]:
        cp = load_checkpoint(root, step)

        # The download stage has its own per-file checkpoint and must always
        # be allowed to inspect the directory. This is what permits a partially
        # completed download to resume at the first missing range.
        if step != "download" and cp.get("status") == "completed" and not args.force:
            print(f"\n=== {step}: already completed; skipping ===")
            continue

        print(f"\n========== PIPELINE STEP: {step} ==========")

        if step == "download":
            run_download(root, cfg)
        elif step == "validation":
            print("Validation boundary reached. The full production validation module is not enabled in this release.")
        else:
            run_legacy(root, step)

        # Do not replace a detailed per-file checkpoint with a generic status;
        # the status is stored in the same checkpoint file for resumability.
        cp = load_checkpoint(root, step)
        cp["status"] = "completed"
        save_checkpoint(root, step, cp)

    print("\nPIPELINE FINISHED")


if __name__ == "__main__":
    main()
