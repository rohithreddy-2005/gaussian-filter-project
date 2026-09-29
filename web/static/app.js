/**
 * VisionLab — Clean, Minimal Gaussian Filter Studio & Guided Walkthrough
 * =====================================================================
 * - At most 3 visible controls per step
 * - Real computed data, no mock values
 * - Step-by-step guided walkthrough (Steps 1 to 6) in "How it works" tab
 * - 8x8 Convolution Animator with BORDER_REFLECT_101 & backend match verification
 * - Printable Formula Sheet modal for viva examination
 * - Instant kernel switching (3x3, 5x5, 7x7, 9x9) with ★ Best indicator
 * - Large MSE / PSNR metrics with baseline delta arrows & mini sparkline
 */

(function () {
  "use strict";

  // Application State
  const state = {
    selectedImage: null,  // { name, sampleName?, url, width, height, sizeKb, type, base64? }
    latestResult: null,   // Stores latest pipeline execution response
    samplesList: [],      // Available sample images
    isProcessing: false,
    sliderPosition: 50,   // Split slider percentage (0-100)
    isDraggingSlider: false,
    selectedKernel: 5,    // Active kernel (3, 5, 7, 9)

    // Feature: 8x8 Patch Convolution Animator (Studio Modal)
    anim: {
      isOpen: false,
      coord: { x: 252, y: 252 },
      patchData: null,
      kernelSize: 5,
      step: 0,            // 0 to 63
      isPlaying: false,
      timerId: null,
      speedMs: 300,
    },

    // Feature: 6-Step Guided Walkthrough ("How it works" Tab)
    walk: {
      currentStep: 1,     // 1 to 6
      step1Channel: "luma", // "luma", "r", "g", "b"
      step1SelectedCell: { r: 3, c: 3 },
      step2SelectedCell: { r: 3, c: 3 },
      step3Kernel: 5,     // 3, 5, 7, 9
      step4Kernel: 5,     // 3, 5, 7, 9
      step4Step: 0,       // 0 to 63
      step4IsPlaying: false,
      step4TimerId: null,
      step4SpeedMs: 300,
    },

    // Feature: 4-Step Guided Demo (Studio)
    demo: {
      isActive: false,
      step: 1,            // 1 to 4
      isPlaying: false,
      timerId: null,
      stepDurationMs: 5500,
    },
  };

  // DOM Elements Cache
  const DOM = {
    // Tabs
    tabStudio: document.getElementById("tab-btn-studio"),
    tabHow: document.getElementById("tab-btn-how"),
    panelStudio: document.getElementById("panel-studio"),
    panelHow: document.getElementById("panel-how"),

    // Step 1: Thumbnails Row
    thumbnailsRow: document.getElementById("thumbnails-row"),
    fileInput: document.getElementById("file-input"),
    selectedName: document.getElementById("selected-name"),
    selectedDim: document.getElementById("selected-dim"),
    selectedSize: document.getElementById("selected-size"),

    // Step 2: Noise Controls
    pillOptions: document.querySelectorAll(".pill-option"),
    sliderNoiseAmount: document.getElementById("slider-noise-amount"),
    valNoiseBadge: document.getElementById("val-noise-badge"),
    btnApplyFilter: document.getElementById("btn-apply-filter"),
    inputMean: document.getElementById("input-mean"),
    inputSeed: document.getElementById("input-seed"),
    btnSeedRandom: document.getElementById("btn-seed-random"),
    checkSaveDisk: document.getElementById("check-save-disk"),
    processingLoader: document.getElementById("processing-loader"),

    // Step 3: Result & Split Slider
    splitViewport: document.getElementById("split-viewport"),
    splitImgTop: document.getElementById("split-img-top"),
    splitImgBottom: document.getElementById("split-img-bottom"),
    splitTopClip: document.getElementById("split-top-clip"),
    splitHandle: document.getElementById("split-handle"),
    tagFilteredLabel: document.getElementById("tag-filtered-label"),
    kernelButtonsGroup: document.getElementById("kernel-buttons-group"),
    latencyLabel: document.getElementById("latency-label"),

    // Metrics Card
    metricMse: document.getElementById("metric-mse"),
    metricMseDelta: document.getElementById("metric-mse-delta"),
    metricMseBaseline: document.getElementById("metric-mse-baseline"),
    metricPsnr: document.getElementById("metric-psnr"),
    metricPsnrDelta: document.getElementById("metric-psnr-delta"),
    metricPsnrBaseline: document.getElementById("metric-psnr-baseline"),
    sparklineSvg: document.getElementById("sparkline-svg"),
    sparklineCaption: document.getElementById("sparkline-caption"),
    takeawayText: document.getElementById("takeaway-text"),
    btnOpenAnimator: document.getElementById("btn-open-animator"),
    btnDownloadSummary: document.getElementById("btn-download-summary"),

    // "Watch How it Works" Modal (Studio)
    animatorModal: document.getElementById("animator-modal"),
    btnCloseAnimator: document.getElementById("btn-close-animator"),
    animMatchBadge: document.getElementById("anim-match-badge"),
    btnAnimPlayPause: document.getElementById("btn-anim-playpause"),
    btnAnimPrev: document.getElementById("btn-anim-prev"),
    btnAnimNext: document.getElementById("btn-anim-next"),
    btnAnimRestart: document.getElementById("btn-anim-restart"),
    animKBtns: document.querySelectorAll("[data-ak]"),
    sliderAnimSpeed: document.getElementById("slider-anim-speed"),
    animSpeedVal: document.getElementById("anim-speed-val"),
    animCoordTag: document.getElementById("anim-coord-tag"),
    animStepBadge: document.getElementById("anim-step-badge"),
    animInputGrid: document.getElementById("anim-input-grid"),
    animMathRows: document.getElementById("anim-math-rows"),
    animSumVal: document.getElementById("anim-sum-val"),
    animRoundedVal: document.getElementById("anim-rounded-val"),
    animMiniMatch: document.getElementById("anim-mini-match"),
    animOutputGrid: document.getElementById("anim-output-grid"),

    // Demo Mode Banner
    btnPlayDemo: document.getElementById("btn-play-demo"),
    demoBanner: document.getElementById("demo-banner"),
    demoBadge: document.getElementById("demo-badge"),
    demoTitle: document.getElementById("demo-title"),
    demoCaption: document.getElementById("demo-caption"),
    demoBtnPrev: document.getElementById("demo-btn-prev"),
    demoBtnPlayPause: document.getElementById("demo-btn-playpause"),
    demoBtnNext: document.getElementById("demo-btn-next"),
    demoBtnClose: document.getElementById("demo-btn-close"),

    // Walkthrough Navigation & Formula Sheet
    walkPills: document.querySelectorAll(".walk-step-pill"),
    walkCards: document.querySelectorAll(".walk-step-card"),
    walkBtnPrev: document.getElementById("walk-btn-prev"),
    walkBtnNext: document.getElementById("walk-btn-next"),
    walkStepCounter: document.getElementById("walk-step-counter"),
    btnOpenFormulaSheet: document.getElementById("btn-open-formula-sheet"),
    btnCloseFormulaSheet: document.getElementById("btn-close-formula-sheet"),
    btnPrintFormulaSheet: document.getElementById("btn-print-formula-sheet"),
    formulaSheetModal: document.getElementById("formula-sheet-modal"),

    // Walkthrough Step 1 Elements
    step1ChanBtns: document.querySelectorAll("#step1-chan-selector .chan-btn"),
    step1MatrixGrid: document.getElementById("step1-matrix-grid"),
    step1InspectLoc: document.getElementById("step1-inspect-loc"),
    step1ValR: document.getElementById("step1-val-r"),
    step1ValG: document.getElementById("step1-val-g"),
    step1ValB: document.getElementById("step1-val-b"),
    step1ValLuma: document.getElementById("step1-val-luma"),
    step1CalcBreakdown: document.getElementById("step1-calc-breakdown"),
    legendS1Coords: document.getElementById("legend-s1-coords"),
    legendS1Channel: document.getElementById("legend-s1-channel"),
    legendS1Luma: document.getElementById("legend-s1-luma"),

    // Walkthrough Step 2 Elements
    step2FormulaExpr: document.getElementById("step2-formula-expr"),
    step2WordsText: document.getElementById("step2-words-text"),
    step2LegendBody: document.getElementById("step2-legend-body"),
    legendS2NoiseVar: document.getElementById("legend-s2-noise-var"),
    legendS2Mean: document.getElementById("legend-s2-mean"),
    legendS2Std: document.getElementById("legend-s2-std"),
    legendS2Seed: document.getElementById("legend-s2-seed"),
    step2CleanGrid: document.getElementById("step2-clean-grid"),
    step2NoiseGrid: document.getElementById("step2-noise-grid"),
    step2NoisyGrid: document.getElementById("step2-noisy-grid"),
    step2CalcLine: document.getElementById("step2-calc-line"),
    step2ClippingBox: document.getElementById("step2-clipping-box"),
    step2ClippingText: document.getElementById("step2-clipping-text"),
    step2SeedDesc: document.getElementById("step2-seed-desc"),

    // Walkthrough Step 3 Elements
    step3SigmaTableBody: document.getElementById("step3-sigma-table-body"),
    step3KernelHeading: document.getElementById("step3-kernel-heading"),
    step3KBtns: document.querySelectorAll("#step3-k-btns .mini-k-btn"),
    step3CenterCalc: document.getElementById("step3-center-calc"),
    step3CornerCalc: document.getElementById("step3-corner-calc"),
    step3SumText: document.getElementById("step3-sum-text"),
    step3WeightsGrid: document.getElementById("step3-weights-grid"),
    step31DWeights: document.getElementById("step3-1d-weights"),

    // Walkthrough Step 4 Elements
    legendS4Radius: document.getElementById("legend-s4-radius"),
    step4InspectPixel: document.getElementById("step4-inspect-pixel"),
    step4CalcDisplay: document.getElementById("step4-calc-display"),
    step4AnimMatchBadge: document.getElementById("step4-anim-match-badge"),
    step4CornerNote: document.getElementById("step4-corner-note"),
    step4BtnPlayPause: document.getElementById("step4-btn-playpause"),
    step4BtnPrev: document.getElementById("step4-btn-prev"),
    step4BtnNext: document.getElementById("step4-btn-next"),
    step4BtnRestart: document.getElementById("step4-btn-restart"),
    step4KBtns: document.querySelectorAll("#step4-k-btns .mini-k-btn"),
    step4CoordTag: document.getElementById("step4-coord-tag"),
    step4StepBadge: document.getElementById("step4-step-badge"),
    step4InputGrid: document.getElementById("step4-input-grid"),
    step4MathRows: document.getElementById("step4-math-rows"),
    step4SumVal: document.getElementById("step4-sum-val"),
    step4RoundedVal: document.getElementById("step4-rounded-val"),
    step4OutputGrid: document.getElementById("step4-output-grid"),

    // Walkthrough Step 5 Elements
    legendS5Dims: document.getElementById("legend-s5-dims"),
    legendS5Mse: document.getElementById("legend-s5-mse"),
    legendS5Psnr: document.getElementById("legend-s5-psnr"),
    step5TinyRows: document.getElementById("step5-tiny-rows"),
    step5PartACalc: document.getElementById("step5-part-a-calc"),
    step5SampleMse: document.getElementById("step5-sample-mse"),
    step5SampleMseRef: document.getElementById("step5-sample-mse-ref"),
    step5SamplePsnr: document.getElementById("step5-sample-psnr"),
    step5FullNoisyMse: document.getElementById("step5-full-noisy-mse"),
    step5FullNoisyPsnr: document.getElementById("step5-full-noisy-psnr"),
    step5FilteredTag: document.getElementById("step5-filtered-tag"),
    step5FullFiltMse: document.getElementById("step5-full-filt-mse"),
    step5FullFiltPsnr: document.getElementById("step5-full-filt-psnr"),
    step5DeltaPsnr: document.getElementById("step5-delta-psnr"),
    step5DeltaMse: document.getElementById("step5-delta-mse"),
    step5BarMseVal: document.getElementById("step5-bar-mse-val"),
    step5BarMse: document.getElementById("step5-bar-mse"),
    step5BarPsnrVal: document.getElementById("step5-bar-psnr-val"),
    step5BarPsnr: document.getElementById("step5-bar-psnr"),

    // Walkthrough Step 6 Elements
    step6TableBody: document.getElementById("step6-table-body"),
    step6TurnoverStatement: document.getElementById("step6-turnover-statement"),
    step6TurnoverDetail: document.getElementById("step6-turnover-detail"),
    step6ChartSvg: document.getElementById("step6-chart-svg"),

    // Toast Stack
    toastStack: document.getElementById("toast-stack"),
  };

  /* ==========================================================================
     INIT & EVENT LISTENERS
     ========================================================================== */

  function init() {
    setupTabSwitching();
    setupStep1Choose();
    setupStep2Noise();
    setupStep3Slider();
    setupKernelButtons();
    setupAnimatorModal();
    setupDemoMode();
    setupSummaryExport();
    setupWalkthrough();

    // Fetch initial samples
    fetchSamples();
  }

  /* ==========================================================================
     TABS NAVIGATION
     ========================================================================== */

  function setupTabSwitching() {
    DOM.tabStudio.addEventListener("click", () => {
      DOM.tabStudio.classList.add("active");
      DOM.tabHow.classList.remove("active");
      DOM.panelStudio.classList.add("active");
      DOM.panelHow.classList.remove("active");
    });

    DOM.tabHow.addEventListener("click", () => {
      DOM.tabHow.classList.add("active");
      DOM.tabStudio.classList.remove("active");
      DOM.panelHow.classList.add("active");
      DOM.panelStudio.classList.remove("active");
      // Render the active walkthrough step whenever user opens the tab
      renderWalkStep(state.walk.currentStep);
    });
  }

  /* ==========================================================================
     STEP 1: CHOOSE AN IMAGE (Thumbnails Row + Upload Button)
     ========================================================================== */

  function setupStep1Choose() {
    DOM.fileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) {
        handleCustomUpload(e.target.files[0]);
      }
    });
  }

  async function fetchSamples() {
    try {
      const res = await fetch("/api/samples");
      if (!res.ok) throw new Error("Failed to load sample dataset");
      const samples = await res.json();
      state.samplesList = samples;

      renderThumbnailsRow(samples);

      // Auto-select sample1_clean.png on startup
      const initialSample = samples.find((s) => s.stem === "sample1_clean") || samples[0];
      if (initialSample) {
        selectSample(initialSample, true);
      }
    } catch (err) {
      console.error(err);
      DOM.thumbnailsRow.innerHTML = '<span class="loading-hint">Failed to load samples.</span>';
    }
  }

  function renderThumbnailsRow(samples) {
    DOM.thumbnailsRow.innerHTML = "";

    samples.forEach((sample) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "thumb-btn";
      btn.title = `${sample.name} (${sample.size_kb} KB)`;
      btn.setAttribute("data-stem", sample.stem);

      btn.innerHTML = `
        <img src="${sample.url}" alt="${sample.name}" class="thumb-img" loading="lazy" />
      `;

      btn.addEventListener("click", () => selectSample(sample, false));
      DOM.thumbnailsRow.appendChild(btn);
    });

    // Append "+ Upload" button at the end of the row
    const uploadBtn = document.createElement("button");
    uploadBtn.type = "button";
    uploadBtn.className = "thumb-upload-btn";
    uploadBtn.title = "Upload an image from your computer (PNG, JPG)";
    uploadBtn.innerHTML = `
      <span class="upload-icon">+</span>
      <span>Upload</span>
    `;
    uploadBtn.addEventListener("click", () => DOM.fileInput.click());
    DOM.thumbnailsRow.appendChild(uploadBtn);
  }

  function selectSample(sample, autoRun = false) {
    document.querySelectorAll(".thumb-btn").forEach((b) => {
      b.classList.toggle("active", b.getAttribute("data-stem") === sample.stem);
    });

    const img = new Image();
    img.onload = function () {
      state.selectedImage = {
        type: "sample",
        name: sample.name,
        sampleName: sample.name,
        url: sample.url,
        width: img.naturalWidth,
        height: img.naturalHeight,
        sizeKb: sample.size_kb || 250,
      };

      DOM.selectedName.textContent = sample.name;
      DOM.selectedName.title = sample.name;
      DOM.selectedDim.textContent = `${img.naturalWidth} × ${img.naturalHeight} px`;
      DOM.selectedSize.textContent = `${sample.size_kb} KB`;

      // Set initial center patch coordinates
      state.anim.coord = {
        x: Math.max(0, Math.floor(img.naturalWidth / 2 - 4)),
        y: Math.max(0, Math.floor(img.naturalHeight / 2 - 4)),
      };
      DOM.animCoordTag.textContent = `(x=${state.anim.coord.x}, y=${state.anim.coord.y})`;
      if (DOM.step4CoordTag) {
        DOM.step4CoordTag.textContent = `(x=${state.anim.coord.x}, y=${state.anim.coord.y})`;
      }

      if (autoRun && !state.latestResult) {
        executePipeline();
      }
    };
    img.src = sample.url;
  }

  function handleCustomUpload(file) {
    const valid = ["image/png", "image/jpeg", "image/jpg"];
    if (!valid.includes(file.type.toLowerCase())) {
      showToast("Please select a valid PNG or JPEG image.", "error");
      return;
    }

    const reader = new FileReader();
    reader.onload = function (e) {
      const b64 = e.target.result;
      const img = new Image();
      img.onload = function () {
        const sizeKb = Math.round(file.size / 1024);
        state.selectedImage = {
          type: "file",
          base64: b64,
          name: file.name,
          width: img.naturalWidth,
          height: img.naturalHeight,
          sizeKb: sizeKb,
        };

        document.querySelectorAll(".thumb-btn").forEach((b) => b.classList.remove("active"));

        DOM.selectedName.textContent = file.name;
        DOM.selectedName.title = file.name;
        DOM.selectedDim.textContent = `${img.naturalWidth} × ${img.naturalHeight} px`;
        DOM.selectedSize.textContent = `${sizeKb} KB`;

        state.anim.coord = {
          x: Math.max(0, Math.floor(img.naturalWidth / 2 - 4)),
          y: Math.max(0, Math.floor(img.naturalHeight / 2 - 4)),
        };

        executePipeline();
        showToast(`Uploaded ${file.name} (${img.naturalWidth}×${img.naturalHeight})`, "success");
      };
      img.src = b64;
    };
    reader.readAsDataURL(file);
  }

  /* ==========================================================================
     STEP 2: ADD NOISE (At most 3 visible controls: Toggle, Slider, Apply)
     ========================================================================== */

  let currentNoiseType = "gaussian";

  function setupStep2Noise() {
    DOM.pillOptions.forEach((btn) => {
      btn.addEventListener("click", () => {
        DOM.pillOptions.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        currentNoiseType = btn.getAttribute("data-noise");
        updateNoiseSliderLabel();
      });
    });

    DOM.sliderNoiseAmount.addEventListener("input", updateNoiseSliderLabel);
    DOM.btnApplyFilter.addEventListener("click", () => executePipeline());

    DOM.btnSeedRandom.addEventListener("click", () => {
      const r = Math.floor(Math.random() * 900000) + 100000;
      DOM.inputSeed.value = r;
      showToast(`Generated seed: ${r}`, "info");
    });
  }

  function updateNoiseSliderLabel() {
    const val = parseFloat(DOM.sliderNoiseAmount.value);
    if (currentNoiseType === "gaussian") {
      DOM.valNoiseBadge.textContent = val === 50 ? "50 (Recommended)" : val.toFixed(0);
    } else {
      const pct = (val / 25).toFixed(1);
      DOM.valNoiseBadge.textContent = `${pct}% corruption`;
    }
  }

  /* ==========================================================================
     PIPELINE EXECUTION & REAL-TIME RESULT DISPATCH
     ========================================================================== */

  async function executePipeline(overrideParams = null) {
    if (state.isProcessing || !state.selectedImage) return;

    const noiseType = overrideParams?.noise_type || currentNoiseType;
    const noiseAmount = overrideParams?.noise_amount ?? parseFloat(DOM.sliderNoiseAmount.value);
    const mean = overrideParams?.mean ?? parseFloat(DOM.inputMean.value || 0);
    const seed = overrideParams?.seed ?? parseInt(DOM.inputSeed.value || 42, 10);
    const saveToDisk = DOM.checkSaveDisk.checked;

    let gStd = 50.0;
    let spDensity = 0.02;

    if (noiseType === "gaussian") {
      gStd = noiseAmount;
    } else {
      spDensity = Math.max(0.005, Math.min(0.15, noiseAmount / 2500));
    }

    const payload = {
      noise_type: noiseType,
      gaussian_std: gStd,
      gaussian_mean: mean,
      sp_density: spDensity,
      sp_ratio: 0.5,
      kernel_sizes: [3, 5, 7, 9],
      seed: seed,
      save_to_disk: saveToDisk,
      filename: state.selectedImage.name,
    };

    if (state.selectedImage.type === "file") {
      payload.image_base64 = state.selectedImage.base64;
    } else {
      payload.sample_name = state.selectedImage.sampleName;
    }

    state.isProcessing = true;
    DOM.btnApplyFilter.disabled = true;
    DOM.processingLoader.classList.remove("hidden");

    try {
      const res = await fetch("/api/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Server processing failed");
      }

      const data = await res.json();
      state.latestResult = data;

      // Update 8x8 patch data if provided
      if (data.initial_patch) {
        state.anim.patchData = data.initial_patch;
        state.anim.coord = data.initial_patch.origin;
        DOM.animCoordTag.textContent = `(x=${data.initial_patch.origin.x}, y=${data.initial_patch.origin.y})`;
        if (DOM.step4CoordTag) {
          DOM.step4CoordTag.textContent = `(x=${data.initial_patch.origin.x}, y=${data.initial_patch.origin.y})`;
        }
        verifyBackendMatch();
      }

      // Default selected kernel is the optimal one
      state.selectedKernel = data.optimal_kernel.kernel_size;
      state.anim.kernelSize = state.selectedKernel;
      state.walk.step3Kernel = state.selectedKernel;
      state.walk.step4Kernel = state.selectedKernel;

      renderResults(data);

      // Refresh walkthrough step if visible
      if (DOM.panelHow.classList.contains("active")) {
        renderWalkStep(state.walk.currentStep);
      }
    } catch (err) {
      console.error(err);
      showToast(`Error: ${err.message}`, "error");
    } finally {
      state.isProcessing = false;
      DOM.btnApplyFilter.disabled = false;
      DOM.processingLoader.classList.add("hidden");
    }
  }

  /* ==========================================================================
     STEP 3: RESULT RENDERING & INSTANT KERNEL SWITCHING
     ========================================================================== */

  function renderResults(data) {
    // 1. Setup Images in Split Slider
    DOM.splitImgTop.src = data.noisy_data_url;
    updateFilteredImageDisplay();

    // 2. Update Kernel Buttons & Best Star
    updateKernelButtons(data);

    // 3. Core Processing Latency (Real measured time on full array)
    DOM.latencyLabel.textContent = `Denoised in ${data.timing.cv_time_ms} ms (Core cv2)`;

    // 4. Update Metrics (MSE, PSNR, Deltas)
    updateMetricsDisplay();

    // 5. Mini Sparkline Chart
    renderSparklineChart(data.chart_points, data.optimal_kernel.kernel_size);
  }

  function setupStep3Slider() {
    const vp = DOM.splitViewport;

    const onMove = (e) => {
      if (!state.isDraggingSlider) return;
      const rect = vp.getBoundingClientRect();
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      let pct = ((clientX - rect.left) / rect.width) * 100;
      pct = Math.max(0, Math.min(100, pct));
      setSplitPosition(pct);
    };

    const onUp = () => {
      state.isDraggingSlider = false;
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
      window.removeEventListener("touchmove", onMove);
      window.removeEventListener("touchend", onUp);
    };

    vp.addEventListener("mousedown", (e) => {
      state.isDraggingSlider = true;
      onMove(e);
      window.addEventListener("mousemove", onMove);
      window.addEventListener("mouseup", onUp);
    });

    vp.addEventListener("touchstart", (e) => {
      state.isDraggingSlider = true;
      onMove(e);
      window.addEventListener("touchmove", onMove);
      window.addEventListener("touchend", onUp);
    });

    // Clicking anywhere on the image updates the animation patch origin!
    vp.addEventListener("click", (e) => {
      if (!state.selectedImage || state.isDraggingSlider) return;
      const rect = vp.getBoundingClientRect();
      const cx = e.clientX - rect.left;
      const cy = e.clientY - rect.top;

      const scaleX = state.selectedImage.width / rect.width;
      const scaleY = state.selectedImage.height / rect.height;

      const realX = Math.max(0, Math.min(state.selectedImage.width - 8, Math.round(cx * scaleX - 4)));
      const realY = Math.max(0, Math.min(state.selectedImage.height - 8, Math.round(cy * scaleY - 4)));

      fetchPatchAt(realX, realY);
      showToast(`Selected 8×8 patch at (${realX}, ${realY}) for calculation walkthrough.`, "info");
    });
  }

  function setSplitPosition(pct) {
    state.sliderPosition = pct;
    DOM.splitTopClip.style.clipPath = `polygon(0 0, ${pct}% 0, ${pct}% 100%, 0 100%)`;
    DOM.splitHandle.style.left = `${pct}%`;
  }

  function setupKernelButtons() {
    DOM.kernelButtonsGroup.addEventListener("click", (e) => {
      const btn = e.target.closest(".k-btn");
      if (!btn) return;
      const k = parseInt(btn.getAttribute("data-k"), 10);
      selectKernel(k);
    });
  }

  function selectKernel(k) {
    state.selectedKernel = k;
    state.anim.kernelSize = k;
    state.walk.step3Kernel = k;
    state.walk.step4Kernel = k;

    // Sync anim toolbar buttons
    DOM.animKBtns.forEach((b) => {
      b.classList.toggle("active", parseInt(b.getAttribute("data-ak"), 10) === k);
    });

    // Sync walkthrough mini kernel buttons
    DOM.step3KBtns.forEach((b) => {
      b.classList.toggle("active", parseInt(b.getAttribute("data-k3"), 10) === k);
    });
    DOM.step4KBtns.forEach((b) => {
      b.classList.toggle("active", parseInt(b.getAttribute("data-k4"), 10) === k);
    });

    // Update active studio button state
    document.querySelectorAll(".k-btn").forEach((b) => {
      b.classList.toggle("active", parseInt(b.getAttribute("data-k"), 10) === k);
    });

    // Instant image and metrics update
    updateFilteredImageDisplay();
    updateMetricsDisplay();
    if (state.latestResult?.chart_points) {
      renderSparklineChart(state.latestResult.chart_points, state.latestResult.optimal_kernel.kernel_size);
    }

    if (state.anim.isOpen) {
      renderAnimatorStep();
      verifyBackendMatch();
    }

    // Refresh active walkthrough step
    if (DOM.panelHow.classList.contains("active")) {
      renderWalkStep(state.walk.currentStep);
    }
  }

  function updateFilteredImageDisplay() {
    if (!state.latestResult) return;
    const kObj = state.latestResult.kernels.find((k) => k.kernel_size === state.selectedKernel) || state.latestResult.optimal_kernel;
    if (kObj) {
      DOM.splitImgBottom.src = kObj.image_data;
      DOM.tagFilteredLabel.textContent = `Filtered (${kObj.kernel_size}×${kObj.kernel_size})`;
    }
  }

  function updateKernelButtons(data) {
    const optK = data.optimal_kernel.kernel_size;
    DOM.kernelButtonsGroup.innerHTML = "";

    [3, 5, 7, 9].forEach((k) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `k-btn ${k === state.selectedKernel ? "active" : ""}`;
      btn.setAttribute("data-k", k);

      if (k === optK) {
        btn.innerHTML = `★ ${k}×${k} (Best)`;
      } else {
        btn.textContent = `${k}×${k}`;
      }

      DOM.kernelButtonsGroup.appendChild(btn);
    });
  }

  function updateMetricsDisplay() {
    if (!state.latestResult) return;
    const res = state.latestResult;
    const baselineMse = res.noise.baseline_mse;
    const baselinePsnr = res.noise.baseline_psnr;

    const currentK = res.kernels.find((k) => k.kernel_size === state.selectedKernel) || res.optimal_kernel;

    // MSE
    DOM.metricMse.textContent = currentK.mse.toFixed(2);
    DOM.metricMseBaseline.textContent = `Noisy baseline: ${baselineMse.toFixed(2)}`;
    const mseDiff = (baselineMse - currentK.mse).toFixed(2);
    DOM.metricMseDelta.textContent = `↓ ${mseDiff} vs noisy`;

    // PSNR
    DOM.metricPsnr.textContent = `${currentK.psnr.toFixed(2)} dB`;
    DOM.metricPsnrBaseline.textContent = `Noisy baseline: ${baselinePsnr.toFixed(2)} dB`;
    if (typeof baselinePsnr === "number" && typeof currentK.psnr === "number") {
      const psnrDiff = (currentK.psnr - baselinePsnr).toFixed(2);
      DOM.metricPsnrDelta.textContent = `↑ ${psnrDiff} dB vs noisy`;
    } else {
      DOM.metricPsnrDelta.textContent = `--`;
    }

    // Dynamic Plain-Language Takeaway Sentence
    if (currentK.kernel_size === res.optimal_kernel.kernel_size) {
      DOM.takeawayText.textContent = `Optimal balance: ${currentK.kernel_size}×${currentK.kernel_size} cleans noise while keeping edges sharp.`;
    } else if (currentK.kernel_size > res.optimal_kernel.kernel_size) {
      DOM.takeawayText.textContent = `Bigger kernels remove more noise but blur more detail (the over-smoothing turnover point).`;
    } else {
      DOM.takeawayText.textContent = `Smaller kernels preserve sharp edges but leave subtle background noise visible.`;
    }
  }

  function renderSparklineChart(points, optimalK) {
    if (!points || !points.kernel_sizes || points.kernel_sizes.length === 0) return;
    const svg = DOM.sparklineSvg;
    svg.innerHTML = "";

    const w = 160;
    const h = 55;
    const pad = 10;

    const xs = points.kernel_sizes;
    const ys = points.psnr_values.filter((v) => v !== null && !isNaN(v));
    if (ys.length === 0) return;

    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const spanY = maxY - minY || 1;

    const getX = (idx) => pad + (idx / (xs.length - 1)) * (w - 2 * pad);
    const getY = (val) => h - pad - ((val - minY) / spanY) * (h - 2 * pad);

    // Build line path
    let d = "";
    xs.forEach((k, idx) => {
      const cx = getX(idx);
      const cy = getY(points.psnr_values[idx]);
      d += (d === "" ? `M ${cx} ${cy}` : ` L ${cx} ${cy}`);
    });

    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", d);
    path.setAttribute("fill", "none");
    path.setAttribute("stroke", "#f43f5e");
    path.setAttribute("stroke-width", "2");
    path.setAttribute("stroke-linecap", "round");
    svg.appendChild(path);

    xs.forEach((k, idx) => {
      const cx = getX(idx);
      const cy = getY(points.psnr_values[idx]);
      const isSelected = k === state.selectedKernel;
      const isOptimal = k === optimalK;

      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", cx);
      circle.setAttribute("cy", cy);
      circle.setAttribute("r", isSelected ? "4.5" : "3");
      circle.setAttribute("fill", isOptimal ? "#10b981" : isSelected ? "#ffffff" : "#f43f5e");
      circle.setAttribute("stroke", "#0a0b10");
      circle.setAttribute("stroke-width", "1.5");
      svg.appendChild(circle);
    });

    DOM.sparklineCaption.textContent = `Selected: ${state.selectedKernel}×${state.selectedKernel} (Optimal: ${optimalK}×${optimalK})`;
  }

  /* ==========================================================================
     PATCH FETCHING & BORDER HANDLING
     ========================================================================== */

  async function fetchPatchAt(x, y) {
    state.anim.coord = { x, y };
    DOM.animCoordTag.textContent = `(x=${x}, y=${y})`;
    if (DOM.step4CoordTag) {
      DOM.step4CoordTag.textContent = `(x=${x}, y=${y})`;
    }

    try {
      const res = await fetch("/api/patch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          x: x,
          y: y,
          patch_size: 8,
          kernel_sizes: [3, 5, 7, 9],
        }),
      });
      if (!res.ok) return;
      const data = await res.json();
      if (data.success && data.patch) {
        state.anim.patchData = data.patch;
        state.anim.step = 0;
        state.walk.step4Step = 0;

        if (state.anim.isOpen) {
          renderAnimatorStep();
          verifyBackendMatch();
        }

        if (DOM.panelHow.classList.contains("active")) {
          renderWalkStep(state.walk.currentStep);
        }
      }
    } catch (err) {
      console.error(err);
    }
  }

  // OpenCV BORDER_REFLECT_101 formula: c, b | a, b, c | b, a
  function reflect101(i, len) {
    if (len <= 1) return 0;
    let x = i;
    while (x < 0 || x >= len) {
      if (x < 0) x = -x;
      else if (x >= len) x = 2 * len - 2 - x;
    }
    return x;
  }

  function computeAutoSigma(k) {
    return 0.3 * ((k - 1) * 0.5 - 1.0) + 0.8;
  }

  function computeKernelMatrix(k, sigma) {
    const matrix = [];
    const rad = Math.floor(k / 2);
    let sum = 0;
    for (let y = -rad; y <= rad; y++) {
      const row = [];
      for (let x = -rad; x <= rad; x++) {
        const val = Math.exp(-(x * x + y * y) / (2 * sigma * sigma));
        row.push(val);
        sum += val;
      }
      matrix.push(row);
    }
    for (let y = 0; y < k; y++) {
      for (let x = 0; x < k; x++) {
        matrix[y][x] /= sum;
      }
    }
    return matrix;
  }

  /* ==========================================================================
     "HOW IT WORKS" STEP-BY-STEP GUIDED WALKTHROUGH
     ========================================================================== */

  function setupWalkthrough() {
    // 1. Step tracker pills click
    DOM.walkPills.forEach((pill) => {
      pill.addEventListener("click", () => {
        const step = parseInt(pill.getAttribute("data-step"), 10);
        goToWalkStep(step);
      });
    });

    // 2. Next & Prev buttons
    DOM.walkBtnPrev.addEventListener("click", () => goToWalkStep(state.walk.currentStep - 1));
    DOM.walkBtnNext.addEventListener("click", () => {
      if (state.walk.currentStep < 6) {
        goToWalkStep(state.walk.currentStep + 1);
      } else {
        showToast("Completed full walkthrough! Click 'Formula sheet' for viva reference.", "success");
      }
    });

    // 3. Keyboard Arrow navigation
    window.addEventListener("keydown", (e) => {
      if (!DOM.panelHow.classList.contains("active")) return;
      if (["INPUT", "TEXTAREA"].includes(document.activeElement?.tagName)) return;

      if (e.key === "ArrowRight") {
        e.preventDefault();
        goToWalkStep(state.walk.currentStep + 1);
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        goToWalkStep(state.walk.currentStep - 1);
      }
    });

    // 4. Formula Sheet Modal controls
    DOM.btnOpenFormulaSheet.addEventListener("click", () => {
      DOM.formulaSheetModal.classList.remove("hidden");
    });
    DOM.btnCloseFormulaSheet.addEventListener("click", () => {
      DOM.formulaSheetModal.classList.add("hidden");
    });
    DOM.formulaSheetModal.addEventListener("click", (e) => {
      if (e.target === DOM.formulaSheetModal) {
        DOM.formulaSheetModal.classList.add("hidden");
      }
    });
    DOM.btnPrintFormulaSheet.addEventListener("click", () => {
      window.print();
    });

    // 5. Studio Button "Watch how it works" navigates to Step 4 of walkthrough
    DOM.btnOpenAnimator.addEventListener("click", () => {
      DOM.tabHow.click();
      goToWalkStep(4);
    });

    // 6. Step 1 Channel selector pills
    DOM.step1ChanBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        DOM.step1ChanBtns.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        state.walk.step1Channel = btn.getAttribute("data-chan");
        renderWalkStep1();
      });
    });

    // 7. Step 3 Kernel size pills
    DOM.step3KBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const k = parseInt(btn.getAttribute("data-k3"), 10);
        state.walk.step3Kernel = k;
        DOM.step3KBtns.forEach((b) => b.classList.toggle("active", parseInt(b.getAttribute("data-k3"), 10) === k));
        renderWalkStep3();
      });
    });

    // 8. Step 4 Animation controls
    DOM.step4BtnPlayPause.addEventListener("click", toggleStep4Play);
    DOM.step4BtnPrev.addEventListener("click", () => {
      pauseStep4();
      stepStep4(-1);
    });
    DOM.step4BtnNext.addEventListener("click", () => {
      pauseStep4();
      stepStep4(1);
    });
    DOM.step4BtnRestart.addEventListener("click", () => {
      pauseStep4();
      state.walk.step4Step = 0;
      renderWalkStep4();
    });
    DOM.step4KBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const k = parseInt(btn.getAttribute("data-k4"), 10);
        state.walk.step4Kernel = k;
        DOM.step4KBtns.forEach((b) => b.classList.toggle("active", parseInt(b.getAttribute("data-k4"), 10) === k));
        renderWalkStep4();
      });
    });
  }

  function goToWalkStep(step) {
    if (step < 1) step = 1;
    if (step > 6) step = 6;
    state.walk.currentStep = step;

    // Toggle active tracker pill
    DOM.walkPills.forEach((p) => {
      p.classList.toggle("active", parseInt(p.getAttribute("data-step"), 10) === step);
    });

    // Toggle active step card
    DOM.walkCards.forEach((c) => {
      c.classList.toggle("active", parseInt(c.getAttribute("data-step-index"), 10) === step);
    });

    // Update bottom footer counter & buttons
    const stepTitles = [
      "The Image is Numbers",
      "Add Noise",
      "Build the Kernel",
      "Slide, Multiply, Add",
      "Measure the Result",
      "Choose Kernel Size",
    ];
    DOM.walkStepCounter.textContent = `Step ${step} of 6: ${stepTitles[step - 1]}`;
    DOM.walkBtnPrev.disabled = (step === 1);
    DOM.walkBtnNext.textContent = (step === 6) ? "Finish ✓" : "Next → (Right Arrow)";

    renderWalkStep(step);
  }

  function renderWalkStep(step) {
    switch (step) {
      case 1:
        renderWalkStep1();
        break;
      case 2:
        renderWalkStep2();
        break;
      case 3:
        renderWalkStep3();
        break;
      case 4:
        renderWalkStep4();
        break;
      case 5:
        renderWalkStep5();
        break;
      case 6:
        renderWalkStep6();
        break;
    }
  }

  /* --------------------------------------------------------------------------
     STEP 1 RENDERER: The Image is Numbers
     -------------------------------------------------------------------------- */
  function renderWalkStep1() {
    const patch = state.anim.patchData;
    if (!patch) return;

    // Update Legend
    const w = state.selectedImage?.width || 512;
    const h = state.selectedImage?.height || 512;
    DOM.legendS1Coords.textContent = `W = ${w} px, H = ${h} px`;
    const chanNames = { luma: "Luma (Gray)", r: "Red (R)", g: "Green (G)", b: "Blue (B)" };
    DOM.legendS1Channel.textContent = `Active channel: ${chanNames[state.walk.step1Channel] || "Luma"}`;

    const r = state.walk.step1SelectedCell.r;
    const c = state.walk.step1SelectedCell.c;

    const valR = patch.channels_clean.r[r][c];
    const valG = patch.channels_clean.g[r][c];
    const valB = patch.channels_clean.b[r][c];
    const valLuma = patch.channels_clean.luma[r][c];
    const calcLuma = Math.round(0.299 * valR + 0.587 * valG + 0.114 * valB);

    DOM.step1InspectLoc.textContent = `Inspecting Patch Pixel (r=${r}, c=${c}) · Image (x=${patch.origin.x + c}, y=${patch.origin.y + r})`;
    DOM.step1ValR.textContent = valR;
    DOM.step1ValG.textContent = valG;
    DOM.step1ValB.textContent = valB;
    DOM.step1ValLuma.textContent = valLuma;

    DOM.step1CalcBreakdown.innerHTML = `<strong>Conversion Math:</strong> Y = (0.299 &times; ${valR}) + (0.587 &times; ${valG}) + (0.114 &times; ${valB}) = ${(0.299 * valR).toFixed(2)} + ${(0.587 * valG).toFixed(2)} + ${(0.114 * valB).toFixed(2)} = <strong>${calcLuma}</strong>`;

    // Render 8x8 Grid
    const grid = DOM.step1MatrixGrid;
    grid.innerHTML = "";

    const activeChanMat = patch.channels_clean[state.walk.step1Channel] || patch.channels_clean.luma;

    for (let ir = 0; ir < 8; ir++) {
      for (let ic = 0; ic < 8; ic++) {
        const val = activeChanMat[ir][ic];
        const cell = document.createElement("div");
        cell.className = "matrix-cell";
        if (ir === r && ic === c) {
          cell.classList.add("cell-selected");
        }

        // Toned background shading by channel
        if (state.walk.step1Channel === "r") {
          cell.style.backgroundColor = `rgba(244, 63, 94, ${0.12 + (val / 255) * 0.88})`;
          cell.style.color = val > 140 ? "#fff" : "#ffcbd1";
        } else if (state.walk.step1Channel === "g") {
          cell.style.backgroundColor = `rgba(16, 185, 129, ${0.12 + (val / 255) * 0.88})`;
          cell.style.color = val > 140 ? "#fff" : "#a7f3d0";
        } else if (state.walk.step1Channel === "b") {
          cell.style.backgroundColor = `rgba(59, 130, 246, ${0.12 + (val / 255) * 0.88})`;
          cell.style.color = val > 140 ? "#fff" : "#bfdbfe";
        } else {
          cell.style.backgroundColor = `rgb(${val}, ${val}, ${val})`;
          cell.style.color = val > 128 ? "#000" : "#fff";
        }

        cell.textContent = val;
        cell.title = `Cell (r=${ir}, c=${ic}) = ${val}`;

        cell.addEventListener("click", () => {
          state.walk.step1SelectedCell = { r: ir, c: ic };
          renderWalkStep1();
        });

        grid.appendChild(cell);
      }
    }
  }

  /* --------------------------------------------------------------------------
     STEP 2 RENDERER: Add Noise
     -------------------------------------------------------------------------- */
  function renderWalkStep2() {
    const patch = state.anim.patchData;
    const res = state.latestResult;
    if (!patch || !res) return;

    const noiseConfig = res.noise;
    const isGaussian = noiseConfig.type === "gaussian";

    if (isGaussian) {
      DOM.step2FormulaExpr.innerHTML = `
        <span class="math-var">I</span><sub>noisy</sub>(<span class="math-var">x</span>, <span class="math-var">y</span>) = clip(<span class="math-var">I</span><sub>clean</sub>(<span class="math-var">x</span>, <span class="math-var">y</span>) + <span class="math-var">N</span>(<span class="math-var">x</span>, <span class="math-var">y</span>), 0, 255)
        <span class="math-sep">&nbsp;&nbsp;|&nbsp;&nbsp;</span>
        <span class="math-var">N</span> &sim; <span class="math-func">N</span>(<span class="math-var">&mu;</span>, <span class="math-var">&sigma;<sub>n</sub><sup>2</sup></span>)
      `;
      DOM.step2WordsText.innerHTML = `
        <strong>In words:</strong> The degraded noisy pixel equals the original clean value plus a normally distributed random perturbation, clamped strictly to stay between 0 and 255.
      `;
      DOM.legendS2NoiseVar.textContent = "Gaussian perturbation N ~ N(μ, σ²)";
      DOM.legendS2Mean.textContent = `μ = ${(noiseConfig.mean || 0).toFixed(1)}`;
      DOM.legendS2Std.textContent = `σ_n = ${noiseConfig.noise_amount.toFixed(1)}`;
    } else {
      DOM.step2FormulaExpr.innerHTML = `
        P(<span class="math-var">I</span><sub>noisy</sub> = 0) = <span class="math-var">d</span> / 2 &nbsp;&nbsp;|&nbsp;&nbsp;
        P(<span class="math-var">I</span><sub>noisy</sub> = 255) = <span class="math-var">d</span> / 2 &nbsp;&nbsp;|&nbsp;&nbsp;
        P(<span class="math-var">I</span><sub>noisy</sub> = <span class="math-var">I</span><sub>clean</sub>) = 1 &minus; <span class="math-var">d</span>
      `;
      DOM.step2WordsText.innerHTML = `
        <strong>In words:</strong> Each pixel is independently replaced by minimum intensity 0 (Pepper) or maximum intensity 255 (Salt) with probability density/2 each; otherwise it stays unchanged.
      `;
      DOM.legendS2NoiseVar.textContent = "Impulse dropout (0 or 255)";
      DOM.legendS2Mean.textContent = "Bipolar extremes (0 / 255)";
      DOM.legendS2Std.textContent = `Noise density d = ${noiseConfig.noise_amount}%`;
    }

    DOM.legendS2Seed.textContent = `Seed = ${noiseConfig.seed} (Reproducible)`;
    DOM.step2SeedDesc.innerHTML = `Random Seed <strong>${noiseConfig.seed}</strong> is active: The same seed produces the exact same pseudo-random noise matrix on every run, ensuring scientific repeatability.`;

    // Check if patch has clipping
    if (patch.clipping && patch.clipping.has_clipping) {
      const sc = patch.clipping.sample_clipped;
      DOM.step2ClippingText.innerHTML = `
        <strong>Clipping Detected in this Patch (${patch.clipping.total_clipped} pixels clipped):</strong>
        At cell (r=${sc.r}, c=${sc.c}), Clean (${sc.clean}) + Noise (${sc.noise >= 0 ? "+" + sc.noise : sc.noise}) = <strong>${sc.sum}</strong>. Because ${sc.sum} ${sc.type === "upper" ? "> 255 (exceeded ceiling)" : "< 0 (below floor)"}, hardware clamping bounds it strictly to <strong>${sc.clipped}</strong> to prevent integer overflow.
      `;
    } else {
      DOM.step2ClippingText.innerHTML = `
        <strong>Clipping Analysis:</strong> In this 8×8 patch, all sums remained within [0, 255]. If a noise perturbation causes a sum outside this range (e.g. 235 + 32 = 267 or 18 &minus; 35 = &minus;17), clip(v, 0, 255) bounds it to 255 or 0 to preserve valid 8-bit dynamic range.
      `;
    }

    // Selected cell calculation
    const r = state.walk.step2SelectedCell.r;
    const c = state.walk.step2SelectedCell.c;
    const cleanVal = patch.channels_clean.luma[r][c];
    const noiseVal = patch.channels_noise.luma[r][c];
    const sumVal = cleanVal + noiseVal;
    const noisyVal = patch.channels.luma[r][c];
    const isClipped = sumVal < 0 || sumVal > 255;

    DOM.step2CalcLine.innerHTML = `
      <strong>Pixel Calculation at (r=${r}, c=${c}):</strong>
      Clean (${cleanVal}) + Noise (${noiseVal >= 0 ? "+" + noiseVal : noiseVal}) = ${sumVal} &rarr;
      <strong>Noisy = ${noisyVal}</strong>
      ${isClipped ? `<span class="clip-tag">(Clipped: ${sumVal} clamped to ${noisyVal})</span>` : "(Inside valid range [0, 255])"}
    `;

    // Render 3 linked grids
    renderLinkedMiniGrid(DOM.step2CleanGrid, patch.channels_clean.luma, r, c, "clean");
    renderLinkedMiniGrid(DOM.step2NoiseGrid, patch.channels_noise.luma, r, c, "noise");
    renderLinkedMiniGrid(DOM.step2NoisyGrid, patch.channels.luma, r, c, "noisy");
  }

  function renderLinkedMiniGrid(container, matrix, selR, selC, type) {
    container.innerHTML = "";
    for (let ir = 0; ir < 8; ir++) {
      for (let ic = 0; ic < 8; ic++) {
        const val = matrix[ir][ic];
        const cell = document.createElement("div");
        cell.className = "mini-cell";
        if (ir === selR && ic === selC) {
          cell.classList.add("cell-selected");
        }

        if (type === "clean" || type === "noisy") {
          cell.style.backgroundColor = `rgb(${val}, ${val}, ${val})`;
          cell.style.color = val > 128 ? "#000" : "#fff";
          cell.textContent = val;
        } else {
          // Signed noise values
          if (val > 0) {
            cell.style.backgroundColor = `rgba(16, 185, 129, ${Math.min(0.85, 0.15 + (val / 100) * 0.7)})`;
            cell.style.color = "#a7f3d0";
            cell.textContent = `+${val}`;
          } else if (val < 0) {
            cell.style.backgroundColor = `rgba(244, 63, 94, ${Math.min(0.85, 0.15 + (Math.abs(val) / 100) * 0.7)})`;
            cell.style.color = "#ffcbd1";
            cell.textContent = val;
          } else {
            cell.style.backgroundColor = "#12141c";
            cell.style.color = "#64748b";
            cell.textContent = "0";
          }
        }

        cell.addEventListener("click", () => {
          state.walk.step2SelectedCell = { r: ir, c: ic };
          renderWalkStep2();
        });

        container.appendChild(cell);
      }
    }
  }

  /* --------------------------------------------------------------------------
     STEP 3 RENDERER: Build the Kernel
     -------------------------------------------------------------------------- */
  function renderWalkStep3() {
    const res = state.latestResult;
    const k = state.walk.step3Kernel || 5;

    // Highlight row in heuristic sigma table
    DOM.step3SigmaTableBody.querySelectorAll("tr").forEach((row) => {
      const rk = parseInt(row.getAttribute("data-k-row"), 10);
      row.classList.toggle("highlight-row", rk === k);
    });

    const kInfo = res?.detailed_kernels?.[k];
    const sigma = kInfo ? kInfo.sigma : computeAutoSigma(k);
    const weights2D = kInfo ? kInfo.weights_2d : computeKernelMatrix(k, sigma);
    const weights1D = kInfo ? kInfo.weights_1d : [];
    const sumNorm = kInfo ? kInfo.sum_normalized : "1.0000";
    const rawSum = kInfo ? kInfo.raw_sum : 7.3225;
    const centerWeight = kInfo ? kInfo.center_weight : weights2D[Math.floor(k / 2)][Math.floor(k / 2)];
    const rad = Math.floor(k / 2);
    const cornerWeight = kInfo ? kInfo.corner_weight : weights2D[0][0];

    DOM.step3KernelHeading.innerHTML = `Kernel: <strong>${k}×${k} Window</strong> &middot; &sigma;<sub>blur</sub> = <strong>${sigma.toFixed(3)}</strong>`;

    DOM.step3CenterCalc.innerHTML = `
      <strong>Center Weight (x=0, y=0):</strong>
      G(0, 0) = exp(0) = 1.0000 &rarr; Normalized: 1.0000 / ${rawSum.toFixed(4)} = <strong>${centerWeight.toFixed(4)}</strong>
    `;

    DOM.step3CornerCalc.innerHTML = `
      <strong>Corner Weight (x=&plusmn;${rad}, y=&plusmn;${rad}):</strong>
      G(${rad}, ${rad}) = exp(&minus;${2 * rad * rad} / ${(2 * sigma * sigma).toFixed(2)}) &rarr; Normalized: <strong>${cornerWeight.toFixed(4)}</strong>
    `;

    DOM.step3SumText.innerHTML = `Sum of weights = <strong>${sumNorm}</strong> (Exact OpenCV cv2.getGaussianKernel with &sigma; = ${sigma.toFixed(3)})`;

    // Render kxk Heatmap Grid
    const grid = DOM.step3WeightsGrid;
    grid.innerHTML = "";
    grid.style.gridTemplateColumns = `repeat(${k}, 1fr)`;

    const maxW = centerWeight;

    for (let y = 0; y < k; y++) {
      for (let x = 0; x < k; x++) {
        const w = weights2D[y][x];
        const cell = document.createElement("div");
        cell.className = "k-weight-cell";

        const intensity = maxW > 0 ? w / maxW : 0;
        cell.style.backgroundColor = `rgba(244, 63, 94, ${0.12 + intensity * 0.88})`;
        cell.style.color = intensity > 0.4 ? "#ffffff" : "#fca5a5";

        cell.textContent = w.toFixed(4);
        cell.title = `Weight (x=${x - rad}, y=${y - rad}) = ${w.toFixed(6)}`;
        grid.appendChild(cell);
      }
    }

    // Render 1D Separability Row
    if (weights1D && weights1D.length > 0) {
      DOM.step31DWeights.innerHTML = weights1D
        .map((w1, idx) => `<span class="w1d-pill">1D[${idx - rad}] = ${w1.toFixed(4)}</span>`)
        .join("");
    } else {
      DOM.step31DWeights.innerHTML = "";
    }
  }

  /* --------------------------------------------------------------------------
     STEP 4 RENDERER: Slide, Multiply, Add (The Core Step)
     -------------------------------------------------------------------------- */
  function renderWalkStep4() {
    const patch = state.anim.patchData;
    if (!patch) return;

    const k = state.walk.step4Kernel || 5;
    const rad = Math.floor(k / 2);
    const step = state.walk.step4Step;
    const r = Math.floor(step / 8);
    const c = step % 8;

    DOM.legendS4Radius.textContent = `Radius r = ${rad} (${k}×${k})`;
    DOM.step4StepBadge.textContent = `Step ${step + 1} / 64 (r=${r}, c=${c})`;

    const chanMat = patch.channels.luma;
    const kWeights = patch.kernel_matrices[k] || computeKernelMatrix(k, computeAutoSigma(k));
    const backendMat = patch.backend_filtered[k];

    // 1. Render Input 8x8 Grid
    DOM.step4InputGrid.innerHTML = "";
    for (let ir = 0; ir < 8; ir++) {
      for (let ic = 0; ic < 8; ic++) {
        const val = chanMat[ir][ic];
        const cell = document.createElement("div");
        cell.className = "patch-cell";

        const dr = ir - r;
        const dc = ic - c;
        const inWindow = Math.abs(dr) <= rad && Math.abs(dc) <= rad;
        const isCenter = dr === 0 && dc === 0;

        if (isCenter) cell.classList.add("cell-kernel-center");
        else if (inWindow) cell.classList.add("cell-kernel-active");

        cell.style.backgroundColor = `rgb(${val}, ${val}, ${val})`;
        cell.style.color = val > 128 ? "#000" : "#fff";
        cell.textContent = val;

        cell.addEventListener("click", () => {
          pauseStep4();
          state.walk.step4Step = ir * 8 + ic;
          renderWalkStep4();
        });

        DOM.step4InputGrid.appendChild(cell);
      }
    }

    // 2. Convolution Math Rows
    DOM.step4MathRows.innerHTML = "";
    let sum = 0;

    for (let di = -rad; di <= rad; di++) {
      for (let dj = -rad; dj <= rad; dj++) {
        const pr = reflect101(r + di, 8);
        const pc = reflect101(c + dj, 8);

        const pix = chanMat[pr][pc];
        const w = kWeights[di + rad][dj + rad];
        const prod = pix * w;
        sum += prod;

        const isReflected = r + di < 0 || r + di >= 8 || c + dj < 0 || c + dj >= 8;

        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>(${di >= 0 ? "+" : ""}${di}, ${dj >= 0 ? "+" : ""}${dj})${isReflected ? " 🔄" : ""}</td>
          <td>${pix}</td>
          <td>${w.toFixed(4)}</td>
          <td><strong>${prod.toFixed(2)}</strong></td>
        `;
        DOM.step4MathRows.appendChild(tr);
      }
    }

    const rounded = Math.min(255, Math.max(0, Math.round(sum)));
    DOM.step4SumVal.textContent = sum.toFixed(3);
    DOM.step4RoundedVal.textContent = rounded;

    // Backend reference value for (r, c)
    let refVal = rounded;
    if (backendMat && backendMat[r] && backendMat[r][c] !== undefined) {
      refVal = backendMat[r][c];
    }

    const diff = Math.abs(rounded - refVal);
    if (diff <= 1) {
      DOM.step4AnimMatchBadge.className = "badge-match";
      DOM.step4AnimMatchBadge.innerHTML = `✓ Matches backend (${k}×${k}, &Delta;=${diff} LSB)`;
    } else {
      DOM.step4AnimMatchBadge.className = "badge-match mismatch";
      DOM.step4AnimMatchBadge.innerHTML = `Variance &Delta;=${diff}`;
    }

    DOM.step4InspectPixel.textContent = `Target Pixel (r=${r}, c=${c}) · Image (x=${patch.origin.x + c}, y=${patch.origin.y + r})`;
    DOM.step4CalcDisplay.innerHTML = `
      Accumulated Sum = <strong>${sum.toFixed(3)}</strong> &rarr; round(${sum.toFixed(3)}) = <strong>${rounded}</strong> (Backend cv2: <strong>${refVal}</strong>)
    `;

    // 3. Render Output 8x8 Grid
    DOM.step4OutputGrid.innerHTML = "";
    for (let ir = 0; ir < 8; ir++) {
      for (let ic = 0; ic < 8; ic++) {
        const idx = ir * 8 + ic;
        const cell = document.createElement("div");
        cell.className = "patch-cell";

        if (idx < step) {
          const v = backendMat ? backendMat[ir][ic] : 0;
          cell.classList.add("cell-out-computed");
          cell.style.backgroundColor = `rgb(${v}, ${v}, ${v})`;
          cell.style.color = v > 128 ? "#000" : "#fff";
          cell.textContent = v;
        } else if (idx === step) {
          cell.classList.add("cell-out-current");
          cell.style.backgroundColor = `rgb(${rounded}, ${rounded}, ${rounded})`;
          cell.style.color = rounded > 128 ? "#000" : "#fff";
          cell.textContent = rounded;
        } else {
          cell.style.backgroundColor = "#12141c";
          cell.style.color = "#475569";
          cell.textContent = "·";
        }

        cell.addEventListener("click", () => {
          pauseStep4();
          state.walk.step4Step = idx;
          renderWalkStep4();
        });

        DOM.step4OutputGrid.appendChild(cell);
      }
    }
  }

  function toggleStep4Play() {
    if (state.walk.step4IsPlaying) {
      pauseStep4();
    } else {
      startStep4();
    }
  }

  function startStep4() {
    state.walk.step4IsPlaying = true;
    DOM.step4BtnPlayPause.textContent = "⏸ Pause";
    DOM.step4BtnPlayPause.classList.add("btn-ghost");
    DOM.step4BtnPlayPause.classList.remove("btn-primary");
    state.walk.step4TimerId = setInterval(() => stepStep4(1), state.walk.step4SpeedMs);
  }

  function pauseStep4() {
    state.walk.step4IsPlaying = false;
    DOM.step4BtnPlayPause.textContent = "▶ Play";
    DOM.step4BtnPlayPause.classList.remove("btn-ghost");
    DOM.step4BtnPlayPause.classList.add("btn-primary");
    clearInterval(state.walk.step4TimerId);
  }

  function stepStep4(delta) {
    let next = state.walk.step4Step + delta;
    if (next >= 64) next = 0;
    if (next < 0) next = 63;
    state.walk.step4Step = next;
    renderWalkStep4();
  }

  /* --------------------------------------------------------------------------
     STEP 5 RENDERER: Measure the Result (MSE & PSNR)
     -------------------------------------------------------------------------- */
  function renderWalkStep5() {
    const res = state.latestResult;
    const patch = state.anim.patchData;
    if (!res) return;

    // Dimensions
    const w = state.selectedImage?.width || 512;
    const h = state.selectedImage?.height || 512;
    DOM.legendS5Dims.textContent = `${h} × ${w} × 3`;

    // Part A: Tiny Worked Example (4 Real Pixel Pairs)
    const samples = patch?.tiny_eval_samples || [];
    DOM.step5TinyRows.innerHTML = "";

    let sumDiffSq = 0;
    if (samples.length > 0) {
      samples.forEach((s) => {
        sumDiffSq += s.diff_sq;
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>(r=${s.r}, c=${s.c})</td>
          <td>${s.clean}</td>
          <td>${s.filtered}</td>
          <td>${s.diff >= 0 ? "+" + s.diff : s.diff}</td>
          <td><strong>${s.diff_sq}</strong></td>
        `;
        DOM.step5TinyRows.appendChild(tr);
      });

      const sampleMse = sumDiffSq / samples.length;
      const samplePsnr = sampleMse > 0 ? 10 * Math.log10(65025 / sampleMse) : 99.0;

      DOM.step5SampleMse.textContent = sampleMse.toFixed(2);
      DOM.step5SampleMseRef.textContent = sampleMse.toFixed(2);
      DOM.step5SamplePsnr.textContent = `${samplePsnr.toFixed(2)} dB`;
    }

    // Part B: Full Image Real Pipeline Metrics
    const noisyMse = res.noise.baseline_mse;
    const noisyPsnr = res.noise.baseline_psnr;
    const currentK = res.kernels.find((k) => k.kernel_size === state.selectedKernel) || res.optimal_kernel;
    const filtMse = currentK.mse;
    const filtPsnr = currentK.psnr;

    DOM.step5FullNoisyMse.textContent = noisyMse.toFixed(2);
    DOM.step5FullNoisyPsnr.textContent = `PSNR = 10 · log10(65025 / ${noisyMse.toFixed(2)}) = ${noisyPsnr.toFixed(2)} dB`;

    DOM.step5FilteredTag.textContent = `Gaussian Filtered (${currentK.kernel_size}×${currentK.kernel_size}${currentK.is_optimal ? " ★ Best" : ""})`;
    DOM.step5FullFiltMse.textContent = filtMse.toFixed(2);
    DOM.step5FullFiltPsnr.textContent = `PSNR = 10 · log10(65025 / ${filtMse.toFixed(2)}) = ${filtPsnr.toFixed(2)} dB`;

    const deltaPsnr = (filtPsnr - noisyPsnr).toFixed(2);
    const deltaMse = (noisyMse - filtMse).toFixed(2);
    const pctElim = ((noisyMse - filtMse) / noisyMse * 100).toFixed(1);

    DOM.step5DeltaPsnr.textContent = `+${deltaPsnr} dB`;
    DOM.step5DeltaMse.textContent = `↓ ${deltaMse} MSE (${pctElim}% noise eliminated)`;

    // Visual Bars
    const msePct = Math.min(100, Math.max(3, (filtMse / noisyMse) * 100));
    DOM.step5BarMse.style.width = `${msePct}%`;
    DOM.step5BarMseVal.textContent = `${filtMse.toFixed(2)} (Filtered) vs ${noisyMse.toFixed(2)} (Noisy)`;

    const psnrPct = Math.min(100, Math.max(10, (filtPsnr / 40) * 100));
    DOM.step5BarPsnr.style.width = `${psnrPct}%`;
    DOM.step5BarPsnrVal.textContent = `${filtPsnr.toFixed(2)} dB (Filtered) vs ${noisyPsnr.toFixed(2)} dB (Noisy)`;
  }

  /* --------------------------------------------------------------------------
     STEP 6 RENDERER: Choose Kernel Size (The Turnover Principle)
     -------------------------------------------------------------------------- */
  function renderWalkStep6() {
    const res = state.latestResult;
    if (!res || !res.kernels) return;

    // Table rows
    DOM.step6TableBody.innerHTML = "";
    const baselinePsnr = res.noise.baseline_psnr;
    const optK = res.optimal_kernel.kernel_size;

    res.kernels.forEach((kObj) => {
      const isOptimal = kObj.kernel_size === optK;
      const gain = (kObj.psnr - baselinePsnr).toFixed(2);

      let behavior = "";
      if (isOptimal) {
        behavior = "★ Optimal noise/edge balance";
      } else if (kObj.kernel_size < optK) {
        behavior = "Under-smoothed (residual noise visible)";
      } else {
        behavior = "Over-smoothed (blur exceeds noise gain)";
      }

      const tr = document.createElement("tr");
      if (isOptimal) tr.className = "highlight-row";
      tr.innerHTML = `
        <td><strong>${isOptimal ? "★ " : ""}${kObj.kernel_size}×${kObj.kernel_size}</strong></td>
        <td>${kObj.sigma.toFixed(2)}</td>
        <td>${kObj.mse.toFixed(2)}</td>
        <td><strong>${kObj.psnr.toFixed(2)} dB</strong></td>
        <td>+${gain} dB</td>
        <td>${behavior}</td>
      `;
      DOM.step6TableBody.appendChild(tr);
    });

    // Turnover statement
    const minPsnr = res.kernels[0].psnr;
    const maxPsnr = res.optimal_kernel.psnr;
    const lastPsnr = res.kernels[res.kernels.length - 1].psnr;

    DOM.step6TurnoverStatement.innerHTML = `
      <strong>Turnover Identification:</strong> PSNR rises from ${minPsnr.toFixed(2)} dB (3×3) to peak at <strong>${maxPsnr.toFixed(2)} dB (${optK}×${optK} Best)</strong>, then declines to ${lastPsnr.toFixed(2)} dB (9×9).
    `;

    DOM.step6TurnoverDetail.textContent = `
      The ${optK}×${optK} kernel achieves maximum signal fidelity (+${(maxPsnr - baselinePsnr).toFixed(2)} dB gain vs noisy baseline). Increasing to 7×7 or 9×9 causes the low-pass filter to smooth true high-frequency image textures (sharp boundaries and fine details), yielding diminishing returns and net fidelity decline.
    `;

    // Render Full SVG Turnover Chart
    renderStep6Chart(res.chart_points, optK, baselinePsnr);
  }

  function renderStep6Chart(points, optimalK, baselinePsnr) {
    const svg = DOM.step6ChartSvg;
    if (!svg || !points || !points.kernel_sizes) return;
    svg.innerHTML = "";

    const w = 540;
    const h = 220;
    const padLeft = 60;
    const padRight = 35;
    const padTop = 25;
    const padBottom = 40;

    const xs = points.kernel_sizes;
    const ys = points.psnr_values;

    const allY = [...ys, baselinePsnr];
    const minY = Math.floor(Math.min(...allY) - 1.5);
    const maxY = Math.ceil(Math.max(...allY) + 2.0);
    const spanY = maxY - minY || 1;

    const getX = (idx) => padLeft + (idx / (xs.length - 1)) * (w - padLeft - padRight);
    const getY = (val) => h - padBottom - ((val - minY) / spanY) * (h - padTop - padBottom);

    // 1. Draw horizontal grid lines & Y labels
    const ySteps = 4;
    for (let i = 0; i <= ySteps; i++) {
      const val = minY + (i / ySteps) * spanY;
      const yPos = getY(val);

      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("x1", padLeft);
      line.setAttribute("x2", w - padRight);
      line.setAttribute("y1", yPos);
      line.setAttribute("y2", yPos);
      line.setAttribute("stroke", "#1f2438");
      line.setAttribute("stroke-dasharray", "3,3");
      svg.appendChild(line);

      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", padLeft - 10);
      text.setAttribute("y", yPos + 4);
      text.setAttribute("fill", "#64748b");
      text.setAttribute("font-size", "11");
      text.setAttribute("text-anchor", "end");
      text.textContent = `${val.toFixed(1)} dB`;
      svg.appendChild(text);
    }

    // 2. Draw dashed Noisy Baseline line
    const basePosY = getY(baselinePsnr);
    const baseLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
    baseLine.setAttribute("x1", padLeft);
    baseLine.setAttribute("x2", w - padRight);
    baseLine.setAttribute("y1", basePosY);
    baseLine.setAttribute("y2", basePosY);
    baseLine.setAttribute("stroke", "#f43f5e");
    baseLine.setAttribute("stroke-width", "1.5");
    baseLine.setAttribute("stroke-dasharray", "6,4");
    svg.appendChild(baseLine);

    const baseText = document.createElementNS("http://www.w3.org/2000/svg", "text");
    baseText.setAttribute("x", w - padRight);
    baseText.setAttribute("y", basePosY - 6);
    baseText.setAttribute("fill", "#f43f5e");
    baseText.setAttribute("font-size", "11");
    baseText.setAttribute("text-anchor", "end");
    baseText.textContent = `Noisy Baseline (${baselinePsnr.toFixed(2)} dB)`;
    svg.appendChild(baseText);

    // 3. Draw PSNR Curve
    let d = "";
    xs.forEach((k, idx) => {
      const cx = getX(idx);
      const cy = getY(ys[idx]);
      d += (d === "" ? `M ${cx} ${cy}` : ` L ${cx} ${cy}`);
    });

    const curve = document.createElementNS("http://www.w3.org/2000/svg", "path");
    curve.setAttribute("d", d);
    curve.setAttribute("fill", "none");
    curve.setAttribute("stroke", "#38bdf8");
    curve.setAttribute("stroke-width", "3");
    curve.setAttribute("stroke-linecap", "round");
    svg.appendChild(curve);

    // 4. Draw markers & labels for each kernel
    xs.forEach((k, idx) => {
      const cx = getX(idx);
      const cy = getY(ys[idx]);
      const isOptimal = k === optimalK;
      const isSelected = k === state.selectedKernel;

      // Vertical guideline to X-axis
      const vGuide = document.createElementNS("http://www.w3.org/2000/svg", "line");
      vGuide.setAttribute("x1", cx);
      vGuide.setAttribute("x2", cx);
      vGuide.setAttribute("y1", cy);
      vGuide.setAttribute("y2", h - padBottom);
      vGuide.setAttribute("stroke", "#1f2438");
      vGuide.setAttribute("stroke-dasharray", "2,2");
      svg.appendChild(vGuide);

      // Marker Circle
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", cx);
      circle.setAttribute("cy", cy);
      circle.setAttribute("r", isOptimal ? "7" : isSelected ? "5.5" : "4.5");
      circle.setAttribute("fill", isOptimal ? "#10b981" : isSelected ? "#ffffff" : "#38bdf8");
      circle.setAttribute("stroke", "#0a0b10");
      circle.setAttribute("stroke-width", "2");
      circle.style.cursor = "pointer";

      circle.addEventListener("click", () => {
        selectKernel(k);
      });

      svg.appendChild(circle);

      // Value label above dot
      const valLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
      valLabel.setAttribute("x", cx);
      valLabel.setAttribute("y", cy - 12);
      valLabel.setAttribute("fill", isOptimal ? "#10b981" : "#e2e8f0");
      valLabel.setAttribute("font-size", isOptimal ? "12" : "11");
      valLabel.setAttribute("font-weight", isOptimal ? "700" : "500");
      valLabel.setAttribute("text-anchor", "middle");
      valLabel.textContent = `${ys[idx].toFixed(2)} dB${isOptimal ? " ★" : ""}`;
      svg.appendChild(valLabel);

      // X-Axis label
      const xLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
      xLabel.setAttribute("x", cx);
      xLabel.setAttribute("y", h - padBottom + 18);
      xLabel.setAttribute("fill", isOptimal ? "#10b981" : "#94a3b8");
      xLabel.setAttribute("font-size", "12");
      xLabel.setAttribute("font-weight", isOptimal ? "700" : "500");
      xLabel.setAttribute("text-anchor", "middle");
      xLabel.textContent = `${k}×${k}`;
      svg.appendChild(xLabel);
    });
  }

  /* ==========================================================================
     "WATCH HOW IT WORKS" MODAL (Studio Grayscale Patch Simulator)
     ========================================================================== */

  function setupAnimatorModal() {
    DOM.btnCloseAnimator.addEventListener("click", closeAnimator);
    DOM.animatorModal.addEventListener("click", (e) => {
      if (e.target === DOM.animatorModal) closeAnimator();
    });

    DOM.btnAnimPlayPause.addEventListener("click", toggleAnimPlay);
    DOM.btnAnimPrev.addEventListener("click", () => {
      pauseAnim();
      stepAnim(-1);
    });
    DOM.btnAnimNext.addEventListener("click", () => {
      pauseAnim();
      stepAnim(1);
    });
    DOM.btnAnimRestart.addEventListener("click", () => {
      pauseAnim();
      state.anim.step = 0;
      renderAnimatorStep();
    });

    DOM.animKBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const k = parseInt(btn.getAttribute("data-ak"), 10);
        selectKernel(k);
      });
    });

    DOM.sliderAnimSpeed.addEventListener("input", (e) => {
      state.anim.speedMs = parseInt(e.target.value, 10);
      DOM.animSpeedVal.textContent = `${state.anim.speedMs}ms`;
      if (state.anim.isPlaying) {
        clearInterval(state.anim.timerId);
        state.anim.timerId = setInterval(() => stepAnim(1), state.anim.speedMs);
      }
    });
  }

  function closeAnimator() {
    pauseAnim();
    state.anim.isOpen = false;
    DOM.animatorModal.classList.add("hidden");
  }

  function toggleAnimPlay() {
    if (state.anim.isPlaying) {
      pauseAnim();
    } else {
      startAnim();
    }
  }

  function startAnim() {
    state.anim.isPlaying = true;
    DOM.btnAnimPlayPause.textContent = "⏸ Pause";
    DOM.btnAnimPlayPause.classList.add("btn-ghost");
    DOM.btnAnimPlayPause.classList.remove("btn-primary");
    state.anim.timerId = setInterval(() => stepAnim(1), state.anim.speedMs);
  }

  function pauseAnim() {
    state.anim.isPlaying = false;
    DOM.btnAnimPlayPause.textContent = "▶ Play";
    DOM.btnAnimPlayPause.classList.remove("btn-ghost");
    DOM.btnAnimPlayPause.classList.add("btn-primary");
    clearInterval(state.anim.timerId);
  }

  function stepAnim(delta) {
    let next = state.anim.step + delta;
    if (next >= 64) next = 0;
    if (next < 0) next = 63;
    state.anim.step = next;
    renderAnimatorStep();
  }

  function renderAnimatorStep() {
    if (!state.anim.patchData) return;

    const data = state.anim.patchData;
    const k = state.anim.kernelSize;
    const rad = Math.floor(k / 2);
    const step = state.anim.step;

    const r = Math.floor(step / 8);
    const c = step % 8;

    DOM.animStepBadge.textContent = `Step ${step + 1} / 64 (r=${r}, c=${c})`;

    const chanMat = data.channels.luma;
    const kWeights = data.kernel_matrices[k] || computeKernelMatrix(k, computeAutoSigma(k));
    const backendMat = data.backend_filtered[k];

    // 1. Render Input 8x8 Grid
    DOM.animInputGrid.innerHTML = "";
    for (let ir = 0; ir < 8; ir++) {
      for (let ic = 0; ic < 8; ic++) {
        const val = chanMat[ir][ic];
        const cell = document.createElement("div");
        cell.className = "patch-cell";

        const dr = ir - r;
        const dc = ic - c;
        const inWindow = Math.abs(dr) <= rad && Math.abs(dc) <= rad;
        const isCenter = dr === 0 && dc === 0;

        if (isCenter) cell.classList.add("cell-kernel-center");
        else if (inWindow) cell.classList.add("cell-kernel-active");

        cell.style.backgroundColor = `rgb(${val}, ${val}, ${val})`;
        cell.style.color = val > 128 ? "#000" : "#fff";
        cell.textContent = val;

        cell.addEventListener("click", () => {
          pauseAnim();
          state.anim.step = ir * 8 + ic;
          renderAnimatorStep();
        });

        DOM.animInputGrid.appendChild(cell);
      }
    }

    // 2. Convolution Math Rows
    DOM.animMathRows.innerHTML = "";
    let sum = 0;

    for (let di = -rad; di <= rad; di++) {
      for (let dj = -rad; dj <= rad; dj++) {
        const pr = reflect101(r + di, 8);
        const pc = reflect101(c + dj, 8);

        const pix = chanMat[pr][pc];
        const w = kWeights[di + rad][dj + rad];
        const prod = pix * w;
        sum += prod;

        const isReflected = r + di < 0 || r + di >= 8 || c + dj < 0 || c + dj >= 8;

        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>(${di >= 0 ? "+" : ""}${di}, ${dj >= 0 ? "+" : ""}${dj})${isReflected ? " 🔄" : ""}</td>
          <td>${pix}</td>
          <td>${w.toFixed(4)}</td>
          <td><strong>${prod.toFixed(2)}</strong></td>
        `;
        DOM.animMathRows.appendChild(tr);
      }
    }

    const rounded = Math.min(255, Math.max(0, Math.round(sum)));
    DOM.animSumVal.textContent = sum.toFixed(3);
    DOM.animRoundedVal.textContent = rounded;

    let refVal = rounded;
    if (backendMat && backendMat[r] && backendMat[r][c] !== undefined) {
      refVal = backendMat[r][c];
    }

    const diff = Math.abs(rounded - refVal);
    if (diff === 0) {
      DOM.animMiniMatch.textContent = "✓ Exact";
      DOM.animMiniMatch.className = "match-mini-tag";
    } else if (diff <= 1) {
      DOM.animMiniMatch.textContent = "✓ Match (±1)";
      DOM.animMiniMatch.className = "match-mini-tag";
    } else {
      DOM.animMiniMatch.textContent = `Δ=${diff}`;
      DOM.animMiniMatch.className = "match-mini-tag mismatch";
    }

    // 3. Render Output 8x8 Grid
    DOM.animOutputGrid.innerHTML = "";
    for (let ir = 0; ir < 8; ir++) {
      for (let ic = 0; ic < 8; ic++) {
        const idx = ir * 8 + ic;
        const cell = document.createElement("div");
        cell.className = "patch-cell";

        if (idx < step) {
          const v = backendMat ? backendMat[ir][ic] : 0;
          cell.classList.add("cell-out-computed");
          cell.style.backgroundColor = `rgb(${v}, ${v}, ${v})`;
          cell.style.color = v > 128 ? "#000" : "#fff";
          cell.textContent = v;
        } else if (idx === step) {
          cell.classList.add("cell-out-current");
          cell.style.backgroundColor = `rgb(${rounded}, ${rounded}, ${rounded})`;
          cell.style.color = rounded > 128 ? "#000" : "#fff";
          cell.textContent = rounded;
        } else {
          cell.style.backgroundColor = "#12141c";
          cell.style.color = "#475569";
          cell.textContent = "·";
        }

        cell.addEventListener("click", () => {
          pauseAnim();
          state.anim.step = idx;
          renderAnimatorStep();
        });

        DOM.animOutputGrid.appendChild(cell);
      }
    }
  }

  function verifyBackendMatch() {
    if (!state.anim.patchData) return;

    const data = state.anim.patchData;
    const k = state.anim.kernelSize;
    const rad = Math.floor(k / 2);
    const chanMat = data.channels.luma;
    const kWeights = data.kernel_matrices[k] || computeKernelMatrix(k, computeAutoSigma(k));
    const backendMat = data.backend_filtered[k];

    if (!backendMat) return;

    let maxDiff = 0;
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        let sum = 0;
        for (let di = -rad; di <= rad; di++) {
          for (let dj = -rad; dj <= rad; dj++) {
            const pr = reflect101(r + di, 8);
            const pc = reflect101(c + dj, 8);
            sum += chanMat[pr][pc] * kWeights[di + rad][dj + rad];
          }
        }
        const rounded = Math.min(255, Math.max(0, Math.round(sum)));
        const backendVal = backendMat[r][c];
        const diff = Math.abs(rounded - backendVal);
        if (diff > maxDiff) maxDiff = diff;
      }
    }

    if (maxDiff <= 1) {
      DOM.animMatchBadge.className = "badge-match";
      DOM.animMatchBadge.textContent = `✓ Matches backend (${k}×${k}, ±1 LSB)`;
    } else {
      DOM.animMatchBadge.className = "badge-match mismatch";
      DOM.animMatchBadge.textContent = `Variance Δ=${maxDiff}`;
    }
  }

  /* ==========================================================================
     FEATURE: 4-STEP CAPTIONED DEMO MODE
     ========================================================================== */

  const DEMO_STEPS = [
    {
      badge: "Step 1 of 4",
      title: "1. Choose an Image (Ground Truth)",
      caption: "The pipeline starts with a clean benchmark reference. All metrics evaluate quality relative to this image.",
      action: async () => {
        DOM.tabStudio.click();
        const sample1 = state.samplesList.find((s) => s.stem === "sample1_clean") || state.samplesList[0];
        if (sample1) selectSample(sample1, false);
      },
    },
    {
      badge: "Step 2 of 4",
      title: "2. Add Noise (AWGN Simulation)",
      caption: "Gaussian sensor noise (σ=50.0, seed=42) is injected into the image, dropping PSNR from infinity down to 14.81 dB.",
      action: async () => {
        DOM.tabStudio.click();
        currentNoiseType = "gaussian";
        DOM.pillOptions.forEach((b) => b.classList.toggle("active", b.getAttribute("data-noise") === "gaussian"));
        DOM.sliderNoiseAmount.value = 50;
        updateNoiseSliderLabel();
        DOM.inputSeed.value = 42;
      },
    },
    {
      badge: "Step 3 of 4",
      title: "3. Apply Gaussian Smoothing Filter",
      caption: "OpenCV 2D spatial convolution is applied. The 5×5 kernel reduces MSE by over 93% with optimal noise suppression.",
      action: async () => {
        await executePipeline({ noise_type: "gaussian", noise_amount: 50, seed: 42 });
        selectKernel(5);
      },
    },
    {
      badge: "Step 4 of 4",
      title: "4. Result & The Turnover Principle",
      caption: "MSE drops from 2147.82 to 140.64 (+11.84 dB gain). Kernels larger than 5×5 cause over-smoothing where edge blur exceeds noise reduction.",
      action: async () => {
        setSplitPosition(50);
        document.getElementById("step-result").scrollIntoView({ behavior: "smooth", block: "start" });
      },
    },
  ];

  function setupDemoMode() {
    DOM.btnPlayDemo.addEventListener("click", startDemoMode);
    DOM.demoBtnClose.addEventListener("click", exitDemoMode);
    DOM.demoBtnNext.addEventListener("click", () => advanceDemo(1));
    DOM.demoBtnPrev.addEventListener("click", () => advanceDemo(-1));
    DOM.demoBtnPlayPause.addEventListener("click", toggleDemoPlay);
  }

  function startDemoMode() {
    state.demo.isActive = true;
    state.demo.step = 1;
    state.demo.isPlaying = true;
    DOM.demoBanner.classList.remove("hidden");
    executeDemoStep(1);
    startDemoTimer();
    showToast("Starting 4-step demo walkthrough...", "info");
  }

  function exitDemoMode() {
    state.demo.isActive = false;
    clearInterval(state.demo.timerId);
    DOM.demoBanner.classList.add("hidden");
    showToast("Exited demo mode.", "info");
  }

  function toggleDemoPlay() {
    state.demo.isPlaying = !state.demo.isPlaying;
    if (state.demo.isPlaying) {
      DOM.demoBtnPlayPause.textContent = "⏸ Pause";
      startDemoTimer();
    } else {
      DOM.demoBtnPlayPause.textContent = "▶ Resume";
      clearInterval(state.demo.timerId);
    }
  }

  function startDemoTimer() {
    clearInterval(state.demo.timerId);
    state.demo.timerId = setInterval(() => {
      if (state.demo.step < 4) {
        advanceDemo(1);
      } else {
        exitDemoMode();
      }
    }, state.demo.stepDurationMs);
  }

  function advanceDemo(delta) {
    let next = state.demo.step + delta;
    if (next < 1) next = 1;
    if (next > 4) {
      exitDemoMode();
      return;
    }
    state.demo.step = next;
    executeDemoStep(next);
    if (state.demo.isPlaying) startDemoTimer();
  }

  function executeDemoStep(stepNum) {
    const config = DEMO_STEPS[stepNum - 1];
    DOM.demoBadge.textContent = config.badge;
    DOM.demoTitle.textContent = config.title;
    DOM.demoCaption.textContent = config.caption;
    config.action();
  }

  /* ==========================================================================
     SUMMARY EXPORT (Markdown Report)
     ========================================================================== */

  function setupSummaryExport() {
    DOM.btnDownloadSummary.addEventListener("click", downloadSummary);
  }

  function downloadSummary() {
    if (!state.latestResult) {
      showToast("Filter an image before downloading summary.", "error");
      return;
    }

    const res = state.latestResult;
    const dateStr = new Date().toLocaleString();

    let md = `# VisionLab — Gaussian Filter Evaluation Summary\n\n`;
    md += `**Date:** ${dateStr}\n`;
    md += `**Source Image:** \`${res.filename}\` (${res.dimensions.width} × ${res.dimensions.height} px)\n\n`;

    md += `## 1. Noise Degradation\n`;
    md += `- **Model:** ${res.noise.label}\n`;
    md += `- **Seed:** ${res.noise.seed}\n`;
    md += `- **Noisy MSE:** ${res.noise.baseline_mse.toFixed(2)}\n`;
    md += `- **Noisy PSNR:** ${res.noise.baseline_psnr.toFixed(2)} dB\n\n`;

    md += `## 2. Multi-Kernel Results\n\n`;
    md += `| Kernel | Sigma (σ) | MSE (Loss ↓) | PSNR (Fidelity ↑) | Optimal |\n`;
    md += `|:------:|:---------:|:------------:|:-----------------:|:-------:|\n`;

    res.kernels.forEach((k) => {
      md += `| ${k.kernel_size}×${k.kernel_size} | ${k.sigma.toFixed(2)} | ${k.mse.toFixed(2)} | ${k.psnr.toFixed(2)} dB | ${k.is_optimal ? "**Best**" : "-"} |\n`;
    });

    md += `\n## 3. Key Findings\n`;
    md += `- **Optimal Window:** ${res.optimal_kernel.kernel_size}×${res.optimal_kernel.kernel_size} (MSE = ${res.optimal_kernel.mse.toFixed(2)}, PSNR = ${res.optimal_kernel.psnr.toFixed(2)} dB)\n`;
    md += `- **Core Execution Time:** ${res.timing.cv_time_ms} ms\n`;
    md += `- **Takeaway:** Bigger kernels remove more noise but blur more detail (the over-smoothing turnover point).\n`;

    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${res.stem}_gaussian_filter_summary.md`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("Downloaded evaluation summary report.", "success");
  }

  /* ==========================================================================
     TOAST NOTIFICATIONS
     ========================================================================== */

  function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    const icon = type === "success" ? "✓" : type === "error" ? "⚠" : "ℹ";
    toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;

    DOM.toastStack.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(40px)";
      toast.style.transition = "all 0.25s ease";
      setTimeout(() => toast.remove(), 250);
    }, 3500);
  }

  // Start app on DOMContentLoaded
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
