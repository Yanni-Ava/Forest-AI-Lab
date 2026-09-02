import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

from vegetation_baseline import vegetation_mask


AI_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT_DIR = AI_DIR / "input"
DEFAULT_MODEL_PATH = AI_DIR / "weights" / "yolo26n.pt"
OUTPUT_ROOT = AI_DIR / "runs" / "batch_experiments"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a repeatable AI V1 batch experiment on image files."
    )
    parser.add_argument(
        "--source",
        default=str(DEFAULT_INPUT_DIR),
        help="Image file or directory. Defaults to AI/input.",
    )
    parser.add_argument(
        "--model",
        default=str(DEFAULT_MODEL_PATH),
        help="YOLO model path. Defaults to AI/weights/yolo26n.pt.",
    )
    parser.add_argument(
        "--name",
        default=f"EXP-{datetime.now().strftime('%Y%m%d')}-BATCH-V1",
        help="Experiment name.",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="Inference device. Use cpu on the current laptop.",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.25,
        help="YOLO confidence threshold.",
    )
    return parser.parse_args()


def resolve_source(value: str) -> Path:
    source = Path(value).expanduser()
    if source.is_absolute():
        return source
    cwd_source = (Path.cwd() / source).resolve()
    if cwd_source.exists():
        return cwd_source
    return (AI_DIR / "input" / source).resolve()


def collect_images(source: Path) -> list[Path]:
    if source.is_file() and source.suffix.lower() in IMAGE_SUFFIXES:
        return [source]
    if source.is_dir():
        return sorted(path for path in source.rglob("*") if path.suffix.lower() in IMAGE_SUFFIXES)
    raise FileNotFoundError(f"No image file or directory found: {source}")


def detection_rows(result, model: YOLO) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for box in result.boxes:
        class_id = int(box.cls.item())
        x1, y1, x2, y2 = (round(value, 2) for value in box.xyxy[0].tolist())
        rows.append(
            {
                "class_id": class_id,
                "class_name": model.names[class_id],
                "confidence": round(float(box.conf.item()), 4),
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "image",
        "width",
        "height",
        "detection_count",
        "detection_classes",
        "max_confidence",
        "vegetation_coverage_pct",
        "inference_ms",
        "result_image",
        "notes",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    source = resolve_source(args.source)
    model_path = Path(args.model).expanduser().resolve()
    if not model_path.is_file():
        raise FileNotFoundError(f"Model not found: {model_path}")

    images = collect_images(source)
    if not images:
        raise FileNotFoundError(f"No supported images found under: {source}")

    output_dir = OUTPUT_ROOT / args.name
    annotated_dir = output_dir / "annotated"
    vegetation_dir = output_dir / "vegetation"
    annotated_dir.mkdir(parents=True, exist_ok=True)
    vegetation_dir.mkdir(parents=True, exist_ok=True)

    model = YOLO(str(model_path))
    summary_rows: list[dict[str, object]] = []
    details: list[dict[str, object]] = []

    for image_path in images:
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is None:
            summary_rows.append(
                {
                    "image": str(image_path),
                    "width": "",
                    "height": "",
                    "detection_count": 0,
                    "detection_classes": "",
                    "max_confidence": "",
                    "vegetation_coverage_pct": "",
                    "inference_ms": "",
                    "result_image": "",
                    "notes": "unreadable image",
                }
            )
            continue

        result = model.predict(
            source=image,
            device=args.device,
            conf=args.confidence,
            verbose=False,
        )[0]
        detections = detection_rows(result, model)

        annotated_path = annotated_dir / f"{image_path.stem}_detected.jpg"
        cv2.imwrite(str(annotated_path), result.plot())

        mask, threshold = vegetation_mask(image)
        vegetation_pixels = int(np.count_nonzero(mask))
        coverage = vegetation_pixels / int(mask.size)
        overlay = image.copy()
        green_layer = np.zeros_like(image)
        green_layer[:, :, 1] = 255
        blended = cv2.addWeighted(image, 0.55, green_layer, 0.45, 0)
        overlay[mask > 0] = blended[mask > 0]
        vegetation_path = vegetation_dir / f"{image_path.stem}_vegetation_overlay.jpg"
        cv2.imwrite(str(vegetation_path), overlay)

        classes = sorted({str(row["class_name"]) for row in detections})
        confidences = [float(row["confidence"]) for row in detections]
        height, width = image.shape[:2]
        summary_rows.append(
            {
                "image": str(image_path),
                "width": width,
                "height": height,
                "detection_count": len(detections),
                "detection_classes": ",".join(classes),
                "max_confidence": round(max(confidences), 4) if confidences else "",
                "vegetation_coverage_pct": round(coverage * 100.0, 2),
                "inference_ms": round(float(result.speed.get("inference", 0.0)), 2),
                "result_image": str(annotated_path),
                "notes": "generic YOLO baseline; not a forest-specific trained model",
            }
        )
        details.append(
            {
                "image": str(image_path),
                "width": width,
                "height": height,
                "detections": detections,
                "vegetation": {
                    "method": "RGB Excess Green (ExG) + Otsu threshold",
                    "threshold": round(float(threshold), 2),
                    "vegetation_coverage_pct": round(coverage * 100.0, 2),
                    "overlay": str(vegetation_path),
                },
            }
        )

    write_csv(output_dir / "summary.csv", summary_rows)
    report = {
        "experiment": args.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source),
        "model": str(model_path),
        "device": args.device,
        "confidence": args.confidence,
        "image_count": len(images),
        "outputs": {
            "summary_csv": str(output_dir / "summary.csv"),
            "details_json": str(output_dir / "details.json"),
            "annotated_dir": str(annotated_dir),
            "vegetation_dir": str(vegetation_dir),
        },
        "details": details,
    }
    (output_dir / "details.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({k: v for k, v in report.items() if k != "details"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
