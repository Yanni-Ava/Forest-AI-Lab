import argparse
from pathlib import Path

from ultralytics import YOLO


AI_DIR = Path(__file__).resolve().parent
MODEL_PATH = AI_DIR / "weights" / "yolo26n.pt"
DEFAULT_IMAGE_PATH = AI_DIR / "input" / "tree.png"
OUTPUT_DIR = AI_DIR / "runs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect objects in an image with YOLO26n.")
    parser.add_argument(
        "image",
        nargs="?",
        default=str(DEFAULT_IMAGE_PATH),
        help="Image path. Defaults to AI/input/tree.png.",
    )
    parser.add_argument(
        "--name",
        help="Output folder name. Defaults to <image-name>_result.",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="Inference device. Use cpu on this computer.",
    )
    return parser.parse_args()


def resolve_image_path(value: str) -> Path:
    image_path = Path(value).expanduser()
    if image_path.is_absolute():
        return image_path

    working_directory_path = (Path.cwd() / image_path).resolve()
    if working_directory_path.exists():
        return working_directory_path

    return (AI_DIR / "input" / image_path).resolve()


def main() -> None:
    args = parse_args()
    image_path = resolve_image_path(args.image)
    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    output_name = args.name or f"{image_path.stem}_result"
    model = YOLO(str(MODEL_PATH))
    results = model.predict(
        source=str(image_path),
        project=str(OUTPUT_DIR),
        name=output_name,
        device=args.device,
        save=True,
        exist_ok=True,
    )

    for result in results:
        for box in result.boxes:
            class_id = int(box.cls.item())
            confidence = float(box.conf.item())
            class_name = model.names[class_id]
            print(f"{class_name}: {confidence:.2%}")

    print(f"Result saved to: {OUTPUT_DIR / output_name}")


if __name__ == "__main__":
    main()
