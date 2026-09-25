import requests
import json

aid = 2927

url = (
    f"https://pubchem.ncbi.nlm.nih.gov/"
    f"rest/pug_view/data/assay/{aid}/JSON"
)

data = requests.get(url).json()

import re


def extract_target_metadata(record):

    row = {

        "Assay_Name": None,
        "Target_Name": None,
        "UniProtKB_ID": None,
        "Gene_Symbol": None,
        "Organism": None
    }

    row["Assay_Name"] = record.get(
        "RecordTitle"
    )

    sections = record.get(
        "Section",
        []
    )

    for sec in sections:

        if sec.get(
            "TOCHeading"
        ) != "Target":
            continue

        for subsec in sec.get(
            "Section",
            []
        ):

            heading = subsec.get(
                "TOCHeading",
                ""
            )

            infos = subsec.get(
                "Information",
                []
            )

            if len(infos) == 0:
                continue

            info = infos[0]

            # ---------------------------------
            # Protein Target
            # ---------------------------------

            if heading == "Protein Target":

                try:

                    row["Target_Name"] = (

                        info["Value"]
                        ["StringWithMarkup"][0]
                        ["String"]

                    )

                except:
                    pass

                try:

                    url = info.get(
                        "URL",
                        ""
                    )

                    m = re.search(
                        r"/protein/([A-Z0-9]+)",
                        url
                    )

                    if m:

                        row[
                            "UniProtKB_ID"
                        ] = m.group(1)

                except:
                    pass

            # ---------------------------------
            # Encoding Gene
            # ---------------------------------

            elif heading == "Encoding Gene":

                try:

                    row["Gene_Symbol"] = (

                        info["Value"]
                        ["StringWithMarkup"][0]
                        ["String"]

                    )

                except:
                    pass

            # ---------------------------------
            # Taxonomy
            # ---------------------------------

            elif heading == "Taxonomy":

                try:

                    row["Organism"] = (

                        info["Value"]
                        ["StringWithMarkup"][0]
                        ["String"]

                    )

                except:
                    pass

    return row

def get_aid_metadata(aid):

    url = (
        "https://pubchem.ncbi.nlm.nih.gov/"
        f"rest/pug_view/data/assay/{aid}/JSON"
    )

    try:

        r = requests.get(
            url,
            timeout=30
        )

        if r.status_code != 200:
            return None

        data = r.json()

        record = data.get(
            "Record"
        )

        if record is None:
            return None

        row = extract_target_metadata(
            record
        )

        row["PUBCHEM_AID"] = aid

        return row

    except:

        return None

print(get_aid_metadata(aid))