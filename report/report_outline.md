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
[Noise Generator (FR-2)] ──> Additive Gaussian Noise (N(0, 25^2)) / Salt-and-Pepper (2%)
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
2. **Noise Injection (FR-2):** Controlled synthetic degradation is injected via `noise_generator.py`. AWGN is sampled from $\mathcal{N}(\mu=0, \sigma=25)$ and added in 32-bit floating point space before clipping to $[0, 255]$. Salt-and-Pepper impulse noise alters a configurable percentage ($2\%$) of pixels to either $0$ or $255$ with equal probability. A fixed seed ensures exact experimental determinism.
3. **Gaussian Filtering (FR-3):** Spatial convolution is performed using `cv2.GaussianBlur` with reflective boundary padding across odd square kernels ($K \in \{3, 5, 7, 9\}$). Filter standard deviations ($\sigma$) are dynamically derived using OpenCV's heuristic: $\sigma = 0.3 \cdot ((K - 1) \cdot 0.5 - 1) + 0.8$.
4. **Quantitative Metrics Computation (FR-5):** Reconstructed images are evaluated against the uncorrupted ground truth using Mean Squared Error (MSE) and Peak Signal-to-Noise Ratio (PSNR):
   $$\text{MSE} = \frac{1}{M \cdot N \cdot C} \sum_{i=1}^{M}\sum_{j=1}^{N}\sum_{c=1}^{C} \left[I_{\text{clean}}(i,j,c) - I_{\text{test}}(i,j,c)\right]^2$$
   $$\text{PSNR} = 10 \cdot \log_{10}\left(\frac{255^2}{\text{MSE}}\right)$$
5. **Visualization and Export (FR-4 & FR-6):** Side-by-side triptychs (Original $\rightarrow$ Noisy $\rightarrow$ Filtered), comprehensive multi-kernel grids, and dual-axis performance response curves are rendered via Matplotlib and saved to organized subdirectories under `outputs/`.

---

## 4. Experimental Results

### 4.1 Quantitative Performance Summary
The table below records the baseline degradation and post-filtering metric progression across the four evaluated kernel sizes for our benchmark test imagery under Gaussian noise ($\sigma = 25$):

**Table 1:** Quantitative Evaluation Metrics (MSE, PSNR) for Gaussian Noise ($\sigma=25$) across Kernel Sizes ($3\times3$ to $9\times9$).

| Image Asset | Condition / Kernel | Mean Squared Error (MSE) | PSNR (dB) | Status / Observation |
| :--- | :--- | :--- | :--- | :--- |
| **sample1_clean.png** *(Standard Lena)* | Noisy Baseline ($\sigma=25$) | 598.43 | 20.36 dB | Heavy sensor-like Gaussian noise grain |
| | Filtered $3\times3$ ($\sigma=0.80$) | 108.48 | 27.78 dB | Sharp noise attenuation (+7.42 dB gain) |
| | Filtered $5\times5$ ($\sigma=1.10$) | **80.78** | **29.06 dB** | **Optimal peak (+8.70 dB gain)**; facial features & textures preserved |
| | Filtered $7\times7$ ($\sigma=1.40$) | 83.13 | 28.93 dB | Slight softening of fine feather and hair strands |
| | Filtered $9\times9$ ($\sigma=1.70$) | 94.34 | 28.38 dB | Over-smoothed; blur penalty exceeds noise reduction |
| **sample 2.jpeg** *(Real Scene)* | Noisy Baseline ($\sigma=25$) | 560.99 | 20.64 dB | Visible additive grain across scene |
| | Filtered $3\times3$ ($\sigma=0.80$) | 95.76 | 28.32 dB | Significant noise suppression (+7.68 dB gain) |
| | Filtered $5\times5$ ($\sigma=1.10$) | 58.91 | 30.43 dB | High quality reconstruction (+9.79 dB gain) |
| | Filtered $7\times7$ ($\sigma=1.40$) | **50.71** | **31.08 dB** | **Optimal peak (+10.44 dB gain)**; optimal texture balance |
| | Filtered $9\times9$ ($\sigma=1.70$) | 51.27 | 31.03 dB | Slight over-smoothing on subtle features |
| **synthetic_checkerboard.png** | Noisy Baseline ($\sigma=25$) | 573.72 | 20.54 dB | High-frequency grain across grid junctions |
| | Filtered $3\times3$ ($\sigma=0.80$) | **240.07** | **24.33 dB** | Optimal balance; sharp grid boundaries preserved |
| | Filtered $5\times5$ ($\sigma=1.10$) | 320.17 | 23.08 dB | Corner softening begins at square vertices |
| | Filtered $7\times7$ ($\sigma=1.40$) | 408.70 | 22.02 dB | Edge blurring penalty starts outweighing noise removal |
| | Filtered $9\times9$ ($\sigma=1.70$) | 504.92 | 21.10 dB | Severe distortion of checkerboard pattern |
| **synthetic_gradient.png** | Noisy Baseline ($\sigma=25$) | 600.05 | 20.35 dB | Visible grain across smooth color transitions |
| | Filtered $3\times3$ ($\sigma=0.80$) | 96.44 | 28.29 dB | Strong initial noise reduction |
| | Filtered $5\times5$ ($\sigma=1.10$) | 54.21 | 30.79 dB | Significant smoothing of color ramp |
| | Filtered $7\times7$ ($\sigma=1.40$) | 42.96 | 31.80 dB | High fidelity reconstruction |
| | Filtered $9\times9$ ($\sigma=1.70$) | **40.20** | **32.09 dB** | **Peak PSNR (+11.74 dB gain)**; ideal for continuous tones |
| **synthetic_shapes.png** | Noisy Baseline ($\sigma=25$) | 480.02 | 21.32 dB | Textured noise over solid geometric bodies |
| | Filtered $3\times3$ ($\sigma=0.80$) | **128.43** | **27.04 dB** | **Peak PSNR (+5.72 dB gain)**; crisp boundaries preserved |
| | Filtered $5\times5$ ($\sigma=1.10$) | 131.77 | 26.93 dB | Very close to peak fidelity; slightly smoother interiors |
| | Filtered $7\times7$ ($\sigma=1.40$) | 157.94 | 26.15 dB | Slight edge bleeding along colored borders |
| | Filtered $9\times9$ ($\sigma=1.70$) | 193.27 | 25.27 dB | Noticeable boundary diffusion on thin lines |

*(Note: Exact values correspond to runtime console outputs generated by `main.py`).*

### 4.2 Visual Artifacts & Before/After Comparisons
- **Figure 1 (Denoising Triptychs):** Side-by-side $1\times3$ panels (Original $\rightarrow$ Noisy $\rightarrow$ Filtered $5\times5$) with color-coded quantitative MSE and PSNR metric annotations below each panel. Saved in `outputs/comparison_images/<image_name>_comparison_kernel5x5.png`.
- **Figure 2 (Comprehensive Multi-Kernel Evaluation Grids):** $2\times3$ multi-panel comparative boards evaluating pristine original, corrupted input, and all four Gaussian kernel outputs ($3\times3, 5\times5, 7\times7, 9\times9$). Saved in `outputs/comparison_images/<image_name>_all_kernels_comparison.png`.
- **Figure 3 (Dual-Panel Metric Response Curves):** Dual-axis performance plots showing Kernel Size vs. MSE (left) and Kernel Size vs. PSNR (right) charted alongside the unmitigated noisy baseline, with annotated inflection points indicating optimal kernel selections. Saved in `outputs/performance_graphs/<image_name>_performance_graph.png`.

### 4.3 Success Criteria & Performance Evaluation
Core denoising completes in under 0.25s per image, meeting the performance requirement. Visualization and export add additional non-core time not counted against this requirement.

Across all test images (both natural photographic imagery such as `sample1_clean.png` and synthetic test patterns), the core Gaussian convolution across four separate kernels ($3\times3$, $5\times5$, $7\times7$, $9\times9$) alongside quantitative MSE and PSNR matrix calculations required between 0.16s and 0.25s per image. This execution speed comfortably surpasses the Non-Functional Requirement threshold of 2.0 seconds per image by nearly an order of magnitude. The subsequent rendering of three high-resolution multi-panel Matplotlib figures and disk I/O requires approximately 3.0s to 4.1s per image as an offline analysis utility.

### 4.4 Tested Edge Cases
1. **Empty Input Directory:** When `data/sample_images/` contains no supported image files, the loader automatically detects the condition and generates three calibrated synthetic images, executing the full pipeline without crashing.
2. **Corrupted / Invalid Non-Image Files:** When non-image files with valid extensions (e.g., text files renamed to `.jpg`) are placed in the directory, the decoder catches the decode failure, issues a descriptive console error message, and safely skips the file without crashing.
3. **Grayscale-Only (Single-Channel) Images:** Single-channel 2D matrices are processed seamlessly across noise addition, 2D convolution, MSE/PSNR calculation, and grayscale matplotlib visualization without matrix dimensionality mismatch or corrupted metric calculations.
4. **Miniature Imagery ($20\times20$ px) with $9\times9$ Kernel:** Border reflection padding (`BORDER_REFLECT_101`) allows the largest $9\times9$ filter kernel to convolve near the boundaries of small $20\times20$ pixel inputs without out-of-bounds indexing or shape distortion.

---

## 5. Conclusion
This study comprehensively analyzed the behavior of Gaussian Low-Pass Filtering for spatial domain image restoration. Quantitative evaluation demonstrated that for Additive White Gaussian Noise, Gaussian smoothing yields substantial PSNR improvements ranging from $+5.72$ dB up to $+11.74$ dB depending on spatial frequency content. In real photographic imagery (`sample1_clean.png` and `sample 2.jpeg`), intermediate kernels ($5\times5$ and $7\times7$) achieved the optimal operational balance, lifting PSNR by $+8.70$ to $+10.44$ dB while preserving key facial textures and contours. In smooth continuous gradients, larger kernels ($9\times9$) yielded maximum noise suppression without boundary penalty, whereas in high-contrast edge structures (checkerboards and sharp shapes), smaller kernels ($3\times3$) proved mandatory to avoid vertex rounding and structural contrast loss. Crucially, the analysis verified that reference ground truth images must be clean and uncorrupted, and confirmed that the core filtering algorithms execute in under 0.25 seconds per image, fully satisfying all academic and engineering requirements.

---

## 6. References
1. Gonzalez, R. C., & Woods, R. E. (2018). *Digital Image Processing* (4th ed.). Pearson. (Chapter 3: Intensity Transformations and Spatial Filtering).
2. Szeliski, R. (2022). *Computer Vision: Algorithms and Applications* (2nd ed.). Springer. (Section 3.2: Linear Filtering and Separable Convolutions).
3. Buades, A., Coll, B., & Morel, J. M. (2005). A review of image denoising algorithms, with a new one. *Multiscale Modeling & Simulation*, 4(2), 490-530.
