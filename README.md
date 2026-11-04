# SignalKeep

**Does batch correction erase disease biology?** SignalKeep benchmarks single-cell integration methods (Harmony, BBKNN, Scanorama, scVI, scANVI) on a multi-study atlas of idiopathic pulmonary fibrosis (IPF) and control lung. It asks which methods remove study effects while keeping the disease signal that matters for drug discovery.

Alongside the standard `scib` metrics, SignalKeep scores:

1. **Disease signal preservation:** IPF vs control separability within each cell type, scored at donor level.
2. **IPF biology checks:** whether aberrant basaloid cells, SPP1+ profibrotic macrophages, CTHRC1+ pathologic fibroblasts and transitional AT2 cells stay distinct.
3. **Confounding stress test:** a balanced design vs a design where study and disease are confounded.

> Status: Phase 0 (setup) and the Census exploration are done. Results and the hero figure will appear here.

## Data

The data come from the CELLxGENE Census: lung, `is_primary_data == True`, `idiopathic pulmonary fibrosis` vs `normal`, preferably 10x 3′ assays. The Census version is pinned in [config/config.yaml](config/config.yaml). The study table (`metadata_report.csv`) will go here after Phase 1.

## How to run

```bash
module load Miniforge3/25.11.0-1
conda env create -p <env-prefix> -f environment.yml
conda activate <env-prefix> && pip install -e .

python scripts/00_explore_census.py --config config/config.yaml   # metadata only
# Heavy steps run on SLURM (VT ARC):
sbatch -M owl slurm/cpu.sbatch scripts/03_qc.py --config config/config.yaml --small
sbatch        slurm/gpu.sbatch scripts/05_integrate.py --config config/config.yaml --small
```

`--small` runs a pipeline of about 30k cells and 3 studies end to end, for development and CI.

## Repository layout

```
config/config.yaml   all paths, parameters and seeds
src/signalkeep/      library code (one module per pipeline step)
scripts/             thin CLI wrappers, 00–09
slurm/               CPU (Owl) and GPU (Falcon) job templates
docs/DEVIATIONS.md   approved deviations from the original spec
results/             small tables and figures (committed)
data/, logs/         gitignored
```

Approved deviations from the original spec are listed in [docs/DEVIATIONS.md](docs/DEVIATIONS.md).
