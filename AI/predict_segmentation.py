import argparse
from pathlib import Path

from ultralytics import YOLO


AI_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = AI_DIR / "runs" / "segment_predict"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run vegetation segmentation inference.")
    parser.add_argument("source", help="Image, folder, video, or camera index.")
    parser.add_argument("--model", required=True, help="Path to trained segmentation weights.")
    parser.add_argument("--name", default="prediction")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_path = Path(args.model).expanduser().resolve()
    if not model_path.is_file():
        raise FileNotFoundError(f"Model not found: {model_path}")
    source: str | int = int(args.source) if args.source.isdigit() else args.source
    results = YOLO(str(model_path)).predict(
        source=source,
        imgsz=args.imgsz,
        conf=args.conf,
        device=args.device,
        project=str(OUTPUT_DIR),
        name=args.name,
        save=True,
        save_txt=True,
        save_conf=True,
        exist_ok=True,
    )
    print(f"Processed {len(results)} item(s). Results saved to: {OUTPUT_DIR / args.name}")


if __name__ == "__main__":
    main()
