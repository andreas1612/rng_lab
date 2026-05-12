"""2D spatial uniformity test: grid chi-square on 8000 uniform points.

Implementation note: this is a grid chi-square rather than a true minimum-
distance test. The grid form avoids the boundary bias inherent in nearest-
neighbour distances on a finite square and is the chosen MiniLab method.
"""
import numpy as np
from scipy import stats as scipy_stats

from core.labels import classify_p_value, LABEL_INDICATIVE_ONLY, LABEL_INCONCLUSIVE

TEST_ID = "SUPP-07"
TEST_NAME = "Minimum Distance (2D)"
MIN_BITS = 8000 * 2 * 8
RECOMMENDED_BITS = 1_000_000


def run(data: bytes) -> dict:
    arr = np.frombuffer(data, dtype=np.uint8)
    n_points = 8000
    needed = n_points * 2
    if len(arr) < needed:
        return {
            "test_id": TEST_ID, "name": TEST_NAME,
            "statistic": None, "p_value": None,
            "status": LABEL_INDICATIVE_ONLY,
            "detail": f"Need at least {needed} bytes, got {len(arr)}.",
        }
    try:
        xy = arr[:needed].reshape(n_points, 2).astype(float) / 255.0
        n_grid = 10
        cell_x = np.floor(xy[:, 0] * n_grid).clip(0, n_grid - 1).astype(int)
        cell_y = np.floor(xy[:, 1] * n_grid).clip(0, n_grid - 1).astype(int)
        cell_idx = cell_x * n_grid + cell_y
        counts = np.bincount(cell_idx, minlength=n_grid ** 2).astype(float)
        expected = np.full(n_grid ** 2, n_points / (n_grid ** 2))
        chi2, p = scipy_stats.chisquare(counts, f_exp=expected)
        chi2, p = float(chi2), float(p)
    except Exception as exc:
        return {
            "test_id": TEST_ID, "name": TEST_NAME,
            "statistic": None, "p_value": None,
            "status": LABEL_INCONCLUSIVE, "detail": str(exc),
        }
    return {
        "test_id": TEST_ID, "name": TEST_NAME,
        "statistic": round(chi2, 4),
        "p_value": round(p, 6),
        "status": classify_p_value(p),
        "detail": (
            f"2D grid chi-sq={chi2:.2f} on {n_grid**2 - 1} df "
            f"({n_points} points in {n_grid}x{n_grid} grid, expected "
            f"{n_points//n_grid**2} per cell), p={p:.6f}."
        ),
    }
