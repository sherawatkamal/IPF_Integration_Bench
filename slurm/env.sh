# Sourced by job scripts. Override SIGNALKEEP_ENV to use a different conda env prefix.
export SIGNALKEEP_ENV=${SIGNALKEEP_ENV:-/projects/intro2gds/I2GDS2026/Team1/Kamal/envs/signalkeep}
export PATH="$SIGNALKEEP_ENV/bin:$PATH"
export PYTHONNOUSERSITE=1
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export NUMBA_CACHE_DIR=${TMPDIR:-/tmp}/numba_cache
