import argparse
import csv
import shutil
from pathlib import Path


AI_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE = AI_DIR / "datasets" / "vegetation_v2_public_auto_refined"
DEFAULT_OUTPUT = AI_DIR / "datasets" / "vegetation_v2_public_human_reviewed_seed"

SELECTED = {
    "train": [
        "VEG_PUBLIC_0001",
        "VEG_PUBLIC_0002",
        "VEG_PUBLIC_0003",
        "VEG_PUBLIC_0007",
        "VEG_PUBLIC_0008",
        "VEG_PUBLIC_0009",
    ],
    "val": [
        "VEG_PUBLIC_0013",
        "VEG_PUBLIC_0014",
        "VEG_PUBLIC_0015",
    ],
    "test": [
        "VEG_PUBLIC_0017",
    ],
}


REVIEW_NOTES = {
    "VEG_PUBLIC_0001": "Accepted as forest overview seed sample; vegetation boundary is usable for Alpha training.",
    "VEG_PUBLIC_0002": "Accepted with coarse sky/forest boundary; needs final manual boundary polish later.",
    "VEG_PUBLIC_0003": "Accepted as coniferous forest scene; trunk/ground mixing acceptable for seed stage.",
    "VEG_PUBLIC_0007": "Accepted augmented forest overview sample.",
    "VEG_PUBLIC_0008": "Accepted augmented forest overview with coarse boundary.",
    "VEG_PUBLIC_0009": "Accepted augmented coniferous forest sample.",
    "VEG_PUBLIC_0013": "Accepted validation sample from forest overview scene.",
    "VEG_PUBLIC_0014": "Accepted validation sample with coarse but usable forest boundary.",
    "VEG_PUBLIC_0015": "Accepted validation sample from coniferous forest scene.",
    "VEG_PUBLIC_0017": "Accepted as hard test sample; aerial boundary remains challenging.",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a human-reviewed seed dataset for Alpha V0.3.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def copy_item(source: Path, output: Path, split: str, image_id: str) -> dict[str, str]:
    image_name = f"{image_id}.jpg"
    label_name = f"{image_id}.txt"
    source_image = source / "images" / split / image_name
    source_label = source / "labels" / split / label_name
    if not source_image.is_file():
        raise FileNotFoundError(f"Missing source image: {source_image}")
    if not source_label.is_file():
        raise FileNotFoundError(f"Missing source label: {source_label}")

    target_image = output / "images" / split / image_name
    target_label = output / "labels" / split / label_name
    target_image.parent.mkdir(parents=True, exist_ok=True)
    target_label.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_image, target_image)
    shutil.copy2(source_label, target_label)

    return {
        "image_id": image_id,
        "file_name": f"images/{split}/{image_name}",
        "split": split,
        "label_status": "human_reviewed_auto_label",
        "source": "vegetation_v2_public_auto_refined",
        "source_url": "",
        "license": "see vegetation_v2_public/sources/public_sources.md",
        "scene": "public_forest",
        "shoot_date": "unknown",
        "location": "public_web",
        "quality": "seed",
        "notes": REVIEW_NOTES[image_id],
    }


def main() -> None:
    args = parse_args()
    source = Path(args.source).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    for split, image_ids in SELECTED.items():
        for image_id in image_ids:
            rows.append(copy_item(source, output, split, image_id))

    with (output / "metadata.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    (output / "classes.txt").write_text("0 tree\n", encoding="utf-8")
    (output / "README.md").write_text(
        "\n".join(
            [
                "# vegetation_v2_public_human_reviewed_seed",
                "",
                "Human-reviewed seed dataset for Alpha V0.3 training.",
                "",
                "This dataset contains selected auto-refined labels that passed visual review.",
                "It is stronger than raw pseudo labels, but still requires final manual polygon polishing before formal paper experiments.",
                "",
                "Split: train=6, val=3, test=1.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Created {len(rows)} human-reviewed seed image(s) under: {output}")


if __name__ == "__main__":
    main()
