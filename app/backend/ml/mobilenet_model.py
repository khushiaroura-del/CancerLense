import torch
import torch.nn as nn
from torchvision.models import (
    mobilenet_v3_small,
    MobileNet_V3_Small_Weights
)


# ============================================================
# CancerLense MobileNetV3 Model
# ============================================================

NUM_CLASSES = 2


class CancerLenseModel(nn.Module):

    def __init__(self, num_classes=NUM_CLASSES):

        super().__init__()

        # Load ImageNet-pretrained MobileNetV3 Small
        weights = MobileNet_V3_Small_Weights.DEFAULT

        self.model = mobilenet_v3_small(
            weights=weights
        )

        # ----------------------------------------------------
        # Replace the original classifier
        # ----------------------------------------------------

        input_features = self.model.classifier[-1].in_features

        self.model.classifier[-1] = nn.Linear(
            input_features,
            num_classes
        )

    def forward(self, x):

        return self.model(x)


# ============================================================
# Model Creation Function
# ============================================================

def create_model():

    model = CancerLenseModel(
        num_classes=NUM_CLASSES
    )

    return model


# ============================================================
# Model Test
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("CancerLense MobileNetV3")
    print("=" * 60)

    print()
    print("Creating model...")

    model = create_model()

    print()
    print("Model created successfully.")

    print("Number of classes:", NUM_CLASSES)

    print()
    print("Testing forward pass...")

    # Dummy RGB batch:
    # Batch = 2
    # Channels = 3
    # Height = 224
    # Width = 224

    test_input = torch.randn(
        2,
        3,
        224,
        224
    )

    with torch.no_grad():

        output = model(test_input)

    print()
    print("Input shape:", test_input.shape)
    print("Output shape:", output.shape)

    print()
    print("Expected output shape:")
    print("(batch_size, 2)")

    print()
    print("=" * 60)
    print("CancerLense MobileNetV3 test successful.")
    print("=" * 60)