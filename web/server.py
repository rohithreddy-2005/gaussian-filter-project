"""
Interactive Gaussian Filter Web Application Server
==================================================
Course: CS-305 Computer Vision Case Study
Provides an interactive localhost web interface to upload images, configure
noise and kernel parameters in real time, view side-by-side visual comparisons,
run educational convolution animations, inspect kernel weights and frequency
spectra, and analyze quantitative MSE & PSNR metrics.

Features:
- Real-time Gaussian and Salt-and-Pepper noise injection
- Multi-kernel Gaussian low-pass filtering (3x3, 5x5, 7x7, 9x9)
- Exact mathematical evaluation of MSE and PSNR adhering to CS-305 formulas
- Real 12x12 patch extraction with backend-matched convolution verification
- 2D FFT magnitude spectrum generation
- Absolute difference error heatmaps
- 1D Scanline intensity profile extraction
- Optimized on-screen preview downscaling for ultra-large (e.g. 4000x6000) images
  while computing benchmarks and metrics on full-resolution arrays
"""

import os
import sys
import json
import base64
import io
import time
import mimetypes
import urllib.parse
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Dict, Any, List, Optional, Tuple

# Reconfigure stdout/stderr for Unicode safety on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import cv2
import numpy as np
import matplotlib
# Headless Agg backend for matplotlib in server environment
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Ensure src modules are resolvable
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
STATIC_DIR = CURRENT_DIR / "static"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from image_loader import load_image, load_all_images, SUPPORTED_EXTENSIONS
from noise_generator import (
    DEFAULT_GAUSSIAN_STD,
    add_gaussian_noise,
    add_salt_and_pepper_noise,
)
from gaussian_filter import apply_gaussian_filter, apply_multiple_kernels, compute_auto_sigma
from metrics import compute_mse, compute_psnr, plot_performance_graphs
from visualizer import (
    save_image_to_disk,
    create_triptych_comparison,
    create_multipanel_comparison,
)

DATA_DIR = PROJECT_ROOT / "data" / "sample_images"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

# In-memory cache of latest processed images to serve fast patch and scanline requests
ACTIVE_SESSION = {
    "original": None,
    "noisy": None,
    "filtered_dict": {},
    "filename": "sample1_clean.png",
    "optimal_kernel": 5,
    "noise_type": "gaussian",
    "seed": 42,
}


def get_kernel_weights(kernel_size: int, sigma: Optional[float] = None) -> Tuple[float, List[List[float]]]:
    """Computes normalized 2D Gaussian kernel weights using cv2.getGaussianKernel (backend ground truth)."""
    if sigma is None:
        sigma = compute_auto_sigma(kernel_size)
    k1d = cv2.getGaussianKernel(kernel_size, sigma)
    k2d = k1d @ k1d.T
    return float(sigma), k2d.tolist()


def get_detailed_kernel_info(kernel_size: int, sigma: Optional[float] = None) -> Dict[str, Any]:
    """Provides complete 1D, 2D, raw, and normalized weights computed via OpenCV."""
    if sigma is None:
        sigma = compute_auto_sigma(kernel_size)
    k1d = cv2.getGaussianKernel(kernel_size, sigma)
    k2d = k1d @ k1d.T

    # Raw unnormalized exponential values for Step 3 demonstration
    ax = np.arange(-kernel_size // 2 + 1.0, kernel_size // 2 + 1.0)
    xx, yy = np.meshgrid(ax, ax)
    raw_k2d = np.exp(-(xx**2 + yy**2) / (2.0 * sigma**2))
    sum_raw = float(np.sum(raw_k2d))

    rad = kernel_size // 2
    return {
        "kernel_size": kernel_size,
        "sigma": round(float(sigma), 3),
        "k1d": [round(float(w), 4) for w in k1d.ravel()],
        "weights_1d": [round(float(w), 4) for w in k1d.ravel()],
        "k2d": k2d.tolist(),
        "weights_2d": k2d.tolist(),
        "weights_2d_rounded": [[round(float(c), 4) for c in row] for row in k2d],
        "raw_k2d": [[round(float(c), 4) for c in row] for row in raw_k2d],
        "raw_2d": [[round(float(c), 4) for c in row] for row in raw_k2d],
        "sum_raw": round(sum_raw, 4),
        "raw_sum": round(sum_raw, 4),
        "sum_normalized": "1.0000",
        "center_1d": round(float(k1d[rad, 0]), 4),
        "center_2d": round(float(k2d[rad, rad]), 4),
        "center_weight": round(float(k2d[rad, rad]), 4),
        "corner_weight": round(float(k2d[0, 0]), 4),
        "opencv_aligned": True,
    }




def compute_fft_spectrum(img_rgb: np.ndarray) -> str:
    """Computes log-scaled 2D FFT magnitude spectrum colored with INFERNO colormap."""
    if img_rgb.ndim == 3:
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_rgb
    f = np.fft.fft2(gray.astype(np.float32))
    fshift = np.fft.fftshift(f)
    magnitude = 20 * np.log(np.abs(fshift) + 1.0)
    norm = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    colored_bgr = cv2.applyColorMap(norm, cv2.COLORMAP_INFERNO)
    colored_rgb = cv2.cvtColor(colored_bgr, cv2.COLOR_BGR2RGB)
    return numpy_to_base64_png(colored_rgb)


def compute_error_heatmap(original_rgb: np.ndarray, filtered_rgb: np.ndarray, gain: float = 4.0) -> str:
    """Computes pixel-by-pixel absolute difference |Original - Filtered| with TURBO colormap."""
    diff = np.abs(original_rgb.astype(np.float32) - filtered_rgb.astype(np.float32))
    if diff.ndim == 3:
        diff_mag = np.mean(diff, axis=-1)
    else:
        diff_mag = diff
    amplified = np.clip(diff_mag * gain, 0, 255).astype(np.uint8)
    heatmap_bgr = cv2.applyColorMap(amplified, cv2.COLORMAP_TURBO)
    heatmap_rgb = cv2.cvtColor(heatmap_bgr, cv2.COLOR_BGR2RGB)
    return numpy_to_base64_png(heatmap_rgb)


def extract_patch_bundle(
    clean_rgb: np.ndarray,
    noisy_rgb: Optional[np.ndarray] = None,
    x: int = 0,
    y: int = 0,
    patch_size: int = 8,
    kernel_sizes: Optional[List[int]] = None,
    noise_type: str = "gaussian",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """
    Extracts a patch_size x patch_size patch at (x, y) with clean, noisy, and noise delta grids,
    exact OpenCV Gaussian weights, BORDER_REFLECT_101 filtered patches, and corner verification.
    """
    if kernel_sizes is None:
        kernel_sizes = [3, 5, 7, 9]

    if noisy_rgb is None:
        noisy_rgb = clean_rgb.copy()

    h, w = clean_rgb.shape[:2]
    # Clamp top-left origin
    x0 = max(0, min(w - patch_size, x))
    y0 = max(0, min(h - patch_size, y))

    patch_clean_rgb = clean_rgb[y0 : y0 + patch_size, x0 : x0 + patch_size]
    patch_noisy_rgb = noisy_rgb[y0 : y0 + patch_size, x0 : x0 + patch_size]

    def split_rgb(p):
        if p.ndim == 3:
            r = p[:, :, 0].tolist()
            g = p[:, :, 1].tolist()
            b = p[:, :, 2].tolist()
            gray = cv2.cvtColor(p, cv2.COLOR_RGB2GRAY).tolist()
            return {"r": r, "g": g, "b": b, "luma": gray}
        else:
            gray = p.tolist()
            return {"r": gray, "g": gray, "b": gray, "luma": gray}

    clean_chans = split_rgb(patch_clean_rgb)
    noisy_chans = split_rgb(patch_noisy_rgb)

    # Compute actual noise delta array (signed integers: Noisy - Clean)
    noise_vals = []
    clipped_pixels = []
    for r in range(patch_size):
        row_deltas = []
        for c in range(patch_size):
            c_val = clean_chans["luma"][r][c]
            n_val = noisy_chans["luma"][r][c]
            delta = n_val - c_val
            row_deltas.append(delta)

            # Check if clipping occurred
            if n_val == 255 and c_val + delta >= 255 and (delta > 0 or c_val == 255):
                clipped_pixels.append({
                    "r": r, "c": c, "clean": c_val, "noise": delta,
                    "raw_sum": c_val + delta, "clipped": 255, "type": "upper"
                })
            elif n_val == 0 and c_val + delta <= 0 and (delta < 0 or c_val == 0):
                clipped_pixels.append({
                    "r": r, "c": c, "clean": c_val, "noise": delta,
                    "raw_sum": c_val + delta, "clipped": 0, "type": "lower"
                })
        noise_vals.append(row_deltas)

    # Compute backend filtered patches on noisy luma patch
    noisy_luma_arr = np.array(noisy_chans["luma"], dtype=np.uint8)
    backend_filtered = {}
    kernel_matrices = {}
    kernel_sigmas = {}
    detailed_kernels = {}
    corner_verification = {}

    for k in kernel_sizes:
        sigma = compute_auto_sigma(k)
        info = get_detailed_kernel_info(k, sigma)
        detailed_kernels[k] = info
        kernel_matrices[k] = info["k2d"]
        kernel_sigmas[k] = info["sigma"]

        # Apply cv2.GaussianBlur on noisy luma patch using BORDER_REFLECT_101
        filtered_patch = cv2.GaussianBlur(
            noisy_luma_arr, (k, k), sigmaX=sigma, sigmaY=sigma, borderType=cv2.BORDER_REFLECT_101
        )
        backend_filtered[k] = filtered_patch.tolist()

        # Corner reflection verification: corner (0, 0)
        rad = k // 2
        k2d_np = np.array(info["k2d"])
        padded = cv2.copyMakeBorder(noisy_luma_arr, rad, rad, rad, rad, cv2.BORDER_REFLECT_101)
        manual_corner = int(round(float(np.sum(padded[0:k, 0:k].astype(float) * k2d_np))))
        cv_corner = int(filtered_patch[0, 0])
        c_verif = {
            "manual": manual_corner,
            "backend": cv_corner,
            "cv2": cv_corner,
            "diff": abs(manual_corner - cv_corner),
            "matches": abs(manual_corner - cv_corner) <= 1,
        }
        corner_verification[k] = c_verif
        corner_verification[f"k_{k}"] = c_verif

    # Step 5 Part A: 4 representative real pixel pairs (clean vs filtered)
    sample_coords = [
        (1, 1),
        (1, min(6, patch_size - 2)),
        (min(6, patch_size - 2), 1),
        (min(6, patch_size - 2), min(6, patch_size - 2))
    ]
    sample_4_pixels = []
    opt_k = 5 if 5 in backend_filtered else kernel_sizes[0]
    for r, c in sample_coords:
        clean_v = clean_chans["luma"][r][c]
        filt_v = backend_filtered[opt_k][r][c]
        diff = clean_v - filt_v
        sample_4_pixels.append({
            "r": r,
            "c": c,
            "clean": clean_v,
            "filtered": filt_v,
            "diff": diff,
            "diff_sq": diff ** 2,
        })

    return {
        "origin": {"x": int(x0), "y": int(y0)},
        "patch_size": patch_size,
        "noise_type": noise_type,
        "seed": seed,
        "clean": clean_chans,
        "noisy": noisy_chans,
        "channels": noisy_chans,
        "channels_clean": clean_chans,
        "channels_noise": {"luma": noise_vals},
        "noise_vals": noise_vals,
        "clipping": {
            "has_clipping": len(clipped_pixels) > 0,
            "total_clipped": len(clipped_pixels),
            "sample_clipped": clipped_pixels[0] if clipped_pixels else None,
        },
        "clipped_pixels": clipped_pixels,
        "tiny_eval_samples": sample_4_pixels,
        "sample_4_pixels": sample_4_pixels,
        "backend_filtered": backend_filtered,
        "kernel_matrices": kernel_matrices,
        "kernel_sigmas": kernel_sigmas,
        "detailed_kernels": detailed_kernels,
        "corner_verification": corner_verification,
    }


def extract_scanline(orig_rgb: np.ndarray, noisy_rgb: np.ndarray, filt_rgb: np.ndarray, row_y: int, max_points: int = 500) -> Dict[str, Any]:
    """Extracts 1D luminance profile across a chosen row."""
    h, w = orig_rgb.shape[:2]
    row_y = max(0, min(h - 1, row_y))

    def get_row_luma(img):
        if img.ndim == 3:
            row = cv2.cvtColor(img[row_y : row_y + 1, :], cv2.COLOR_RGB2GRAY)[0]
        else:
            row = img[row_y]
        return row

    row_orig = get_row_luma(orig_rgb)
    row_noisy = get_row_luma(noisy_rgb)
    row_filt = get_row_luma(filt_rgb)

    # Downsample points evenly if wider than max_points to keep JSON compact
    if w > max_points:
        indices = np.linspace(0, w - 1, max_points, dtype=int)
        x_coords = indices.tolist()
        val_orig = [float(row_orig[i]) for i in indices]
        val_noisy = [float(row_noisy[i]) for i in indices]
        val_filt = [float(row_filt[i]) for i in indices]
    else:
        x_coords = list(range(w))
        val_orig = [float(v) for v in row_orig]
        val_noisy = [float(v) for v in row_noisy]
        val_filt = [float(v) for v in row_filt]

    return {
        "row_index": row_y,
        "width": w,
        "x_coords": x_coords,
        "original": val_orig,
        "noisy": val_noisy,
        "filtered": val_filt,
    }


def make_preview_image(img: np.ndarray, max_dim: int = 1280) -> np.ndarray:
    """Downscales large images for on-screen preview ONLY, ensuring 60fps responsiveness."""
    h, w = img.shape[:2]
    if max(h, w) <= max_dim:
        return img
    scale = max_dim / max(h, w)
    new_w, new_h = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)


def numpy_to_base64_png(img_rgb: np.ndarray) -> str:
    """Encodes an RGB numpy array to a Base64 data URL PNG string."""
    if img_rgb.ndim == 3:
        bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    else:
        bgr = img_rgb
    success, buffer = cv2.imencode(".png", bgr)
    if not success:
        raise ValueError("Failed to encode image to PNG format")
    b64_str = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"


def base64_to_rgb_numpy(b64_str: str) -> np.ndarray:
    """Decodes a Base64 image string to an RGB numpy array."""
    if "," in b64_str:
        b64_str = b64_str.split(",", 1)[1]
    raw_bytes = base64.b64decode(b64_str)
    nparr = np.frombuffer(raw_bytes, np.uint8)
    bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("Could not decode image from provided payload.")
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def fig_to_base64_png(fig: plt.Figure, dpi: int = 140) -> str:
    """Encodes a Matplotlib Figure directly into a Base64 PNG data URL."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    b64_str = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Multi-threaded HTTP Server handling concurrent requests gracefully."""
    daemon_threads = True
    allow_reuse_address = True


class GaussianFilterRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler supporting static asset delivery and REST APIs."""

    def log_message(self, format: str, *args: Any) -> None:
        """Safe log message formatting that handles variable argument counts without crashing."""
        try:
            msg = format % args
        except Exception:
            msg = " ".join(str(a) for a in args)
        sys.stdout.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")

    def send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # Static assets
        if path in ("/", "/index.html"):
            self.serve_file(STATIC_DIR / "index.html", "text/html")
        elif path == "/styles.css":
            self.serve_file(STATIC_DIR / "styles.css", "text/css")
        elif path == "/app.js":
            self.serve_file(STATIC_DIR / "app.js", "application/javascript")

        # API Endpoints
        elif path == "/api/health":
            self.send_json({
                "status": "online",
                "course": "CS-305 Computer Vision",
                "title": "Gaussian Filter for Low-Pass Image Smoothing",
                "python_version": sys.version,
                "opencv_version": cv2.__version__,
                "numpy_version": np.__version__,
            })
        elif path == "/api/samples":
            self.handle_get_samples()
        elif path == "/api/sample-image":
            self.handle_get_sample_image(query)
        elif path == "/api/gallery":
            self.handle_get_gallery()
        elif path == "/api/output-file":
            self.handle_get_output_file(query)
        else:
            self.send_error(404, f"File or endpoint not found: {path}")

    def do_POST(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == "/api/process":
            self.handle_post_process()
        elif path == "/api/patch":
            self.handle_post_patch()
        elif path == "/api/scanline":
            self.handle_post_scanline()
        elif path == "/api/batch-process":
            self.handle_post_batch_process()
        else:
            self.send_error(404, f"Endpoint not found: {path}")

    def serve_file(self, file_path: Path, content_type: Optional[str] = None) -> None:
        if not file_path.is_file():
            self.send_error(404, f"File not found: {file_path.name}")
            return

        if not content_type:
            content_type, _ = mimetypes.guess_type(str(file_path))
            content_type = content_type or "application/octet-stream"

        try:
            with open(file_path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_error(500, f"Error reading file: {e}")

    def send_json(self, data: Any, status: int = 200) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(payload)

    def handle_get_samples(self) -> None:
        """Returns list of all available sample images in data/sample_images/."""
        if not DATA_DIR.exists():
            self.send_json([])
            return

        samples = []
        for file in sorted(DATA_DIR.iterdir()):
            if file.is_file() and file.suffix.lower() in SUPPORTED_EXTENSIONS:
                size_kb = round(file.stat().st_size / 1024, 1)
                samples.append({
                    "name": file.name,
                    "stem": file.stem,
                    "size_kb": size_kb,
                    "extension": file.suffix.lower(),
                    "url": f"/api/sample-image?name={urllib.parse.quote(file.name)}",
                })
        self.send_json(samples)

    def handle_get_sample_image(self, query: Dict[str, List[str]]) -> None:
        name_list = query.get("name")
        if not name_list:
            self.send_error(400, "Missing 'name' query parameter.")
            return

        filename = Path(name_list[0]).name
        file_path = DATA_DIR / filename
        self.serve_file(file_path)

    def handle_get_gallery(self) -> None:
        """Discovers all outputs generated by previous runs grouped by image identifier."""
        results_by_stem: Dict[str, Dict[str, Any]] = {}

        # 1. Comparison images
        comp_dir = OUTPUT_DIR / "comparison_images"
        if comp_dir.exists():
            for f in comp_dir.glob("*.png"):
                if "_all_kernels_comparison" in f.name:
                    stem = f.name.replace("_all_kernels_comparison.png", "")
                    if stem not in results_by_stem:
                        results_by_stem[stem] = {"stem": stem, "filtered": {}}
                    results_by_stem[stem]["all_kernels_url"] = (
                        f"/api/output-file?folder=comparison_images&file={urllib.parse.quote(f.name)}"
                    )
                elif "_comparison_kernel5x5" in f.name:
                    stem = f.name.replace("_comparison_kernel5x5.png", "")
                    if stem not in results_by_stem:
                        results_by_stem[stem] = {"stem": stem, "filtered": {}}
                    results_by_stem[stem]["triptych_url"] = (
                        f"/api/output-file?folder=comparison_images&file={urllib.parse.quote(f.name)}"
                    )

        # 2. Performance graphs
        graphs_dir = OUTPUT_DIR / "performance_graphs"
        if graphs_dir.exists():
            for f in graphs_dir.glob("*_performance_graph.png"):
                stem = f.name.replace("_performance_graph.png", "")
                if stem not in results_by_stem:
                    results_by_stem[stem] = {"stem": stem, "filtered": {}}
                results_by_stem[stem]["graph_url"] = (
                    f"/api/output-file?folder=performance_graphs&file={urllib.parse.quote(f.name)}"
                )

        # 3. Filtered images
        filtered_dir = OUTPUT_DIR / "filtered_images"
        if filtered_dir.exists():
            for f in filtered_dir.glob("*.png"):
                for k in [3, 5, 7, 9]:
                    suffix = f"_kernel{k}x{k}_filtered.png"
                    if f.name.endswith(suffix):
                        stem = f.name.replace(suffix, "")
                        if stem not in results_by_stem:
                            results_by_stem[stem] = {"stem": stem, "filtered": {}}
                        results_by_stem[stem]["filtered"][k] = (
                            f"/api/output-file?folder=filtered_images&file={urllib.parse.quote(f.name)}"
                        )

        # Match with original sample if exists
        for stem in results_by_stem:
            for ext in [".png", ".jpg", ".jpeg"]:
                candidate = DATA_DIR / f"{stem}{ext}"
                if candidate.exists():
                    results_by_stem[stem]["sample_url"] = (
                        f"/api/sample-image?name={urllib.parse.quote(candidate.name)}"
                    )
                    break

        self.send_json(list(results_by_stem.values()))

    def handle_get_output_file(self, query: Dict[str, List[str]]) -> None:
        folder_list = query.get("folder")
        file_list = query.get("file")
        if not folder_list or not file_list:
            self.send_error(400, "Missing 'folder' or 'file' parameter.")
            return

        folder = Path(folder_list[0]).name
        file_name = Path(file_list[0]).name

        allowed_folders = {"comparison_images", "filtered_images", "performance_graphs"}
        if folder not in allowed_folders:
            self.send_error(403, "Access to requested folder is forbidden.")
            return

        target_file = OUTPUT_DIR / folder / file_name
        self.serve_file(target_file)

    def handle_post_process(self) -> None:
        """Executes the Gaussian filter pipeline on demand on full resolution image."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)
            payload = json.loads(raw_body.decode("utf-8"))

            image_base64 = payload.get("image_base64")
            sample_name = payload.get("sample_name")
            filename = payload.get("filename", "uploaded_image.png")
            img_stem = Path(filename).stem

            # Parameters
            noise_type = payload.get("noise_type", "gaussian").lower()
            gaussian_mean = float(payload.get("gaussian_mean", 0.0))
            gaussian_std = float(payload.get("gaussian_std", DEFAULT_GAUSSIAN_STD))
            sp_density = float(payload.get("sp_density", 0.02))
            sp_ratio = float(payload.get("sp_ratio", 0.5))
            raw_kernels = payload.get("kernel_sizes", [3, 5, 7, 9])
            kernel_sizes = sorted([int(k) for k in raw_kernels if int(k) > 0 and int(k) % 2 == 1])
            if not kernel_sizes:
                kernel_sizes = [3, 5, 7, 9]

            seed = payload.get("seed", 42)
            if seed is not None:
                seed = int(seed)

            save_to_disk = bool(payload.get("save_to_disk", True))

            # 1. Acquire Image
            if image_base64:
                original_img = base64_to_rgb_numpy(image_base64)
            elif sample_name:
                sample_file = DATA_DIR / Path(sample_name).name
                if not sample_file.exists():
                    self.send_json({"error": f"Sample file not found: {sample_name}"}, status=404)
                    return
                original_img = load_image(sample_file, as_rgb=True)
            else:
                self.send_json({"error": "No image payload or sample name specified."}, status=400)
                return

            h, w = original_img.shape[:2]
            channels = original_img.shape[2] if original_img.ndim == 3 else 1

            total_start_time = time.perf_counter()

            # 2. Add Noise (On full resolution image)
            if noise_type == "gaussian":
                noisy_img = add_gaussian_noise(
                    original_img, mean=gaussian_mean, std=gaussian_std, seed=seed
                )
                noise_label = f"Gaussian (μ={gaussian_mean}, σ={gaussian_std})"
            elif noise_type in ["salt_and_pepper", "sp", "impulse"]:
                noisy_img = add_salt_and_pepper_noise(
                    original_img, density=sp_density, salt_vs_pepper=sp_ratio, seed=seed
                )
                noise_label = f"Salt-and-Pepper ({sp_density * 100:.1f}%)"
            elif noise_type in ["none", "clean"]:
                noisy_img = original_img.copy()
                noise_label = "Clean / Direct Filter (No Added Noise)"
            else:
                raise ValueError(f"Unknown noise type: {noise_type}")

            # Baseline metrics on full resolution
            noisy_mse = compute_mse(original_img, noisy_img)
            noisy_psnr = compute_psnr(original_img, noisy_img)

            # 3. Apply Multi-Kernel Filtering (On full resolution image)
            cv_start_time = time.perf_counter()
            filtered_dict = apply_multiple_kernels(noisy_img, kernel_sizes=kernel_sizes)
            cv_elapsed = time.perf_counter() - cv_start_time

            # Update Active Session Cache
            ACTIVE_SESSION["original"] = original_img
            ACTIVE_SESSION["noisy"] = noisy_img
            ACTIVE_SESSION["filtered_dict"] = filtered_dict
            ACTIVE_SESSION["filename"] = filename
            ACTIVE_SESSION["noise_type"] = noise_type
            ACTIVE_SESSION["seed"] = seed

            # 4. Quantitative Evaluation (Full resolution array metrics)
            metrics_dict: Dict[int, Tuple[float, float]] = {}
            kernel_results = []
            mse_list = []
            psnr_list = []

            # Generate preview-friendly versions for large images (e.g. 4000x6000)
            orig_preview = make_preview_image(original_img)
            noisy_preview = make_preview_image(noisy_img)

            for k in kernel_sizes:
                f_img = filtered_dict[k]
                f_mse = compute_mse(original_img, f_img)
                f_psnr = compute_psnr(original_img, f_img)
                metrics_dict[k] = (f_mse, f_psnr)
                mse_list.append(f_mse)
                psnr_list.append(f_psnr)

                auto_sigma = compute_auto_sigma(k)
                f_preview = make_preview_image(f_img)
                kernel_results.append({
                    "kernel_size": k,
                    "sigma": round(auto_sigma, 3),
                    "mse": round(f_mse, 2),
                    "psnr": round(f_psnr, 2) if not np.isinf(f_psnr) else "Infinity",
                    "psnr_val": 999.0 if np.isinf(f_psnr) else float(f_psnr),
                    "image_data": numpy_to_base64_png(f_preview),
                })

            # Identify optimal kernel
            best_idx = int(np.argmax([item["psnr_val"] for item in kernel_results]))
            for idx, item in enumerate(kernel_results):
                item["is_optimal"] = (idx == best_idx)

            optimal_kernel = kernel_results[best_idx]
            opt_k = optimal_kernel["kernel_size"]
            ACTIVE_SESSION["optimal_kernel"] = opt_k

            # 5. Visualizations & Figures
            # 5a. Performance Graph (FR-5)
            graph_dest = OUTPUT_DIR / "performance_graphs" / f"{img_stem}_performance_graph.png"
            if save_to_disk:
                plot_performance_graphs(
                    kernel_sizes=kernel_sizes,
                    mse_values=mse_list,
                    psnr_values=psnr_list,
                    baseline_mse=noisy_mse,
                    baseline_psnr=noisy_psnr,
                    image_name=img_stem,
                    noise_type=noise_type.capitalize(),
                    save_path=graph_dest,
                )
                with open(graph_dest, "rb") as f:
                    graph_b64 = f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
            else:
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8))
                ax1.plot(kernel_sizes, mse_list, marker="o", color="#D9381E", linewidth=2.2, label="Filtered MSE")
                ax1.axhline(y=noisy_mse, color="#7F8C8D", linestyle="--", label=f"Noisy MSE ({noisy_mse:.2f})")
                ax1.set_title("Kernel Size vs. MSE", fontweight="bold")
                ax1.set_xlabel("Kernel Size")
                ax1.set_ylabel("MSE")
                ax1.set_xticks(kernel_sizes)
                ax1.grid(True, linestyle=":", alpha=0.6)
                ax1.legend()

                ax2.plot(kernel_sizes, psnr_list, marker="s", color="#1E8449", linewidth=2.2, label="Filtered PSNR")
                ax2.axhline(y=noisy_psnr, color="#7F8C8D", linestyle="--", label=f"Noisy PSNR ({noisy_psnr:.2f} dB)")
                ax2.set_title("Kernel Size vs. PSNR", fontweight="bold")
                ax2.set_xlabel("Kernel Size")
                ax2.set_ylabel("PSNR (dB)")
                ax2.set_xticks(kernel_sizes)
                ax2.grid(True, linestyle=":", alpha=0.6)
                ax2.legend()
                plt.tight_layout()
                graph_b64 = fig_to_base64_png(fig)

            # 5b. Side-by-side Triptych (FR-4)
            triptych_kernel = 5 if 5 in filtered_dict else kernel_sizes[0]
            triptych_dest = OUTPUT_DIR / "comparison_images" / f"{img_stem}_comparison_kernel{triptych_kernel}x{triptych_kernel}.png"
            if save_to_disk:
                create_triptych_comparison(
                    original=orig_preview,
                    noisy=noisy_preview,
                    filtered=make_preview_image(filtered_dict[triptych_kernel]),
                    kernel_size=triptych_kernel,
                    metrics_noisy=(noisy_mse, noisy_psnr),
                    metrics_filtered=metrics_dict[triptych_kernel],
                    title_prefix=img_stem,
                    save_path=triptych_dest,
                )
                with open(triptych_dest, "rb") as f:
                    triptych_b64 = f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
            else:
                fig, axes = plt.subplots(1, 3, figsize=(15, 5.2))
                panels = [
                    ("Original (Clean)", orig_preview, "Reference", "#2E4053"),
                    ("Noisy Input", noisy_preview, f"MSE: {noisy_mse:.2f}\nPSNR: {noisy_psnr:.2f} dB", "#C0392B"),
                    (f"Gaussian Filtered ({triptych_kernel}x{triptych_kernel})", make_preview_image(filtered_dict[triptych_kernel]), f"MSE: {metrics_dict[triptych_kernel][0]:.2f}\nPSNR: {metrics_dict[triptych_kernel][1]:.2f} dB", "#27AE60"),
                ]
                for ax, (title, img, metric_text, color) in zip(axes, panels):
                    ax.imshow(img if img.ndim == 3 else img, cmap=None if img.ndim == 3 else "gray")
                    ax.set_title(title, fontweight="bold")
                    ax.set_xlabel(metric_text, fontweight="bold", color=color)
                    ax.set_xticks([]); ax.set_yticks([])
                plt.tight_layout()
                triptych_b64 = fig_to_base64_png(fig)

            # 5c. Multi-panel comprehensive grid
            multipanel_dest = OUTPUT_DIR / "comparison_images" / f"{img_stem}_all_kernels_comparison.png"
            if save_to_disk:
                preview_filtered_dict = {k: make_preview_image(filtered_dict[k]) for k in filtered_dict}
                create_multipanel_comparison(
                    original=orig_preview,
                    noisy=noisy_preview,
                    filtered_dict=preview_filtered_dict,
                    metrics_dict=metrics_dict,
                    noisy_metrics=(noisy_mse, noisy_psnr),
                    title_prefix=img_stem,
                    save_path=multipanel_dest,
                )
                with open(multipanel_dest, "rb") as f:
                    multipanel_b64 = f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
            else:
                multipanel_b64 = None

            # 5d. Save individual filtered images if save_to_disk
            if save_to_disk:
                filtered_dir = OUTPUT_DIR / "filtered_images"
                filtered_dir.mkdir(parents=True, exist_ok=True)
                for k in kernel_sizes:
                    save_image_to_disk(filtered_dict[k], filtered_dir / f"{img_stem}_kernel{k}x{k}_filtered.png")

            # 6. Advanced Educational Assets (FFT Spectra & Error Heatmap & Patch & Scanline)
            fft_orig_b64 = compute_fft_spectrum(orig_preview)
            fft_noisy_b64 = compute_fft_spectrum(noisy_preview)
            fft_filtered_b64 = compute_fft_spectrum(make_preview_image(filtered_dict[opt_k]))
            error_heatmap_b64 = compute_error_heatmap(orig_preview, make_preview_image(filtered_dict[opt_k]))

            # Extract default center patch (8x8)
            default_patch = extract_patch_bundle(
                clean_rgb=original_img,
                noisy_rgb=noisy_img,
                x=w // 2 - 4,
                y=h // 2 - 4,
                patch_size=8,
                kernel_sizes=kernel_sizes,
                noise_type=noise_type,
                seed=seed,
            )

            # Extract default scanline (center row)
            default_scanline = extract_scanline(
                orig_preview,
                noisy_preview,
                make_preview_image(filtered_dict[opt_k]),
                row_y=orig_preview.shape[0] // 2,
            )

            total_elapsed = time.perf_counter() - total_start_time

            # Format Response
            response_data = {
                "success": True,
                "filename": filename,
                "stem": img_stem,
                "dimensions": {"width": w, "height": h, "channels": channels},
                "preview_dimensions": {"width": orig_preview.shape[1], "height": orig_preview.shape[0]},
                "timing": {
                    "cv_time_ms": round(cv_elapsed * 1000, 2),
                    "total_time_ms": round(total_elapsed * 1000, 2),
                    "benchmark_target_passed": (cv_elapsed < 2.0),
                },
                "noise": {
                    "type": noise_type,
                    "label": noise_label,
                    "baseline_mse": round(noisy_mse, 2),
                    "baseline_psnr": round(noisy_psnr, 2) if not np.isinf(noisy_psnr) else "Infinity",
                    "seed": seed,
                },
                "original_data_url": numpy_to_base64_png(orig_preview),
                "noisy_data_url": numpy_to_base64_png(noisy_preview),
                "kernels": kernel_results,
                "optimal_kernel": optimal_kernel,
                "triptych_data_url": triptych_b64,
                "multipanel_data_url": multipanel_b64,
                "performance_graph_data_url": graph_b64,
                "chart_points": {
                    "kernel_sizes": kernel_sizes,
                    "mse_values": [round(m, 2) for m in mse_list],
                    "psnr_values": [round(p, 2) if not np.isinf(p) else None for p in psnr_list],
                    "baseline_mse": round(noisy_mse, 2),
                    "baseline_psnr": round(noisy_psnr, 2) if not np.isinf(noisy_psnr) else None,
                },
                "frequency_view": {
                    "fft_original": fft_orig_b64,
                    "fft_noisy": fft_noisy_b64,
                    "fft_filtered": fft_filtered_b64,
                    "caption": "A 2D Gaussian filter is isotropic in spatial and frequency domains. High-frequency noise components (outer periphery) are heavily attenuated while the central low-frequency passband is preserved.",
                },
                "error_heatmap_data_url": error_heatmap_b64,
                "initial_patch": default_patch,
                "initial_scanline": default_scanline,
                "detailed_kernels": {k: get_detailed_kernel_info(k, compute_auto_sigma(k)) for k in kernel_sizes},
            }

            self.send_json(response_data)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_json({"error": str(e), "trace": traceback.format_exc()}, status=500)

    def handle_post_patch(self) -> None:
        """Extracts a 12x12 patch bundle at specific coordinate (x, y)."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)
            payload = json.loads(raw_body.decode("utf-8"))

            if ACTIVE_SESSION["original"] is None:
                self.send_json({"error": "No image currently loaded."}, status=400)
                return

            x = int(payload.get("x", 0))
            y = int(payload.get("y", 0))
            patch_size = int(payload.get("patch_size", 12))
            kernel_sizes = payload.get("kernel_sizes", [3, 5, 7, 9])

            patch_data = extract_patch_bundle(
                clean_rgb=ACTIVE_SESSION["original"],
                noisy_rgb=ACTIVE_SESSION.get("noisy"),
                x=x,
                y=y,
                patch_size=patch_size,
                kernel_sizes=kernel_sizes,
                noise_type=ACTIVE_SESSION.get("noise_type", "gaussian"),
                seed=ACTIVE_SESSION.get("seed", 42),
            )
            self.send_json({"success": True, "patch": patch_data})
        except Exception as e:
            self.send_json({"error": str(e)}, status=500)

    def handle_post_scanline(self) -> None:
        """Extracts scanline intensity profile across a selected row."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)
            payload = json.loads(raw_body.decode("utf-8"))

            if ACTIVE_SESSION["original"] is None or ACTIVE_SESSION["noisy"] is None:
                self.send_json({"error": "No image currently loaded."}, status=400)
                return

            row_y = int(payload.get("row", 0))
            opt_k = ACTIVE_SESSION.get("optimal_kernel", 5)
            filt_img = ACTIVE_SESSION["filtered_dict"].get(opt_k, ACTIVE_SESSION["noisy"])

            orig_prev = make_preview_image(ACTIVE_SESSION["original"])
            noisy_prev = make_preview_image(ACTIVE_SESSION["noisy"])
            filt_prev = make_preview_image(filt_img)

            # Scale row_y if requested relative to preview height
            req_h = payload.get("preview_height")
            if req_h and req_h > 0 and req_h != orig_prev.shape[0]:
                row_y = int(round(row_y * (orig_prev.shape[0] / req_h)))

            scanline_data = extract_scanline(orig_prev, noisy_prev, filt_prev, row_y=row_y)
            self.send_json({"success": True, "scanline": scanline_data})
        except Exception as e:
            self.send_json({"error": str(e)}, status=500)

    def handle_post_batch_process(self) -> None:
        """Runs pipeline on all sample images."""
        try:
            from main import run_pipeline
            exported = run_pipeline(
                data_dir=DATA_DIR,
                output_dir=OUTPUT_DIR,
                noise_type="gaussian",
                seed=42,
            )
            self.send_json({
                "success": True,
                "message": "Successfully batch-processed dataset.",
                "artifacts": exported,
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_json({"error": str(e)}, status=500)


def run_server(port: int = 8000, host: str = "127.0.0.1") -> None:
    """Starts the HTTP server with automatic port recovery if port is busy."""
    server_address = (host, port)
    current_port = port
    max_tries = 10
    httpd = None

    for attempt in range(max_tries):
        try:
            httpd = ThreadedHTTPServer((host, current_port), GaussianFilterRequestHandler)
            break
        except OSError as e:
            print(f"[PORT BUSY] Port {current_port} is already in use. Trying port {current_port + 1}...")
            current_port += 1

    if httpd is None:
        raise RuntimeError(f"Could not bind to any port in range {port} to {current_port - 1}")

    local_url = f"http://localhost:{current_port}"
    print("=" * 72)
    print("  [*] CS-305 GAUSSIAN FILTER WEB INTERFACE IS RUNNING")
    print("=" * 72)
    print(f"  - Localhost URL : {local_url}")
    print(f"  - Network Host  : {host}:{current_port}")
    print(f"  - Static Assets : {STATIC_DIR.resolve()}")
    print(f"  - Sample Data   : {DATA_DIR.resolve()}")
    print(f"  - Outputs Dir   : {OUTPUT_DIR.resolve()}")
    print("-" * 72)
    print("  Ready to upload images and analyze results in your web browser.")
    print("  Press CTRL+C in this terminal to gracefully stop the server.")
    print("=" * 72)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[STOPPING] Shutting down Gaussian Filter Web Server...")
    finally:
        httpd.server_close()
        print("[STOPPED] Server closed cleanly.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gaussian Filter Web Application Server")
    parser.add_argument("--port", type=int, default=8000, help="Localhost port (default: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    args = parser.parse_args()
    run_server(port=args.port, host=args.host)
