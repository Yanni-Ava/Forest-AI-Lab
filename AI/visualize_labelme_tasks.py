import argparse
import json
import math
from pathlib import Path

import cv2
import numpy as np


AI_DIR = Path(__file__).resolve().parent
DEFAULT_TASKS = AI_DIR / "annotation_tasks" / "vegetation_alpha_v04_labelme"
DEFAULT_OUTPUT = AI_DIR.parent / "docs" / "evidence" / "0902_labelme_annotation_tasks" / "labelme_task_contact_sheet.jpg"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a contact sheet for LabelMe polygon review tasks.")
    parser.add_argument("--tasks", default=str(DEFAULT_TASKS))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--thumb-width", type=int, default=360)
    return parser.parse_args()


def draw_task(json_path: Path, thumb_width: int) -> np.ndarray:
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    image_path = Path(payload["imagePath"]).expanduser().resolve()
    image = cv2.imread(str(image_path))
    if image is None:
        image = np.full((260, thumb_width, 3), 245, dtype=np.uint8)
        cv2.putText(image, "IMAGE NOT FOUND", (18, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    else:
        for shape in payload.get("shapes", []):
            points = np.array(shape.get("points", []), dtype=np.int32)
            if len(points) >= 3:
                cv2.polylines(image, [points], isClosed=True, color=(255, 0, 255), thickness=3)
                overlay = image.copy()
                cv2.fillPoly(overlay, [points], color=(255, 0, 255))
                image = cv2.addWeighted(overlay, 0.2, image, 0.8, 0)

        height, width = image.shape[:2]
        scale = thumb_width / width
        image = cv2.resize(image, (thumb_width, max(1, int(height * scale))))

    label = f"{json_path.parent.name}/{json_path.stem}"
    header = np.full((42, image.shape[1], 3), 30, dtype=np.uint8)
    cv2.putText(header, label, (10, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 2)
    return np.vstack([header, image])


def pad_to_size(image: np.ndarray, width: int, height: int) -> np.ndarray:
    canvas = np.full((height, width, 3), 245, dtype=np.uint8)
    canvas[: image.shape[0], : image.shape[1]] = image
    return canvas


def main() -> None:
    args = parse_args()
    task_dir = Path(args.tasks).resolve()
    output_path = Path(args.output).resolve()
    json_paths = sorted(task_dir.glob("*/*.json"))
    if not json_paths:
        raise FileNotFoundError(f"No LabelMe JSON found under {task_dir}")

    thumbs = [draw_task(path, args.thumb_width) for path in json_paths]
    cell_width = max(item.shape[1] for item in thumbs)
    cell_height = max(item.shape[0] for item in thumbs)
    columns = 2
    rows = math.ceil(len(thumbs) / columns)
    sheet = np.full((rows * cell_height, columns * cell_width, 3), 250, dtype=np.uint8)

    for index, thumb in enumerate(thumbs):
        row = index // columns
        col = index % columns
        cell = pad_to_size(thumb, cell_width, cell_height)
        y0 = row * cell_height
        x0 = col * cell_width
        sheet[y0 : y0 + cell_height, x0 : x0 + cell_width] = cell

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), sheet)
    print(f"Saved LabelMe task contact sheet: {output_path}")


if __name__ == "__main__":
    main()
