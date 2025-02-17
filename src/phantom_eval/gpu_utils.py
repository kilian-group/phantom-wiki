import subprocess


def get_gpu_count() -> int:
    """
    Get the number of GPUs available on the system.
    """
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            check=True,
            text=True,
        )
        gpu_list = result.stdout.strip().split("\n")
        return len(gpu_list)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while trying to get GPU count: {e}")
        return 0
    except FileNotFoundError:
        print("nvidia-smi command not found. Ensure that the NVIDIA drivers are installed.")
        return 0
