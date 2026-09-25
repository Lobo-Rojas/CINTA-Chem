#!/bin/bash
#SBATCH --job-name=pubchem_pipeline_inactive
#SBATCH --partition=short-cpu
#SBATCH --output=logs/pipeline_%j.log
#SBATCH --error=logs/pipeline_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=4-12:00:00
#SBATCH --mail-type=END,FAIL

set -e

echo "============================================================"
echo "PubChem Chemogenomics Pipeline"
echo "Inactive-compound pipeline"
echo "============================================================"
echo "Pipeline execution started: $(date)"
echo "============================================================"

# ------------------------------------------------------------
# 1. Load Conda
# ------------------------------------------------------------

module load conda

if [ -f "$(conda info --base)/etc/profile.d/conda.sh" ]; then
    source "$(conda info --base)/etc/profile.d/conda.sh"
else
    echo "ERROR: Could not locate the base Conda installation."
    exit 1
fi

# ------------------------------------------------------------
# 2. Activate pipeline environment
# ------------------------------------------------------------

echo ""
echo "Activating virtual environment: pubchem_env..."

conda activate pubchem_env

echo "Python executable: $(which python)"
echo "Python version: $(python --version)"

# ------------------------------------------------------------
# 3. Check/install DuckDB automatically
# ------------------------------------------------------------

echo ""
echo "Checking DuckDB installation..."

if python -c "import duckdb" >/dev/null 2>&1; then

    echo "DuckDB is already installed."
    echo "DuckDB version: $(python -c 'import duckdb; print(duckdb.__version__)')"

else

    echo "DuckDB is not installed."
    echo "Installing DuckDB into pubchem_env..."

    python -m pip install duckdb

    echo "DuckDB installation completed."
    echo "DuckDB version: $(python -c 'import duckdb; print(duckdb.__version__)')"

fi

# ------------------------------------------------------------
# 4. Verify DuckDB functionality
# ------------------------------------------------------------

echo ""
echo "Testing DuckDB..."

python -c "import duckdb; print(duckdb.sql('SELECT 42').fetchall())"

echo "DuckDB test successful."

# ------------------------------------------------------------
# 5. Display allocated HPC resources
# ------------------------------------------------------------

echo ""
echo "============================================================"
echo "Allocated HPC resources"
echo "============================================================"

echo "SLURM_CPUS_PER_TASK = ${SLURM_CPUS_PER_TASK:-not set}"
echo "SLURM_CPUS_ON_NODE  = ${SLURM_CPUS_ON_NODE:-not set}"
echo "SLURM_MEM_PER_NODE  = ${SLURM_MEM_PER_NODE:-not set}"
echo "SLURM_MEM_PER_CPU   = ${SLURM_MEM_PER_CPU:-not set}"
echo "SLURM_TMPDIR        = ${SLURM_TMPDIR:-not set}"

# ------------------------------------------------------------
# 6. Configure fast temporary storage
# ------------------------------------------------------------

if [ -d "$SLURM_TMPDIR" ]; then

    export DUCKDB_TMPDIR="$SLURM_TMPDIR/duckdb_tmp"
    mkdir -p "$DUCKDB_TMPDIR"

    export SMILES_CACHE_DIR="$SLURM_TMPDIR/smiles_cache"
    mkdir -p "$SMILES_CACHE_DIR"

    echo ""
    echo "Using node-local temporary storage:"
    echo "DuckDB temporary directory: $DUCKDB_TMPDIR"
    echo "SMILES cache directory:     $SMILES_CACHE_DIR"

else

    echo ""
    echo "WARNING: SLURM_TMPDIR is not available."
    echo "DuckDB will use its default temporary directory."

fi

# ------------------------------------------------------------
# 7. Create log directory
# ------------------------------------------------------------

mkdir -p logs

# ------------------------------------------------------------
# 8. Run inactive-compound pipeline
# ------------------------------------------------------------

echo ""
echo "============================================================"
echo "Starting inactive-compound pipeline"
echo "============================================================"
echo ""

python run_inactive_pipeline.py #--from-step inactive_balanced_filter

# ------------------------------------------------------------
# 9. Completion
# ------------------------------------------------------------

echo ""
echo "============================================================"
echo "Pipeline execution completed successfully"
echo "Finished: $(date)"
echo "============================================================"
