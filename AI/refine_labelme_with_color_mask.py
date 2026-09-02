import argparse
import json
from pathlib import Path

import cv2
import numpy as np


AI_DIR = Path(__file__).resolve().parent
DEFAULT_TASKS = AI_DIR / "annotation_tasks" / "vegetation_alpha_v04_labelme"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refine LabelMe tree polygons with image color masks.")
    parser.add_argument("--tasks", default=str(DEFAULT_TASKS))
    parser.add_argument("--min-area-ratio", type=float, default=0.006)
    parser.add_argument("--epsilon-ratio", type=float, default=0.004)
    return parser.parse_args()


def polygon_to_mask(shapes: list[dict], width: int, height: int) -> np.ndarray:
    mask = np.zeros((height, width), dtype=np.uint8)
    for shape in shapes:
        if shape.get("shape_type") != "polygon":
            continue
        points = np.array(shape.get("points", []), dtype=np.int32)
        if len(points) >= 3:
            cv2.fillPoly(mask, [points], 255)
    return mask


def vegetation_like_mask(image: np.ndarray) -> np.ndarray:
    b, g, r = cv2.split(image)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    exg = (2 * g.astype(np.int16) - r.astype(np.int16) - b.astype(np.int16))
    green_signal = exg > 8

    green_hsv = (h >= 28) & (h <= 98) & (s >= 25) & (v >= 25)
    yellow_brown_hsv = (h >= 10) & (h <= 35) & (s >= 35) & (v >= 35) & (v <= 225)
    dark_forest = (v < 95) & (s >= 18)

    sky_or_water = ((s < 38) & (v > 120)) | ((h >= 95) & (h <= 130) & (s < 85) & (v > 80))
    very_bright_background = (v > 235) & (s < 55)

    mask = (green_signal | green_hsv | yellow_brown_hsv | dark_forest) & ~sky_or_water & ~very_bright_background
    mask = mask.astype(np.uint8) * 255

    kernel = np.ones((7, 7), dtype=np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    return mask


def contours_to_shapes(mask: np.ndarray, min_area: float, epsilon_ratio: float) -> list[dict]:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    shapes: list[dict] = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue
        epsilon = max(2.0, epsilon_ratio * cv2.arcLength(contour, True))
        approx = cv2.approxPolyDP(contour, epsilon, True)
        if len(approx) < 3:
            continue
        points = approx.reshape(-1, 2).astype(float).tolist()
        shapes.append(
            {
                "label": "tree",
                "points": points,
                "group_id": None,
                "description": "",
                "shape_type": "polygon",
                "flags": {},
                "mask": None,
            }
        )
    return shapes


def refine_one(json_path: Path, min_area_ratio: float, epsilon_ratio: float) -> tuple[int, int]:
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    image_path = Path(payload["imagePath"]).expanduser().resolve()
    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(f"Image referenced by LabelMe JSON not found: {image_path}")

    height, width = image.shape[:2]
    seed = polygon_to_mask(payload.get("shapes", []), width, height)
    color = vegetation_like_mask(image)
    refined = cv2.bitwise_and(seed, color)

    if cv2.countNonZero(refined) < 0.08 * max(cv2.countNonZero(seed), 1):
        refined = seed

    min_area = width * height * min_area_ratio
    old_count = len(payload.get("shapes", []))
    payload["shapes"] = contours_to_shapes(refined, min_area, epsilon_ratio)
    payload["imageWidth"] = width
    payload["imageHeight"] = height
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return old_count, len(payload["shapes"])


def main() -> None:
    args = parse_args()
    task_dir = Path(args.tasks).resolve()
    json_paths = sorted(task_dir.glob("*/*.json"))
    if not json_paths:
        raise FileNotFoundError(f"No LabelMe JSON found under {task_dir}")

    for json_path in json_paths:
        old_count, new_count = refine_one(json_path, args.min_area_ratio, args.epsilon_ratio)
        print(f"{json_path.relative_to(task_dir)}: {old_count} -> {new_count} polygon(s)")


if __name__ == "__main__":
    main()
