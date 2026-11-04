#!/bin/bash
# GPU steps on Falcon: A30 preferred, L40S fallback (SLURM starts on whichever partition frees first).
# Usage: sbatch slurm/gpu.sbatch scripts/05_integrate.py --config config/config.yaml [--small]
#SBATCH --account=introtogds
#SBATCH --partition=a30_normal_q,l40s_normal_q
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=12:00:00
#SBATCH --output=logs/slurm_%x_%j.out
set -euo pipefail
source slurm/env.sh
echo "host=$(hostname) job=$SLURM_JOB_ID gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader) args=$*"
python "$@"
