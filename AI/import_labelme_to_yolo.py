import argparse
import csv
import json
import shutil
from pathlib import Path


AI_DIR = Path(__file__).resolve().parent
DEFAULT_TASKS = AI_DIR / "annotation_tasks" / "vegetation_alpha_v04_labelme"
DEFAULT_OUTPUT = AI_DIR / "datasets" / "vegetation_v2_public_human_corrected_v04"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import corrected LabelMe polygons into a YOLO dataset.")
    parser.add_argument("--tasks", default=str(DEFAULT_TASKS))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def normalize_points(points: list[list[float]], width: int, height: int) -> list[str]:
    values: list[str] = []
    for x, y in points:
        nx = min(max(float(x) / width, 0.0), 1.0)
        ny = min(max(float(y) / height, 0.0), 1.0)
        values.extend([f"{nx:.6f}", f"{ny:.6f}"])
    return values


def import_one(task_json: Path, output: Path, split: str) -> dict[str, str]:
    payload = json.loads(task_json.read_text(encoding="utf-8"))
    image_path = Path(payload["imagePath"]).expanduser().resolve()
    if not image_path.is_file():
        raise FileNotFoundError(f"Image referenced by LabelMe JSON not found: {image_path}")

    width = int(payload["imageWidth"])
    height = int(payload["imageHeight"])
    labels: list[str] = []
    for shape in payload.get("shapes", []):
        if shape.get("shape_type") != "polygon":
            continue
        points = shape.get("points", [])
        if len(points) < 3:
            continue
        labels.append(" ".join(["0", *normalize_points(points, width, height)]))

    image_name = image_path.name
    label_name = f"{image_path.stem}.txt"
    target_image = output / "images" / split / image_name
    target_label = output / "labels" / split / label_name
    target_image.parent.mkdir(parents=True, exist_ok=True)
    target_label.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(image_path, target_image)
    target_label.write_text("\n".join(labels) + ("\n" if labels else ""), encoding="utf-8")

    return {
        "image_id": image_path.stem,
        "file_name": f"images/{split}/{image_name}",
        "split": split,
        "label_status": "human_corrected",
        "source": str(image_path),
        "source_url": "",
        "license": "see vegetation_v2_public/sources/public_sources.md",
        "scene": "public_forest",
        "shoot_date": "unknown",
        "location": "public_web",
        "quality": "human_corrected_v04",
        "notes": "Imported from LabelMe manual polygon correction task.",
    }


def main() -> None:
    args = parse_args()
    tasks = Path(args.tasks).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()

    rows: list[dict[str, str]] = []
    for split in ("train", "val", "test"):
        for task_json in sorted((tasks / split).glob("*.json")):
            rows.append(import_one(task_json, output, split))

    if not rows:
        raise RuntimeError("No LabelMe JSON files found.")

    output.mkdir(parents=True, exist_ok=True)
    with (output / "metadata.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    (output / "classes.txt").write_text("0 tree\n", encoding="utf-8")
    (output / "README.md").write_text(
        "\n".join(
            [
                "# vegetation_v2_public_human_corrected_v04",
                "",
                "YOLO segmentation dataset imported from corrected LabelMe polygon files.",
                "",
                "This dataset should only be used as formal Alpha V0.4 input after the LabelMe files have been manually checked.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Imported {len(rows)} corrected item(s) under: {output}")


if __name__ == "__main__":
    main()
