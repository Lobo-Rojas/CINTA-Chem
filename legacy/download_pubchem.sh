#!/bin/bash

# ==================================================
# CONFIG
# ==================================================

OUTPUT_DIR="$HOME/Documents/CINTA-Chem/data/raw_assays"
LOG_DIR="$HOME/Documents/CINTA-Chem/log"

mkdir -p "$OUTPUT_DIR"
mkdir -p "$LOG_DIR"

BASE_URL="https://ftp.ncbi.nlm.nih.gov/pubchem/Bioassay/CSV/Data"

START=1
END=2202000
STEP=1000
MIN_FILESIZE=100000

ERROR_LOG="${LOG_DIR}/CINTA-Chem_Download_Errors.log"

# ==================================================
# LOGGING
# ==================================================

log_error() {
    local file="$1"
    local message="$2"
    printf '%s\t%s\t%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$file" "$message" >> "$ERROR_LOG"
}

# ==================================================
# DOWNLOAD LOOP
# ==================================================

for ((A=START; A<=END; A+=STEP))
do

    END_RANGE=$((A + 999))

    START_PADDED=$(printf "%07d" "$A")
    END_PADDED=$(printf "%07d" "$END_RANGE")

    FILE="${START_PADDED}_${END_PADDED}.zip"

    echo
    echo "=================================================="
    echo "Downloading $FILE"
    echo "=================================================="

    OUTPUT_FILE="${OUTPUT_DIR}/${FILE}"
    TEMP_FILE="${OUTPUT_FILE}.part"

    # --------------------------------------------------
    # Skip if already present and valid
    # --------------------------------------------------

    if [[ -f "$OUTPUT_FILE" ]]; then

        FILESIZE=$(stat -c%s "$OUTPUT_FILE" 2>/dev/null || echo 0)

        if [[ "$FILESIZE" -gt "$MIN_FILESIZE" ]]; then

            # Also verify ZIP integrity when unzip is available.
            if command -v unzip >/dev/null 2>&1; then
                if unzip -tq "$OUTPUT_FILE" >/dev/null 2>&1; then
                    echo "Already exists and is valid, skipping: $FILE"
                    continue
                else
                    echo "Existing ZIP is corrupted, removing: $FILE"
                    rm -f "$OUTPUT_FILE"
                    log_error "$FILE" "Existing file failed ZIP integrity test and was removed."
                fi
            else
                echo "Already exists, skipping: $FILE"
                continue
            fi

        else
            echo "Corrupted/incomplete file detected, removing: $FILE"
            rm -f "$OUTPUT_FILE"
            log_error "$FILE" "Existing file was smaller than ${MIN_FILESIZE} bytes and was removed."
        fi
    fi

    # Remove any interrupted partial download from a previous attempt.
    rm -f "$TEMP_FILE"

    # --------------------------------------------------
    # Download to a temporary file
    # --------------------------------------------------

    curl \
        --retry 10 \
        --retry-delay 5 \
        --connect-timeout 30 \
        --max-time 1800 \
        -L \
        -o "$TEMP_FILE" \
        "${BASE_URL}/${FILE}"

    CURL_STATUS=$?

    # --------------------------------------------------
    # Validate download
    # --------------------------------------------------

    if [[ "$CURL_STATUS" -ne 0 ]]; then
        echo "ERROR: curl failed for $FILE (exit code $CURL_STATUS)."
        rm -f "$TEMP_FILE" "$OUTPUT_FILE"
        log_error "$FILE" "curl failed with exit code ${CURL_STATUS}; temporary/partial file removed."
        sleep 2
        continue
    fi

    if [[ ! -f "$TEMP_FILE" ]]; then
        echo "ERROR: no downloaded file produced for $FILE."
        rm -f "$OUTPUT_FILE"
        log_error "$FILE" "curl returned successfully but no temporary output file was produced."
        sleep 2
        continue
    fi

    FILESIZE=$(stat -c%s "$TEMP_FILE" 2>/dev/null || echo 0)

    if [[ "$FILESIZE" -le "$MIN_FILESIZE" ]]; then
        echo "ERROR: removing invalid/incomplete file: $FILE (size: ${FILESIZE} bytes)"
        rm -f "$TEMP_FILE" "$OUTPUT_FILE"
        log_error "$FILE" "Downloaded file was ${FILESIZE} bytes (threshold: >${MIN_FILESIZE}); file removed."
        sleep 2
        continue
    fi

    # ZIP integrity check catches files that are large enough but corrupted.
    if command -v unzip >/dev/null 2>&1; then
        if ! unzip -tq "$TEMP_FILE" >/dev/null 2>&1; then
            echo "ERROR: ZIP integrity check failed for $FILE; removing corrupted file."
            rm -f "$TEMP_FILE" "$OUTPUT_FILE"
            log_error "$FILE" "Downloaded file passed size check but failed ZIP integrity test; file removed."
            sleep 2
            continue
        fi
    fi

    mv -f "$TEMP_FILE" "$OUTPUT_FILE"

    echo "Download successful: $FILE"
    echo "Size: $(du -h "$OUTPUT_FILE" | cut -f1)"

    sleep 2

done

echo
echo "DOWNLOAD COMPLETE"
