from pathlib import Path

import torch
from torch.utils.data import DataLoader
from torchvision import datasets, transforms


# ============================================================
# CancerLense Dataset Configuration
# ============================================================

IMAGE_SIZE = 224
BATCH_SIZE = 8

# Project root:
# C:\Users\DELL\Desktop\CancerLense
PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATASET_ROOT = PROJECT_ROOT / "datasets"


# ============================================================
# Image Transformations
# ============================================================

train_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),

    # Data augmentation for training
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(10),

    transforms.ColorJitter(
        brightness=0.15,
        contrast=0.15,
        saturation=0.10
    ),

    transforms.ToTensor(),

    # ImageNet normalization
    # Required because MobileNetV3 uses ImageNet pretrained weights
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])


# Validation and test images should NOT receive random augmentation.
eval_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])


# ============================================================
# Dataset Loader Function
# ============================================================

def create_dataloaders():

    train_path = DATASET_ROOT / "train"
    val_path = DATASET_ROOT / "val"
    test_path = DATASET_ROOT / "test"

    # Check dataset paths before loading
    if not train_path.exists():
        raise FileNotFoundError(
            f"Training dataset not found:\n{train_path}"
        )

    if not val_path.exists():
        raise FileNotFoundError(
            f"Validation dataset not found:\n{val_path}"
        )

    if not test_path.exists():
        raise FileNotFoundError(
            f"Test dataset not found:\n{test_path}"
        )

    # --------------------------------------------------------
    # Training Dataset
    # --------------------------------------------------------

    train_dataset = datasets.ImageFolder(
        train_path,
        transform=train_transform
    )

    # --------------------------------------------------------
    # Validation Dataset
    # --------------------------------------------------------

    val_dataset = datasets.ImageFolder(
        val_path,
        transform=eval_transform
    )

    # --------------------------------------------------------
    # Test Dataset
    # --------------------------------------------------------

    test_dataset = datasets.ImageFolder(
        test_path,
        transform=eval_transform
    )

    # --------------------------------------------------------
    # DataLoaders
    # --------------------------------------------------------

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0
    )

    return (
        train_loader,
        val_loader,
        test_loader,
        train_dataset,
        val_dataset,
        test_dataset,
    )


# ============================================================
# Dataset Test
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("CancerLense Dataset Loader")
    print("=" * 60)

    print()
    print("Project root:")
    print(PROJECT_ROOT)

    print()
    print("Dataset root:")
    print(DATASET_ROOT)

    print()
    print("Loading datasets...")

    (
        train_loader,
        val_loader,
        test_loader,
        train_dataset,
        val_dataset,
        test_dataset,
    ) = create_dataloaders()

    print()
    print("Datasets loaded successfully.")

    # --------------------------------------------------------
    # Class Mapping
    # --------------------------------------------------------

    print()
    print("Class mapping:")
    print(train_dataset.class_to_idx)

    # --------------------------------------------------------
    # Dataset Sizes
    # --------------------------------------------------------

    print()
    print("Train images:", len(train_dataset))
    print("Validation images:", len(val_dataset))
    print("Test images:", len(test_dataset))

    # --------------------------------------------------------
    # Number of batches
    # --------------------------------------------------------

    print()
    print("Train batches:", len(train_loader))
    print("Validation batches:", len(val_loader))
    print("Test batches:", len(test_loader))

    # --------------------------------------------------------
    # Load one training batch
    # --------------------------------------------------------

    images, labels = next(iter(train_loader))

    print()
    print("First training batch:")
    print("Image tensor shape:", images.shape)
    print("Label tensor shape:", labels.shape)

    print()
    print("Image tensor dtype:", images.dtype)
    print("Label tensor dtype:", labels.dtype)

    # --------------------------------------------------------
    # Show labels in first batch
    # --------------------------------------------------------

    print()
    print("Labels in first batch:")
    print(labels.tolist())

    # --------------------------------------------------------
    # Final status
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("CancerLense dataset loader working successfully.")
    print("=" * 60)