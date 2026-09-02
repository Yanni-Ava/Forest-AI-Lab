import argparse
import json
from pathlib import Path

import cv2


AI_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET = AI_DIR / "datasets" / "vegetation_v2_public_human_reviewed_seed"
DEFAULT_OUTPUT = AI_DIR / "annotation_tasks" / "vegetation_alpha_v04_labelme"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export YOLO segmentation labels to LabelMe JSON.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def read_classes(dataset: Path) -> dict[int, str]:
    class_path = dataset / "classes.txt"
    if not class_path.is_file():
        return {0: "tree"}
    names: dict[int, str] = {}
    for index, line in enumerate(class_path.read_text(encoding="utf-8").splitlines()):
        name = line.strip()
        if name:
            if " " in name and name.split()[0].isdigit():
                class_id, class_name = name.split(maxsplit=1)
                names[int(class_id)] = class_name
            else:
                names[index] = name
    return names or {0: "tree"}


def label_path_for(image_path: Path) -> Path:
    parts = list(image_path.parts)
    positions = [index for index, part in enumerate(parts) if part.lower() == "images"]
    if positions:
        parts[positions[-1]] = "labels"
        return Path(*parts).with_suffix(".txt")
    return image_path.parent.parent / "labels" / image_path.parent.name / f"{image_path.stem}.txt"


def export_one(image_path: Path, label_path: Path, output_json: Path, names: dict[int, str]) -> None:
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Unreadable image: {image_path}")
    height, width = image.shape[:2]

    shapes: list[dict[str, object]] = []
    if label_path.is_file():
        for line in label_path.read_text(encoding="utf-8").splitlines():
            tokens = line.strip().split()
            if len(tokens) < 7:
                continue
            class_id = int(tokens[0])
            coordinates = [float(value) for value in tokens[1:]]
            points = [
                [round(coordinates[index] * width, 2), round(coordinates[index + 1] * height, 2)]
                for index in range(0, len(coordinates), 2)
            ]
            shapes.append(
                {
                    "label": names.get(class_id, str(class_id)),
                    "points": points,
                    "group_id": None,
                    "description": "",
                    "shape_type": "polygon",
                    "flags": {},
                    "mask": None,
                }
            )

    payload = {
        "version": "5.5.0",
        "flags": {},
        "shapes": shapes,
        "imagePath": str(image_path),
        "imageData": None,
        "imageHeight": height,
        "imageWidth": width,
        "description": "Exported from YOLO segmentation. Manually refine polygon boundaries before importing back.",
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    dataset = Path(args.dataset).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    names = read_classes(dataset)
    created = 0

    for split in ("train", "val", "test"):
        for image_path in sorted((dataset / "images" / split).glob("*.*")):
            if image_path.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            label_path = label_path_for(image_path)
            export_one(image_path, label_path, output / split / f"{image_path.stem}.json", names)
            created += 1

    print(f"Exported {created} LabelMe task(s) under: {output}")


if __name__ == "__main__":
    main()
