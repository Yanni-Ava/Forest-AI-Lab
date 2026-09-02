import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

from vegetation_baseline import vegetation_mask


AI_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE = AI_DIR / "input" / "tree.png"
DEFAULT_OUTPUT = AI_DIR / "datasets" / "vegetation_v1"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
SPLITS = {
    "train": 8,
    "val": 2,
    "test": 2,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a small pseudo-labeled vegetation dataset for bootstrap training."
    )
    parser.add_argument(
        "--source",
        default=str(DEFAULT_SOURCE),
        help="Source image or folder. Defaults to AI/input/tree.png.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Dataset output folder. Defaults to AI/datasets/vegetation_v1.",
    )
    return parser.parse_args()


def resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    cwd_path = (Path.cwd() / path).resolve()
    if cwd_path.exists():
        return cwd_path
    return (AI_DIR / value).resolve()


def collect_sources(source: Path) -> list[Path]:
    if source.is_file() and source.suffix.lower() in IMAGE_SUFFIXES:
        return [source]
    if source.is_dir():
        return sorted(path for path in source.rglob("*") if path.suffix.lower() in IMAGE_SUFFIXES)
    raise FileNotFoundError(f"No image source found: {source}")


def augment(image: np.ndarray, index: int) -> np.ndarray:
    variants = [
        image,
        cv2.flip(image, 1),
        cv2.flip(image, 0),
        cv2.rotate(image, cv2.ROTATE_180),
        cv2.convertScaleAbs(image, alpha=1.08, beta=8),
        cv2.convertScaleAbs(image, alpha=0.92, beta=-6),
        cv2.GaussianBlur(image, (3, 3), 0),
        sharpen(image),
        crop_resize(image, 0.05, 0.00, 0.95, 0.95),
        crop_resize(image, 0.00, 0.05, 0.95, 0.95),
        crop_resize(image, 0.05, 0.05, 1.00, 1.00),
        crop_resize(image, 0.00, 0.00, 0.95, 0.95),
    ]
    return variants[index % len(variants)]


def sharpen(image: np.ndarray) -> np.ndarray:
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
    return cv2.filter2D(image, -1, kernel)


def crop_resize(image: np.ndarray, left: float, top: float, right: float, bottom: float) -> np.ndarray:
    height, width = image.shape[:2]
    x1 = int(width * left)
    y1 = int(height * top)
    x2 = int(width * right)
    y2 = int(height * bottom)
    crop = image[y1:y2, x1:x2]
    return cv2.resize(crop, (width, height), interpolation=cv2.INTER_LINEAR)


def mask_to_yolo_segments(mask: np.ndarray, min_area_ratio: float = 0.003) -> list[str]:
    height, width = mask.shape[:2]
    min_area = height * width * min_area_ratio
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    labels: list[str] = []
    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:8]:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue
        epsilon = 0.006 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        if len(approx) < 3:
            continue
        values = ["0"]
        for point in approx.reshape(-1, 2):
            x = min(max(float(point[0]) / width, 0.0), 1.0)
            y = min(max(float(point[1]) / height, 0.0), 1.0)
            values.extend([f"{x:.6f}", f"{y:.6f}"])
        labels.append(" ".join(values))
    return labels


def ensure_structure(output: Path) -> None:
    for split in SPLITS:
        (output / "images" / split).mkdir(parents=True, exist_ok=True)
        (output / "labels" / split).mkdir(parents=True, exist_ok=True)
    (output / "sources").mkdir(parents=True, exist_ok=True)


def main() -> None:
    args = parse_args()
    source = resolve_path(args.source)
    output = resolve_path(args.output)
    sources = collect_sources(source)
    ensure_structure(output)

    metadata_rows: list[dict[str, str]] = []
    created = 0
    split_plan = [split for split, count in SPLITS.items() for _ in range(count)]
    source_image = cv2.imread(str(sources[0]), cv2.IMREAD_COLOR)
    if source_image is None:
        raise ValueError(f"Unreadable source image: {sources[0]}")

    for index, split in enumerate(split_plan, start=1):
        image = augment(source_image, index - 1)
        mask, _ = vegetation_mask(image)
        labels = mask_to_yolo_segments(mask)
        if not labels:
            continue

        image_id = f"VEG_BOOTSTRAP_{index:04d}"
        image_name = f"{image_id}.jpg"
        label_name = f"{image_id}.txt"
        image_path = output / "images" / split / image_name
        label_path = output / "labels" / split / label_name

        cv2.imwrite(str(image_path), image)
        label_path.write_text("\n".join(labels) + "\n", encoding="utf-8")
        metadata_rows.append(
            {
                "image_id": image_id,
                "file_name": f"images/{split}/{image_name}",
                "split": split,
                "label_status": "pseudo_label",
                "source": "AI/input/tree.png",
                "source_url": "",
                "license": "project internal bootstrap sample",
                "scene": "vegetation_demo",
                "shoot_date": "unknown",
                "location": "unknown",
                "quality": "bootstrap",
                "notes": "Pseudo segmentation label generated by ExG+Otsu; replace with human labels for formal experiments.",
            }
        )
        created += 1

    metadata_path = output / "metadata.csv"
    with metadata_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(metadata_rows[0].keys()))
        writer.writeheader()
        writer.writerows(metadata_rows)

    source_note = output / "sources" / "bootstrap_source.md"
    source_note.write_text(
        "\n".join(
            [
                "# Bootstrap Source",
                "",
                f"Created at: {datetime.now(timezone.utc).isoformat()}",
                f"Source image: {sources[0]}",
                "",
                "This is a pseudo-labeled bootstrap dataset generated from the available vegetation sample.",
                "It is suitable for verifying the training pipeline, but it is not a formal research dataset.",
                "Formal experiments must replace these labels with real images and human-checked annotations.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Created {created} pseudo-labeled images under: {output}")
    print(f"Metadata: {metadata_path}")


if __name__ == "__main__":
    main()
