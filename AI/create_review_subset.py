import argparse
import csv
import shutil
from pathlib import Path


AI_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET = AI_DIR / "datasets" / "vegetation_v2_public"
DEFAULT_REVIEW = DEFAULT_DATASET / "manual_review_v0.1.csv"
DEFAULT_OUTPUT = AI_DIR / "datasets" / "vegetation_v2_public_review_subset"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a dataset subset from reviewed candidates.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--review", default=str(DEFAULT_REVIEW))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def copy_candidate(dataset: Path, output: Path, row: dict[str, str]) -> dict[str, str]:
    split = row["split"]
    image_name = f"{row['image_id']}.jpg"
    label_name = f"{row['image_id']}.txt"
    source_image = dataset / "images" / split / image_name
    source_label = dataset / "labels" / split / label_name
    target_image = output / "images" / split / image_name
    target_label = output / "labels" / split / label_name
    target_image.parent.mkdir(parents=True, exist_ok=True)
    target_label.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_image, target_image)
    shutil.copy2(source_label, target_label)
    return {
        "image_id": row["image_id"],
        "file_name": f"images/{split}/{image_name}",
        "split": split,
        "label_status": "pseudo_label_review_candidate",
        "source": "vegetation_v2_public",
        "source_url": "",
        "license": "see vegetation_v2_public/sources/public_sources.md",
        "scene": "",
        "shoot_date": "unknown",
        "location": "public_web",
        "quality": row["quality_level"],
        "notes": f"Selected from manual review list; issue={row['issue']}; next_action={row['next_action']}",
    }


def main() -> None:
    args = parse_args()
    dataset = Path(args.dataset).expanduser().resolve()
    review = Path(args.review).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    for split in ("train", "val", "test"):
        (output / "images" / split).mkdir(parents=True, exist_ok=True)
        (output / "labels" / split).mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    with review.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row["decision"] == "candidate_for_manual_refine":
                rows.append(copy_candidate(dataset, output, row))

    if not rows:
        raise RuntimeError("No review candidates found.")

    fieldnames = list(rows[0].keys())
    with (output / "metadata.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    (output / "classes.txt").write_text("0 tree\n", encoding="utf-8")
    (output / "README.md").write_text(
        "\n".join(
            [
                "# vegetation_v2_public_review_subset",
                "",
                "This subset contains the pseudo-labeled public forest images selected as manual-refinement candidates.",
                "",
                "It is not a formal dataset yet. Labels must be manually checked before formal paper experiments.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Created {len(rows)} review candidate image(s) under: {output}")


if __name__ == "__main__":
    main()
