"""
Gaussian Filtering Module (FR-3)
================================
Applies 2D Gaussian Low-Pass Filtering for spatial domain image smoothing.

Theory:
A 2D Gaussian kernel is mathematically defined as:
    G(x, y) = (1 / (2 * pi * sigma^2)) * exp(-(x^2 + y^2) / (2 * sigma^2))

Because the Gaussian function is isotropic and linearly separable, 2D convolution
can be computed as two successive 1D convolutions (horizontal then vertical),
achieving O(K) instead of O(K^2) per pixel.

As a low-pass filter, it attenuates high spatial frequency variations (noise, fine texture, sharp edges)
while preserving low spatial frequencies (homogeneous regions and overall illumination).
"""

from typing import List, Dict, Optional
import cv2
import numpy as np


def compute_auto_sigma(kernel_size: int) -> float:
    """
    Computes an appropriate standard deviation (sigma) for a given square kernel size.
    Uses OpenCV's standard heuristic formula:
        sigma = 0.3 * ((kernel_size - 1) * 0.5 - 1) + 0.8

    For example:
        k = 3 -> sigma ≈ 0.80
        k = 5 -> sigma ≈ 1.10
        k = 7 -> sigma ≈ 1.40
        k = 9 -> sigma ≈ 1.70

    Args:
        kernel_size (int): Dimension of the odd-sized square kernel (e.g., 3, 5, 7, 9).

    Returns:
        float: Computed sigma value.
    """
    return 0.3 * ((kernel_size - 1) * 0.5 - 1.0) + 0.8


def apply_gaussian_filter(
    image: np.ndarray,
    kernel_size: int = 5,
    sigma: Optional[float] = None,
) -> np.ndarray:
    """
    Applies Gaussian blur to an image using cv2.GaussianBlur.

    Args:
        image (np.ndarray): Input image array (uint8).
        kernel_size (int): Size of the square filter window. Must be positive and odd.
        sigma (Optional[float]): Standard deviation in both X and Y directions.
                                 If None, automatically computed via `compute_auto_sigma`.

    Returns:
        np.ndarray: Filtered smoothed image.

    Raises:
        ValueError: If kernel_size is non-positive or even.
    """
    if kernel_size <= 0 or kernel_size % 2 == 0:
        raise ValueError(
            f"Invalid kernel size {kernel_size}. Kernel size must be a positive odd integer (e.g. 3, 5, 7, 9)."
        )

    if sigma is None:
        sigma_val = compute_auto_sigma(kernel_size)
    else:
        sigma_val = float(sigma)

    # cv2.GaussianBlur performs separable convolution using border reflection
    filtered = cv2.GaussianBlur(
        image,
        ksize=(kernel_size, kernel_size),
        sigmaX=sigma_val,
        sigmaY=sigma_val,
        borderType=cv2.BORDER_REFLECT_101,
    )
    return filtered


def apply_multiple_kernels(
    image: np.ndarray,
    kernel_sizes: Optional[List[int]] = None,
    sigma_overrides: Optional[Dict[int, float]] = None,
) -> Dict[int, np.ndarray]:
    """
    Applies Gaussian filtering across multiple kernel sizes in a single execution.
    Defaults to the standard evaluation suite: [3, 5, 7, 9].

    Args:
        image (np.ndarray): Noisy or clean input image.
        kernel_sizes (Optional[List[int]]): List of odd kernel sizes. Defaults to [3, 5, 7, 9].
        sigma_overrides (Optional[Dict[int, float]]): Optional mapping from kernel_size to custom sigma.

    Returns:
        Dict[int, np.ndarray]: Dictionary mapping kernel_size -> filtered_image.
    """
    if kernel_sizes is None:
        kernel_sizes = [3, 5, 7, 9]

    results = {}
    for k in kernel_sizes:
        custom_sigma = None
        if sigma_overrides and k in sigma_overrides:
            custom_sigma = sigma_overrides[k]

        filtered = apply_gaussian_filter(image, kernel_size=k, sigma=custom_sigma)
        results[k] = filtered

    return results
