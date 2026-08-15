import argparse
import json
from pathlib import Path

from ultralytics import YOLO


AI_DIR = Path(__file__).resolve().parent
DEFAULT_DATA = AI_DIR / "config" / "vegetation_v1.yaml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a vegetation segmentation model.")
    parser.add_argument("--model", required=True, help="Path to best.pt or another segmentation weight.")
    parser.add_argument("--data", default=str(DEFAULT_DATA))
    parser.add_argument("--split", choices=("val", "test"), default="test")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output", help="Optional JSON metrics path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_path = Path(args.model).expanduser().resolve()
    data_path = Path(args.data).expanduser().resolve()
    if not model_path.is_file():
        raise FileNotFoundError(f"Model not found: {model_path}")
    if not data_path.is_file():
        raise FileNotFoundError(f"Dataset config not found: {data_path}")

    metrics = YOLO(str(model_path)).val(
        data=str(data_path), split=args.split, imgsz=args.imgsz, device=args.device
    )
    payload = {
        "model": str(model_path),
        "data": str(data_path),
        "split": args.split,
        "results": metrics.results_dict,
        "speed_ms": metrics.speed,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2, default=float)
    print(text)
    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
