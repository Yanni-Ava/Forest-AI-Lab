import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np


AI_DIR = Path(__file__).resolve().parent
DEFAULT_IMAGE_PATH = AI_DIR / "input" / "tree.png"
OUTPUT_ROOT = AI_DIR / "runs" / "vegetation_baseline"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estimate green vegetation coverage in an RGB image using an ExG baseline."
    )
    parser.add_argument("image", nargs="?", default=str(DEFAULT_IMAGE_PATH))
    parser.add_argument("--name", help="Experiment folder name. Defaults to the image stem.")
    return parser.parse_args()


def resolve_image_path(value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    cwd_path = (Path.cwd() / path).resolve()
    if cwd_path.exists():
        return cwd_path
    return (AI_DIR / "input" / path).resolve()


def vegetation_mask(image: np.ndarray) -> tuple[np.ndarray, float]:
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB).astype(np.float32)
    channel_sum = np.maximum(rgb.sum(axis=2), 1.0)
    red = rgb[:, :, 0] / channel_sum
    green = rgb[:, :, 1] / channel_sum
    blue = rgb[:, :, 2] / channel_sum
    exg = 2.0 * green - red - blue

    exg_normalized = cv2.normalize(exg, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    threshold, mask = cv2.threshold(
        exg_normalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    kernel = np.ones((5, 5), dtype=np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask, float(threshold)


def main() -> None:
    args = parse_args()
    image_path = resolve_image_path(args.image)
    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Unsupported or invalid image: {image_path}")

    mask, threshold = vegetation_mask(image)
    vegetation_pixels = int(np.count_nonzero(mask))
    total_pixels = int(mask.size)
    coverage = vegetation_pixels / total_pixels

    experiment_name = args.name or image_path.stem
    output_dir = OUTPUT_ROOT / experiment_name
    output_dir.mkdir(parents=True, exist_ok=True)

    overlay = image.copy()
    green_layer = np.zeros_like(image)
    green_layer[:, :, 1] = 255
    blended = cv2.addWeighted(image, 0.55, green_layer, 0.45, 0)
    overlay[mask > 0] = blended[mask > 0]

    mask_path = output_dir / "vegetation_mask.png"
    overlay_path = output_dir / "vegetation_overlay.jpg"
    cv2.imwrite(str(mask_path), mask)
    cv2.imwrite(str(overlay_path), overlay)

    metrics = {
        "experiment": experiment_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "RGB Excess Green (ExG) + Otsu threshold",
        "source_image": str(image_path),
        "width": int(image.shape[1]),
        "height": int(image.shape[0]),
        "threshold": round(threshold, 2),
        "vegetation_pixels": vegetation_pixels,
        "total_pixels": total_pixels,
        "vegetation_coverage": round(coverage, 6),
        "vegetation_coverage_pct": round(coverage * 100.0, 2),
        "limitations": "Baseline only; not a trained segmentation model and not valid NDVI.",
    }
    metrics_path = output_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"Results saved to: {output_dir}")


if __name__ == "__main__":
    main()
