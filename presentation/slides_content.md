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
  * Benchmarked under standardized heavy Additive White Gaussian Noise (AWGN, $\sigma=50$) and Salt-and-Pepper impulse noise ($2\%$).
* **Evaluation Framework:** Quantitative evaluation via Mean Squared Error (MSE) and Peak Signal-to-Noise Ratio (PSNR), combined with visual fidelity inspection.
* **Key Finding:** Gaussian filtering delivers up to $+13.2$ dB PSNR gain on continuous gradients, while natural scenes under heavy noise ($\sigma=50$) achieve optimal restoration with larger $7\times7$ and $9\times9$ kernels to suppress strong variance.

---

## Slide 2: Literature Review
* **Image Degradation Models:**
  * *Gaussian Noise (AWGN):* Continuous, zero-mean normal distribution ($\mu=0, \sigma=50$); models heavy thermal sensor agitation.
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
  2. *Noise Simulation (FR-2):* Injects parameterized AWGN ($\sigma=50$) or Salt-and-Pepper ($2\%$) with deterministic random seeding.
  3. *Gaussian Filtering (FR-3):* Convolves image using OpenCV `cv2.GaussianBlur` with border reflection across $3\times3$, $5\times5$, $7\times7$, $9\times9$.
  4. *Quantitative Metrics (FR-5):* Computes exact MSE and PSNR against pristine ground truth.
  5. *Visualization & Export (FR-4 & FR-6):* Renders side-by-side triptychs, multi-kernel boards, and dual-axis performance curves.
* **Auto-Sigma Heuristic:** $\sigma = 0.3 \cdot ((K - 1) \cdot 0.5 - 1) + 0.8$ ($K=3 \rightarrow 0.8$, $K=5 \rightarrow 1.1$, $K=7 \rightarrow 1.4$, $K=9 \rightarrow 1.7$).
* **Performance Constraint:** Core denoising and evaluation executes in $< 0.40$ s per image (surpassing the $< 2.0$ s project requirement).

---

## Slide 4: Results & Conclusion
* **Quantitative Findings (Benchmark Summary on Gaussian Noise, $\sigma=50$):**
  * *Photographic Imagery (Lena / sample1_clean):* Optimal at $9\times9$ (PSNR $14.81\text{ dB (Noisy)} \rightarrow 22.57\text{ dB }(3\times3) \rightarrow 24.88\text{ dB }(5\times5) \rightarrow 26.05\text{ dB }(9\times9)$); MSE drops from $2147.8$ to $161.3$ (+11.24 dB gain).
  * *Real Scenes (sample2 & s4):* Optimal at $9\times9$ (sample2 PSNR reaches $26.76\text{ dB}$, $+11.66\text{ dB}$ gain; s4 reaches $25.29\text{ dB}$, $+9.79\text{ dB}$ gain).
  * *Smooth Gradient:* Monotonic PSNR increase ($14.79\text{ dB (Noisy)} \rightarrow 22.74\text{ dB }(3\times3) \rightarrow 28.02\text{ dB }(9\times9)$); MSE drops from $2158.7$ to $102.5$ (+13.23 dB gain).
  * *Geometric Shapes:* Optimal peak at $7\times7$ (PSNR $23.21\text{ dB}$, MSE $310.6$, $+7.03\text{ dB}$ gain); $9\times9$ begins perimeter edge blurring.
  * *Checkerboard Pattern:* Optimal peak at $5\times5$ (PSNR $21.36\text{ dB}$, $+6.03\text{ dB}$ gain); larger kernels severely round square junctions.
* **Noise Sensitivity & Kernel Scaling Insights:**
  * Heavier noise ($\sigma=50$) shifts optimal kernel sizes upward ($7\times7, 9\times9$ win on complex natural scenes) because aggressive spatial averaging is required to suppress severe noise variance.
  * Ineffective for Salt-and-Pepper noise: spreads impulse spikes into blurry halos (requires non-linear median filtering).
* **Engineering Recommendations:**
  * Use $3\times3$ or $5\times5$ when edge preservation is paramount under mild-to-moderate noise.
  * Employ larger kernels ($7\times7, 9\times9$) under heavy AWGN regimes ($\sigma \ge 50$) or for smooth continuous backgrounds.

---

## Slide 5: References
* Gonzalez, R. C., & Woods, R. E. (2018). *Digital Image Processing* (4th ed.). Pearson. (Chapter 3: Intensity Transformations and Spatial Filtering).
* Szeliski, R. (2022). *Computer Vision: Algorithms and Applications* (2nd ed.). Springer. (Section 3.2: Linear Filtering and Separable Convolutions).
* Buades, A., Coll, B., & Morel, J. M. (2005). A review of image denoising algorithms, with a new one. *Multiscale Modeling & Simulation*, 4(2), 490–530.
* OpenCV Development Team (2024). *Image Filtering: Gaussian Blur*. OpenCV Documentation. https://docs.opencv.org/
