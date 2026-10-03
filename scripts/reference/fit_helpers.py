"""NumPy-only helpers for sparse, conservative reference fitting.

These functions do not know MakeHuman vertex indices and do not edit scenes.
Choose homologous anatomical mesh points explicitly. Fit the camera before
deforming a character. Preserve depth from the anatomical source and separately
validate profile renders; never substitute MediaPipe's inferred z for anatomy.
"""
from __future__ import annotations

import numpy as np


def similarity_2d(source, target, weights=None):
    """Return row-vector rotation, scale and translation mapping source to target.

    y may point down or up, provided both sets use the same convention. Scale is
    isotropic and reflection is forbidden. Intended for aligning comparison
    images or estimating a long-lens reference camera from measured anchors.
    """
    source = np.asarray(source, dtype=float)
    target = np.asarray(target, dtype=float)
    if source.shape != target.shape or source.ndim != 2 or source.shape[1] != 2:
        raise ValueError("source and target must have matching (N, 2) shapes")
    if len(source) < 2:
        raise ValueError("At least two noncoincident point pairs are needed")
    weights = np.ones(len(source)) if weights is None else np.asarray(weights, dtype=float)
    if weights.shape != (len(source),) or np.any(weights < 0) or weights.sum() <= 0:
        raise ValueError("weights must be nonnegative, one per pair, with nonzero sum")
    weights = weights / weights.sum()
    center_s = (source * weights[:, None]).sum(axis=0)
    center_t = (target * weights[:, None]).sum(axis=0)
    xs, xt = source - center_s, target - center_t
    covariance = (xs * weights[:, None]).T @ xt
    u, _, vt = np.linalg.svd(covariance)
    correction = np.eye(2)
    correction[1, 1] = np.linalg.det(u @ vt)
    rotation = u @ correction @ vt
    denominator = float(np.sum(weights[:, None] * xs * xs))
    if denominator < 1e-12:
        raise ValueError("Degenerate source anchors")
    scale = float(np.sum(weights[:, None] * (xs @ rotation) * xt) / denominator)
    translation = center_t - scale * center_s @ rotation
    fitted = scale * source @ rotation + translation
    return {
        "rotation": rotation, "scale": scale, "translation": translation,
        "fitted": fitted,
        "weighted_rms": float(np.sqrt(np.sum(weights * np.sum((fitted - target) ** 2, axis=1)))),
    }


def project_front_to_reference_uv(vertices, world_eye_mid, world_interiris,
                                  ref_eyes_px=((388.4, 353.9), (548.4, 352.8)),
                                  image_size=(928, 1152),
                                  world_right=(1, 0, 0), world_up=(0, 0, 1)):
    """Orthographic diagnostic projection into the front reference.

    Returns conventional texture UV (v up). This is a camera-projection starting
    point, not a final skin atlas. Restrict to visible front-facing skin; exclude
    eyeballs, cavity, occluded ears, hair and silhouette. Fit camera / geometry
    first, then reproject. Image illumination and specular highlights remain
    baked into the photograph unless an independent de-lighting stage removes
    them. This must not overwrite a clean material's roughness/normal maps.
    """
    if world_interiris <= 0:
        raise ValueError("world_interiris must be positive")
    vertices = np.asarray(vertices, dtype=float)
    eye_ref = np.asarray(ref_eyes_px, dtype=float)
    midpoint = eye_ref.mean(axis=0)
    eye_delta = eye_ref[1] - eye_ref[0]
    pixels_per_world = np.linalg.norm(eye_delta) / world_interiris
    right2 = eye_delta / np.linalg.norm(eye_delta)
    up2 = np.array([right2[1], -right2[0]])
    right3, up3 = np.asarray(world_right, float), np.asarray(world_up, float)
    right3 = right3 / np.linalg.norm(right3)
    up3 = up3 / np.linalg.norm(up3)
    if abs(float(right3 @ up3)) > 1e-6:
        raise ValueError("world_right and world_up must be orthogonal")
    relative = vertices - np.asarray(world_eye_mid, dtype=float)
    pixels = midpoint + pixels_per_world * (
        (relative @ right3)[:, None] * right2 + (relative @ up3)[:, None] * up2)
    uv = pixels / np.asarray(image_size, dtype=float)
    uv[:, 1] = 1 - uv[:, 1]
    return uv


def smooth_displacement_2d(points, source_anchors, target_anchors, radius,
                           regularization=.001, mask=None, max_displacement=None):
    """Smooth local image-plane displacement from *mapped anatomical* anchors.

    Use x,z for a front-facing Blender source; keep y depth unchanged. Input
    units must match. Supply unchanged boundary anchors at forehead, cheek and
    jaw limits and a vertex mask selecting only intended front-face vertices.
    Fit source/target camera pose first. This Gaussian interpolator adds neither
    an affine global warp nor a generic replacement surface.

    Outputs displacement vectors. Caller owns conservative strength (e.g. 0.3),
    a physical maximum, mirrored-control policy and eyelid/oral seam QA.
    """
    points = np.asarray(points, dtype=float)
    source = np.asarray(source_anchors, dtype=float)
    target = np.asarray(target_anchors, dtype=float)
    if source.shape != target.shape or source.ndim != 2 or source.shape[1] != 2:
        raise ValueError("Anchors must have matching (N, 2) shapes")
    if radius <= 0 or regularization < 0:
        raise ValueError("radius > 0 and regularization >= 0 required")
    sq = np.sum((source[:, None, :] - source[None, :, :]) ** 2, axis=-1)
    kernel = np.exp(-sq / (2 * radius ** 2)) + regularization * np.eye(len(source))
    coefficients = np.linalg.solve(kernel, target - source)
    sq_query = np.sum((points[:, None, :] - source[None, :, :]) ** 2, axis=-1)
    displacement = np.exp(-sq_query / (2 * radius ** 2)) @ coefficients
    if mask is not None:
        mask = np.asarray(mask, dtype=float)
        if mask.shape != (len(points),) or np.any((mask < 0) | (mask > 1)):
            raise ValueError("mask must have one [0,1] value per point")
        displacement *= mask[:, None]
    if max_displacement is not None:
        norm = np.linalg.norm(displacement, axis=1)
        displacement *= np.minimum(1, max_displacement / np.maximum(norm, 1e-12))[:, None]
    return displacement


def self_test():
    source = np.array([[0, 0], [1, 0], [0, 1], [1, 1.]])
    angle = .15
    rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    target = 2.3 * source @ rotation + [4, -2]
    fit = similarity_2d(source, target)
    assert np.allclose(fit["fitted"], target)
    assert fit["weighted_rms"] < 1e-12
    assert np.isclose(np.linalg.det(fit["rotation"]), 1)
    world_eyes = np.array([[-.031, 0, 1.6], [.031, 0, 1.6]])
    uv = project_front_to_reference_uv(world_eyes, [0, 0, 1.6], .062)
    ref = np.array([[388.4 / 928, 1 - 353.9 / 1152], [548.4 / 928, 1 - 352.8 / 1152]])
    assert np.allclose(uv, ref)
    delta = smooth_displacement_2d(source, source, source + [.1, -.05], radius=.5,
                                   regularization=0, max_displacement=.2)
    assert np.allclose(delta, [.1, -.05])
    masked = smooth_displacement_2d(source, source, target, .5, mask=np.zeros(4))
    assert np.allclose(masked, 0)
    return "similarity, reference UV, sparse warp and mask tests passed"


if __name__ == "__main__":
    print(self_test())
