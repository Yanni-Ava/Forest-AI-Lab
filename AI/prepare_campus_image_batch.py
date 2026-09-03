import argparse
import csv
import shutil
from pathlib import Path


AI_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET = AI_DIR / "datasets" / "campus_forest_v05"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
METADATA_COLUMNS = [
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
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a raw campus/forest image batch for campus_forest_v05.")
    parser.add_argument("source", help="Folder containing raw images.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--start-index", type=int, default=1)
    parser.add_argument("--source-type", default="self_shot")
    parser.add_argument("--source-detail", default="to_be_filled")
    parser.add_argument("--location-or-url", default="to_be_filled")
    parser.add_argument("--capture-date", default="to_be_filled")
    parser.add_argument("--weather-or-scene", default="to_be_filled")
    parser.add_argument("--permission", default="team_owned")
    parser.add_argument("--copy", action="store_true", help="Copy files into dataset. Without this flag, only preview.")
    return parser.parse_args()


def decide_split(index: int, total: int) -> str:
    train_limit = round(total * 0.70)
    val_limit = train_limit + round(total * 0.15)
    if index < train_limit:
        return "train"
    if index < val_limit:
        return "val"
    return "test"


def existing_metadata_rows(metadata_path: Path) -> list[dict[str, str]]:
    if not metadata_path.is_file():
        return []
    with metadata_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [{key: (value or "").strip() for key, value in row.items()} for row in reader]
    return [
        row
        for row in rows
        if not (row.get("image_id") == "CAMPUS_FOREST_0001" and row.get("source_detail") == "example")
    ]


def write_metadata(metadata_path: Path, rows: list[dict[str, str]]) -> None:
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with metadata_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=METADATA_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in METADATA_COLUMNS})


def main() -> None:
    args = parse_args()
    source_dir = Path(args.source).resolve()
    dataset = Path(args.dataset).resolve()
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Source folder not found: {source_dir}")

    raw_images = sorted(path for path in source_dir.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES)
    if not raw_images:
        raise FileNotFoundError(f"No supported images found in: {source_dir}")

    metadata_path = dataset / "metadata_template.csv"
    rows = existing_metadata_rows(metadata_path)
    existing_names = {row.get("filename") for row in rows}

    planned_rows: list[dict[str, str]] = []
    for offset, raw_path in enumerate(raw_images):
        number = args.start_index + offset
        image_id = f"CAMPUS_FOREST_{number:04d}"
        filename = f"{image_id}.jpg"
        split = decide_split(offset, len(raw_images))
        target_path = dataset / "images" / split / filename
        planned_rows.append(
            {
                "image_id": image_id,
                "filename": filename,
                "split": split,
                "source_type": args.source_type,
                "source_detail": args.source_detail,
                "location_or_url": args.location_or_url,
                "capture_date": args.capture_date,
                "weather_or_scene": args.weather_or_scene,
                "permission": args.permission,
                "note": f"prepared from {raw_path.name}",
                "review_status": "pending",
                "_source_path": str(raw_path),
                "_target_path": str(target_path),
            }
        )

    print(f"Found {len(raw_images)} image(s).")
    print("Planned split:")
    for split in ("train", "val", "test"):
        count = sum(1 for row in planned_rows if row["split"] == split)
        print(f"- {split}: {count}")

    if not args.copy:
        print("Preview only. Re-run with --copy to write files.")
        return

    for row in planned_rows:
        if row["filename"] in existing_names:
            raise FileExistsError(f"Metadata already contains filename: {row['filename']}")
        target_path = Path(row["_target_path"])
        if target_path.exists():
            raise FileExistsError(f"Target image already exists: {target_path}")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(row["_source_path"], target_path)
        row.pop("_source_path", None)
        row.pop("_target_path", None)

    rows.extend(planned_rows)
    write_metadata(metadata_path, rows)
    print(f"Copied {len(planned_rows)} image(s) into: {dataset}")
    print(f"Updated metadata: {metadata_path}")


if __name__ == "__main__":
    main()
