"""Landmark-guided pose warping keeps moving hands aligned and opaque."""
import cv2
import numpy as np


def refine_hand(sheet, seed):
    """Find the nearest warm skin pixels inside the annotated palm area."""
    pixels = np.asarray(sheet, dtype=np.float32)
    x, y = seed
    left, top = max(0, int(x - 42)), max(0, int(y - 42))
    patch = pixels[top:min(pixels.shape[0], int(y + 43)), left:min(pixels.shape[1], int(x + 43))]
    red, green, blue, alpha = [patch[:, :, index] for index in range(4)]
    skin = ((red > 120) & (green > 80) & (red - green >= 4) & (red - green <= 55)
            & (green - blue >= 2) & (green - blue <= 48) & (alpha >= 160))
    yy, xx = np.mgrid[:patch.shape[0], :patch.shape[1]]
    xx, yy = xx + left, yy + top
    weights = skin * np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * 13 ** 2))
    total = weights.sum()
    if total < 1:
        raise ValueError(f"Palm annotation {seed} misses opaque skin")
    return np.array([(weights * xx).sum() / total, (weights * yy).sum() / total], dtype=np.float32)


def build_points(sheet, spec, transform, cell):
    centers = {name: np.asarray(value, dtype=np.float32) for name, value in spec.items()}
    centers["hand"] = refine_hand(sheet, centers["hand"])
    points = []
    for name, radius in [("hand", 14), ("elbow", 10), ("shoulder", 9), ("face", 15), ("hip", 22)]:
        center = centers[name]
        for delta in [(0, 0), (-radius, -radius), (radius, -radius),
                      (radius, radius), (-radius, radius)]:
            points.append(transform(center + delta))
    width, height = cell
    points.extend([(width / 2 - 48, height - 24), (width / 2, height - 24),
                   (width / 2 + 48, height - 24)])
    points.extend([(0, 0), (width - 1, 0), (width - 1, height - 1), (0, height - 1),
                   (width / 2, 0), (width / 2, height - 1),
                   (0, height / 4), (0, height / 2), (0, height * 3 / 4),
                   (width - 1, height / 4), (width - 1, height / 2), (width - 1, height * 3 / 4)])
    points = np.asarray(points, dtype=np.float32)
    points[:, 0] = np.clip(points[:, 0], 0, width - 1)
    points[:, 1] = np.clip(points[:, 1], 0, height - 1)
    return points


def intermediate_points(pair, amount):
    first, second = pair
    points = np.float32(first * (1 - amount) + second * amount)
    # The palm travels around the shoulder, not straight through the torso.
    direction = np.sign(second[0, 0] - second[10, 0]) or 1
    arc = np.float32([direction * 30, -6]) * (4 * amount * (1 - amount))
    points[:5] += arc
    points[5:10] += arc * 0.45
    return points


def triangulate(pair, cell):
    points = intermediate_points(pair, 0.5)
    subdivision = cv2.Subdiv2D((0, 0, cell[0], cell[1]))
    inserted = []
    for point in points:
        if not any(np.linalg.norm(point - previous) < 0.1 for previous in inserted):
            subdivision.insert(tuple(float(value) for value in point))
            inserted.append(point)
    triangles = []
    for triangle in subdivision.getTriangleList():
        vertices = triangle.reshape(3, 2)
        indices = [int(np.argmin(np.sum((points - vertex) ** 2, axis=1))) for vertex in vertices]
        if max(np.linalg.norm(points[index] - vertex) for index, vertex in zip(indices, vertices)) < 0.2:
            triangles.append(indices)
    return triangles


def warp_pose(pixels, source_points, destination_points, triangles, grid):
    xx, yy = grid
    map_x, map_y = xx.copy(), yy.copy()
    height, width = xx.shape
    for indices in triangles:
        source = source_points[indices]
        destination = destination_points[indices]
        if abs(cv2.contourArea(destination)) < 0.05:
            continue
        x, y, w, h = cv2.boundingRect(destination)
        left, top, right, bottom = max(0, x), max(0, y), min(width, x + w), min(height, y + h)
        if right <= left or bottom <= top:
            continue
        mask = np.zeros((bottom - top, right - left), dtype=np.uint8)
        cv2.fillConvexPoly(mask, np.rint(destination - [left, top]).astype(np.int32), 1)
        affine = cv2.getAffineTransform(destination, source)
        region_x, region_y = xx[top:bottom, left:right], yy[top:bottom, left:right]
        mapped_x = affine[0, 0] * region_x + affine[0, 1] * region_y + affine[0, 2]
        mapped_y = affine[1, 0] * region_x + affine[1, 1] * region_y + affine[1, 2]
        map_x[top:bottom, left:right][mask > 0] = mapped_x[mask > 0]
        map_y[top:bottom, left:right][mask > 0] = mapped_y[mask > 0]
    return cv2.remap(pixels, map_x, map_y, cv2.INTER_LINEAR)


def pose_amount(phase, motion):
    amount = 0.5 - 0.5 * np.cos(phase)
    if motion == "channeling":
        return amount ** 0.8
    if motion == "resolve":
        return amount * amount * (3 - 2 * amount)
    if motion == "wind":
        return 0.5 - 0.5 * np.cos(phase + 0.45)
    return amount


def require_solid_hands(frames, pair, motion):
    minimum = 1.0
    for index in (8, 16, 24, 40, 48, 56):
        amount = pose_amount(2 * np.pi * index / len(frames), motion)
        hand = intermediate_points(pair, amount)[0]
        x, y = np.rint(hand).astype(int)
        image = np.asarray(frames[index])
        patch = image[max(0, y - 2):y + 3, max(0, x - 2):x + 3]
        coverage = float(np.mean(patch[:, :, 3] >= 160))
        minimum = min(minimum, coverage)
    if minimum < 0.80:
        raise AssertionError(f"{motion}: moving palm becomes transparent ({minimum:.0%} opaque coverage)")
    return minimum
