# SLURM usage example

Spinner integrates nicely into SLURM job scripts. Rather than calling `srun` or `mpirun` directly inside Spinner, you typically let SLURM handle resource allocation, then pass any node/host info as `--extra-args`.

Example SLURM submission script:

```bash
#!/bin/bash
#SBATCH --nodes=4
#SBATCH --partition=gpu-partition
#SBATCH --time=04:00:00
#SBATCH --job-name=cool-benchmark
#SBATCH --output=job_log_%j.out

set -e

module purge
module load cmake/3.27.9
module load mpich/4.0.2
module load singularity/3.7.1

# Activate Spinner environment
source spinner/.venv/bin/activate

# Capture the allocated nodes for the MPI run
host_list=$(scontrol show hostname $SLURM_JOB_NODELIST | paste -sd "," -)

spinner run bench_settings.yaml \
    --extra-args "hosts=$host_list"
```

Here:

- SLURM decides which nodes to use.
- We pass the node list (`hosts`) as an extra argument to Spinner’s YAML config.
