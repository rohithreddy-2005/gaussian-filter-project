"""
Visualizer and Result Export Module (FR-4 & FR-6)
=================================================
Produces visual figures and exports filtered and comparison outputs:
- Generates side-by-side (Original -> Noisy -> Filtered) comparisons.
- Generates comprehensive multi-kernel comparison boards (Original, Noisy, 3x3, 5x5, 7x7, 9x9).
- Annotates MSE and PSNR scores directly on figures.
- Exports raw filtered images and high-resolution comparison plots into structured output folders.
"""

from pathlib import Path
from typing import Dict, Tuple, Optional
import cv2
import numpy as np
import matplotlib.pyplot as plt


def save_image_to_disk(image_rgb: np.ndarray, output_path: str | Path) -> str:
    """
    Saves an RGB NumPy image array to disk as a standard image file (.png or .jpg).

    Args:
        image_rgb (np.ndarray): Image in RGB format (uint8).
        output_path (str | Path): Destination file path.

    Returns:
        str: Absolute path of saved file.
    """
    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Convert RGB back to BGR for OpenCV saving
    if image_rgb.ndim == 3:
        bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    else:
        bgr = image_rgb

    success = cv2.imwrite(str(dest.resolve()), bgr)
    if not success:
        raise IOError(f"Failed to write image to {dest.resolve()}")
    return str(dest.resolve())


def create_triptych_comparison(
    original: np.ndarray,
    noisy: np.ndarray,
    filtered: np.ndarray,
    kernel_size: int,
    metrics_noisy: Tuple[float, float],
    metrics_filtered: Tuple[float, float],
    title_prefix: str = "Image",
    save_path: Optional[str | Path] = None,
) -> str:
    """
    Generates a single 1x3 figure showing:
        Original -> Noisy -> Filtered
    with metrics displayed below each panel.

    Args:
        original (np.ndarray): Pristine ground truth image.
        noisy (np.ndarray): Degraded input image.
        filtered (np.ndarray): Image after Gaussian smoothing.
        kernel_size (int): Dimension of Gaussian kernel used.
        metrics_noisy (Tuple[float, float]): (MSE, PSNR) of noisy image against original.
        metrics_filtered (Tuple[float, float]): (MSE, PSNR) of filtered image against original.
        title_prefix (str): Prefix name for the figure title.
        save_path (Optional[str | Path]): File path where figure should be saved.

    Returns:
        str: Path to saved comparison image.
    """
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.5))
    fig.suptitle(
        f"{title_prefix} - Gaussian Filtering Comparison (Kernel {kernel_size}x{kernel_size})",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )

    panels = [
        ("Original (Clean)", original, "Reference\nGround Truth", "#2E4053"),
        ("Noisy Input", noisy, f"MSE: {metrics_noisy[0]:.2f}\nPSNR: {metrics_noisy[1]:.2f} dB", "#C0392B"),
        (f"Gaussian Filtered ({kernel_size}x{kernel_size})", filtered, f"MSE: {metrics_filtered[0]:.2f}\nPSNR: {metrics_filtered[1]:.2f} dB", "#27AE60"),
    ]

    for ax, (title, img, metric_text, color) in zip(axes, panels):
        if img.ndim == 2:
            ax.imshow(img, cmap="gray")
        else:
            ax.imshow(img)
        ax.set_title(title, fontsize=12, fontweight="bold", pad=8)
        ax.set_xlabel(metric_text, fontsize=10, fontweight="bold", color=color, labelpad=8)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_edgecolor(color)
            spine.set_linewidth(2)

    plt.tight_layout()

    if save_path is not None:
        dest = Path(save_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(str(dest), dpi=150)
        plt.close(fig)
        return str(dest.resolve())

    plt.close(fig)
    return ""


def create_multipanel_comparison(
    original: np.ndarray,
    noisy: np.ndarray,
    filtered_dict: Dict[int, np.ndarray],
    metrics_dict: Dict[int, Tuple[float, float]],
    noisy_metrics: Tuple[float, float],
    title_prefix: str = "Image",
    save_path: Optional[str | Path] = None,
) -> str:
    """
    Creates a comprehensive 2x3 comparison grid displaying:
    [Row 1]: Original (Clean) | Noisy Image | Filtered 3x3
    [Row 2]: Filtered 5x5     | Filtered 7x7 | Filtered 9x9

    Args:
        original (np.ndarray): Original image.
        noisy (np.ndarray): Noisy image.
        filtered_dict (Dict[int, np.ndarray]): Mapping of kernel_size -> filtered image.
        metrics_dict (Dict[int, Tuple[float, float]]): Mapping of kernel_size -> (MSE, PSNR).
        noisy_metrics (Tuple[float, float]): (MSE, PSNR) of noisy image.
        title_prefix (str): Prefix name for the figure title.
        save_path (Optional[str | Path]): File path where figure should be saved.

    Returns:
        str: Path to saved comparison image.
    """
    fig, axes = plt.subplots(2, 3, figsize=(16, 10.5))
    fig.suptitle(
        f"{title_prefix} - Comprehensive Gaussian Filter Kernel Evaluation (3x3 to 9x9)",
        fontsize=15,
        fontweight="bold",
        y=0.98,
    )

    plot_items = [
        ("Original (Clean)", original, "Reference\nGround Truth", "#2E4053"),
        ("Noisy Input", noisy, f"MSE: {noisy_metrics[0]:.2f}\nPSNR: {noisy_metrics[1]:.2f} dB", "#C0392B"),
    ]

    for k in sorted(filtered_dict.keys()):
        m_mse, m_psnr = metrics_dict[k]
        plot_items.append(
            (f"Filtered {k}x{k}", filtered_dict[k], f"MSE: {m_mse:.2f}\nPSNR: {m_psnr:.2f} dB", "#2980B9")
        )

    flat_axes = axes.flatten()
    for ax, (title, img, metric_text, color) in zip(flat_axes, plot_items):
        if img.ndim == 2:
            ax.imshow(img, cmap="gray")
        else:
            ax.imshow(img)
        ax.set_title(title, fontsize=11, fontweight="bold", pad=6)
        ax.set_xlabel(metric_text, fontsize=10, fontweight="bold", color=color, labelpad=6)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_edgecolor(color)
            spine.set_linewidth(1.8)

    plt.tight_layout()

    if save_path is not None:
        dest = Path(save_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(str(dest), dpi=150)
        plt.close(fig)
        return str(dest.resolve())

    plt.close(fig)
    return ""
