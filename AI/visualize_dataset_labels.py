import argparse
import math
from pathlib import Path

import cv2
import numpy as np


AI_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET = AI_DIR / "datasets" / "vegetation_v2_public"
DEFAULT_OUTPUT = AI_DIR / "runs" / "dataset_review" / "vegetation_v2_public"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render YOLO segmentation labels for dataset review.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--thumb-size", type=int, default=320)
    return parser.parse_args()


def read_segments(label_path: Path) -> list[np.ndarray]:
    if not label_path.is_file():
        return []
    segments: list[np.ndarray] = []
    for line in label_path.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split()
        if len(parts) < 7:
            continue
        values = [float(value) for value in parts[1:]]
        points = np.array(values, dtype=np.float32).reshape(-1, 2)
        segments.append(points)
    return segments


def render_label(image_path: Path, label_path: Path, output_path: Path) -> dict[str, object]:
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Unreadable image: {image_path}")
    height, width = image.shape[:2]
    overlay = image.copy()
    segments = read_segments(label_path)
    for segment in segments:
        points = segment.copy()
        points[:, 0] = np.clip(points[:, 0] * width, 0, width - 1)
        points[:, 1] = np.clip(points[:, 1] * height, 0, height - 1)
        polygon = points.astype(np.int32)
        cv2.fillPoly(overlay, [polygon], (40, 220, 80))
        cv2.polylines(image, [polygon], True, (0, 120, 255), 2)

    rendered = cv2.addWeighted(image, 0.65, overlay, 0.35, 0)
    cv2.putText(
        rendered,
        f"{image_path.stem} | segments={len(segments)}",
        (12, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 0, 0),
        4,
        cv2.LINE_AA,
    )
    cv2.putText(
        rendered,
        f"{image_path.stem} | segments={len(segments)}",
        (12, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), rendered)
    return {"image": str(image_path), "label": str(label_path), "segments": len(segments)}


def make_contact_sheet(rendered_paths: list[Path], output_path: Path, thumb_size: int) -> None:
    thumbnails: list[np.ndarray] = []
    for path in rendered_paths:
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            continue
        height, width = image.shape[:2]
        scale = thumb_size / max(height, width)
        resized = cv2.resize(
            image,
            (max(1, int(width * scale)), max(1, int(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
        canvas = np.full((thumb_size, thumb_size, 3), 245, dtype=np.uint8)
        y = (thumb_size - resized.shape[0]) // 2
        x = (thumb_size - resized.shape[1]) // 2
        canvas[y : y + resized.shape[0], x : x + resized.shape[1]] = resized
        thumbnails.append(canvas)

    if not thumbnails:
        return

    columns = 3
    rows = math.ceil(len(thumbnails) / columns)
    sheet = np.full((rows * thumb_size, columns * thumb_size, 3), 255, dtype=np.uint8)
    for index, thumbnail in enumerate(thumbnails):
        row = index // columns
        column = index % columns
        sheet[
            row * thumb_size : (row + 1) * thumb_size,
            column * thumb_size : (column + 1) * thumb_size,
        ] = thumbnail
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), sheet)


def main() -> None:
    args = parse_args()
    dataset = Path(args.dataset).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    rendered_paths: list[Path] = []
    rows: list[str] = ["split,image,label,segments,review_status,notes"]

    for split in ("train", "val", "test"):
        image_dir = dataset / "images" / split
        label_dir = dataset / "labels" / split
        for image_path in sorted(image_dir.glob("*.*")):
            if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
                continue
            label_path = label_dir / f"{image_path.stem}.txt"
            rendered_path = output / "overlays" / split / f"{image_path.stem}_overlay.jpg"
            summary = render_label(image_path, label_path, rendered_path)
            rendered_paths.append(rendered_path)
            rows.append(
                ",".join(
                    [
                        split,
                        image_path.name,
                        label_path.name,
                        str(summary["segments"]),
                        "pending_human_review",
                        "Check whether the green mask covers tree/vegetation areas accurately.",
                    ]
                )
            )

    (output / "review_index.csv").write_text("\n".join(rows) + "\n", encoding="utf-8-sig")
    make_contact_sheet(rendered_paths, output / "contact_sheet.jpg", args.thumb_size)
    print(f"Rendered {len(rendered_paths)} label review image(s) under: {output}")


if __name__ == "__main__":
    main()
