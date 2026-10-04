from pathlib import Path

import cv2
import numpy as np


def estimate_lesion_size(image_path: str):
    """
    Research-only image-based lesion size estimation.

    IMPORTANT:
    This function estimates dimensions only in image pixels.
    It does NOT estimate millimeters or centimeters unless
    a valid calibration/reference scale is provided.
    """

    image_path = Path(image_path)

    image = cv2.imread(str(image_path))

    if image is None:
        return {
            "status": "UNAVAILABLE",
            "message": "Unable to read image for lesion size estimation."
        }

    height, width = image.shape[:2]

    if width == 0 or height == 0:
        return {
            "status": "UNAVAILABLE",
            "message": "Invalid image dimensions."
        }

    # Convert image to HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Mild smoothing to reduce noise
    blurred = cv2.GaussianBlur(hsv, (7, 7), 0)

    # Extract saturation and brightness
    saturation = blurred[:, :, 1]
    brightness = blurred[:, :, 2]

    # Generate a conservative candidate mask.
    #
    # This is NOT a clinical lesion segmentation model.
    # It simply searches for visually distinct regions.
    sat_threshold = np.percentile(saturation, 75)
    bright_threshold = np.percentile(brightness, 25)

    mask = (
        (saturation >= sat_threshold) &
        (brightness <= bright_threshold)
    ).astype(np.uint8) * 255

    # Clean small noise
    kernel = np.ones((5, 5), np.uint8)

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel
    )

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return {
            "status": "NOT_DETECTED",
            "message": "No suitable image region was found for size estimation.",
            "calibration_available": False
        }

    # Ignore extremely tiny regions
    min_area = max(50, int(width * height * 0.0001))

    valid_contours = [
        contour
        for contour in contours
        if cv2.contourArea(contour) >= min_area
    ]

    if not valid_contours:
        return {
            "status": "NOT_DETECTED",
            "message": "No sufficiently large candidate region was found.",
            "calibration_available": False
        }

    # Select largest candidate region
    largest_contour = max(
        valid_contours,
        key=cv2.contourArea
    )

    x, y, box_width, box_height = cv2.boundingRect(
        largest_contour
    )

    area_pixels = float(cv2.contourArea(largest_contour))

    center_x = x + box_width / 2
    center_y = y + box_height / 2

    return {
        "status": "ESTIMATED",
        "method": "image-based candidate region estimation",
        "width_pixels": int(box_width),
        "height_pixels": int(box_height),
        "area_pixels": round(area_pixels, 2),
        "center": {
            "x": round(center_x, 2),
            "y": round(center_y, 2)
        },
        "bounding_box": {
            "x": int(x),
            "y": int(y),
            "width": int(box_width),
            "height": int(box_height)
        },
        "calibration_available": False,
        "physical_size": None,
        "note": (
            "Physical size in millimeters or centimeters cannot be "
            "determined without a valid image calibration reference."
        )
    }