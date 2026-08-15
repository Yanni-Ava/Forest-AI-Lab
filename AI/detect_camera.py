import argparse
from pathlib import Path

import cv2
from ultralytics import YOLO


AI_DIR = Path(__file__).resolve().parent
MODEL_PATH = AI_DIR / "weights" / "yolo26n.pt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run real-time YOLO detection with a camera.")
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Camera number. The default camera is 0.",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.25,
        help="Minimum confidence from 0 to 1. Default: 0.25.",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="Inference device. Use cpu on this computer.",
    )
    return parser.parse_args()


def open_camera(camera_number: int) -> cv2.VideoCapture:
    camera = cv2.VideoCapture(camera_number, cv2.CAP_DSHOW)
    if camera.isOpened():
        return camera

    camera.release()
    return cv2.VideoCapture(camera_number)


def main() -> None:
    args = parse_args()
    if not 0 <= args.confidence <= 1:
        raise ValueError("--confidence must be between 0 and 1.")

    model = YOLO(str(MODEL_PATH))
    camera = open_camera(args.camera)
    if not camera.isOpened():
        raise RuntimeError(
            f"Cannot open camera {args.camera}. Check Windows camera permissions "
            "or try --camera 1."
        )

    window_name = "YOLO Camera Detection - press Q to exit"
    try:
        while True:
            success, frame = camera.read()
            if not success:
                raise RuntimeError("The camera opened, but no video frame was received.")

            result = model.predict(
                source=frame,
                conf=args.confidence,
                device=args.device,
                verbose=False,
            )[0]
            cv2.imshow(window_name, result.plot())

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):
                break
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
