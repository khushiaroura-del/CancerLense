import cv2
import torch
import numpy as np
from pathlib import Path

from app.backend.ml.mobilenet_model import create_model
from app.backend.ml.image_processor import process_image


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = PROJECT_ROOT / "models" / "best_model.pth"
OUTPUT_DIR = PROJECT_ROOT / "results" / "gradcam"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CLASS_NAMES = {
    0: "cancer",
    1: "non-cancer"
}


def load_model():
    model = create_model()

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=torch.device("cpu"),
        weights_only=False
    )

    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        model.load_state_dict(checkpoint)

    model.eval()

    return model


def run_gradcam(image_path):
    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    # -----------------------------
    # 1. Process image
    # -----------------------------
    processed = process_image(str(image_path))

    quality = processed["quality"]

    print("\nImage Quality")
    print(f"Width     : {quality['width']}")
    print(f"Height    : {quality['height']}")
    print(f"Brightness: {quality['brightness']}")
    print(f"Sharpness : {quality['sharpness']}")
    print(f"Status    : {quality['quality_status']}")

    if quality["quality_status"] != "ACCEPTABLE":
        raise ValueError(
            f"Image quality rejected: {quality['quality_status']}"
        )

    # -----------------------------
    # 2. Prepare tensor
    # -----------------------------
    image = processed["processed_image"]

    image_tensor = torch.tensor(
        image,
        dtype=torch.float32
    )

    # HWC -> CHW
    image_tensor = image_tensor.permute(2, 0, 1)

    # ImageNet normalization
    mean = torch.tensor(
        [0.485, 0.456, 0.406],
        dtype=torch.float32
    ).view(3, 1, 1)

    std = torch.tensor(
        [0.229, 0.224, 0.225],
        dtype=torch.float32
    ).view(3, 1, 1)

    image_tensor = (image_tensor - mean) / std

    image_tensor = image_tensor.unsqueeze(0)
    image_tensor.requires_grad_(True)

    # -----------------------------
    # 3. Load model
    # -----------------------------
    model = load_model()

    # MobileNetV3 Small final feature layer
    target_layer = model.model.features[-1]

    activations = None
    gradients = None

    # -----------------------------
    # 4. Hooks
    # -----------------------------
    def forward_hook(module, input, output):
        nonlocal activations
        activations = output

    def backward_hook(module, grad_input, grad_output):
        nonlocal gradients
        gradients = grad_output[0]

    forward_handle = target_layer.register_forward_hook(
        forward_hook
    )

    backward_handle = target_layer.register_full_backward_hook(
        backward_hook
    )

    # -----------------------------
    # 5. Forward pass
    # -----------------------------
    output = model(image_tensor)

    probabilities = torch.softmax(output, dim=1)

    predicted_class = torch.argmax(
        probabilities,
        dim=1
    ).item()

    confidence = probabilities[
        0,
        predicted_class
    ].item()

    prediction_name = CLASS_NAMES[predicted_class]

    print("\nPrediction")
    print(f"Class      : {prediction_name}")
    print(f"Confidence : {confidence * 100:.2f}%")

    # -----------------------------
    # 6. Backward pass
    # -----------------------------
    model.zero_grad()

    target_score = output[
        0,
        predicted_class
    ]

    target_score.backward()

    # Remove hooks
    forward_handle.remove()
    backward_handle.remove()

    if activations is None:
        raise RuntimeError("Grad-CAM activations were not captured.")

    if gradients is None:
        raise RuntimeError("Grad-CAM gradients were not captured.")

    # -----------------------------
    # 7. Calculate Grad-CAM
    # -----------------------------
    activations = activations.detach()
    gradients = gradients.detach()

    # Global average pooling of gradients
    weights = gradients.mean(
        dim=(2, 3),
        keepdim=True
    )

    cam = (weights * activations).sum(
        dim=1
    )

    cam = torch.relu(cam)

    cam = cam.squeeze().cpu().numpy()

    # -----------------------------
    # 8. Normalize heatmap
    # -----------------------------
    cam = cam - cam.min()

    if cam.max() > 0:
        cam = cam / cam.max()

    cam = np.uint8(
        cam * 255
    )

    # -----------------------------
    # 9. Resize heatmap
    # -----------------------------
    original_image = processed["original_image"]

    original_height, original_width = (
        original_image.shape[:2]
    )

    cam = cv2.resize(
        cam,
        (original_width, original_height)
    )

    # -----------------------------
    # 10. Create heatmap
    # -----------------------------
    heatmap = cv2.applyColorMap(
        cam,
        cv2.COLORMAP_JET
    )

    # OpenCV original image is BGR
    if len(original_image.shape) == 3:
        base_image = original_image.copy()
    else:
        base_image = cv2.cvtColor(
            original_image,
            cv2.COLOR_GRAY2BGR
        )

    # -----------------------------
    # 11. Overlay
    # -----------------------------
    visualization = cv2.addWeighted(
        base_image,
        0.60,
        heatmap,
        0.40,
        0
    )

    # -----------------------------
    # 12. Add label
    # -----------------------------
    label = (
        f"Prediction: {prediction_name} | "
        f"Confidence: {confidence * 100:.2f}%"
    )

    cv2.rectangle(
        visualization,
        (0, 0),
        (original_width, 45),
        (0, 0, 0),
        -1
    )

    cv2.putText(
        visualization,
        label,
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

    # -----------------------------
    # 13. Save Grad-CAM
    # -----------------------------
    output_path = (
        OUTPUT_DIR /
        f"{image_path.stem}_gradcam.jpg"
    )

    success = cv2.imwrite(
        str(output_path),
        visualization
    )

    if not success:
        raise RuntimeError(
            "Failed to save Grad-CAM image."
        )

    print(
        f"\nGrad-CAM saved to: {output_path}"
    )

    # IMPORTANT:
    # Return path so FastAPI can send it
    return str(output_path)


if __name__ == "__main__":

    test_image = (
        PROJECT_ROOT /
        "datasets" /
        "test" /
        "cancer" /
        "1200px-ZungenCa2a.jpg"
    )

    result = run_gradcam(
        str(test_image)
    )

    print(
        f"\nReturned path: {result}"
    )