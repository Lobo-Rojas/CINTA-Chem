import re
import time
import requests
import pandas as pd

# ==========================================================
# FILES
# ==========================================================

INPUT_FILE = "data/output/unique_uniprots_inactive.txt"
OUTPUT_FILE = "data/output/uniprot_target_classification_inactive.csv"

# ==========================================================
# READ UNIQUE UNIPROT IDS
# ==========================================================

with open(INPUT_FILE, "r") as f:
    uniprot_ids = [
        line.strip()
        for line in f
        if line.strip()
    ]

print(f"Total UniProt IDs: {len(uniprot_ids)}")

# ==========================================================
# UNIPROT REST API
# ==========================================================

BASE_URL = "https://rest.uniprot.org/uniprotkb/{}.json"


# ==========================================================
# CLEAN PROTEIN FAMILY
# ==========================================================

def clean_family(text):
    """
    Example:
    Belongs to the hexokinase family.
        -> Hexokinase

    Belongs to the ABC transporter family.
        -> ABC transporter
    """

    if not text:
        return None

    text = text.strip()

    text = re.sub(
        r"(?i)^belongs to (the )?",
        "",
        text
    )

    text = re.sub(
        r"(?i)\s+family\.?$",
        "",
        text
    )

    text = re.sub(
        r"\.$",
        "",
        text
    )

    text = text.strip()

    if len(text):
        text = text[0].upper() + text[1:]

    return text


# ==========================================================
# EXTRACT INFORMATION
# ==========================================================

def extract_annotation(uniprot_id):

    url = BASE_URL.format(uniprot_id)

    try:

        response = requests.get(url, timeout=30)

        if response.status_code != 200:

            return {
                "UniProt_ID": uniprot_id,
                "Protein_Family": None,
                "EC_Number": None
            }

        data = response.json()

        # --------------------------------------------------
        # Protein Family
        # --------------------------------------------------

        families = []

        for comment in data.get("comments", []):

            if comment.get("commentType") == "SIMILARITY":

                for text in comment.get("texts", []):

                    fam = clean_family(
                        text.get("value", "")
                    )

                    if fam:
                        families.append(fam)

        protein_family = "; ".join(
            sorted(set(families))
        )

        if protein_family == "":
            protein_family = None

        # --------------------------------------------------
        # EC Numbers
        # --------------------------------------------------

        ec_numbers = set()

        protein_desc = data.get(
            "proteinDescription",
            {}
        )

        def collect_ec(block):

            if not isinstance(block, dict):
                return

            for ec in block.get("ecNumbers", []):

                if isinstance(ec, dict):

                    value = ec.get("value")

                else:

                    value = ec

                if value:
                    ec_numbers.add(value)

        collect_ec(
            protein_desc.get(
                "recommendedName",
                {}
            )
        )

        for alt in protein_desc.get(
            "alternativeNames",
            []
        ):
            collect_ec(alt)

        for sub in protein_desc.get(
            "submissionNames",
            []
        ):
            collect_ec(sub)

        for comment in data.get("comments", []):

            if comment.get("commentType") == "CATALYTIC ACTIVITY":

                reaction = comment.get(
                    "reaction",
                    {}
                )

                for ec in reaction.get(
                    "ecNumbers",
                    []
                ):

                    if isinstance(ec, dict):
                        value = ec.get("value")
                    else:
                        value = ec

                    if value:
                        ec_numbers.add(value)

        ec_number = "; ".join(
            sorted(ec_numbers)
        )

        if ec_number == "":
            ec_number = None

        return {
            "UniProt_ID": uniprot_id,
            "Protein_Family": protein_family,
            "EC_Number": ec_number
        }

    except Exception as e:

        print(f"Error retrieving {uniprot_id}: {e}")

        return {
            "UniProt_ID": uniprot_id,
            "Protein_Family": None,
            "EC_Number": None
        }


# ==========================================================
# RETRIEVE DATA
# ==========================================================

results = []

for i, uid in enumerate(uniprot_ids, 1):

    print(f"[{i}/{len(uniprot_ids)}] {uid}")

    appended_line = extract_annotation(uid)

    results.append(appended_line
        
    )

    time.sleep(0.2)

# ==========================================================
# SAVE CSV
# ==========================================================

df = pd.DataFrame(results)

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nFinished.")
print(f"Saved: {OUTPUT_FILE}")