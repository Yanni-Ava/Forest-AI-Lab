import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from ultralytics import YOLO


AI_DIR = Path(__file__).resolve().parent
DEFAULT_DATA = AI_DIR / "config" / "vegetation_v1.yaml"
RUNS_DIR = AI_DIR / "runs" / "segment"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the vegetation segmentation baseline.")
    parser.add_argument("--data", default=str(DEFAULT_DATA))
    parser.add_argument("--model", default=str(AI_DIR / "weights" / "yolo26n-seg.pt"))
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--name", default=f"EXP-{datetime.now():%Y%m%d}-SEG-V1")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_path = Path(args.data).expanduser().resolve()
    if not data_path.is_file():
        raise FileNotFoundError(f"Dataset config not found: {data_path}")
    run_dir = RUNS_DIR / args.name
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "data": str(data_path),
        "model": args.model,
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "device": args.device,
        "workers": args.workers,
        "seed": args.seed,
        "status": "started",
    }
    manifest_path = run_dir / "experiment_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    try:
        model = YOLO(args.model)
        results = model.train(
            data=str(data_path),
            task="segment",
            epochs=args.epochs,
            imgsz=args.imgsz,
            batch=args.batch,
            device=args.device,
            workers=args.workers,
            seed=args.seed,
            deterministic=True,
            project=str(RUNS_DIR),
            name=args.name,
            exist_ok=True,
        )
    except Exception as error:
        manifest["status"] = "failed"
        manifest["error"] = str(error)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        raise
    manifest["status"] = "completed"
    manifest["save_dir"] = str(results.save_dir)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Training completed: {results.save_dir}")


if __name__ == "__main__":
    main()
