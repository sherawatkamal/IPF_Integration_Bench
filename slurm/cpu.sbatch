#!/bin/bash
# CPU steps on Owl. Usage: sbatch -M owl slurm/cpu.sbatch scripts/03_qc.py --config config/config.yaml [--small]
#SBATCH --account=introtogds
#SBATCH --partition=normal_q
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=12:00:00
#SBATCH --output=logs/slurm_%x_%j.out
set -euo pipefail
source slurm/env.sh
echo "host=$(hostname) job=$SLURM_JOB_ID args=$*"
python "$@"
