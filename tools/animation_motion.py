"""Measure visible pose changes after removing whole-image translation.

Opaque character silhouettes exclude particles. A tint, pan, or tiny breathing
warp must never qualify as articulated motion.
"""
import cv2
import numpy as np

LIMITS = {"changed_fraction": 0.07, "upper_changed_fraction": 0.12,
          "silhouette_change_fraction": 0.02}


def motion_metrics(first, opposite):
    a = np.asarray(first.convert("RGBA"), dtype=np.float32)
    b = np.asarray(opposite.convert("RGBA"), dtype=np.float32)
    # Align silhouettes so translating an unchanged portrait cannot pass.
    shift, confidence = cv2.phaseCorrelate(a[:, :, 3], b[:, :, 3])
    dx, dy = shift if confidence > 0.1 else (0.0, 0.0)
    b = cv2.warpAffine(b, np.float32([[1, 0, -dx], [0, 1, -dy]]),
                      (a.shape[1], a.shape[0]), flags=cv2.INTER_LINEAR)
    opaque_a, opaque_b = a[:, :, 3] >= 160, b[:, :, 3] >= 160
    body = opaque_a | opaque_b
    if not body.any():
        return {key: 0.0 for key in LIMITS}
    rgb_a = a[:, :, :3] * (a[:, :, 3:4] / 255)
    rgb_b = b[:, :, :3] * (b[:, :, 3:4] / 255)
    changed = np.mean(np.abs(rgb_a - rgb_b), axis=2) >= 24
    upper = body.copy()
    upper[int(a.shape[0] * 0.60):] = False
    return {
        "changed_fraction": float(np.count_nonzero(changed & body) / body.sum()),
        "upper_changed_fraction": float(np.count_nonzero(changed & upper) / max(upper.sum(), 1)),
        "silhouette_change_fraction": float(np.count_nonzero(opaque_a ^ opaque_b) / body.sum()),
    }


def require_visible_motion(metrics, label):
    for key, minimum in LIMITS.items():
        if metrics[key] < minimum:
            raise AssertionError(f"{label}: {key}={metrics[key]:.3f} below {minimum:.2f}; pose movement is too small")
