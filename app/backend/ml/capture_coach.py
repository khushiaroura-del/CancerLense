"""
CancerLense Smart Capture Coach

Evaluates whether an oral image is reasonably suitable
for AI-assisted research screening.

IMPORTANT:
This module provides image-capture guidance only.
It does not diagnose disease and does not modify
the MobileNetV3 prediction.
"""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np


# ============================================================
# THRESHOLDS
# ============================================================

MIN_WIDTH = 224
MIN_HEIGHT = 224

MIN_BRIGHTNESS = 35.0
MAX_BRIGHTNESS = 235.0

MIN_SHARPNESS = 20.0

# Additional guidance thresholds
VERY_DARK_BRIGHTNESS = 55.0
VERY_BRIGHT_BRIGHTNESS = 215.0

GOOD_SHARPNESS = 80.0

MIN_ASPECT_RATIO = 0.55
MAX_ASPECT_RATIO = 2.20


# ============================================================
# IMAGE METRICS
# ============================================================


def _calculate_metrics(image: np.ndarray) -> dict[str, float | int]:
    """
    Calculate image-derived metrics used by the capture coach.

    These are technical image-quality measurements only.
    """

    if image is None or image.size == 0:
        raise ValueError("Invalid image supplied to capture coach.")

    if len(image.shape) == 2:
        gray = image
    else:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    height, width = gray.shape

    brightness = float(np.mean(gray))

    sharpness = float(
        cv2.Laplacian(gray, cv2.CV_64F).var()
    )

    aspect_ratio = float(width / height) if height else 0.0

    return {
        "width": int(width),
        "height": int(height),
        "brightness": round(brightness, 2),
        "sharpness": round(sharpness, 2),
        "aspect_ratio": round(aspect_ratio, 3),
    }


# ============================================================
# CAPTURE COACH
# ============================================================


def evaluate_capture(image: np.ndarray) -> dict[str, Any]:
    """
    Evaluate whether an image is suitable for the next
    AI-assisted research screening step.

    Returns:
        readiness
        score
        status
        checks
        guidance
        metrics

    IMPORTANT:
    This result is capture guidance, not a medical assessment.
    """

    metrics = _calculate_metrics(image)

    width = metrics["width"]
    height = metrics["height"]
    brightness = metrics["brightness"]
    sharpness = metrics["sharpness"]
    aspect_ratio = metrics["aspect_ratio"]

    checks: dict[str, dict[str, Any]] = {}

    guidance: list[str] = []

    score = 100

    # --------------------------------------------------------
    # Resolution
    # --------------------------------------------------------

    resolution_ok = (
        width >= MIN_WIDTH
        and height >= MIN_HEIGHT
    )

    checks["resolution"] = {
        "status": "PASS" if resolution_ok else "FAIL",
        "message": (
            "Image resolution is sufficient."
            if resolution_ok
            else "Image resolution is too low."
        ),
    }

    if not resolution_ok:
        score -= 30
        guidance.append(
            "Move closer or use a higher-resolution image."
        )

    # --------------------------------------------------------
    # Brightness
    # --------------------------------------------------------

    if brightness < MIN_BRIGHTNESS:
        brightness_status = "FAIL"
        brightness_message = "Image is too dark."
        score -= 30

        guidance.append(
            "Increase the lighting and avoid capturing the image in a dark area."
        )

    elif brightness > MAX_BRIGHTNESS:
        brightness_status = "FAIL"
        brightness_message = "Image is too bright."
        score -= 25

        guidance.append(
            "Reduce direct light or glare and retake the image."
        )

    elif (
        brightness < VERY_DARK_BRIGHTNESS
        or brightness > VERY_BRIGHT_BRIGHTNESS
    ):
        brightness_status = "WARN"
        brightness_message = "Lighting may affect image visibility."
        score -= 10

        guidance.append(
            "Use even lighting and avoid strong shadows or reflections."
        )

    else:
        brightness_status = "PASS"
        brightness_message = "Lighting is within a useful range."

    checks["brightness"] = {
        "status": brightness_status,
        "message": brightness_message,
    }

    # --------------------------------------------------------
    # Sharpness
    # --------------------------------------------------------

    if sharpness < MIN_SHARPNESS:
        sharpness_status = "FAIL"
        sharpness_message = "Image appears blurry."
        score -= 30

        guidance.append(
            "Hold the camera steady and retake the image in focus."
        )

    elif sharpness < GOOD_SHARPNESS:
        sharpness_status = "WARN"
        sharpness_message = "Image sharpness could be improved."
        score -= 10

        guidance.append(
            "Keep the camera steady and make sure the area of interest is in focus."
        )

    else:
        sharpness_status = "PASS"
        sharpness_message = "Image sharpness is good."

    checks["sharpness"] = {
        "status": sharpness_status,
        "message": sharpness_message,
    }

    # --------------------------------------------------------
    # Framing
    # --------------------------------------------------------

    framing_ok = (
        MIN_ASPECT_RATIO
        <= aspect_ratio
        <= MAX_ASPECT_RATIO
    )

    if framing_ok:
        framing_status = "PASS"
        framing_message = "Image framing is reasonable."
    else:
        framing_status = "WARN"
        framing_message = "Image framing may be unusual."
        score -= 10

        guidance.append(
            "Center the area of interest and avoid excessive empty space."
        )

    checks["framing"] = {
        "status": framing_status,
        "message": framing_message,
    }

    # --------------------------------------------------------
    # Final score
    # --------------------------------------------------------

    score = max(0, min(100, int(score)))

    failed_checks = [
        name
        for name, check in checks.items()
        if check["status"] == "FAIL"
    ]

    warning_checks = [
        name
        for name, check in checks.items()
        if check["status"] == "WARN"
    ]

    # --------------------------------------------------------
    # Readiness classification
    # --------------------------------------------------------

    if failed_checks:
        readiness = "RETAKE_RECOMMENDED"
        status = "NOT_READY"

        headline = "Image needs improvement before screening."

    elif warning_checks:
        readiness = "ACCEPTABLE_WITH_CAUTION"
        status = "READY_WITH_CAUTION"

        headline = "Image may be usable, but capture quality could improve."

    else:
        readiness = "READY"
        status = "READY"

        headline = "Image appears suitable for research screening."

    # --------------------------------------------------------
    # Positive guidance
    # --------------------------------------------------------

    if not guidance:
        guidance.append(
            "Keep the area of interest centered, well lit, and in focus."
        )

    return {
        "status": status,
        "readiness": readiness,
        "score": score,
        "headline": headline,
        "checks": checks,
        "guidance": guidance,
        "metrics": metrics,
        "failed_checks": failed_checks,
        "warning_checks": warning_checks,
        "note": (
            "Capture Coach evaluates technical image quality only. "
            "It does not diagnose disease, identify a lesion, "
            "or change the AI screening prediction."
        ),
    }


# ============================================================
# SIMPLE HELPER
# ============================================================


def capture_is_ready(image: np.ndarray) -> bool:
    """
    Return True only when the image passes the main
    capture-quality checks.
    """

    result = evaluate_capture(image)

    return result["status"] == "READY"


# ============================================================
# CLI TEST SUPPORT
# ============================================================


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="CancerLense Smart Capture Coach"
    )

    parser.add_argument(
        "image",
        help="Path to image",
    )

    args = parser.parse_args()

    image = cv2.imread(args.image)

    if image is None:
        raise SystemExit(
            f"Unable to read image: {args.image}"
        )

    result = evaluate_capture(image)

    print(
        json.dumps(
            result,
            indent=2,
        )
    )