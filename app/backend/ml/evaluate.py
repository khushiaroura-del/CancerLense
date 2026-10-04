from pathlib import Path
import json

import torch

from app.backend.ml.mobilenet_model import create_model
from app.backend.ml.dataset import create_dataloaders


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

MODEL_PATH = PROJECT_ROOT / "models" / "best_model.pth"
RESULTS_DIR = PROJECT_ROOT / "results"

RESULTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)

TEST_RESULTS_PATH = (
    RESULTS_DIR / "test_results.json"
)


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(
    predictions,
    targets
):

    tp = 0
    tn = 0
    fp = 0
    fn = 0

    for prediction, target in zip(
        predictions,
        targets
    ):

        # Cancer = 0
        # Non-cancer = 1

        if target == 0 and prediction == 0:

            tp += 1

        elif target == 0 and prediction == 1:

            fn += 1

        elif target == 1 and prediction == 1:

            tn += 1

        elif target == 1 and prediction == 0:

            fp += 1


    total = (
        tp +
        tn +
        fp +
        fn
    )


    # --------------------------------------------------------
    # Accuracy
    # --------------------------------------------------------

    accuracy = (
        (tp + tn) / total
        if total > 0
        else 0.0
    )


    # --------------------------------------------------------
    # Sensitivity / Recall
    # --------------------------------------------------------

    sensitivity = (
        tp / (tp + fn)
        if (tp + fn) > 0
        else 0.0
    )


    # --------------------------------------------------------
    # Specificity
    # --------------------------------------------------------

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

        "fn": fn

    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)

    print(
        "CancerLens - Final Test Evaluation"
    )

    print("=" * 70)

    print()


    # --------------------------------------------------------
    # DEVICE
    # --------------------------------------------------------

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(
        "Device:",
        device
    )

    print()


    # --------------------------------------------------------
    # CHECK MODEL
    # --------------------------------------------------------

    if not MODEL_PATH.exists():

        raise FileNotFoundError(
            f"Best model not found:\n"
            f"{MODEL_PATH}"
        )


    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    print(
        "Loading dataset..."
    )

    (
        train_loader,
        val_loader,
        test_loader,
        train_dataset,
        val_dataset,
        test_dataset
    ) = create_dataloaders()


    print(
        "Dataset loaded."
    )

    print()


    print(
        "Class mapping:"
    )

    print(
        test_dataset.class_to_idx
    )

    print()


    print(
        "Test images:",
        len(test_dataset)
    )

    print()


    # --------------------------------------------------------
    # LOAD MODEL
    # --------------------------------------------------------

    print(
        "Loading best trained model..."
    )

    model = create_model()


    checkpoint = torch.load(
        MODEL_PATH,
        map_location=device,
        weights_only=False
    )


    # --------------------------------------------------------
    # Load checkpoint
    # --------------------------------------------------------

    if (
        isinstance(checkpoint, dict)
        and "model_state_dict" in checkpoint
    ):

        model.load_state_dict(
            checkpoint["model_state_dict"]
        )

    else:

        model.load_state_dict(
            checkpoint
        )


    model = model.to(device)

    model.eval()


    print(
        "Best model loaded successfully."
    )

    print()


    # --------------------------------------------------------
    # Checkpoint information
    # --------------------------------------------------------

    if (
        isinstance(checkpoint, dict)
        and "best_val_loss" in checkpoint
    ):

        print(
            "Best validation loss:"
        )

        print(
            f"{checkpoint['best_val_loss']:.4f}"
        )


    if (
        isinstance(checkpoint, dict)
        and "epoch" in checkpoint
    ):

        print(
            "Saved from epoch:"
        )

        print(
            checkpoint["epoch"]
        )


    print()


    # --------------------------------------------------------
    # TEST EVALUATION
    # --------------------------------------------------------

    print("=" * 70)

    print(
        "Evaluating untouched test set..."
    )

    print("=" * 70)

    print()


    all_predictions = []

    all_targets = []

    image_results = []


    with torch.no_grad():

        image_index = 0


        for images, labels in test_loader:

            images = images.to(device)

            labels = labels.to(device)


            # ------------------------------------------------
            # Model output
            # ------------------------------------------------

            outputs = model(
                images
            )


            probabilities = torch.softmax(
                outputs,
                dim=1
            )


            predictions = torch.argmax(
                probabilities,
                dim=1
            )


            # ------------------------------------------------
            # Process every image
            # ------------------------------------------------

            for i in range(
                len(images)
            ):

                target = labels[
                    i
                ].item()


                prediction = predictions[
                    i
                ].item()


                # Cancer = class 0
                cancer_probability = (
                    probabilities[
                        i, 0
                    ].item()
                )


                # Non-cancer = class 1
                non_cancer_probability = (
                    probabilities[
                        i, 1
                    ].item()
                )


                # ------------------------------------------------
                # Get original filename
                # ------------------------------------------------

                filename, actual_class = (
                    test_dataset.samples[
                        image_index
                    ]
                )


                # ------------------------------------------------
                # Convert class IDs to names
                # ------------------------------------------------

                prediction_class = (
                    "cancer"
                    if prediction == 0
                    else "non-cancer"
                )


                actual_class_name = (
                    "cancer"
                    if target == 0
                    else "non-cancer"
                )


                # ------------------------------------------------
                # Model confidence
                # ------------------------------------------------

                confidence = max(
                    cancer_probability,
                    non_cancer_probability
                )


                # ------------------------------------------------
                # Correct / incorrect
                # ------------------------------------------------

                correct = (
                    prediction == target
                )


                # ------------------------------------------------
                # Store result
                # ------------------------------------------------

                result = {

                    "image": Path(
                        filename
                    ).name,

                    "actual":
                        actual_class_name,

                    "predicted":
                        prediction_class,

                    "cancer_probability":
                        round(
                            cancer_probability,
                            6
                        ),

                    "non_cancer_probability":
                        round(
                            non_cancer_probability,
                            6
                        ),

                    "confidence":
                        round(
                            confidence,
                            6
                        ),

                    "correct":
                        correct

                }


                image_results.append(
                    result
                )


                all_predictions.append(
                    prediction
                )


                all_targets.append(
                    target
                )


                image_index += 1


    # ========================================================
    # CALCULATE METRICS
    # ========================================================

    metrics = calculate_metrics(
        all_predictions,
        all_targets
    )


    # ========================================================
    # PRINT RESULTS
    # ========================================================

    print(
        "FINAL TEST RESULTS"
    )

    print(
        "-" * 70
    )


    print(
        f"Test Accuracy     : "
        f"{metrics['accuracy']:.4f}"
    )


    print(
        f"Test Sensitivity  : "
        f"{metrics['sensitivity']:.4f}"
    )


    print(
        f"Test Specificity  : "
        f"{metrics['specificity']:.4f}"
    )


    print()


    # ========================================================
    # CONFUSION MATRIX
    # ========================================================

    print(
        "Confusion Matrix Components"
    )

    print(
        "-" * 70
    )


    print(
        "True Positives  (TP):",
        metrics["tp"]
    )


    print(
        "True Negatives  (TN):",
        metrics["tn"]
    )


    print(
        "False Positives (FP):",
        metrics["fp"]
    )


    print(
        "False Negatives (FN):",
        metrics["fn"]
    )


    print()


    # ========================================================
    # PER-IMAGE RESULTS
    # ========================================================

    print(
        "Per-image predictions"
    )

    print(
        "-" * 70
    )


    for index, result in enumerate(
        image_results,
        start=1
    ):

        status = (
            "CORRECT"
            if result["correct"]
            else "WRONG"
        )


        print(
            f"{index:02d}. "
            f"{result['image']} | "
            f"Actual: "
            f"{result['actual']} | "
            f"Predicted: "
            f"{result['predicted']} | "
            f"Confidence: "
            f"{result['confidence']:.2%} | "
            f"{status}"
        )


    # ========================================================
    # SAVE RESULTS
    # ========================================================

    checkpoint_epoch = None


    if (
        isinstance(checkpoint, dict)
        and "epoch" in checkpoint
    ):

        checkpoint_epoch = (
            checkpoint["epoch"]
        )


    output = {

        "model":
            "MobileNetV3 Small",

        "checkpoint_epoch":
            checkpoint_epoch,

        "class_mapping": {

            "cancer": 0,

            "non-cancer": 1

        },

        "test_images":
            len(test_dataset),

        "metrics":
            metrics,

        "per_image_results":
            image_results

    }


    with open(
        TEST_RESULTS_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            indent=4
        )


    # ========================================================
    # COMPLETE
    # ========================================================

    print()

    print("=" * 70)

    print(
        "TEST EVALUATION COMPLETE"
    )

    print("=" * 70)

    print()


    print(
        "Results saved to:"
    )

    print(
        TEST_RESULTS_PATH
    )

    print()


    print(
        "The test set was evaluated only "
        "after training and model selection."
    )

    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()