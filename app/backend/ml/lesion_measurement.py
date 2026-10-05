"""
CancerLense Lesion Measurement

Image-based candidate-region estimation only.

IMPORTANT:
This is NOT clinical lesion segmentation.
It does NOT diagnose cancer.
Physical dimensions require a valid calibration reference.
"""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

MIN_AREA_RATIO = 0.003
MAX_AREA_RATIO = 0.35

MIN_WIDTH = 20
MIN_HEIGHT = 20

MIN_CANDIDATE_SCORE = 0.18


# ============================================================
# HELPERS
# ============================================================

def _clip(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def _candidate_score(
    area_ratio: float,
    center_x: float,
    center_y: float,
    image_width: int,
    image_height: int,
) -> float:
    """
    Score a candidate using simple image geometry.

    This is only a heuristic for selecting an image-based
    candidate region. It is NOT a clinical probability.
    """

    # Prefer moderate-sized regions.
    if area_ratio <= 0:
        area_score = 0.0
    elif area_ratio <= 0.15:
        area_score = 1.0
    elif area_ratio <= 0.35:
        area_score = 0.7
    else:
        area_score = 0.0

    # Prefer regions away from extreme image borders.
    normalized_x = center_x / max(image_width, 1)
    normalized_y = center_y / max(image_height, 1)

    distance_from_center = np.sqrt(
        ((normalized_x - 0.5) ** 2)
        + ((normalized_y - 0.5) ** 2)
    )

    center_score = 1.0 - _clip(
        distance_from_center / 0.7071,
        0.0,
        1.0,
    )

    score = (
        0.60 * area_score
        + 0.40 * center_score
    )

    return float(
        _clip(score, 0.0, 1.0)
    )


# ============================================================
# MAIN ESTIMATOR
# ============================================================

def estimate_lesion_measurement(
    image_bgr: np.ndarray,
) -> dict[str, Any]:
    """
    Estimate a candidate abnormal-looking region.

    This is an image-processing heuristic only.

    It should never be interpreted as:
    - clinical segmentation
    - cancer localization
    - diagnosis
    - lesion boundary detection
    """

    if (
        image_bgr is None
        or image_bgr.size == 0
    ):
        raise ValueError(
            "Invalid image supplied for lesion measurement."
        )

    image = image_bgr.copy()

    height, width = image.shape[:2]

    image_area = width * height

    if image_area <= 0:
        return _not_estimated(
            "Invalid image dimensions."
        )

    # --------------------------------------------------------
    # HSV analysis
    # --------------------------------------------------------

    hsv = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2HSV,
    )

    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]

    # --------------------------------------------------------
    # Red / pink candidate regions
    # --------------------------------------------------------

    red_1 = cv2.inRange(
        hsv,
        np.array([0, 45, 45]),
        np.array([15, 255, 255]),
    )

    red_2 = cv2.inRange(
        hsv,
        np.array([165, 45, 45]),
        np.array([180, 255, 255]),
    )

    red_mask = cv2.bitwise_or(
        red_1,
        red_2,
    )

    # --------------------------------------------------------
    # Brightness filtering
    # --------------------------------------------------------

    valid_brightness = cv2.inRange(
        value,
        45,
        245,
    )

    mask = cv2.bitwise_and(
        red_mask,
        valid_brightness,
    )

    # --------------------------------------------------------
    # Saturation filtering
    # --------------------------------------------------------

    saturation_mask = cv2.inRange(
        saturation,
        45,
        255,
    )

    mask = cv2.bitwise_and(
        mask,
        saturation_mask,
    )

    # --------------------------------------------------------
    # Morphological cleanup
    # --------------------------------------------------------

    kernel = np.ones(
        (5, 5),
        np.uint8,
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel,
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel,
    )

    # --------------------------------------------------------
    # Find contours
    # --------------------------------------------------------

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    candidates: list[dict[str, Any]] = []

    for contour in contours:

        area = float(
            cv2.contourArea(contour)
        )

        area_ratio = (
            area / image_area
        )

        # Reject extremely small candidates.
        if area_ratio < MIN_AREA_RATIO:
            continue

        # Reject giant/full-image candidates.
        if area_ratio > MAX_AREA_RATIO:
            continue

        x, y, w, h = cv2.boundingRect(
            contour
        )

        if (
            w < MIN_WIDTH
            or h < MIN_HEIGHT
        ):
            continue

        # Reject candidates touching too much of the image border.
        touches_left = x <= 1
        touches_top = y <= 1
        touches_right = (
            x + w >= width - 1
        )
        touches_bottom = (
            y + h >= height - 1
        )

        border_count = sum(
            [
                touches_left,
                touches_top,
                touches_right,
                touches_bottom,
            ]
        )

        if border_count >= 3:
            continue

        center_x = (
            x + (w / 2)
        )

        center_y = (
            y + (h / 2)
        )

        score = _candidate_score(
            area_ratio=area_ratio,
            center_x=center_x,
            center_y=center_y,
            image_width=width,
            image_height=height,
        )

        if score < MIN_CANDIDATE_SCORE:
            continue

        candidates.append(
            {
                "area": area,
                "area_ratio": area_ratio,
                "x": int(x),
                "y": int(y),
                "width": int(w),
                "height": int(h),
                "center_x": center_x,
                "center_y": center_y,
                "score": score,
            }
        )

    # --------------------------------------------------------
    # No candidate
    # --------------------------------------------------------

    if not candidates:
        return _not_estimated(
            "No reliable candidate region was identified "
            "using the current image-based estimation method."
        )

    # --------------------------------------------------------
    # Select best candidate
    # --------------------------------------------------------

    candidate = max(
        candidates,
        key=lambda item: item["score"],
    )

    x = candidate["x"]
    y = candidate["y"]

    w = candidate["width"]
    h = candidate["height"]

    area = candidate["area"]

    area_ratio = candidate[
        "area_ratio"
    ]

    score = candidate[
        "score"
    ]

    center_x = candidate[
        "center_x"
    ]

    center_y = candidate[
        "center_y"
    ]

    # --------------------------------------------------------
    # Final candidate safety check
    # --------------------------------------------------------

    if (
        area_ratio >= 0.35
        or w >= width * 0.95
        or h >= height * 0.95
    ):
        return _not_estimated(
            "Candidate region covered too much of the image "
            "to provide a reliable image-based estimate."
        )

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    return {
        "status": "ESTIMATED",
        "method": (
            "image-based candidate region estimation"
        ),
        "candidate_score": round(
            score,
            3,
        ),
        "candidate_area_ratio": round(
            area_ratio,
            4,
        ),
        "width_pixels": int(w),
        "height_pixels": int(h),
        "area_pixels": round(
            area,
            2,
        ),
        "center": {
            "x": round(
                center_x,
                2,
            ),
            "y": round(
                center_y,
                2,
            ),
        },
        "bounding_box": {
            "x": int(x),
            "y": int(y),
            "width": int(w),
            "height": int(h),
        },
        "calibration_available": False,
        "physical_size": None,
        "note": (
            "This is an image-based candidate region estimate, "
            "not a clinical lesion boundary. Physical size in "
            "millimeters or centimeters cannot be determined "
            "without a valid image calibration reference."
        ),
    }


# ============================================================
# NO-ESTIMATE RESULT
# ============================================================

def _not_estimated(
    reason: str,
) -> dict[str, Any]:

    return {
        "status": "NOT_ESTIMATED",
        "method": (
            "image-based candidate region estimation"
        ),
        "candidate_score": None,
        "candidate_area_ratio": None,
        "width_pixels": None,
        "height_pixels": None,
        "area_pixels": None,
        "center": None,
        "bounding_box": None,
        "calibration_available": False,
        "physical_size": None,
        "note": reason,
    }


# ============================================================
# CLI TEST SUPPORT
# ============================================================

if __name__ == "__main__":

    import argparse
    import json

    parser = argparse.ArgumentParser(
        description=(
            "CancerLense lesion candidate estimator"
        )
    )

    parser.add_argument(
        "image",
        help="Path to image",
    )

    args = parser.parse_args()

    image = cv2.imread(
        args.image
    )

    if image is None:
        raise SystemExit(
            f"Unable to read image: {args.image}"
        )

    result = estimate_lesion_measurement(
        image
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )