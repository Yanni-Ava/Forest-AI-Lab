import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import yaml


AI_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = AI_DIR / "config" / "vegetation_v1.yaml"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit a YOLO segmentation dataset.")
    parser.add_argument("--data", default=str(DEFAULT_CONFIG), help="Dataset YAML path.")
    parser.add_argument("--report", help="Optional JSON report path.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failure.")
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def label_path_for(image_path: Path) -> Path:
    parts = list(image_path.parts)
    positions = [index for index, part in enumerate(parts) if part.lower() == "images"]
    if positions:
        parts[positions[-1]] = "labels"
        return Path(*parts).with_suffix(".txt")
    return image_path.parent.parent / "labels" / image_path.parent.name / f"{image_path.stem}.txt"


def resolve_split(config_path: Path, root: Path, value: str) -> Path:
    split_path = Path(value)
    if split_path.is_absolute():
        return split_path
    return (root / split_path).resolve()


def audit(config_path: Path) -> dict[str, object]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    names_raw = config.get("names", {})
    if isinstance(names_raw, list):
        names = {index: name for index, name in enumerate(names_raw)}
    else:
        names = {int(key): value for key, value in names_raw.items()}

    root_value = Path(config.get("path", "."))
    root = root_value if root_value.is_absolute() else (config_path.parent / root_value).resolve()
    errors: list[str] = []
    warnings: list[str] = []
    split_summary: dict[str, dict[str, object]] = {}
    hashes: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for split in ("train", "val", "test"):
        value = config.get(split)
        if not value:
            warnings.append(f"Missing split in YAML: {split}")
            continue
        split_dir = resolve_split(config_path, root, str(value))
        if not split_dir.is_dir():
            errors.append(f"Split directory does not exist: {split_dir}")
            split_summary[split] = {"images": 0, "labels": 0, "instances": 0}
            continue

        images = sorted(path for path in split_dir.rglob("*") if path.suffix.lower() in IMAGE_SUFFIXES)
        class_counts: Counter[int] = Counter()
        label_count = 0
        instance_count = 0
        for image_path in images:
            image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
            if image is None:
                errors.append(f"Unreadable image: {image_path}")
                continue
            hashes[sha256(image_path)].append((split, str(image_path)))
            label_path = label_path_for(image_path)
            if not label_path.is_file():
                errors.append(f"Missing label: {label_path}")
                continue
            label_count += 1
            lines = [line.strip() for line in label_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if not lines:
                warnings.append(f"Empty label file: {label_path}")
            for line_number, line in enumerate(lines, start=1):
                tokens = line.split()
                try:
                    class_id = int(tokens[0])
                    coordinates = [float(token) for token in tokens[1:]]
                except (ValueError, IndexError):
                    errors.append(f"Invalid label syntax: {label_path}:{line_number}")
                    continue
                if class_id not in names:
                    errors.append(f"Unknown class {class_id}: {label_path}:{line_number}")
                if len(coordinates) < 6 or len(coordinates) % 2 != 0:
                    errors.append(f"Not a segmentation polygon: {label_path}:{line_number}")
                if any(value < 0.0 or value > 1.0 for value in coordinates):
                    errors.append(f"Coordinate outside [0,1]: {label_path}:{line_number}")
                class_counts[class_id] += 1
                instance_count += 1

        if not images:
            errors.append(f"No images found in split: {split_dir}")
        split_summary[split] = {
            "path": str(split_dir),
            "images": len(images),
            "labels": label_count,
            "instances": instance_count,
            "class_counts": {names.get(key, str(key)): value for key, value in sorted(class_counts.items())},
        }

    for digest, occurrences in hashes.items():
        splits = {split for split, _ in occurrences}
        if len(splits) > 1:
            joined = "; ".join(f"{split}: {path}" for split, path in occurrences)
            errors.append(f"Identical image appears across splits ({digest[:12]}): {joined}")

    return {
        "dataset_config": str(config_path),
        "dataset_root": str(root),
        "classes": names,
        "splits": split_summary,
        "errors": errors,
        "warnings": warnings,
        "passed": not errors,
    }


def main() -> None:
    args = parse_args()
    config_path = Path(args.data).expanduser().resolve()
    if not config_path.is_file():
        raise FileNotFoundError(f"Dataset config not found: {config_path}")
    report = audit(config_path)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if args.report:
        report_path = Path(args.report).expanduser().resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(text, encoding="utf-8")
    if report["errors"] or (args.strict and report["warnings"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
