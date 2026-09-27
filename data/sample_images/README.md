# Sample Images Directory

This directory is intended to store the input images for the Gaussian Filter Image Smoothing experiment.

## Recommended Image Types
For the CS-305 Computer Vision case study, we recommend placing **10 to 30 diverse images** in this folder, covering:
- **Nature / Landscapes** (e.g., foliage, water, mountains - high frequency textures)
- **Architecture / Buildings** (e.g., geometric edges, bricks, straight lines)
- **Roads / Urban Scenes** (e.g., pavement, street signs, vehicles)
- **Faces / Portraits** (e.g., skin tones, facial contours, eye details)
- **Close-up Objects / Macro** (e.g., tools, text documents, sharp object edges)

## Supported File Formats
- `.jpg` / `.jpeg`
- `.png`

## How to Populate
1. Copy your `.jpg`, `.jpeg`, or `.png` images into this directory (`data/sample_images/`).
2. Example filenames:
   - `nature_01.jpg`
   - `building_02.png`
   - `portrait_03.jpg`
3. Run `python src/main.py` from the `gaussian_filter_project` directory. The pipeline will automatically discover and process all supported images.

## ⚠️ Critical Requirement: Clean Reference Images
> **IMPORTANT:** All reference images placed in this folder **MUST be pristine, clean, and noise-free**. 
>
> The experimental pipeline uses each input image as the uncorrupted **ground truth reference** ($I_{\text{clean}}$) against which synthetic noise is injected and post-filtering fidelity (MSE and PSNR) is calculated. If an input image is already corrupted with sensor grain or noise artifacts, the filtering operation will smooth the pre-existing grain, producing misleading MSE/PSNR metrics that falsely penalize larger filter kernels.

*Note: If this folder is empty when running `main.py`, the system will automatically synthesize 3 clean test images (geometric shapes, smooth gradient, and checkerboard pattern) so the pipeline runs out-of-the-box.*
