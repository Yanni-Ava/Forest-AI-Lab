import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path


AI_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET = AI_DIR / "datasets" / "campus_forest_v05"
DEFAULT_REPORT = AI_DIR / "runs" / "dataset_checks" / "campus_forest_v05_intake_report.json"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
FILENAME_PATTERN = re.compile(r"^CAMPUS_FOREST_\d{4}\.(jpg|jpeg|png|bmp|webp)$", re.IGNORECASE)
REQUIRED_COLUMNS = {
    "image_id",
    "filename",
    "split",
    "source_type",
    "source_detail",
    "location_or_url",
    "capture_date",
    "weather_or_scene",
    "permission",
    "note",
    "review_status",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate campus_forest_v05 data intake readiness.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--min-images", type=int, default=50)
    return parser.parse_args()


def collect_images(dataset: Path) -> dict[str, list[Path]]:
    result: dict[str, list[Path]] = {}
    for split in ("train", "val", "test"):
        split_dir = dataset / "images" / split
        result[split] = sorted(path for path in split_dir.glob("*") if path.suffix.lower() in IMAGE_SUFFIXES)
    return result


def read_metadata(dataset: Path) -> tuple[list[dict[str, str]], list[str]]:
    metadata_path = dataset / "metadata_template.csv"
    if not metadata_path.is_file():
        return [], [f"Missing metadata file: {metadata_path}"]

    with metadata_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = set(reader.fieldnames or [])
        errors = [f"Missing metadata column: {name}" for name in sorted(REQUIRED_COLUMNS - headers)]
        rows = [{key: (value or "").strip() for key, value in row.items()} for row in reader]
    return rows, errors


def validate(dataset: Path, min_images: int) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    suggestions: list[str] = []

    images_by_split = collect_images(dataset)
    all_images = [path for paths in images_by_split.values() for path in paths]
    image_names = {path.name for path in all_images}

    rows, metadata_errors = read_metadata(dataset)
    errors.extend(metadata_errors)
    real_rows = [row for row in rows if not row.get("image_id", "").lower().startswith("campus_forest_0001") or row.get("source_detail") != "example"]
    metadata_names = {row.get("filename", "") for row in real_rows if row.get("filename")}

    for image_path in all_images:
        if not FILENAME_PATTERN.match(image_path.name):
            warnings.append(f"Non-standard filename: {image_path.name}")
        if image_path.name not in metadata_names:
            warnings.append(f"Image not recorded in metadata: {image_path.name}")

    for row in real_rows:
        filename = row.get("filename", "")
        split = row.get("split", "")
        if filename and filename not in image_names:
            warnings.append(f"Metadata references missing image: {filename}")
        if split not in {"train", "val", "test"}:
            errors.append(f"Invalid split in metadata for {filename}: {split}")
        for field in ("source_type", "source_detail", "location_or_url", "permission", "review_status"):
            if not row.get(field):
                warnings.append(f"Metadata field missing for {filename}: {field}")

    split_counts = {split: len(paths) for split, paths in images_by_split.items()}
    total = sum(split_counts.values())
    if total == 0:
        warnings.append("No real images have been placed in campus_forest_v05 yet. This is normal before data delivery.")
    elif total < min_images:
        warnings.append(f"Image count below target: {total}/{min_images}")

    if total >= min_images:
        train_ratio = split_counts["train"] / total
        val_ratio = split_counts["val"] / total
        test_ratio = split_counts["test"] / total
        if not 0.60 <= train_ratio <= 0.80:
            warnings.append(f"Train split ratio is not near 70%: {train_ratio:.2%}")
        if not 0.10 <= val_ratio <= 0.25:
            warnings.append(f"Val split ratio is not near 15%: {val_ratio:.2%}")
        if not 0.10 <= test_ratio <= 0.25:
            warnings.append(f"Test split ratio is not near 15%: {test_ratio:.2%}")

    source_types = Counter(row.get("source_type", "unknown") for row in real_rows)
    if total > 0 and len(metadata_names) < total:
        suggestions.append("补全 metadata_template.csv，确保每张图片都有来源记录。")
    if total < min_images:
        suggestions.append("先让数据同学补到至少 50 张真实校园/森林图片。")
    suggestions.append("进入训练前，再用 LabelMe 标注 polygon，并运行 dataset_check.py。")

    return {
        "dataset": str(dataset),
        "target_min_images": min_images,
        "split_counts": split_counts,
        "total_images": total,
        "metadata_rows": len(real_rows),
        "source_types": dict(source_types),
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions,
        "passed_for_intake": not errors and total >= min_images and len(metadata_names) >= total,
    }


def main() -> None:
    args = parse_args()
    report = validate(Path(args.dataset).resolve(), args.min_images)
    report_path = Path(args.report).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()
