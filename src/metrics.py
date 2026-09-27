"""
Performance Metrics Module (FR-5)
=================================
Quantifies image degradation and reconstruction fidelity using:
1. Mean Squared Error (MSE): Average squared difference between reference and test image.
2. Peak Signal-to-Noise Ratio (PSNR): Logarithmic ratio of maximum signal power to distorting noise power.

Also provides visualization routines to plot Kernel Size vs. MSE and Kernel Size vs. PSNR curves.
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
import matplotlib.pyplot as plt


def compute_mse(image_true: np.ndarray, image_test: np.ndarray) -> float:
    """
    Computes the Mean Squared Error (MSE) between two images:
        MSE = (1 / (M * N * C)) * sum((I_true - I_test)^2)

    Args:
        image_true (np.ndarray): Ground truth reference image.
        image_test (np.ndarray): Degraded or filtered image to evaluate.

    Returns:
        float: Computed MSE value (lower is better, 0.0 is identical).

    Raises:
        ValueError: If image dimensions or shapes do not match.
    """
    if image_true.shape != image_test.shape:
        raise ValueError(
            f"Shape mismatch in MSE computation: true {image_true.shape} vs test {image_test.shape}"
        )

    # Convert to float64 to avoid overflow during squaring
    diff = image_true.astype(np.float64) - image_test.astype(np.float64)
    mse = np.mean(diff ** 2)
    return float(mse)


def compute_psnr(image_true: np.ndarray, image_test: np.ndarray, max_val: float = 255.0) -> float:
    """
    Computes the Peak Signal-to-Noise Ratio (PSNR) in decibels (dB):
        PSNR = 10 * log10(max_val^2 / MSE)

    Args:
        image_true (np.ndarray): Ground truth reference image.
        image_test (np.ndarray): Degraded or filtered image to evaluate.
        max_val (float): Maximum possible pixel intensity (255.0 for uint8).

    Returns:
        float: PSNR in decibels (higher is better). Returns float('inf') if MSE == 0.
    """
    mse = compute_mse(image_true, image_test)
    if mse == 0.0:
        return float("inf")

    psnr = 10.0 * np.log10((max_val ** 2) / mse)
    return float(psnr)


def format_metrics_string(mse: float, psnr: float) -> str:
    """
    Formats MSE and PSNR exactly according to specification:
        MSE = <value>
        PSNR = <value>

    Args:
        mse (float): Computed Mean Squared Error.
        psnr (float): Computed Peak Signal-to-Noise Ratio.

    Returns:
        str: Formatted two-line metrics string.
    """
    psnr_str = "Infinity" if np.isinf(psnr) else f"{psnr:.2f}"
    return f"MSE = {mse:.2f}\nPSNR = {psnr_str}"


def print_metrics(label: str, mse: float, psnr: float) -> None:
    """
    Prints metrics to console adhering strictly to format requirements.

    Args:
        label (str): Description of the comparison (e.g. 'Noisy Image', 'Kernel 5x5').
        mse (float): Mean Squared Error.
        psnr (float): Peak Signal-to-Noise Ratio.
    """
    print(f"--- [{label}] ---")
    print(f"MSE = {mse:.2f}")
    psnr_str = "Infinity" if np.isinf(psnr) else f"{psnr:.2f}"
    print(f"PSNR = {psnr_str}")


def plot_performance_graphs(
    kernel_sizes: List[int],
    mse_values: List[float],
    psnr_values: List[float],
    baseline_mse: float,
    baseline_psnr: float,
    image_name: str,
    noise_type: str,
    save_path: str | Path,
) -> str:
    """
    Generates and saves dual-panel performance curves:
    - Left: Kernel Size vs. MSE (with noisy baseline)
    - Right: Kernel Size vs. PSNR (with noisy baseline)

    Args:
        kernel_sizes (List[int]): Evaluated kernel dimensions (e.g., [3, 5, 7, 9]).
        mse_values (List[float]): Corresponding MSE values for each kernel.
        psnr_values (List[float]): Corresponding PSNR values for each kernel.
        baseline_mse (float): MSE of the noisy input before filtering.
        baseline_psnr (float): PSNR of the noisy input before filtering.
        image_name (str): Identifier of the image being evaluated.
        noise_type (str): Type of noise (e.g., 'Gaussian', 'Salt-and-Pepper').
        save_path (str | Path): Destination file path for the graph (.png).

    Returns:
        str: Absolute or resolved path to the saved graph.
    """
    dest = Path(save_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle(
        f"Gaussian Filter Performance Analysis - {image_name} ({noise_type} Noise)",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )

    # 1. MSE vs Kernel Size
    ax1.plot(
        kernel_sizes,
        mse_values,
        marker="o",
        color="#D9381E",
        linewidth=2.2,
        markersize=7,
        label="Filtered MSE",
    )
    ax1.axhline(
        y=baseline_mse,
        color="#7F8C8D",
        linestyle="--",
        linewidth=1.8,
        label=f"Noisy Baseline MSE ({baseline_mse:.2f})",
    )
    ax1.set_title("Kernel Size vs. MSE", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Kernel Size", fontsize=10)
    ax1.set_ylabel("MSE", fontsize=10)
    ax1.set_xticks(kernel_sizes)
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="best", frameon=True)

    # Annotate minimum MSE point
    min_idx = int(np.argmin(mse_values))
    ax1.annotate(
        f"Optimal: {kernel_sizes[min_idx]}x{kernel_sizes[min_idx]}\n(MSE={mse_values[min_idx]:.2f})",
        xy=(kernel_sizes[min_idx], mse_values[min_idx]),
        xytext=(kernel_sizes[min_idx], mse_values[min_idx] + (baseline_mse * 0.1)),
        arrowprops=dict(facecolor="#D9381E", shrink=0.08, width=1, headwidth=6),
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", fc="#FDEDEC", ec="#D9381E", lw=1),
    )

    # 2. PSNR vs Kernel Size
    ax2.plot(
        kernel_sizes,
        psnr_values,
        marker="s",
        color="#1E8449",
        linewidth=2.2,
        markersize=7,
        label="Filtered PSNR",
    )
    ax2.axhline(
        y=baseline_psnr,
        color="#7F8C8D",
        linestyle="--",
        linewidth=1.8,
        label=f"Noisy Baseline PSNR ({baseline_psnr:.2f} dB)",
    )
    ax2.set_title("Kernel Size vs. PSNR", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Kernel Size", fontsize=10)
    ax2.set_ylabel("PSNR (dB)", fontsize=10)
    ax2.set_xticks(kernel_sizes)
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="best", frameon=True)

    # Annotate maximum PSNR point
    max_idx = int(np.argmax(psnr_values))
    ax2.annotate(
        f"Optimal: {kernel_sizes[max_idx]}x{kernel_sizes[max_idx]}\n(PSNR={psnr_values[max_idx]:.2f} dB)",
        xy=(kernel_sizes[max_idx], psnr_values[max_idx]),
        xytext=(kernel_sizes[max_idx], psnr_values[max_idx] - 2.0),
        arrowprops=dict(facecolor="#1E8449", shrink=0.08, width=1, headwidth=6),
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", fc="#E8F8F5", ec="#1E8449", lw=1),
    )

    plt.tight_layout()
    plt.savefig(str(dest), dpi=150)
    plt.close(fig)
    return str(dest.resolve())
