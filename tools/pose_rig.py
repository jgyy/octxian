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
    centroid_x, centroid_y = (weights * xx).sum() / total, (weights * yy).sum() / total
    interior = cv2.distanceTransform(np.uint8(skin), cv2.DIST_L2, 5)
    scores = interior * np.exp(-((xx - centroid_x) ** 2 + (yy - centroid_y) ** 2) / (2 * 12 ** 2))
    best = np.unravel_index(np.argmax(scores), scores.shape)
    return np.float32([xx[best], yy[best]])


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
    points = first.copy()
    root_offset = first[10] - second[10]
    points[:15] = np.float32(first[:15] * (1 - amount) + (second[:15] + root_offset) * amount)
    # The palm travels around the shoulder, not straight through the torso.
    direction = np.sign(second[0, 0] - second[10, 0]) or 1
    arc = np.float32([direction * 30, -6]) * (4 * amount * (1 - amount))
    points[:5] += arc
    points[5:10] += arc * 0.45
    return points


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
    path = [intermediate_points(pair, pose_amount(2 * np.pi * index / len(frames), motion))[0]
            for index in range(len(frames))]
    travel = max(float(np.linalg.norm(point - path[0])) for point in path)
    if travel < 48:
        raise AssertionError(f"{motion}: palm travels only {travel:.1f}px; visible gesture requires 48px")
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


def split_hand(pixels, hand_point):
    """Separate a feathered hand layer and fill its underlying body plate."""
    height, width = pixels.shape[:2]
    yy, xx = np.mgrid[:height, :width]
    radius = ((xx - hand_point[0]) / 22) ** 2 + ((yy - hand_point[1]) / 29) ** 2
    mask = np.float32(np.clip((1.05 - radius) / 0.20, 0, 1))[:, :, None]
    hand = pixels * mask
    alpha = pixels[:, :, 3:4]
    straight = np.divide(pixels[:, :, :3], alpha, out=np.zeros_like(pixels[:, :, :3]), where=alpha > 0.001)
    inpaint_mask = np.uint8(mask[:, :, 0] > 0.02) * 255
    rgb = cv2.inpaint(np.uint8(np.clip(straight * 255, 0, 255)), inpaint_mask, 3, cv2.INPAINT_TELEA)
    ring = (radius >= 1.1) & (radius < 1.6)
    behind_is_body = float(np.mean(alpha[:, :, 0][ring] >= 0.7)) > 0.70
    body_alpha = alpha * (1 - mask) + float(behind_is_body) * mask
    body = np.concatenate([np.float32(rgb) / 255 * body_alpha, body_alpha], axis=2)
    return body, hand


def place_hand(body, layer, source_center, destination_center):
    offset = destination_center - source_center
    transform = np.float32([[1, 0, offset[0]], [0, 1, offset[1]]])
    hand = cv2.warpAffine(layer, transform, (body.shape[1], body.shape[0]), flags=cv2.INTER_LINEAR)
    return hand + body * (1 - hand[:, :, 3:4])


def capsule_mask(shape, start, end, radius):
    yy, xx = np.mgrid[:shape[0], :shape[1]].astype(np.float32)
    vector = end - start
    length_squared = max(float(vector @ vector), 1)
    along = np.clip(((xx - start[0]) * vector[0] + (yy - start[1]) * vector[1]) / length_squared, 0, 1)
    distance = np.sqrt((xx - start[0] - along * vector[0]) ** 2
                       + (yy - start[1] - along * vector[1]) ** 2)
    return np.float32(np.clip((radius + 1.5 - distance) / 3, 0, 1))[:, :, None]


def arm_layers(pixels, points, radius):
    upper_mask = capsule_mask(pixels.shape, points[10], points[5], radius)
    lower_mask = capsule_mask(pixels.shape, points[5], points[0], radius)
    body, hand = split_hand(pixels, points[0])
    full_mask = np.maximum(upper_mask, lower_mask)
    alpha = pixels[:, :, 3:4]
    straight = np.divide(pixels[:, :, :3], alpha, out=np.zeros_like(pixels[:, :, :3]), where=alpha > 0.001)
    filled = cv2.inpaint(np.uint8(np.clip(straight * 255, 0, 255)),
                         np.uint8(full_mask[:, :, 0] > 0.02) * 255, 3, cv2.INPAINT_TELEA)
    yy, xx = np.mgrid[:pixels.shape[0], :pixels.shape[1]]
    hip, face = points[20], points[15]
    torso = ((np.abs(xx - hip[0]) < 44) & (yy > face[1] + 45)
             & (yy < hip[1] + 90))[:, :, None]
    fill_alpha = alpha * np.float32(torso)
    body_alpha = body[:, :, 3:4] * (1 - full_mask) + fill_alpha * full_mask
    plate = np.concatenate([np.float32(filled) / 255 * body_alpha, body_alpha], axis=2)
    return plate, pixels * upper_mask, pixels * lower_mask, hand


def move_segment(layer, source_start, source_end, target_start, target_end):
    source_vector = source_end - source_start
    target_vector = target_end - target_start
    source_perp = np.float32([-source_vector[1], source_vector[0]])
    target_perp = np.float32([-target_vector[1], target_vector[0]])
    source_perp /= max(float(np.linalg.norm(source_perp)), 1)
    target_perp /= max(float(np.linalg.norm(target_perp)), 1)
    source = np.float32([source_start, source_end, source_start + source_perp * 20])
    target = np.float32([target_start, target_end, target_start + target_perp * 20])
    affine = cv2.getAffineTransform(source, target)
    return cv2.warpAffine(layer, affine, (layer.shape[1], layer.shape[0]), flags=cv2.INTER_LINEAR)


def composite_over(background, foreground):
    return foreground + background * (1 - foreground[:, :, 3:4])
