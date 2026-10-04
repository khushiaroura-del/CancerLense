from pathlib import Path
import json
import random

import numpy as np
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import ReduceLROnPlateau

from mobilenet_model import create_model
from dataset import create_dataloaders


# ============================================================
# CONFIGURATION
# ============================================================

SEED = 42
NUM_EPOCHS = 30
LEARNING_RATE = 1e-4
WEIGHT_DECAY = 1e-4
PATIENCE = 7

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_DIR = PROJECT_ROOT / "models"
RESULTS_DIR = PROJECT_ROOT / "results"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

BEST_MODEL_PATH = MODEL_DIR / "best_model.pth"
HISTORY_PATH = RESULTS_DIR / "training_history.json"


# ============================================================
# REPRODUCIBILITY
# ============================================================

def set_seed(seed=SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(predictions, targets):
    """
    Class mapping:
        0 = cancer
        1 = non-cancer

    Cancer is treated as the positive class.
    """

    predictions = torch.tensor(predictions)
    targets = torch.tensor(targets)

    tp = ((predictions == 0) & (targets == 0)).sum().item()
    fn = ((predictions == 1) & (targets == 0)).sum().item()
    tn = ((predictions == 1) & (targets == 1)).sum().item()
    fp = ((predictions == 0) & (targets == 1)).sum().item()

    total = tp + tn + fp + fn

    accuracy = (tp + tn) / total if total > 0 else 0.0

    sensitivity = (
        tp / (tp + fn)
        if (tp + fn) > 0
        else 0.0
    )

    specificity = (
        tn / (tn + fp)
        if (tn + fp) > 0
        else 0.0
    )

    return {
        "accuracy": accuracy,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


# ============================================================
# TRAIN ONE EPOCH
# ============================================================

def train_one_epoch(model, loader, criterion, optimizer, device):

    model.train()

    running_loss = 0.0
    all_predictions = []
    all_targets = []

    for images, labels in loader:

        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(outputs, labels)

        loss.backward()

        optimizer.step()

        running_loss += loss.item() * images.size(0)

        predictions = torch.argmax(outputs, dim=1)

        all_predictions.extend(predictions.cpu().tolist())
        all_targets.extend(labels.cpu().tolist())

    epoch_loss = running_loss / len(loader.dataset)

    metrics = calculate_metrics(
        all_predictions,
        all_targets
    )

    return epoch_loss, metrics


# ============================================================
# VALIDATION
# ============================================================

def validate(model, loader, criterion, device):

    model.eval()

    running_loss = 0.0

    all_predictions = []
    all_targets = []

    with torch.no_grad():

        for images, labels in loader:

            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)

            loss = criterion(outputs, labels)

            running_loss += loss.item() * images.size(0)

            predictions = torch.argmax(outputs, dim=1)

            all_predictions.extend(predictions.cpu().tolist())
            all_targets.extend(labels.cpu().tolist())

    epoch_loss = running_loss / len(loader.dataset)

    metrics = calculate_metrics(
        all_predictions,
        all_targets
    )

    return epoch_loss, metrics


# ============================================================
# MAIN TRAINING
# ============================================================

def main():

    set_seed()

    print("=" * 70)
    print("CancerLense - Model Training")
    print("=" * 70)
    print()

    # --------------------------------------------------------
    # DEVICE
    # --------------------------------------------------------

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("Device:", device)
    print()

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    print("Loading dataset...")

    (
        train_loader,
        val_loader,
        test_loader,
        train_dataset,
        val_dataset,
        test_dataset
    ) = create_dataloaders()

    print()
    print("Dataset loaded.")
    print()

    print("Class mapping:")
    print(train_dataset.class_to_idx)
    print()

    print("Train images:", len(train_dataset))
    print("Validation images:", len(val_dataset))
    print("Test images:", len(test_dataset))
    print()

    # --------------------------------------------------------
    # CLASS COUNTS
    # --------------------------------------------------------

    class_counts = [0, 0]

    for label in train_dataset.targets:
        class_counts[label] += 1

    print("Training class distribution:")
    print("Cancer:", class_counts[0])
    print("Non-cancer:", class_counts[1])
    print()

    # --------------------------------------------------------
    # CLASS WEIGHTS
    # --------------------------------------------------------

    total_samples = sum(class_counts)

    class_weights = torch.tensor(
        [
            total_samples / (2 * class_counts[0]),
            total_samples / (2 * class_counts[1])
        ],
        dtype=torch.float32
    )

    class_weights = class_weights.to(device)

    print("Class weights:")
    print(class_weights)
    print()

    # --------------------------------------------------------
    # CREATE MODEL
    # --------------------------------------------------------

    print("Creating MobileNetV3 model...")

    model = create_model()

    model = model.to(device)

    print("Model ready.")
    print()

    # --------------------------------------------------------
    # LOSS FUNCTION
    # --------------------------------------------------------

    criterion = nn.CrossEntropyLoss(
        weight=class_weights
    )

    # --------------------------------------------------------
    # OPTIMIZER
    # --------------------------------------------------------

    optimizer = AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY
    )

    # --------------------------------------------------------
    # LEARNING RATE SCHEDULER
    # --------------------------------------------------------

    scheduler = ReduceLROnPlateau(
        optimizer,
        mode="min",
        factor=0.5,
        patience=2
    )

    # --------------------------------------------------------
    # TRAINING HISTORY
    # --------------------------------------------------------

    history = {
        "epoch": [],
        "train_loss": [],
        "val_loss": [],
        "train_accuracy": [],
        "val_accuracy": [],
        "train_sensitivity": [],
        "val_sensitivity": [],
        "train_specificity": [],
        "val_specificity": [],
        "learning_rate": []
    }

    best_val_loss = float("inf")
    epochs_without_improvement = 0

    # --------------------------------------------------------
    # TRAINING LOOP
    # --------------------------------------------------------

    print("=" * 70)
    print("Starting training...")
    print("=" * 70)
    print()

    for epoch in range(1, NUM_EPOCHS + 1):

        current_lr = optimizer.param_groups[0]["lr"]

        print(
            f"Epoch {epoch}/{NUM_EPOCHS}"
        )
        print("-" * 70)

        # TRAIN
        train_loss, train_metrics = train_one_epoch(
            model,
            train_loader,
            criterion,
            optimizer,
            device
        )

        # VALIDATION
        val_loss, val_metrics = validate(
            model,
            val_loader,
            criterion,
            device
        )

        # Scheduler
        scheduler.step(val_loss)

        # Save history
        history["epoch"].append(epoch)

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)

        history["train_accuracy"].append(
            train_metrics["accuracy"]
        )

        history["val_accuracy"].append(
            val_metrics["accuracy"]
        )

        history["train_sensitivity"].append(
            train_metrics["sensitivity"]
        )

        history["val_sensitivity"].append(
            val_metrics["sensitivity"]
        )

        history["train_specificity"].append(
            train_metrics["specificity"]
        )

        history["val_specificity"].append(
            val_metrics["specificity"]
        )

        history["learning_rate"].append(
            current_lr
        )

        # ----------------------------------------------------
        # PRINT METRICS
        # ----------------------------------------------------

        print(
            f"Train Loss       : {train_loss:.4f}"
        )

        print(
            f"Validation Loss   : {val_loss:.4f}"
        )

        print(
            f"Train Accuracy    : {train_metrics['accuracy']:.4f}"
        )

        print(
            f"Validation Accuracy: {val_metrics['accuracy']:.4f}"
        )

        print(
            f"Train Sensitivity : {train_metrics['sensitivity']:.4f}"
        )

        print(
            f"Val Sensitivity   : {val_metrics['sensitivity']:.4f}"
        )

        print(
            f"Train Specificity : {train_metrics['specificity']:.4f}"
        )

        print(
            f"Val Specificity   : {val_metrics['specificity']:.4f}"
        )

        print(
            f"Learning Rate     : {current_lr:.7f}"
        )

        print()

        # ----------------------------------------------------
        # SAVE BEST MODEL
        # ----------------------------------------------------

        if val_loss < best_val_loss:

            best_val_loss = val_loss
            epochs_without_improvement = 0

            checkpoint = {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "best_val_loss": best_val_loss,
                "class_to_idx": train_dataset.class_to_idx,
                "image_size": 224
            }

            torch.save(
                checkpoint,
                BEST_MODEL_PATH
            )

            print(
                f"✓ Best model saved -> {BEST_MODEL_PATH}"
            )

        else:

            epochs_without_improvement += 1

            print(
                f"No validation improvement "
                f"({epochs_without_improvement}/{PATIENCE})"
            )

        print()

        # ----------------------------------------------------
        # EARLY STOPPING
        # ----------------------------------------------------

        if epochs_without_improvement >= PATIENCE:

            print("=" * 70)
            print("Early stopping triggered.")
            print("=" * 70)
            print()

            break

    # --------------------------------------------------------
    # SAVE TRAINING HISTORY
    # --------------------------------------------------------

    with open(
        HISTORY_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            history,
            file,
            indent=4
        )

    # --------------------------------------------------------
    # FINAL MESSAGE
    # --------------------------------------------------------

    print("=" * 70)
    print("TRAINING COMPLETE")
    print("=" * 70)
    print()

    print("Best validation loss:")
    print(f"{best_val_loss:.4f}")
    print()

    print("Best model:")
    print(BEST_MODEL_PATH)
    print()

    print("Training history:")
    print(HISTORY_PATH)
    print()

    print("IMPORTANT:")
    print("The test set was NOT used during training.")
    print("Test evaluation will be performed separately.")
    print()

    print("=" * 70)


if __name__ == "__main__":
    main()