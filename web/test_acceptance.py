import urllib.request
import json
import math
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_pipeline():
    print("=== TEST 1: PIPELINE PROCESSING & STEP 5 PART B REGRESSION ===")
    req_body = json.dumps({
        "sample_name": "sample1_clean.png",
        "noise_type": "gaussian",
        "gaussian_std": 50.0,
        "gaussian_mean": 0.0,
        "seed": 42,
        "kernel_sizes": [3, 5, 7, 9]
    }).encode("utf-8")

    req = urllib.request.Request(f"{BASE_URL}/api/process", data=req_body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    assert data["success"], "Pipeline process returned success=False"
    
    noisy_mse = data["noise"]["baseline_mse"]
    noisy_psnr = data["noise"]["baseline_psnr"]
    print(f"Noisy baseline MSE: {noisy_mse:.2f}, PSNR: {noisy_psnr:.2f} dB")
    assert abs(noisy_mse - 2147.82) < 0.05, f"Expected noisy MSE 2147.82, got {noisy_mse}"

    k9 = next(k for k in data["kernels"] if k["kernel_size"] == 9)
    print(f"9x9 Filtered MSE: {k9['mse']:.2f}, PSNR: {k9['psnr']:.2f} dB")
    assert abs(k9["mse"] - 161.34) < 0.05, f"Expected 9x9 MSE 161.34, got {k9['mse']}"
    assert abs(k9["psnr"] - 26.05) < 0.05, f"Expected 9x9 PSNR 26.05, got {k9['psnr']}"

    opt = data["optimal_kernel"]
    print(f"Optimal Kernel: {opt['kernel_size']}x{opt['kernel_size']}, MSE: {opt['mse']:.2f}, PSNR: {opt['psnr']:.2f} dB")
    print("PASS: Regression Check 1 verified!\n")

    print("=== TEST 2: STEP 3 KERNEL WEIGHTS SUM & OPENCV ALIGNMENT ===")
    detailed = data["detailed_kernels"]
    for k in [3, 5, 7, 9]:
        info = detailed[str(k)]
        sigma = info["sigma"]
        weights_2d = info["weights_2d"]
        sum_norm = info["sum_normalized"]
        center = info["center_weight"]
        corner = info["corner_weight"]
        
        computed_sum = sum(sum(row) for row in weights_2d)
        print(f"Kernel {k}x{k} (sigma={sigma:.2f}): sum={computed_sum:.6f}, display='{sum_norm}', center={center:.4f}, corner={corner:.4f}")
        assert sum_norm == "1.0000", f"Expected sum 1.0000, got {sum_norm}"
        assert abs(computed_sum - 1.0) < 1e-5, f"Float sum discrepancy: {computed_sum}"
        
        if k == 3:
            w1d = info["weights_1d"]
            print(f"  3x3 1D weights: {[round(x, 4) for x in w1d]}")
            assert abs(w1d[0] - 0.2390) < 0.001, f"Expected 1D weight ~0.2390, got {w1d[0]}"
            assert abs(w1d[1] - 0.5220) < 0.001, f"Expected 1D center ~0.5220, got {w1d[1]}"
            assert abs(center - 0.2725) < 0.001, f"Expected 2D center ~0.2725, got {center}"

    print("PASS: Step 3 Weights Check verified!\n")

    print("=== TEST 3: STEP 4 CORNER BORDER REFLECTION & BACKEND MATCH ===")
    patch = data["initial_patch"]
    corner_verif = patch["corner_verification"]
    for k in [3, 5, 7, 9]:
        ck = corner_verif[f"k_{k}"]
        print(f"Corner (0,0) with {k}x{k}: manual={ck['manual']}, backend={ck['backend']}, diff={ck['diff']}, matches={ck['matches']}")
        assert ck["matches"], f"Corner match failed for {k}x{k}: diff={ck['diff']}"
        assert ck["diff"] <= 1, f"Corner diff exceeded 1 level: {ck['diff']}"

    print("PASS: Step 4 Corner Check verified!\n")

    print("=== TEST 4: STEP 2 NOISE ARITHMETIC & CLIPPING CHECK ===")
    clean_luma = patch["channels_clean"]["luma"]
    noise_luma = patch["channels_noise"]["luma"]
    noisy_luma = patch["channels"]["luma"]

    for r in range(8):
        for c in range(8):
            cl = clean_luma[r][c]
            nl = noise_luma[r][c]
            ny = noisy_luma[r][c]
            expected_clipped = max(0, min(255, cl + nl))
            assert ny == expected_clipped, f"Arithmetic mismatch at ({r},{c}): {cl} + {nl} = {cl+nl}, expected {expected_clipped}, got {ny}"

    print(f"All 64 pixels in 8x8 patch have exact arithmetic clean + noise = noisy.")
    clipping = patch["clipping"]
    print(f"Clipping metadata: has_clipping={clipping['has_clipping']}, total_clipped={clipping['total_clipped']}")
    if clipping["has_clipping"]:
        sc = clipping["sample_clipped"]
        print(f"Sample clipped pixel: {sc}")
        assert sc["clipped"] == max(0, min(255, sc["sum"]))

    print("PASS: Step 2 Arithmetic & Clipping Check verified!\n")

    print("=== TEST 5: STEP 5 PART A TINY SAMPLES CHECK ===")
    tiny = patch["tiny_eval_samples"]
    print(f"Tiny eval samples count: {len(tiny)}")
    assert len(tiny) == 4, f"Expected 4 tiny eval samples, got {len(tiny)}"
    for s in tiny:
        expected_diff = s["clean"] - s["filtered"]
        assert s["diff"] == expected_diff, f"Diff mismatch: {s}"
        assert s["diff_sq"] == expected_diff ** 2, f"Diff squared mismatch: {s}"
        print(f"  Pixel ({s['r']}, {s['c']}): clean={s['clean']}, filtered={s['filtered']}, diff={s['diff']}, sq={s['diff_sq']}")

    print("PASS: Step 5 Part A Tiny Samples verified!\n")
    print("ALL API ACCEPTANCE CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_pipeline()
