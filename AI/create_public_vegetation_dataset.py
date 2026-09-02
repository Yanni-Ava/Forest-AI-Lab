import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen, Request

import cv2
import numpy as np

from vegetation_baseline import vegetation_mask
from create_bootstrap_vegetation_dataset import augment, mask_to_yolo_segments


AI_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = AI_DIR / "datasets" / "vegetation_v2_public"
DEFAULT_SOURCE_CACHE = AI_DIR / "input" / "public_forest_sources"
SPLIT_PLAN = ["train"] * 12 + ["val"] * 3 + ["test"] * 3


@dataclass(frozen=True)
class PublicSource:
    file_name: str
    source_page: str
    license: str
    author: str
    scene: str

    @property
    def download_url(self) -> str:
        return f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote(self.file_name)}"


PUBLIC_SOURCES = [
    PublicSource(
        file_name="View at green forest from the observation tower.jpg",
        source_page="https://commons.wikimedia.org/wiki/File:View_at_green_forest_from_the_observation_tower.jpg",
        license="Public domain",
        author="Hillebrand Steve, U.S. Fish and Wildlife Service",
        scene="forest_overview",
    ),
    PublicSource(
        file_name="Vast green forest (Unsplash).jpg",
        source_page="https://commons.wikimedia.org/wiki/File:Vast_green_forest_(Unsplash).jpg",
        license="CC0 1.0",
        author="Unsplash contributor, archived on Wikimedia Commons",
        scene="forest_overview",
    ),
    PublicSource(
        file_name="Green coniferous forest (Unsplash).jpg",
        source_page="https://commons.wikimedia.org/wiki/File:Green_coniferous_forest_(Unsplash).jpg",
        license="CC0 1.0",
        author="Unsplash contributor, archived on Wikimedia Commons",
        scene="coniferous_forest",
    ),
    PublicSource(
        file_name="Foggy green forest (Unsplash).jpg",
        source_page="https://commons.wikimedia.org/wiki/File:Foggy_green_forest_(Unsplash).jpg",
        license="CC0 1.0",
        author="Unsplash contributor, archived on Wikimedia Commons",
        scene="foggy_forest",
    ),
    PublicSource(
        file_name="Green woodland from above (Unsplash).jpg",
        source_page="https://commons.wikimedia.org/wiki/File:Green_woodland_from_above_(Unsplash).jpg",
        license="CC0 1.0",
        author="Unsplash contributor, archived on Wikimedia Commons",
        scene="forest_aerial",
    ),
    PublicSource(
        file_name="Nature-forest-trees-fog.jpg",
        source_page="https://commons.wikimedia.org/wiki/File:Nature-forest-trees-fog.jpg",
        license="CC0 1.0",
        author="Pexels contributor, archived on Wikimedia Commons",
        scene="forest_overview",
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a pseudo-labeled public forest vegetation dataset for Alpha training."
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--source-cache", default=str(DEFAULT_SOURCE_CACHE))
    parser.add_argument("--size", type=int, default=640)
    return parser.parse_args()


def download_source(source: PublicSource, cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    local_path = cache_dir / source.file_name.replace("/", "_")
    if local_path.is_file() and local_path.stat().st_size > 0:
        return local_path

    request = Request(source.download_url, headers={"User-Agent": "Forest-AI-Lab/1.0"})
    with urlopen(request, timeout=60) as response:
        local_path.write_bytes(response.read())
    return local_path


def resize_for_training(image: np.ndarray, size: int) -> np.ndarray:
    height, width = image.shape[:2]
    scale = size / max(height, width)
    new_width = max(1, int(width * scale))
    new_height = max(1, int(height * scale))
    resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    canvas = np.zeros((size, size, 3), dtype=np.uint8)
    canvas[:, :] = (245, 248, 244)
    y = (size - new_height) // 2
    x = (size - new_width) // 2
    canvas[y : y + new_height, x : x + new_width] = resized
    return canvas


def ensure_structure(output: Path) -> None:
    for split in ("train", "val", "test"):
        (output / "images" / split).mkdir(parents=True, exist_ok=True)
        (output / "labels" / split).mkdir(parents=True, exist_ok=True)
    (output / "sources").mkdir(parents=True, exist_ok=True)


def main() -> None:
    args = parse_args()
    output = Path(args.output).expanduser().resolve()
    source_cache = Path(args.source_cache).expanduser().resolve()
    ensure_structure(output)

    metadata_rows: list[dict[str, str]] = []
    created = 0
    source_notes = [
        "# vegetation_v2_public Sources",
        "",
        f"Created at: {datetime.now(timezone.utc).isoformat()}",
        "",
        "All images are public/free media from Wikimedia Commons. Labels are pseudo labels generated by RGB ExG + Otsu and must be replaced or checked manually before formal paper experiments.",
        "",
        "| File | Source page | License | Author |",
        "| --- | --- | --- | --- |",
    ]

    downloaded: list[tuple[PublicSource, Path]] = []
    for source in PUBLIC_SOURCES:
        local_path = download_source(source, source_cache)
        downloaded.append((source, local_path))
        source_notes.append(
            f"| {source.file_name} | {source.source_page} | {source.license} | {source.author} |"
        )

    for index, split in enumerate(SPLIT_PLAN, start=1):
        source, local_path = downloaded[(index - 1) % len(downloaded)]
        image = cv2.imread(str(local_path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Unreadable source image: {local_path}")

        image = resize_for_training(image, args.size)
        image = augment(image, (index - 1) // len(downloaded))
        mask, threshold = vegetation_mask(image)
        labels = mask_to_yolo_segments(mask, min_area_ratio=0.002)
        if not labels:
            continue

        image_id = f"VEG_PUBLIC_{index:04d}"
        image_name = f"{image_id}.jpg"
        label_name = f"{image_id}.txt"
        image_path = output / "images" / split / image_name
        label_path = output / "labels" / split / label_name

        cv2.imwrite(str(image_path), image)
        label_path.write_text("\n".join(labels) + "\n", encoding="utf-8")
        metadata_rows.append(
            {
                "image_id": image_id,
                "file_name": f"images/{split}/{image_name}",
                "split": split,
                "label_status": "pseudo_label",
                "source": source.file_name,
                "source_url": source.source_page,
                "license": source.license,
                "scene": source.scene,
                "shoot_date": "unknown",
                "location": "public_web",
                "quality": "alpha_public_pseudo",
                "notes": f"Pseudo segmentation label generated by ExG+Otsu; threshold={threshold:.2f}; manual review required before formal experiments.",
            }
        )
        created += 1

    if not metadata_rows:
        raise RuntimeError("No pseudo-labeled images were created.")

    metadata_path = output / "metadata.csv"
    with metadata_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(metadata_rows[0].keys()))
        writer.writeheader()
        writer.writerows(metadata_rows)

    (output / "sources" / "public_sources.md").write_text(
        "\n".join(source_notes) + "\n", encoding="utf-8"
    )
    (output / "classes.txt").write_text("0 tree\n", encoding="utf-8")
    print(f"Created {created} public pseudo-labeled images under: {output}")
    print(f"Metadata: {metadata_path}")


if __name__ == "__main__":
    main()
