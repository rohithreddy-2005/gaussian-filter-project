"""
Image Loader Module (FR-1)
==========================
Responsible for loading images (.jpg, .jpeg, .png) from a given folder path,
handling missing or corrupt files safely, providing visual previews, and generating
synthetic images if no real images are present.
"""

import os
from pathlib import Path
from typing import List, Tuple, Optional
import cv2
import numpy as np
import matplotlib.pyplot as plt

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def load_image(file_path: str | Path, as_rgb: bool = True) -> np.ndarray:
    """
    Loads a single image from a local file path with robust error handling.

    Args:
        file_path (str | Path): Full path to the image file.
        as_rgb (bool): If True, converts OpenCV BGR format to RGB format.

    Returns:
        np.ndarray: Loaded image as a uint8 NumPy array.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If file format is not supported or image cannot be decoded.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image file not found: {path.resolve()}")

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format '{path.suffix}'. "
            f"Supported extensions: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    # cv2.imread does not raise exceptions for corrupt/unreadable files; it returns None
    img_bgr = cv2.imread(str(path.resolve()))
    if img_bgr is None:
        raise ValueError(f"Failed to decode image (corrupt or unreadable): {path.resolve()}")

    if as_rgb:
        return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    return img_bgr


def preview_image(image: np.ndarray, title: str = "Image Preview", block: bool = True) -> None:
    """
    Displays an image preview using Matplotlib.

    Args:
        image (np.ndarray): Image array to display.
        title (str): Title for the display window.
        block (bool): Whether matplotlib.pyplot.show blocks execution.
    """
    plt.figure(figsize=(6, 6))
    if image.ndim == 2:
        plt.imshow(image, cmap="gray")
    else:
        plt.imshow(image)
    plt.title(title, fontsize=12, fontweight="bold")
    plt.axis("off")
    plt.tight_layout()
    plt.show(block=block)


def generate_synthetic_images(target_dir: str | Path) -> List[str]:
    """
    Generates 3 synthetic placeholder images (512x512 RGB) with gradients,
    geometric shapes, and high-frequency textures for testing.

    Args:
        target_dir (str | Path): Directory where synthetic images will be saved.

    Returns:
        List[str]: File paths of the generated images.
    """
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)
    created_paths = []

    # 1. Geometric Shapes on Colored Background
    img1 = np.full((512, 512, 3), 235, dtype=np.uint8)
    # Draw blue rectangle
    cv2.rectangle(img1, (60, 60), (220, 220), (30, 100, 220), -1)
    # Draw green circle
    cv2.circle(img1, (360, 150), 90, (40, 180, 80), -1)
    # Draw red triangle
    pts = np.array([[120, 440], [260, 280], [400, 440]], np.int32)
    cv2.fillPoly(img1, [pts], (220, 50, 50))
    # Draw yellow diagonal lines
    cv2.line(img1, (30, 480), (480, 30), (255, 200, 0), 4)
    cv2.putText(
        img1, "CS-305 Test Shapes", (120, 40),
        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (20, 20, 20), 2, cv2.LINE_AA
    )
    p1 = target_path / "synthetic_shapes.png"
    cv2.imwrite(str(p1), cv2.cvtColor(img1, cv2.COLOR_RGB2BGR))
    created_paths.append(str(p1))

    # 2. Smooth Radial & Linear Gradient with Rings
    y, x = np.ogrid[:512, :512]
    # Linear gradient in X
    grad_x = (x / 512.0) * 200
    # Linear gradient in Y
    grad_y = (y / 512.0) * 200
    # Radial distance from center
    center_dist = np.sqrt((x - 256) ** 2 + (y - 256) ** 2)
    ring_pattern = (np.sin(center_dist / 15.0) + 1.0) * 25.0

    r_channel = np.clip(grad_x + ring_pattern, 0, 255).astype(np.uint8)
    g_channel = np.clip(grad_y + ring_pattern, 0, 255).astype(np.uint8)
    b_channel = np.clip(255 - (grad_x * 0.5 + grad_y * 0.5), 0, 255).astype(np.uint8)
    img2 = np.stack([r_channel, g_channel, b_channel], axis=-1)
    cv2.putText(
        img2, "Synthetic Gradient", (130, 260),
        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA
    )
    p2 = target_path / "synthetic_gradient.png"
    cv2.imwrite(str(p2), cv2.cvtColor(img2, cv2.COLOR_RGB2BGR))
    created_paths.append(str(p2))

    # 3. High-Frequency Checkerboard and Grid Textures
    img3 = np.zeros((512, 512, 3), dtype=np.uint8)
    block_size = 32
    for r in range(0, 512, block_size):
        for c in range(0, 512, block_size):
            if (r // block_size + c // block_size) % 2 == 0:
                img3[r : r + block_size, c : c + block_size] = [210, 210, 210]
            else:
                img3[r : r + block_size, c : c + block_size] = [45, 65, 120]
    # Overlay high-contrast fine grid in the center
    img3[180:332, 180:332] = 255
    cv2.rectangle(img3, (180, 180), (332, 332), (0, 0, 255), 3)
    cv2.putText(
        img3, "Checkerboard", (195, 265),
        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2, cv2.LINE_AA
    )
    p3 = target_path / "synthetic_checkerboard.png"
    cv2.imwrite(str(p3), cv2.cvtColor(img3, cv2.COLOR_RGB2BGR))
    created_paths.append(str(p3))

    return created_paths


def load_all_images(
    folder_path: str | Path, auto_generate_synthetic: bool = True
) -> List[Tuple[str, np.ndarray]]:
    """
    Discovers and loads all supported images (.jpg, .jpeg, .png) from a directory.
    If the directory is empty and auto_generate_synthetic is True, generates
    synthetic placeholder images and returns them.

    Args:
        folder_path (str | Path): Folder containing candidate images.
        auto_generate_synthetic (bool): Whether to auto-create synthetic images if empty.

    Returns:
        List[Tuple[str, np.ndarray]]: List of (image_filename, rgb_numpy_array).
    """
    folder = Path(folder_path)
    if not folder.exists():
        folder.mkdir(parents=True, exist_ok=True)

    image_files = [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    # Handle empty folder condition
    if not image_files:
        if auto_generate_synthetic:
            print(f"[INFO] No images found in '{folder}'. Generating 3 synthetic test images...")
            created = generate_synthetic_images(folder)
            image_files = [Path(p) for p in created]
        else:
            print(f"[WARNING] No valid images found in directory: {folder}")
            return []

    loaded_images = []
    for f in sorted(image_files):
        try:
            img = load_image(f, as_rgb=True)
            loaded_images.append((f.name, img))
            print(f"[LOADED] {f.name} - Shape: {img.shape}, Type: {img.dtype}")
        except Exception as e:
            print(f"[ERROR] Skipping file '{f.name}': {e}")

    return loaded_images
