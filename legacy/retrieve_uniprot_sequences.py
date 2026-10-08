
#!/usr/bin/env python3

import argparse
import csv
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import http.client
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import pandas as pd


UNIPROT_STREAM_URL = "https://rest.uniprot.org/uniprotkb/stream"

DEFAULT_INPUT = "data/final/CINTA-Chem_Target_Promiscuity.csv"
DEFAULT_OUTDIR = "data/final"

DEFAULT_BATCH_SIZE = 25
DEFAULT_REQUEST_INTERVAL = 3.0
DEFAULT_TIMEOUT = 120
DEFAULT_MAX_RETRIES = 6

# Identify the pipeline in requests. Replace with a contact address
# if your institution requires one for automated retrieval.
USER_AGENT = "PubChemChemogenomicsSequenceRetrieval/1.0"


def parse_fasta_records(fasta_text):
    """Parse FASTA text into {accession: sequence}."""
    records = {}
    header = None
    sequence_parts = []

    def save_record(current_header, parts):
        if not current_header:
            return

        first_token = current_header.split()[0]
        fields = first_token.split("|")

        if len(fields) >= 3 and fields[0] in ("sp", "tr"):
            accession = fields[1]
        else:
            accession = first_token

        accession = accession.strip().upper()
        sequence = "".join(parts).replace(" ", "").upper()

        if accession and sequence:
            records[accession] = sequence

    for line in fasta_text.splitlines():
        line = line.strip()

        if not line:
            continue

        if line.startswith(">"):
            save_record(header, sequence_parts)
            header = line[1:]
            sequence_parts = []
        else:
            sequence_parts.append(line)

    save_record(header, sequence_parts)
    return records


def read_fasta_cache(path):
    if not path.exists():
        return {}

    records = parse_fasta_records(path.read_text(encoding="utf-8"))
    print(f"Loaded {len(records):,} cached sequences.")
    return records


def write_fasta_atomic(records, path):
    """Write the complete sequence cache using an atomic replacement."""
    temp_path = path.with_suffix(path.suffix + ".tmp")

    with temp_path.open("w", encoding="utf-8") as handle:
        for accession in sorted(records):
            handle.write(f">{accession}\n")
            sequence = records[accession]
            for start in range(0, len(sequence), 60):
                handle.write(sequence[start:start + 60] + "\n")

    os.replace(temp_path, path)


def read_status(path):
    if not path.exists():
        return {}

    status = {}

    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            accession = row["accession"].strip().upper()
            status[accession] = row

    return status


def write_status_atomic(status, path):
    temp_path = path.with_suffix(path.suffix + ".tmp")

    with temp_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["accession", "status", "detail", "updated_utc"],
            delimiter="\t"
        )
        writer.writeheader()

        for accession in sorted(status):
            writer.writerow(status[accession])

    os.replace(temp_path, path)


def make_status(accession, state, detail=""):
    return {
        "accession": accession,
        "status": state,
        "detail": detail,
        "updated_utc": datetime.now(timezone.utc).isoformat()
    }


def retry_after_seconds(value):
    """Parse Retry-After as seconds or an HTTP date."""
    if not value:
        return None

    try:
        return max(0.0, float(value))
    except ValueError:
        pass

    try:
        retry_time = parsedate_to_datetime(value)
        if retry_time.tzinfo is None:
            retry_time = retry_time.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        return max(0.0, (retry_time - now).total_seconds())
    except Exception:
        return None

def fetch_batch(accessions, timeout, max_retries):
    """Retrieve a batch using one sequential HTTP request."""
    query = " OR ".join(f"accession:{acc}" for acc in accessions)

    params = urllib.parse.urlencode({
        "query": query,
        "format": "fasta"
    })

    url = f"{UNIPROT_STREAM_URL}?{params}"

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/plain"
        }
    )

    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8")
                return parse_fasta_records(body)

        except urllib.error.HTTPError as error:
            status_code = error.code
            retry_header = error.headers.get("Retry-After")

            if status_code == 429:
                delay = retry_after_seconds(retry_header)
                if delay is None:
                    delay = min(600.0, 30.0 * (2 ** attempt))

            elif status_code in (500, 502, 503, 504):
                delay = retry_after_seconds(retry_header)
                if delay is None:
                    delay = min(600.0, 15.0 * (2 ** attempt))

            else:
                raise RuntimeError(
                    f"Non-retryable UniProt HTTP error {status_code}: {error}"
                ) from error

            if attempt == max_retries - 1:
                raise RuntimeError(
                    f"UniProt request failed after {max_retries} attempts "
                    f"(HTTP {status_code})."
                ) from error

            print(
                f"HTTP {status_code}; waiting {delay:.1f} seconds "
                f"before retry {attempt + 2}/{max_retries}."
            )
            time.sleep(delay)

        
        except (urllib.error.URLError, TimeoutError, OSError, http.client.IncompleteRead) as error:
            delay = min(600.0, 15.0 * (2 ** attempt))

            if attempt == max_retries - 1:
                raise RuntimeError(
                    f"UniProt request failed after {max_retries} attempts: {error}"
                ) from error

            print(
                f"Network error/Incomplete read: {error}; waiting {delay:.1f} seconds "
                f"before retry {attempt + 2}/{max_retries}."
            )
            time.sleep(delay)

    raise RuntimeError("Unexpected request retry termination.")

def load_accessions(input_csv):
    # Load only the required column, not the full table.
    df = pd.read_csv(input_csv, usecols=["UniProt"], dtype=str)

    accessions = (
        df["UniProt"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
    )

    accessions = [
        accession for accession in accessions
        if accession and accession.lower() not in {"nan", "none", "na"}
    ]

    # Preserve order while removing duplicates.
    unique_accessions = list(dict.fromkeys(accessions))

    print(f"Input accession rows: {len(accessions):,}")
    print(f"Unique accessions: {len(unique_accessions):,}")

    return unique_accessions


def write_missing_report(accessions, sequences, path):
    missing = [acc for acc in accessions if acc not in sequences]

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["accession"])
        for accession in missing:
            writer.writerow([accession])

    print(f"Accessions without retrieved sequences: {len(missing):,}")


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve UniProt sequences with cautious request pacing."
    )

    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--outdir", default=DEFAULT_OUTDIR)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_REQUEST_INTERVAL,
        help="Seconds to pause between successful batch requests."
    )
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    parser.add_argument(
        "--retry-missing",
        action="store_true",
        help="Retry accessions previously recorded as not_found."
    )

    args = parser.parse_args()

    if args.batch_size < 1 or args.batch_size > 25:
        parser.error("--batch-size must be between 1 and 25.")
    if args.interval < 1.0:
        parser.error("--interval must be at least 1 second.")
    if args.max_retries < 1:
        parser.error("--max-retries must be at least 1.")

    input_csv = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    fasta_path = outdir / "CINTA-Chem_Target_Sequences.fasta"
    status_path = outdir / "CINTA-Chem_Target_Sequence_Retrieval_Status.tsv"
    missing_path = outdir / "CINTA-Chem_Target_Sequence_Retrieval_Missing.tsv"

    if not input_csv.exists():
        raise FileNotFoundError(f"Input file not found: {input_csv}")

    accessions = load_accessions(input_csv)
    sequences = read_fasta_cache(fasta_path)
    status = read_status(status_path)

    pending = [
        accession for accession in accessions
        if accession not in sequences
        and (
            status.get(accession, {}).get("status") != "not_found"
            or args.retry_missing
        )
    ]

    print(f"Sequences already cached: {len(sequences):,}")
    print(f"Accessions pending retrieval: {len(pending):,}")
    print("Requests will be sent sequentially, without parallel workers.")

    total_batches = (len(pending) + args.batch_size - 1) // args.batch_size

    for batch_number, start in enumerate(
        range(0, len(pending), args.batch_size), start=1
    ):
        batch = pending[start:start + args.batch_size]

        print(
            f"Requesting batch {batch_number}/{total_batches} "
            f"({len(batch)} accessions)."
        )

        try:
            retrieved = fetch_batch(
                batch,
                timeout=args.timeout,
                max_retries=args.max_retries
            )
        except Exception as error:
            for accession in batch:
                status[accession] = make_status(
                    accession, "error", str(error)
                )

            write_status_atomic(status, status_path)
            write_fasta_atomic(sequences, fasta_path)
            raise

        found_in_batch = 0

        for accession in batch:
            sequence = retrieved.get(accession)

            if sequence:
                sequences[accession] = sequence
                status[accession] = make_status(accession, "found")
                found_in_batch += 1
            else:
                status[accession] = make_status(
                    accession,
                    "not_found",
                    "No exact accession match returned by UniProt."
                )

        # Checkpoint after every successful request.
        write_fasta_atomic(sequences, fasta_path)
        write_status_atomic(status, status_path)

        print(
            f"Batch complete: {found_in_batch}/{len(batch)} sequences found. "
            f"Cached total: {len(sequences):,}."
        )

        if batch_number < total_batches:
            time.sleep(args.interval)

    write_missing_report(accessions, sequences, missing_path)

    print("\nSequence retrieval finished.")
    print(f"FASTA: {fasta_path}")
    print(f"Status: {status_path}")
    print(f"Missing accessions: {missing_path}")


if __name__ == "__main__":
    main()