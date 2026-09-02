import argparse
import csv
import shutil
from pathlib import Path

import cv2
import numpy as np

from create_bootstrap_vegetation_dataset import mask_to_yolo_segments


AI_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE = AI_DIR / "datasets" / "vegetation_v2_public_review_subset"
DEFAULT_OUTPUT = AI_DIR / "datasets" / "vegetation_v2_public_auto_refined"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create stricter auto-refined vegetation labels from review subset images."
    )
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def strict_vegetation_mask(image: np.ndarray) -> tuple[np.ndarray, float]:
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB).astype(np.float32)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    red = rgb[:, :, 0]
    green = rgb[:, :, 1]
    blue = rgb[:, :, 2]
    channel_sum = np.maximum(red + green + blue, 1.0)
    exg = 2.0 * (green / channel_sum) - (red / channel_sum) - (blue / channel_sum)
    exg_normalized = cv2.normalize(exg, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    threshold, otsu_mask = cv2.threshold(
        exg_normalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    hue = hsv[:, :, 0]
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]
    green_hue = ((hue >= 25) & (hue <= 95)).astype(np.uint8) * 255
    enough_saturation = (saturation >= 35).astype(np.uint8) * 255
    not_too_pale = ~((saturation < 45) & (value > 165))
    green_dominance = ((green > red * 0.92) & (green > blue * 0.98)).astype(np.uint8) * 255

    mask = cv2.bitwise_and(otsu_mask, green_hue)
    mask = cv2.bitwise_and(mask, enough_saturation)
    mask = cv2.bitwise_and(mask, green_dominance)
    mask = cv2.bitwise_and(mask, not_too_pale.astype(np.uint8) * 255)

    kernel_open = np.ones((5, 5), dtype=np.uint8)
    kernel_close = np.ones((9, 9), dtype=np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_open)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)
    return mask, float(threshold)


def copy_and_relabel(source: Path, output: Path, split: str, image_path: Path) -> dict[str, str] | None:
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        return None

    mask, threshold = strict_vegetation_mask(image)
    labels = mask_to_yolo_segments(mask, min_area_ratio=0.006)
    if not labels:
        return None

    image_name = image_path.name
    label_name = f"{image_path.stem}.txt"
    target_image = output / "images" / split / image_name
    target_label = output / "labels" / split / label_name
    target_image.parent.mkdir(parents=True, exist_ok=True)
    target_label.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(image_path, target_image)
    target_label.write_text("\n".join(labels) + "\n", encoding="utf-8")
    coverage = float(np.count_nonzero(mask) / mask.size)
    return {
        "image_id": image_path.stem,
        "file_name": f"images/{split}/{image_name}",
        "split": split,
        "label_status": "auto_refined",
        "source": str(source),
        "source_url": "",
        "license": "see vegetation_v2_public/sources/public_sources.md",
        "scene": "public_forest_review_subset",
        "shoot_date": "unknown",
        "location": "public_web",
        "quality": "auto_refined_candidate",
        "notes": f"Strict HSV+ExG auto-refined label; threshold={threshold:.2f}; coverage={coverage:.4f}; human review still required.",
    }


def main() -> None:
    args = parse_args()
    source = Path(args.source).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    for split in ("train", "val", "test"):
        (output / "images" / split).mkdir(parents=True, exist_ok=True)
        (output / "labels" / split).mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    for split in ("train", "val", "test"):
        for image_path in sorted((source / "images" / split).glob("*.*")):
            if image_path.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            row = copy_and_relabel(source, output, split, image_path)
            if row:
                rows.append(row)

    if not rows:
        raise RuntimeError("No auto-refined labels were created.")

    with (output / "metadata.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    (output / "classes.txt").write_text("0 tree\n", encoding="utf-8")
    (output / "README.md").write_text(
        "\n".join(
            [
                "# vegetation_v2_public_auto_refined",
                "",
                "Auto-refined version of the public forest review subset.",
                "",
                "Labels are generated with stricter HSV + ExG filtering to reduce sky, fog, and pale-background false labels.",
                "This is still not a human-labeled formal dataset.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Created {len(rows)} auto-refined image(s) under: {output}")


if __name__ == "__main__":
    main()
