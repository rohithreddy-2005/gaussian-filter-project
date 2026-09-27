"""
Noise Generation Module (FR-2)
==============================
Provides functions to inject synthetic degradation into clean images:
1. Additive White Gaussian Noise (AWGN): models sensor noise and thermal variations.
2. Salt-and-Pepper (Impulse) Noise: models transmission bit errors and dead/saturated pixels.

Both functions support reproducible pseudo-random generation via configurable seeds.
"""

from typing import Optional
import numpy as np


def add_gaussian_noise(
    image: np.ndarray,
    mean: float = 0.0,
    std: float = 25.0,
    seed: Optional[int] = 42,
) -> np.ndarray:
    """
    Adds Additive White Gaussian Noise (AWGN) to an image.

    The noise is modeled as:
        I_noisy(x, y) = I_clean(x, y) + N(mean, std^2)
    where pixel values are clipped to [0, 255] and converted back to uint8.

    Args:
        image (np.ndarray): Original image (2D grayscale or 3D color, uint8).
        mean (float): Mean of the normal distribution (default: 0.0).
        std (float): Standard deviation of the normal distribution (default: 25.0).
        seed (Optional[int]): Random seed for reproducible experiments (default: 42).

    Returns:
        np.ndarray: Noisy image with identical shape and dtype uint8.
    """
    if seed is not None:
        rng = np.random.default_rng(seed)
    else:
        rng = np.random.default_rng()

    # Generate Gaussian noise matching image shape
    noise = rng.normal(loc=mean, scale=std, size=image.shape)

    # Add noise in floating point space to prevent 8-bit wrap-around / overflow
    noisy_float = image.astype(np.float32) + noise

    # Clip values into valid [0, 255] dynamic range and cast back to uint8
    noisy_uint8 = np.clip(noisy_float, 0, 255).astype(np.uint8)
    return noisy_uint8


def add_salt_and_pepper_noise(
    image: np.ndarray,
    density: float = 0.02,
    salt_vs_pepper: float = 0.5,
    seed: Optional[int] = 42,
) -> np.ndarray:
    """
    Adds Salt-and-Pepper (Impulse) Noise to an image.

    Randomly alters a fraction of pixels equal to `density`:
    - 'Salt' noise sets the pixel intensity to maximum (255 - white).
    - 'Pepper' noise sets the pixel intensity to minimum (0 - black).

    Args:
        image (np.ndarray): Original image (2D or 3D, uint8).
        density (float): Total fraction of corrupted pixels in [0.0, 1.0] (default: 0.02, i.e., 2%).
        salt_vs_pepper (float): Ratio of salt (white) vs pepper (black) pixels (default: 0.5).
        seed (Optional[int]): Random seed for reproducibility (default: 42).

    Returns:
        np.ndarray: Corrupted image with salt-and-pepper noise (uint8).
    """
    if not (0.0 <= density <= 1.0):
        raise ValueError(f"Density must be between 0.0 and 1.0, got {density}")
    if not (0.0 <= salt_vs_pepper <= 1.0):
        raise ValueError(f"salt_vs_pepper must be between 0.0 and 1.0, got {salt_vs_pepper}")

    if seed is not None:
        rng = np.random.default_rng(seed)
    else:
        rng = np.random.default_rng()

    noisy = image.copy()
    h, w = image.shape[:2]
    total_pixels = h * w
    num_noisy = int(total_pixels * density)

    # Randomly select pixel coordinates across spatial dimensions
    coords_y = rng.integers(0, h, size=num_noisy)
    coords_x = rng.integers(0, w, size=num_noisy)

    num_salt = int(num_noisy * salt_vs_pepper)

    # First partition receives Salt (255)
    salt_y = coords_y[:num_salt]
    salt_x = coords_x[:num_salt]
    if image.ndim == 3:
        noisy[salt_y, salt_x, :] = 255
    else:
        noisy[salt_y, salt_x] = 255

    # Second partition receives Pepper (0)
    pepper_y = coords_y[num_salt:]
    pepper_x = coords_x[num_salt:]
    if image.ndim == 3:
        noisy[pepper_y, pepper_x, :] = 0
    else:
        noisy[pepper_y, pepper_x] = 0

    return noisy
