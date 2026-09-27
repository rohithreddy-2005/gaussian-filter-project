# Technical Report: Design and Analysis of a Gaussian Filter for Low-Pass Image Smoothing

**Course:** CS-305 Computer Vision Case Study  
**Project Team:** 1–4 Student Engineering Team  
**Date:** March 2026  
**Artifact Version:** 1.0.0  

---

## 1. Abstract
Digital image acquisition and transmission systems are inherently vulnerable to corruptive noise phenomena, including thermal fluctuations in camera sensors and transmission channel bit errors. This case study designs, implements, and evaluates a modular 2D Gaussian Low-Pass Filter pipeline in Python for spatial domain image denoising. We systematically benchmark the filter across four kernel sizes ($3\times3$, $5\times5$, $7\times7$, and $9\times9$) against Additive White Gaussian Noise (AWGN) and Salt-and-Pepper impulse noise. Filtering fidelity is quantitatively assessed using Mean Squared Error (MSE) and Peak Signal-to-Noise Ratio (PSNR), combined with qualitative visual side-by-side inspections. Experimental results confirm that while Gaussian filtering significantly attenuates high-frequency Gaussian noise and improves PSNR, selecting overly large kernels induces edge blurring and contrast degradation, demonstrating the fundamental trade-off between noise suppression and spatial detail preservation.

---

## 2. Literature Review
Digital images are subject to continuous degradation during sensor exposure, analog-to-digital conversion, and wireless transmission. Additive White Gaussian Noise (AWGN) is primarily caused by Johnson–Nyquist thermal noise and photon shot noise within semiconductor photo-detectors, following an independent and identically distributed zero-mean normal distribution across pixels. Conversely, Salt-and-Pepper noise manifests as randomized extreme bit-flips (black and white pixels) caused by faulty memory cells or severe transmission dropouts. 

Spatial low-pass filtering operates on the principle that image noise predominantly occupies high spatial frequency bands, whereas macro-structural scene content resides in lower spatial frequencies. The 2D continuous isotropic Gaussian filter kernel is mathematically defined as:
$$G(x, y) = \frac{1}{2\pi\sigma^2} \exp\left(-\frac{x^2 + y^2}{2\sigma^2}\right)$$
Unlike uniform box (mean) filters that suffer from abrupt frequency cutoffs and ringing artifacts in the spatial domain, the Gaussian function provides smooth, radially symmetric attenuation without high-frequency side lobes. Furthermore, because the 2D Gaussian distribution is strictly separable into product terms $G(x,y) = G_x(x) \cdot G_y(y)$, a 2D convolution of kernel size $K \times K$ can be factorized into two successive 1D convolutions (horizontal then vertical). This reduces the computational complexity from $\mathcal{O}(K^2)$ to $\mathcal{O}(2K)$ operations per pixel, enabling real-time execution in embedded and interactive computer vision applications.

---

## 3. Methodology
Our implementation follows a strictly modular end-to-end processing pipeline adhering to software engineering best practices:

```
[Input Image (FR-1)] 
        │
        ▼
[Noise Generator (FR-2)] ──> Additive Gaussian Noise (N(0, 50^2)) / Salt-and-Pepper (2%)
        │
        ▼
[Gaussian Filter (FR-3)] ──> Separable 2D Convolution (3x3, 5x5, 7x7, 9x9)
        │
        ▼
[Evaluation (FR-5)]      ──> MSE & PSNR Quantitative Metrics Computation
        │
        ▼
[Visualization (FR-4)]   ──> Side-by-Side Triptychs & Dual-Panel Performance Curves
        │
        ▼
[Artifact Export (FR-6)] ──> Structured Disk Storage (outputs/)
```

1. **Image Upload and Ingestion (FR-1):** The `image_loader.py` module discovers, validates, and decodes `.jpg`, `.jpeg`, and `.png` images into normalized 8-bit RGB NumPy arrays. If the dataset directory is unpopulated, it synthesizes three standardized calibration test images (geometric shapes, continuous 2D gradients, and high-frequency checkerboard patterns) to ensure immediate reproducibility.
2. **Noise Injection (FR-2):** Controlled synthetic degradation is injected via `noise_generator.py`. AWGN is sampled from $\mathcal{N}(\mu=0, \sigma=50)$ and added in 32-bit floating point space before clipping to $[0, 255]$. Salt-and-Pepper impulse noise alters a configurable percentage ($2\%$) of pixels to either $0$ or $255$ with equal probability. A fixed seed ensures exact experimental determinism.
3. **Gaussian Filtering (FR-3):** Spatial convolution is performed using `cv2.GaussianBlur` with reflective boundary padding across odd square kernels ($K \in \{3, 5, 7, 9\}$). Filter standard deviations ($\sigma$) are dynamically derived using OpenCV's heuristic: $\sigma = 0.3 \cdot ((K - 1) \cdot 0.5 - 1) + 0.8$.
4. **Quantitative Metrics Computation (FR-5):** Reconstructed images are evaluated against the uncorrupted ground truth using Mean Squared Error (MSE) and Peak Signal-to-Noise Ratio (PSNR):
   $$\text{MSE} = \frac{1}{M \cdot N \cdot C} \sum_{i=1}^{M}\sum_{j=1}^{N}\sum_{c=1}^{C} \left[I_{\text{clean}}(i,j,c) - I_{\text{test}}(i,j,c)\right]^2$$
   $$\text{PSNR} = 10 \cdot \log_{10}\left(\frac{255^2}{\text{MSE}}\right)$$
5. **Visualization and Export (FR-4 & FR-6):** Side-by-side triptychs (Original $\rightarrow$ Noisy $\rightarrow$ Filtered), comprehensive multi-kernel grids, and dual-axis performance response curves are rendered via Matplotlib and saved to organized subdirectories under `outputs/`.

---

## 4. Experimental Results

### 4.1 Quantitative Performance Summary
The tables below record the baseline degradation and post-filtering metric progression across the four evaluated kernel sizes for our complete 10-image benchmark dataset under standardized Gaussian noise ($\sigma = 50$) and Salt-and-Pepper noise ($2\%$ impulse density):

**Table 1:** Quantitative Evaluation Metrics (MSE, PSNR) for Gaussian Noise ($\sigma=50$) across Kernel Sizes ($3\times3$ to $9\times9$).

| Image Asset | Condition / Kernel | Mean Squared Error (MSE) | PSNR (dB) | Status / Observation |
| :--- | :--- | :--- | :--- | :--- |
| **s3.jpeg** *(Real Indoor Scene)* | Noisy Baseline ($\sigma=50$) | 1859.56 | 15.44 dB | Heavy sensor noise grain |
| | Filtered $3\times3$ ($\sigma=0.80$) | 320.36 | 23.07 dB | Significant noise attenuation (+7.63 dB gain) |
| | Filtered $5\times5$ ($\sigma=1.10$) | 183.44 | 25.50 dB | Strong noise suppression (+10.06 dB gain) |
| | Filtered $7\times7$ ($\sigma=1.40$) | 138.84 | 26.71 dB | Clean photographic smoothing (+11.27 dB gain) |
| | Filtered $9\times9$ ($\sigma=1.70$) | **118.44** | **27.40 dB** | **Optimal peak (+11.96 dB gain)**; large kernel needed for heavy noise |
| **s4.jpeg** *(Real Indoor Photo)* | Noisy Baseline ($\sigma=50$) | 1833.94 | 15.50 dB | Prominent grain with boundary clipping attenuation |
| | Filtered $3\times3$ ($\sigma=0.80$) | 353.41 | 22.65 dB | Strong initial noise reduction (+7.15 dB gain) |
| | Filtered $5\times5$ ($\sigma=1.10$) | 231.49 | 24.49 dB | Substantial grain removal (+8.99 dB gain) |
| | Filtered $7\times7$ ($\sigma=1.40$) | 199.67 | 25.13 dB | High-fidelity recovery (+9.63 dB gain) |
| | Filtered $9\times9$ ($\sigma=1.70$) | **192.52** | **25.29 dB** | **Optimal peak (+9.79 dB gain)**; effective background restoration |
| **sample1_clean.png** *(Standard Lena)* | Noisy Baseline ($\sigma=50$) | 2147.82 | 14.81 dB | Dense, prominent Gaussian noise grain |
| | Filtered $3\times3$ ($\sigma=0.80$) | 359.44 | 22.57 dB | Sharp noise attenuation (+7.76 dB gain) |
| | Filtered $5\times5$ ($\sigma=1.10$) | 211.38 | 24.88 dB | Significant noise suppression (+10.07 dB gain) |
| | Filtered $7\times7$ ($\sigma=1.40$) | 171.68 | 25.78 dB | High quality smoothing (+10.97 dB gain) |
| | Filtered $9\times9$ ($\sigma=1.70$) | **161.34** | **26.05 dB** | **Optimal peak (+11.24 dB gain)**; robust smoothing required for heavy noise |
| **sample2.jpeg** *(Real Scene)* | Noisy Baseline ($\sigma=50$) | 2010.43 | 15.10 dB | Prominent additive noise across photographic details |
| | Filtered $3\times3$ ($\sigma=0.80$) | 350.79 | 22.68 dB | Significant noise suppression (+7.58 dB gain) |
| | Filtered $5\times5$ ($\sigma=1.10$) | 203.05 | 25.05 dB | High quality reconstruction (+9.95 dB gain) |
| | Filtered $7\times7$ ($\sigma=1.40$) | 156.22 | 26.19 dB | Clean texture reconstruction (+11.09 dB gain) |
| | Filtered $9\times9$ ($\sigma=1.70$) | **137.18** | **26.76 dB** | **Optimal peak (+11.66 dB gain)**; large kernel required to attenuate $\sigma=50$ noise |
| **sample5_hopper.jpg** *(Historical Benchmark)*| Noisy Baseline ($\sigma=50$) | 1764.72 | 15.66 dB | Additive grain over fine uniform textures |
| | Filtered $3\times3$ ($\sigma=0.80$) | 397.14 | 22.14 dB | Good edge definition (+6.48 dB gain) |
| | Filtered $5\times5$ ($\sigma=1.10$) | **320.14** | **23.08 dB** | **Optimal peak (+7.42 dB gain)**; balance between grain and uniform texture |
| | Filtered $7\times7$ ($\sigma=1.40$) | 324.15 | 23.02 dB | Subtle softening of facial and uniform features |
| | Filtered $9\times9$ ($\sigma=1.70$) | 351.66 | 22.67 dB | Blur penalty begins outweighing noise reduction |
| **synthetic_checkerboard.png** | Noisy Baseline ($\sigma=50$) | 1906.15 | 15.33 dB | Dense noise across high-frequency square grid |
| | Filtered $3\times3$ ($\sigma=0.80$) | 492.33 | 21.21 dB | Attenuates high-frequency noise (+5.88 dB gain) |
| | Filtered $5\times5$ ($\sigma=1.10$) | **475.20** | **21.36 dB** | **Optimal peak (+6.03 dB gain)**; balances heavy noise reduction against edge blur |
| | Filtered $7\times7$ ($\sigma=1.40$) | 531.91 | 20.87 dB | Vertex distortion begins outweighing noise reduction |
| | Filtered $9\times9$ ($\sigma=1.70$) | 613.47 | 20.25 dB | Severe vertex rounding and contrast attenuation |
| **synthetic_concentric_circles.png** | Noisy Baseline ($\sigma=50$) | 1906.58 | 15.33 dB | Additive grain over radial frequency sweep |
| | Filtered $3\times3$ ($\sigma=0.80$) | 383.92 | 22.29 dB | Ring structure preserved (+6.96 dB gain) |
| | Filtered $5\times5$ ($\sigma=1.10$) | **292.73** | **23.47 dB** | **Optimal peak (+8.14 dB gain)**; clean radial transition |
| | Filtered $7\times7$ ($\sigma=1.40$) | 324.05 | 23.02 dB | Outer high-frequency rings merge |
| | Filtered $9\times9$ ($\sigma=1.70$) | 426.03 | 21.84 dB | Radial fringe cancellation and blur |
| **synthetic_gradient.png** | Noisy Baseline ($\sigma=50$) | 2158.73 | 14.79 dB | Dense grain across smooth continuous ramp |
| | Filtered $3\times3$ ($\sigma=0.80$) | 345.87 | 22.74 dB | Strong initial noise reduction (+7.95 dB gain) |
| | Filtered $5\times5$ ($\sigma=1.10$) | 181.90 | 25.53 dB | Smooth gradient restoration (+10.74 dB gain) |
| | Filtered $7\times7$ ($\sigma=1.40$) | 127.68 | 27.07 dB | High-fidelity tonal reconstruction (+12.28 dB gain) |
| | Filtered $9\times9$ ($\sigma=1.70$) | **102.49** | **28.02 dB** | **Peak PSNR (+13.23 dB gain)**; ideal for continuous tones |
| **synthetic_shapes.png** | Noisy Baseline ($\sigma=50$) | 1567.73 | 16.18 dB | Dense noise over geometric color patches |
| | Filtered $3\times3$ ($\sigma=0.80$) | 383.06 | 22.30 dB | Initial noise suppression (+6.12 dB gain) |
| | Filtered $5\times5$ ($\sigma=1.10$) | 310.57 | 23.21 dB | Substantial flat region smoothing (+7.03 dB gain) |
| | Filtered $7\times7$ ($\sigma=1.40$) | **310.56** | **23.21 dB** | **Optimal peak (+7.03 dB gain)**; maximum interior smoothing before edge blur dominates |
| | Filtered $9\times9$ ($\sigma=1.70$) | 332.30 | 22.92 dB | Border bleeding begins degrading boundary fidelity |
| **synthetic_sine_waves.png** | Noisy Baseline ($\sigma=50$) | 2230.78 | 14.65 dB | Noise corrupting harmonic sinusoidal waves |
| | Filtered $3\times3$ ($\sigma=0.80$) | 350.20 | 22.69 dB | Harmonic peaks preserved (+8.04 dB gain) |
| | Filtered $5\times5$ ($\sigma=1.10$) | 184.28 | 25.48 dB | Smooth wave surface (+10.83 dB gain) |
| | Filtered $7\times7$ ($\sigma=1.40$) | 138.81 | 26.71 dB | Clean wave trough reconstruction (+12.06 dB gain) |
| | Filtered $9\times9$ ($\sigma=1.70$) | **134.55** | **26.84 dB** | **Optimal peak (+12.19 dB gain)**; effective sinusoidal smoothing |

<br>

**Table 2:** Quantitative Evaluation Metrics (MSE, PSNR) for Salt-and-Pepper Impulse Noise ($2\%$ Density) across Kernel Sizes ($3\times3$ to $9\times9$).

| Image Asset | Condition / Kernel | Mean Squared Error (MSE) | PSNR (dB) | Status / Observation |
| :--- | :--- | :--- | :--- | :--- |
| **s3.jpeg** *(Real Indoor Scene)* | Noisy Baseline ($2\%$) | 450.64 | 21.59 dB | Random impulse salt-and-pepper spikes |
| | Filtered $3\times3$ ($\sigma=0.80$) | 77.53 | 29.24 dB | Diffuses binary outliers into local neighborhood |
| | Filtered $5\times5$ ($\sigma=1.10$) | 49.60 | 31.18 dB | Further dilutes outlier intensities |
| | Filtered $7\times7$ ($\sigma=1.40$) | 43.28 | 31.77 dB | Outliers spread into broad low-contrast halos |
| | Filtered $9\times9$ ($\sigma=1.70$) | **42.78** | **31.82 dB** | **Peak metric (+10.23 dB gain)**; background edge blur noticeable |
| **s4.jpeg** *(Real Indoor Photo)* | Noisy Baseline ($2\%$) | 455.38 | 21.55 dB | Discrete impulse spikes on walls and faces |
| | Filtered $3\times3$ ($\sigma=0.80$) | 84.78 | 28.85 dB | Outliers smoothed (+7.30 dB gain) |
| | Filtered $5\times5$ ($\sigma=1.10$) | **65.85** | **29.95 dB** | **Optimal balance (+8.40 dB gain)**; larger kernels blur foreground |
| | Filtered $7\times7$ ($\sigma=1.40$) | 69.90 | 29.69 dB | Spreading of dark spots into gray patches |
| | Filtered $9\times9$ ($\sigma=1.70$) | 81.00 | 29.05 dB | Contrast softening exceeds noise reduction benefit |
| **sample1_clean.png** *(Standard Lena)* | Noisy Baseline ($2\%$) | 389.53 | 22.23 dB | Salt-and-pepper noise across facial features |
| | Filtered $3\times3$ ($\sigma=0.80$) | 78.28 | 29.19 dB | Outliers smeared into small blur patches |
| | Filtered $5\times5$ ($\sigma=1.10$) | **66.96** | **29.87 dB** | **Optimal peak (+7.64 dB gain)**; preserves eyes/hat contours |
| | Filtered $7\times7$ ($\sigma=1.40$) | 75.09 | 29.37 dB | Noticeable softening of hair and feather texture |
| | Filtered $9\times9$ ($\sigma=1.70$) | 89.32 | 28.62 dB | Over-smoothed; halo artifacts visible |
| **sample2.jpeg** *(Real Scene)* | Noisy Baseline ($2\%$) | 429.24 | 21.80 dB | Impulse spikes across natural landscape details |
| | Filtered $3\times3$ ($\sigma=0.80$) | 74.01 | 29.44 dB | Rapid initial suppression (+7.64 dB gain) |
| | Filtered $5\times5$ ($\sigma=1.10$) | 47.56 | 31.36 dB | Clean background averaging (+9.56 dB gain) |
| | Filtered $7\times7$ ($\sigma=1.40$) | **43.05** | **31.79 dB** | **Optimal peak (+9.99 dB gain)**; edge blur balances halo dissipation |
| | Filtered $9\times9$ ($\sigma=1.70$) | 45.52 | 31.55 dB | Fine texture loss exceeds smoothing benefit |
| **sample5_hopper.jpg** *(Historical Benchmark)*| Noisy Baseline ($2\%$) | 470.50 | 21.41 dB | High-contrast impulse corruption |
| | Filtered $3\times3$ ($\sigma=0.80$) | **122.12** | **27.26 dB** | **Optimal peak (+5.85 dB gain)**; sharp uniform contours preserved |
| | Filtered $5\times5$ ($\sigma=1.10$) | 138.22 | 26.73 dB | Uniform embroidery blurred by halo spread |
| | Filtered $7\times7$ ($\sigma=1.40$) | 173.69 | 25.73 dB | Edge softening penalty dominates |
| | Filtered $9\times9$ ($\sigma=1.70$) | 216.32 | 24.78 dB | Heavy loss of structural definition |
| **synthetic_checkerboard.png** | Noisy Baseline ($2\%$) | 447.96 | 21.62 dB | Impulse spikes at grid borders |
| | Filtered $3\times3$ ($\sigma=0.80$) | **217.28** | **24.76 dB** | **Optimal peak (+3.14 dB gain)**; square edges intact |
| | Filtered $5\times5$ ($\sigma=1.10$) | 306.35 | 23.27 dB | Vertices softened |
| | Filtered $7\times7$ ($\sigma=1.40$) | 400.54 | 22.10 dB | Severe corner rounding |
| | Filtered $9\times9$ ($\sigma=1.70$) | 498.64 | 21.15 dB | Metric worse than noisy baseline due to geometric blur |
| **synthetic_concentric_circles.png** | Noisy Baseline ($2\%$) | 455.71 | 21.54 dB | Impulse spikes over concentric rings |
| | Filtered $3\times3$ ($\sigma=0.80$) | 86.03 | 28.78 dB | Sharp circular boundaries maintained |
| | Filtered $5\times5$ ($\sigma=1.10$) | **82.71** | **28.96 dB** | **Optimal peak (+7.42 dB gain)**; good ring continuity |
| | Filtered $7\times7$ ($\sigma=1.40$) | 129.86 | 27.00 dB | Narrow rings bleed together |
| | Filtered $9\times9$ ($\sigma=1.70$) | 227.91 | 24.55 dB | High-frequency concentric ripples erased |
| **synthetic_gradient.png** | Noisy Baseline ($2\%$) | 389.07 | 22.23 dB | Impulse spikes along smooth ramp |
| | Filtered $3\times3$ ($\sigma=0.80$) | 64.22 | 30.05 dB | Spikes attenuated (+7.82 dB gain) |
| | Filtered $5\times5$ ($\sigma=1.10$) | 38.19 | 32.31 dB | Smooth gradient restored |
| | Filtered $7\times7$ ($\sigma=1.40$) | **32.67** | **32.99 dB** | **Optimal peak (+10.76 dB gain)**; continuous ramp fidelity |
| | Filtered $9\times9$ ($\sigma=1.70$) | 32.95 | 32.95 dB | Metric plateaus |
| **synthetic_shapes.png** | Noisy Baseline ($2\%$) | 513.75 | 21.02 dB | Impulse noise over geometric polygons |
| | Filtered $3\times3$ ($\sigma=0.80$) | **128.27** | **27.05 dB** | **Optimal peak (+6.03 dB gain)**; sharp polygon perimeters preserved |
| | Filtered $5\times5$ ($\sigma=1.10$) | 128.55 | 27.04 dB | Virtually tied; slight corner radius softening |
| | Filtered $7\times7$ ($\sigma=1.40$) | 153.70 | 26.26 dB | Polygon edge bleeding begins |
| | Filtered $9\times9$ ($\sigma=1.70$) | 187.83 | 25.39 dB | Heavy edge blur penalty |
| **synthetic_sine_waves.png** | Noisy Baseline ($2\%$) | 372.94 | 22.41 dB | Impulse outliers on periodic wave surface |
| | Filtered $3\times3$ ($\sigma=0.80$) | 60.98 | 30.28 dB | Outliers suppressed (+7.87 dB gain) |
| | Filtered $5\times5$ ($\sigma=1.10$) | **38.49** | **32.28 dB** | **Optimal peak (+9.87 dB gain)**; smooth wave crests |
| | Filtered $7\times7$ ($\sigma=1.40$) | 41.31 | 31.97 dB | Slight harmonic amplitude attenuation |
| | Filtered $9\times9$ ($\sigma=1.70$) | 60.07 | 30.34 dB | Loss of high-frequency wave amplitude |

*(Note: Exact values correspond to runtime console outputs generated by `main.py`).*

### 4.2 Visual Artifacts & Before/After Comparisons
- **Figure 1 (Denoising Triptychs):** Side-by-side $1\times3$ panels (Original $\rightarrow$ Noisy $\rightarrow$ Filtered $5\times5$) with color-coded quantitative MSE and PSNR metric annotations below each panel. Saved in `outputs/comparison_images/<image_name>_comparison_kernel5x5.png`.
- **Figure 2 (Comprehensive Multi-Kernel Evaluation Grids):** $2\times3$ multi-panel comparative boards evaluating pristine original, corrupted input, and all four Gaussian kernel outputs ($3\times3, 5\times5, 7\times7, 9\times9$). Saved in `outputs/comparison_images/<image_name>_all_kernels_comparison.png`.
- **Figure 3 (Dual-Panel Metric Response Curves):** Dual-axis performance plots showing Kernel Size vs. MSE (left) and Kernel Size vs. PSNR (right) charted alongside the unmitigated noisy baseline, with annotated inflection points indicating optimal kernel selections. Saved in `outputs/performance_graphs/<image_name>_performance_graph.png`.

### 4.3 Success Criteria & Performance Evaluation
Core denoising completes in under 0.25s to 1.04s per image (depending on resolution, e.g. 1280x960 px), meeting the project performance requirement. Visualization and export add additional non-core time not counted against this requirement.

Across all 10 test images (both natural photographic imagery such as `sample1_clean.png`, `sample2.jpeg`, `s3.jpeg`, `s4.jpeg`, `sample5_hopper.jpg` and synthetic test patterns), the core Gaussian convolution across four separate kernels ($3\times3$, $5\times5$, $7\times7$, $9\times9$) alongside quantitative MSE and PSNR matrix calculations required between 0.17s and 1.04s per image. This execution speed comfortably surpasses the Non-Functional Requirement threshold of 2.0 seconds per image. The subsequent rendering of three high-resolution multi-panel Matplotlib figures and disk I/O requires approximately 3.2s to 5.6s per image as an offline analysis utility.

### 4.4 Tested Edge Cases
1. **Empty Input Directory:** When `data/sample_images/` contains no supported image files, the loader automatically detects the condition and generates calibrated synthetic images, executing the full pipeline without crashing.
2. **Corrupted / Invalid Non-Image Files:** When non-image files with valid extensions (e.g., text files renamed to `.jpg`) are placed in the directory, the decoder catches the decode failure, issues a descriptive console error message, and safely skips the file without crashing.
3. **Grayscale-Only (Single-Channel) Images:** Single-channel 2D matrices are processed seamlessly across noise addition, 2D convolution, MSE/PSNR calculation, and grayscale matplotlib visualization without matrix dimensionality mismatch or corrupted metric calculations.
4. **Miniature Imagery ($20\times20$ px) with $9\times9$ Kernel:** Border reflection padding (`BORDER_REFLECT_101`) allows the largest $9\times9$ filter kernel to convolve near the boundaries of small $20\times20$ pixel inputs without out-of-bounds indexing or shape distortion.

---

## 5. Conclusion
This study comprehensively analyzed the behavior of Gaussian Low-Pass Filtering for spatial domain image restoration under a standardized heavy noise regime ($\sigma = 50$) and impulse noise ($2\%$). Quantitative evaluation demonstrated that for Additive White Gaussian Noise, Gaussian smoothing yields substantial PSNR improvements ranging from $+6.03\text{ dB}$ up to $+13.23\text{ dB}$ depending on spatial frequency content. Under this heavier noise distribution, larger kernels ($7\times7$ and $9\times9$) emerged as the optimal filters across natural photographic images (`sample1_clean.png`, `sample2.jpeg`, `s3.jpeg`, `s4.jpeg`), lifting PSNR by $+9.79\text{ dB}$ to $+11.96\text{ dB}$ because aggressive spatial averaging was necessary to suppress the intense variance. In continuous color gradients, $9\times9$ achieved the highest gain (+13.23 dB) with zero distortion penalty. In structured geometric scenes (checkerboard and concentric circles), $5\times5$ reached peak fidelity before boundary vertex rounding degraded the structure. The experimental analysis verified that dynamic range boundary clipping physically attenuates empirical MSE for high-saturation images, and confirmed that the core filtering algorithms execute well under the 2.0-second threshold per image.

Crucially, the evaluation confirmed that linear Gaussian filtering is substantially less effective against Salt-and-Pepper impulse noise: rather than eliminating extreme outlier pixels, spatial convolution averages impulse spikes with neighboring values, smearing them into diffuse, blurry halos that degrade visual sharpness. For impulse noise mitigation, non-linear rank-order filters such as the Median filter represent the essential algorithmic enhancement for future project iterations.

---

## 6. References
1. Gonzalez, R. C., & Woods, R. E. (2018). *Digital Image Processing* (4th ed.). Pearson. (Chapter 3: Intensity Transformations and Spatial Filtering).
2. Szeliski, R. (2022). *Computer Vision: Algorithms and Applications* (2nd ed.). Springer. (Section 3.2: Linear Filtering and Separable Convolutions).
3. Buades, A., Coll, B., & Morel, J. M. (2005). A review of image denoising algorithms, with a new one. *Multiscale Modeling & Simulation*, 4(2), 490-530.
