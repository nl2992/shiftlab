import importlib.metadata
import shutil
import subprocess

import psutil


def resolve_device(requested: str, *, n: int, d: int, chunk_size: int) -> str:
    """Resolve auto conservatively using the workload range benchmarked on this project.

    The committed end-to-end sweep found CUDA useful at 200k x 64 with chunks >=5k,
    while smaller chunks sometimes lost to transfer and DataFrame assembly overhead.
    This is a default heuristic, not a performance guarantee; explicit cpu/cuda wins.
    """
    if requested != "auto":
        return requested
    if not environment()["cuda_available"]:
        return "cpu"
    if n >= 200_000 and d >= 64 and chunk_size >= 5_000:
        return "cuda"
    return "cpu"


def environment() -> dict:
    result = {
        "cpu_ram_bytes": psutil.virtual_memory().total,
        "disk_free_bytes": shutil.disk_usage(".").free,
        "cuda_available": False,
    }
    try:
        result["nvidia_smi"] = (
            subprocess.check_output(
                [
                    "nvidia-smi",
                    "--query-gpu=name,memory.total,driver_version,utilization.gpu,memory.used",
                    "--format=csv,noheader",
                ],
                timeout=10,
            )
            .decode()
            .strip()
        )
    except (OSError, subprocess.SubprocessError):
        result["nvidia_smi"] = None
    try:
        import torch

        result.update(
            torch_version=importlib.metadata.version("torch"),
            cuda_runtime=torch.version.cuda,
            cuda_available=torch.cuda.is_available(),
        )
        if torch.cuda.is_available():
            result.update(
                gpu_name=torch.cuda.get_device_name(),
                gpu_memory_bytes=torch.cuda.get_device_properties(0).total_memory,
            )
    except ImportError:
        result["torch_version"] = None
    result["versions"] = {}
    for name in ["numpy", "scipy", "pandas", "pyarrow", "folktables"]:
        try:
            result["versions"][name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result["versions"][name] = None
    return result
