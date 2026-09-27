"""
Main Pipeline Orchestrator
==========================
Course: CS-305 Computer Vision Case Study
Title: Design and Analysis of a Gaussian Filter for Low-Pass Image Smoothing

Pipeline Flow:
Input Image -> Add Noise -> Gaussian Filtering -> Evaluate (MSE/PSNR) -> Visualize/Export

This script orchestrates the end-to-end execution of all 6 Functional Requirements:
- FR-1: Image discovery, validation, and loading (with synthetic fallback)
- FR-2: Reproducible Gaussian and Salt-and-Pepper noise injection
- FR-3: Multi-kernel 2D Gaussian filtering (3x3, 5x5, 7x7, 9x9) with auto/custom sigma
- FR-4: Side-by-side triptych & comprehensive visual comparisons
- FR-5: Quantitative MSE & PSNR evaluation and dual-panel performance curves
- FR-6: Systematic disk export of all resulting artifacts
"""

import sys
import time
import argparse
from pathlib import Path
from typing import List, Dict, Tuple

# Ensure src directory is on python module path regardless of invocation directory
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from image_loader import load_all_images
from noise_generator import add_gaussian_noise, add_salt_and_pepper_noise
from gaussian_filter import apply_multiple_kernels, compute_auto_sigma
from metrics import compute_mse, compute_psnr, print_metrics, plot_performance_graphs
from visualizer import (
    save_image_to_disk,
    create_triptych_comparison,
    create_multipanel_comparison,
)


def run_pipeline(
    data_dir: Path,
    output_dir: Path,
    noise_type: str = "gaussian",
    gaussian_mean: float = 0.0,
    gaussian_std: float = 25.0,
    sp_density: float = 0.02,
    kernel_sizes: List[int] = None,
    seed: int = 42,
) -> Dict[str, List[str]]:
    """
    Executes the end-to-end Gaussian filtering pipeline.

    Args:
        data_dir (Path): Directory containing input images.
        output_dir (Path): Root outputs directory.
        noise_type (str): 'gaussian' or 'salt_and_pepper'.
        gaussian_mean (float): Mean for Gaussian noise (default: 0.0).
        gaussian_std (float): Standard deviation for Gaussian noise (default: 25.0).
        sp_density (float): Density for salt-and-pepper noise (default: 0.02).
        kernel_sizes (List[int]): List of kernel sizes (default: [3, 5, 7, 9]).
        seed (int): Seed for reproducible noise generation.

    Returns:
        Dict[str, List[str]]: Summary of all generated file paths.
    """
    if kernel_sizes is None:
        kernel_sizes = [3, 5, 7, 9]

    # Create designated output directories per FR-6
    filtered_dir = output_dir / "filtered_images"
    comparison_dir = output_dir / "comparison_images"
    graphs_dir = output_dir / "performance_graphs"

    for d in (filtered_dir, comparison_dir, graphs_dir):
        d.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("CS-305: Gaussian Filter Low-Pass Image Smoothing Pipeline")
    print("=" * 70)
    print(f"Data Source       : {data_dir.resolve()}")
    print(f"Output Directory  : {output_dir.resolve()}")
    print(f"Noise Profile     : {noise_type.upper()}")
    print(f"Evaluation Kernels: {kernel_sizes}")
    print(f"Random Seed       : {seed}")
    print("-" * 70)

    # -------------------------------------------------------------
    # Step 1: Image Upload / Loading (FR-1)
    # -------------------------------------------------------------
    print("\n[STEP 1/5] Loading Input Dataset...")
    images = load_all_images(data_dir, auto_generate_synthetic=True)
    if not images:
        print("[ABORT] No images available to process.")
        return {}

    print(f"[INFO] Successfully loaded {len(images)} image(s) for processing.")

    exported_files = {
        "filtered": [],
        "comparisons": [],
        "graphs": [],
    }

    total_pipeline_start = time.perf_counter()

    # -------------------------------------------------------------
    # Process each image through the pipeline
    # -------------------------------------------------------------
    for idx, (img_filename, original_img) in enumerate(images, start=1):
        img_stem = Path(img_filename).stem
        print("\n" + "=" * 55)
        print(f"Processing Image [{idx}/{len(images)}]: {img_filename}")
        print("=" * 55)

        img_start_time = time.perf_counter()
        cv_start_time = time.perf_counter()

        # ---------------------------------------------------------
        # Step 2: Add Noise (FR-2)
        # ---------------------------------------------------------
        print(f"\n>> Step 2: Injecting {noise_type} noise (seed={seed})...")
        if noise_type.lower() == "gaussian":
            noisy_img = add_gaussian_noise(
                original_img, mean=gaussian_mean, std=gaussian_std, seed=seed
            )
            noise_label = f"Gaussian (mean={gaussian_mean}, std={gaussian_std})"
        elif noise_type.lower() in ["salt_and_pepper", "sp", "impulse"]:
            noisy_img = add_salt_and_pepper_noise(
                original_img, density=sp_density, seed=seed
            )
            noise_label = f"Salt-and-Pepper ({sp_density * 100:.1f}%)"
        else:
            raise ValueError(f"Unknown noise type: {noise_type}")

        # Compute Baseline Metrics for Noisy Image
        noisy_mse = compute_mse(original_img, noisy_img)
        noisy_psnr = compute_psnr(original_img, noisy_img)

        # Print noisy metrics strictly in specified format
        print_metrics(f"{img_filename} - Initial Noisy Input", noisy_mse, noisy_psnr)

        # ---------------------------------------------------------
        # Step 3: Gaussian Filtering across Kernels (FR-3)
        # ---------------------------------------------------------
        print(f"\n>> Step 3: Applying Gaussian Filtering for kernels {kernel_sizes}...")
        filtered_dict = apply_multiple_kernels(noisy_img, kernel_sizes=kernel_sizes)

        # ---------------------------------------------------------
        # Step 4: Quantitative Evaluation (FR-5)
        # ---------------------------------------------------------
        print("\n>> Step 4: Computing Quantitative Metrics (MSE & PSNR)...")
        metrics_dict: Dict[int, Tuple[float, float]] = {}
        mse_list: List[float] = []
        psnr_list: List[float] = []

        for k in kernel_sizes:
            f_img = filtered_dict[k]
            f_mse = compute_mse(original_img, f_img)
            f_psnr = compute_psnr(original_img, f_img)
            metrics_dict[k] = (f_mse, f_psnr)
            mse_list.append(f_mse)
            psnr_list.append(f_psnr)

            sigma_used = compute_auto_sigma(k)
            label = f"Kernel {k}x{k} (sigma={sigma_used:.2f})"
            print_metrics(label, f_mse, f_psnr)

        cv_elapsed = time.perf_counter() - cv_start_time

        # ---------------------------------------------------------
        # Step 5: Visualizations & Artifact Export (FR-4 & FR-6)
        # ---------------------------------------------------------
        print("\n>> Step 5: Generating Visualizations and Exporting Artifacts...")
        vis_start_time = time.perf_counter()

        # 5a. Save all individual filtered images (FR-6)
        for k in kernel_sizes:
            filtered_filename = f"{img_stem}_kernel{k}x{k}_filtered.png"
            filtered_path = filtered_dir / filtered_filename
            save_image_to_disk(filtered_dict[k], filtered_path)
            exported_files["filtered"].append(str(filtered_path.resolve()))
            print(f"    [SAVED] Filtered Image: {filtered_filename}")

        # 5b. Save individual side-by-side triptych (Original -> Noisy -> Filtered) for 5x5 (FR-4)
        triptych_filename = f"{img_stem}_comparison_kernel5x5.png"
        triptych_path = comparison_dir / triptych_filename
        create_triptych_comparison(
            original=original_img,
            noisy=noisy_img,
            filtered=filtered_dict[5],
            kernel_size=5,
            metrics_noisy=(noisy_mse, noisy_psnr),
            metrics_filtered=metrics_dict[5],
            title_prefix=img_stem,
            save_path=triptych_path,
        )
        exported_files["comparisons"].append(str(triptych_path.resolve()))
        print(f"    [SAVED] Side-by-Side (FR-4): {triptych_filename}")

        # 5c. Save comprehensive multi-panel comparison (Original, Noisy, 3x3, 5x5, 7x7, 9x9)
        multipanel_filename = f"{img_stem}_all_kernels_comparison.png"
        multipanel_path = comparison_dir / multipanel_filename
        create_multipanel_comparison(
            original=original_img,
            noisy=noisy_img,
            filtered_dict=filtered_dict,
            metrics_dict=metrics_dict,
            noisy_metrics=(noisy_mse, noisy_psnr),
            title_prefix=img_stem,
            save_path=multipanel_path,
        )
        exported_files["comparisons"].append(str(multipanel_path.resolve()))
        print(f"    [SAVED] Multi-Kernel Comparison: {multipanel_filename}")

        # 5d. Save dual-panel performance curves (Kernel Size vs MSE, Kernel Size vs PSNR) (FR-5)
        graph_filename = f"{img_stem}_performance_graph.png"
        graph_path = graphs_dir / graph_filename
        plot_performance_graphs(
            kernel_sizes=kernel_sizes,
            mse_values=mse_list,
            psnr_values=psnr_list,
            baseline_mse=noisy_mse,
            baseline_psnr=noisy_psnr,
            image_name=img_stem,
            noise_type=noise_type.capitalize(),
            save_path=graph_path,
        )
        exported_files["graphs"].append(str(graph_path.resolve()))
        print(f"    [SAVED] Performance Curves (FR-5): {graph_filename}")

        vis_elapsed = time.perf_counter() - vis_start_time

        print("\n" + "-" * 55)
        print("Performance Benchmark:")
        cv_status = "PASSED" if cv_elapsed < 2.0 else "FAILED"
        print(f"  • Core Denoising Time      : {cv_elapsed:.4f} s (Target: < 2.0s) -> {cv_status}")
        print(f"  • Visualization/Export Time: {vis_elapsed:.4f} s (Non-core I/O)")
        print("-" * 55)

    total_pipeline_time = time.perf_counter() - total_pipeline_start
    print("\n" + "=" * 70)
    print("PIPELINE EXECUTION COMPLETE")
    print(f"Total Images Processed : {len(images)}")
    print(f"Total Execution Time   : {total_pipeline_time:.2f} seconds")
    print(f"Average Time Per Image : {total_pipeline_time / len(images):.3f} seconds")
    print("=" * 70)
    print(f"\nGenerated Artifacts Summary:")
    print(f" - Filtered Images     : {len(exported_files['filtered'])} files in {filtered_dir}")
    print(f" - Comparison Plots    : {len(exported_files['comparisons'])} files in {comparison_dir}")
    print(f" - Performance Graphs  : {len(exported_files['graphs'])} files in {graphs_dir}")

    return exported_files


def main():
    """CLI entrypoint parsing parameters and triggering the pipeline."""
    parser = argparse.ArgumentParser(
        description="Design and Analysis of a Gaussian Filter for Low-Pass Image Smoothing (CS-305)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=str(PROJECT_ROOT / "data" / "sample_images"),
        help="Path to folder containing source images (.jpg, .jpeg, .png)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(PROJECT_ROOT / "outputs"),
        help="Path to root outputs folder",
    )
    parser.add_argument(
        "--noise-type",
        type=str,
        choices=["gaussian", "salt_and_pepper"],
        default="gaussian",
        help="Type of noise to corrupt images with",
    )
    parser.add_argument(
        "--gaussian-std",
        type=float,
        default=25.0,
        help="Standard deviation for Gaussian noise",
    )
    parser.add_argument(
        "--sp-density",
        type=float,
        default=0.02,
        help="Corrupted pixel density fraction for Salt-and-Pepper noise",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic noise generation",
    )

    args = parser.parse_args()

    run_pipeline(
        data_dir=Path(args.data_dir),
        output_dir=Path(args.output_dir),
        noise_type=args.noise_type,
        gaussian_std=args.gaussian_std,
        sp_density=args.sp_density,
        kernel_sizes=[3, 5, 7, 9],
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
