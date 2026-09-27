# Slide Deck: Design and Analysis of a Gaussian Filter for Low-Pass Image Smoothing

**Course:** CS-305 Computer Vision Case Study  
**Team:** 1–4 Student Engineering Team  
**Format:** 5-Slide Presentation Deck  

---

## Slide 1: Abstract
* **Core Objective:** Design, implement, and benchmark a 2D Gaussian Low-Pass Filter pipeline for spatial domain image denoising.
* **Problem Statement:** Image acquisition sensors introduce corruptive noise (thermal noise, photon shot noise, transmission errors) degrading downstream vision tasks.
* **Technical Scope:**
  * Evaluated across 4 kernel dimensions ($3\times3$, $5\times5$, $7\times7$, $9\times9$) with dynamically computed $\sigma$.
  * Benchmarked against Additive White Gaussian Noise (AWGN) and Salt-and-Pepper impulse noise.
* **Evaluation Framework:** Quantitative evaluation via Mean Squared Error (MSE) and Peak Signal-to-Noise Ratio (PSNR), combined with visual fidelity inspection.
* **Key Finding:** Gaussian filtering delivers up to $+11.7$ dB PSNR gain on continuous gradients, while structured scenes exhibit an optimal threshold at $3\times3$ or $5\times5$ before edge-blur degradation dominates.

---

## Slide 2: Literature Review
* **Image Degradation Models:**
  * *Gaussian Noise (AWGN):* Continuous, zero-mean normal distribution ($\mu=0, \sigma=25$); models thermal sensor agitation.
  * *Salt-and-Pepper Noise:* Discrete impulse spikes ($0$ or $255$); models bit errors and faulty sensor diodes.
* **Spatial Low-Pass Filtering Fundamentals:**
  * High-frequency spatial variations correspond to fine detail and noise; low frequencies represent structural regions.
  * Low-pass filters attenuate high frequencies to smooth out erratic pixel variances.
* **The 2D Gaussian Function:**
  * Equation: $G(x, y) = \frac{1}{2\pi\sigma^2} \exp\left(-\frac{x^2+y^2}{2\sigma^2}\right)$
  * *Isotropic & Bell-Shaped:* Radially symmetric weighting prevents directional bias.
  * *No Ringing Artifacts:* Unlike box/mean filters, the smooth Gaussian frequency response has no sharp cutoff frequencies.
* **Separability Advantage:**
  * Factorizes into $G(x,y) = G(x) \cdot G(y)$ (two 1D convolutions).
  * Reduces computational complexity from $\mathcal{O}(K^2)$ to $\mathcal{O}(2K)$ operations per pixel.

---

## Slide 3: Methodology & Architecture
* **Modular Pipeline Architecture (5-Stage Flow):**
  1. *Image Ingestion (FR-1):* Loads `.jpg`, `.jpeg`, `.png`; auto-generates 3 synthetic test patterns (shapes, gradient, checkerboard) if empty.
  2. *Noise Simulation (FR-2):* Injects parameterized AWGN ($\sigma=25$) or Salt-and-Pepper ($2\%$) with deterministic random seeding.
  3. *Gaussian Filtering (FR-3):* Convolves image using OpenCV `cv2.GaussianBlur` with border reflection across $3\times3$, $5\times5$, $7\times7$, $9\times9$.
  4. *Quantitative Metrics (FR-5):* Computes exact MSE and PSNR against pristine ground truth.
  5. *Visualization & Export (FR-4 & FR-6):* Renders side-by-side triptychs, multi-kernel boards, and dual-axis performance curves.
* **Auto-Sigma Heuristic:** $\sigma = 0.3 \cdot ((K - 1) \cdot 0.5 - 1) + 0.8$ ($K=3 \rightarrow 0.8$, $K=5 \rightarrow 1.1$, $K=7 \rightarrow 1.4$, $K=9 \rightarrow 1.7$).
* **Performance Constraint:** Core denoising and evaluation executes in $< 0.25$ s per image (surpassing the $< 2.0$ s project requirement).

---

## Slide 4: Results & Conclusion
* **Quantitative Findings (Benchmark Summary on Gaussian Noise):**
  * *Photographic Imagery (Lena / sample1_clean):* Optimal at $5\times5$ (PSNR $20.36\text{ dB} \rightarrow 27.78\text{ dB }(3\times3) \rightarrow 29.06\text{ dB }(5\times5)$); MSE drops from $598.4$ to $80.8$.
  * *Smooth Gradient:* PSNR increases monotonically ($20.35\text{ dB (Noisy)} \rightarrow 28.29\text{ dB }(3\times3) \rightarrow 32.09\text{ dB }(9\times9)$); MSE drops from $600.0$ to $40.2$.
  * *Geometric Shapes:* Optimal peak at $3\times3$ / $5\times5$ (PSNR $27.04\text{ dB}$, MSE $128.4$); $7\times7$ & $9\times9$ degrade PSNR due to perimeter edge blur.
  * *Checkerboard Pattern:* Peak at $3\times3$ (PSNR $24.33\text{ dB}$); larger kernels severely round square junctions (PSNR drops to $21.10\text{ dB}$ at $9\times9$).
* **Noise Sensitivity Observations:**
  * Highly effective for Gaussian sensor noise (attenuates random high-frequency fluctuations).
  * Ineffective for Salt-and-Pepper noise: spreads impulse spikes into blurry halos (requires non-linear median filtering).
* **Engineering Recommendations:**
  * Select $3\times3$ or $5\times5$ for general vision preprocessing (object detection, edge detection).
  * Reserve larger kernels ($7\times7+$) for background blur, depth simulation, or low-texture sky/gradient regions.

---

## Slide 5: References
* Gonzalez, R. C., & Woods, R. E. (2018). *Digital Image Processing* (4th ed.). Pearson. (Chapter 3: Intensity Transformations and Spatial Filtering).
* Szeliski, R. (2022). *Computer Vision: Algorithms and Applications* (2nd ed.). Springer. (Section 3.2: Linear Filtering and Separable Convolutions).
* Buades, A., Coll, B., & Morel, J. M. (2005). A review of image denoising algorithms, with a new one. *Multiscale Modeling & Simulation*, 4(2), 490–530.
* OpenCV Development Team (2024). *Image Filtering: Gaussian Blur*. OpenCV Documentation. https://docs.opencv.org/
