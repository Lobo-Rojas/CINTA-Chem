#!/bin/bash
#SBATCH --job-name=cinta_chem_active
#SBATCH --partition=long-cpu          # Recommended partition for long-running jobs without GPU
#SBATCH --output=logs/CINTA-Chem_pipeline_%j.log # Standard output file (%j is replaced by the job ID)
#SBATCH --error=logs/CINTA-Chem_pipeline_%j.err  # Error log file
#SBATCH --nodes=1                     # Centralized execution on a single node
#SBATCH --ntasks=1                    # A single global processing task
#SBATCH --cpus-per-task=32             # CPUs allocated for internal processing
#SBATCH --mem=256G                     # RAM allocated for memory-intensive table merges
#SBATCH --time=7-12:00:00             # Maximum execution time (7 days and 12 hours)
#SBATCH --mail-type=END,FAIL          # Email notification when the job finishes or fails

# Stop script execution immediately if any internal command fails
set -e

echo "=== Pipeline execution started: $(date) ==="

# ==============================================================================
# 1. CONDA ENVIRONMENT INITIALIZATION
# ==============================================================================

# If the system requires loading the conda module first, uncomment the following line:
module load conda

# Enable the Conda environment paths for non-interactive scripts on Slurm nodes
if [ -f "$(conda info --base)/etc/profile.d/conda.sh" ]; then
    source "$(conda info --base)/etc/profile.d/conda.sh"
else
    echo "ERROR: Could not locate the base Conda installation."
    exit 1
fi

# Activate the previously created Python 3.10 environment
echo "Activating site-specific Conda environment: pubchem_env..."
conda activate pubchem_env

# ==============================================================================
# 2. I/O STORAGE OPTIMIZATION (SCRATCH)
# ==============================================================================

# If the assigned compute node has ultra-fast local storage (NVMe SSD)
if [ -d "$SLURM_TMPDIR" ]; then
    export SMILES_CACHE_DIR="$SLURM_TMPDIR/smiles_cache"
    mkdir -p "$SMILES_CACHE_DIR"
    echo "Using fast local storage on the compute node at: $SLURM_TMPDIR"
fi

# Ensure that the directory for Slurm scheduler logs exists
mkdir -p logs

# ==============================================================================
# 3. PIPELINE EXECUTION
# ==============================================================================

echo "Running run_active_pipeline.py (including final UniProt sequence retrieval stage)..."
# Run the active entry point with its documented command-line interface
python run_active_pipeline.py

echo "=== Pipeline execution completed successfully: $(date) ==="
