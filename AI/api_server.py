from pathlib import Path
import sqlite3
from threading import Lock
from typing import Annotated
from datetime import datetime, timezone
from uuid import uuid4

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from ultralytics import YOLO

try:
    from AI.vegetation_baseline import vegetation_mask
except ImportError:
    from vegetation_baseline import vegetation_mask


AI_DIR = Path(__file__).resolve().parent
TRAINED_SEGMENT_MODEL_PATH = (
    AI_DIR
    / "runs"
    / "segment"
    / "EXP-20260902-BOOTSTRAP-TREE-SEG-V1"
    / "weights"
    / "best.pt"
)
GENERAL_DETECT_MODEL_PATH = AI_DIR / "weights" / "yolo26n.pt"
MODEL_PATH = TRAINED_SEGMENT_MODEL_PATH if TRAINED_SEGMENT_MODEL_PATH.is_file() else GENERAL_DETECT_MODEL_PATH
MODEL_KIND = "bootstrap_tree_segmentation" if MODEL_PATH == TRAINED_SEGMENT_MODEL_PATH else "general_detection"
CONFIDENCE_THRESHOLD = 0.005 if MODEL_KIND == "bootstrap_tree_segmentation" else 0.25
IMAGE_SIZE = 416 if MODEL_KIND == "bootstrap_tree_segmentation" else 640
MAX_DETECTIONS = 20 if MODEL_KIND == "bootstrap_tree_segmentation" else 300
RESULTS_DIR = AI_DIR / "runs" / "api"
WEB_DIST_DIR = AI_DIR.parent / "Web" / "dist"
DATA_DIR = AI_DIR.parent / "data"
DATABASE_PATH = DATA_DIR / "forest_ai.db"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Forest AI Vision API",
    description="Local YOLO image detection service for the Forest-AI-Lab web app.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.mount("/results", StaticFiles(directory=str(RESULTS_DIR)), name="results")

model = YOLO(str(MODEL_PATH))
model_lock = Lock()


class SensorReading(BaseModel):
    device_id: str = Field(min_length=1, max_length=64)
    recorded_at: datetime | None = None
    temperature_c: float = Field(ge=-40, le=85)
    humidity_pct: float = Field(ge=0, le=100)
    co2_ppm: float = Field(ge=0, le=100000)
    light_lux: float = Field(ge=0, le=200000)
    soil_moisture_pct: float = Field(ge=0, le=100)


def open_database() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with open_database() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                temperature_c REAL NOT NULL,
                humidity_pct REAL NOT NULL,
                co2_ppm REAL NOT NULL,
                light_lux REAL NOT NULL,
                soil_moisture_pct REAL NOT NULL
            )
            """
        )


initialize_database()


@app.get("/api")
def root() -> dict[str, str]:
    return {
        "service": "Forest AI Vision API",
        "health": "/health",
        "documentation": "/docs",
        "detect": "POST /detect",
        "sensor_upload": "POST /api/sensors/readings",
        "sensor_latest": "GET /api/sensors/latest",
    }


@app.post("/api/sensors/readings", status_code=201)
def create_sensor_reading(reading: SensorReading) -> dict[str, object]:
    recorded_at = reading.recorded_at or datetime.now(timezone.utc)
    if recorded_at.tzinfo is None:
        recorded_at = recorded_at.replace(tzinfo=timezone.utc)
    values = (
        reading.device_id,
        recorded_at.astimezone(timezone.utc).isoformat(),
        reading.temperature_c,
        reading.humidity_pct,
        reading.co2_ppm,
        reading.light_lux,
        reading.soil_moisture_pct,
    )
    with open_database() as connection:
        cursor = connection.execute(
            """
            INSERT INTO sensor_readings (
                device_id, recorded_at, temperature_c, humidity_pct,
                co2_ppm, light_lux, soil_moisture_pct
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )
        reading_id = cursor.lastrowid
    return {"id": reading_id, **reading.model_dump(), "recorded_at": values[1]}


@app.get("/api/sensors/latest")
def get_latest_sensor_reading(device_id: str | None = None) -> dict[str, object]:
    query = "SELECT * FROM sensor_readings"
    parameters: tuple[str, ...] = ()
    if device_id:
        query += " WHERE device_id = ?"
        parameters = (device_id,)
    query += " ORDER BY recorded_at DESC, id DESC LIMIT 1"
    with open_database() as connection:
        row = connection.execute(query, parameters).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="No sensor readings are available.")
    return dict(row)


@app.get("/api/sensors/readings")
def list_sensor_readings(device_id: str | None = None, limit: int = 100) -> dict[str, object]:
    limit = max(1, min(limit, 1000))
    query = "SELECT * FROM sensor_readings"
    parameters: list[object] = []
    if device_id:
        query += " WHERE device_id = ?"
        parameters.append(device_id)
    query += " ORDER BY recorded_at DESC, id DESC LIMIT ?"
    parameters.append(limit)
    with open_database() as connection:
        rows = connection.execute(query, parameters).fetchall()
    return {"count": len(rows), "items": [dict(row) for row in rows]}


@app.get("/api/health")
@app.get("/health", include_in_schema=False)
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "model": MODEL_PATH.name,
        "model_path": str(MODEL_PATH),
        "model_kind": MODEL_KIND,
        "model_exists": MODEL_PATH.is_file(),
        "confidence_threshold": str(CONFIDENCE_THRESHOLD),
        "image_size": str(IMAGE_SIZE),
        "device": "cpu",
    }


@app.post("/api/detect")
@app.post("/detect", include_in_schema=False)
async def detect(
    file: Annotated[UploadFile, File(description="JPG, PNG, BMP, or WebP image")],
) -> dict[str, object]:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Only image uploads are supported.")

    contents = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="The image exceeds the 10 MB limit.")

    encoded_image = np.frombuffer(contents, dtype=np.uint8)
    image = cv2.imdecode(encoded_image, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid image.")

    with model_lock:
        result = model.predict(
            source=image,
            device="cpu",
            imgsz=IMAGE_SIZE,
            conf=CONFIDENCE_THRESHOLD,
            max_det=MAX_DETECTIONS,
            verbose=False,
        )[0]

    mask, vegetation_threshold = vegetation_mask(image)
    vegetation_pixels = int(np.count_nonzero(mask))
    total_pixels = int(mask.size)
    vegetation_coverage = vegetation_pixels / total_pixels

    detections: list[dict[str, object]] = []
    for box in result.boxes:
        class_id = int(box.cls.item())
        x1, y1, x2, y2 = (round(value, 2) for value in box.xyxy[0].tolist())
        detections.append(
            {
                "class_id": class_id,
                "class_name": model.names[class_id],
                "confidence": round(float(box.conf.item()), 4),
                "box": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
            }
        )

    result_filename = f"{uuid4().hex}.jpg"
    result_path = RESULTS_DIR / result_filename
    if not cv2.imwrite(str(result_path), result.plot()):
        raise HTTPException(status_code=500, detail="Failed to save the result image.")

    overlay = image.copy()
    green_layer = np.zeros_like(image)
    green_layer[:, :, 1] = 255
    blended = cv2.addWeighted(image, 0.55, green_layer, 0.45, 0)
    overlay[mask > 0] = blended[mask > 0]
    vegetation_filename = f"{uuid4().hex}_vegetation.jpg"
    vegetation_path = RESULTS_DIR / vegetation_filename
    if not cv2.imwrite(str(vegetation_path), overlay):
        raise HTTPException(status_code=500, detail="Failed to save the vegetation overlay.")

    height, width = image.shape[:2]
    return {
        "filename": file.filename,
        "width": width,
        "height": height,
        "detection_count": len(detections),
        "detections": detections,
        "vegetation": {
            "method": "RGB ExG + Otsu baseline",
            "coverage": round(vegetation_coverage, 6),
            "coverage_pct": round(vegetation_coverage * 100.0, 2),
            "threshold": round(float(vegetation_threshold), 2),
            "vegetation_pixels": vegetation_pixels,
            "total_pixels": total_pixels,
            "note": "Baseline estimate for demo; not NDVI and not formal paper metric.",
        },
        "inference_ms": round(float(result.speed.get("inference", 0.0)), 2),
        "result_url": f"/results/{result_filename}",
        "vegetation_url": f"/results/{vegetation_filename}",
    }


if WEB_DIST_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(WEB_DIST_DIR), html=True), name="web")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
