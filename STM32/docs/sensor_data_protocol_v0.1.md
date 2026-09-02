# STM32 Sensor Data Protocol V0.1

This document defines the temporary sensor data format used before the real STM32/ESP8266 link is connected.

The August goal is not real hardware integration. The goal is to ensure that the AI/API/Web system already has a stable data format for later ground sensor access.

## Upload Endpoint

```text
POST /api/sensors/readings
```

## Request Body

```json
{
  "device_id": "STM32_TEST_001",
  "recorded_at": "2026-08-31T10:00:00Z",
  "temperature_c": 28.6,
  "humidity_pct": 72.5,
  "co2_ppm": 430,
  "light_lux": 18500,
  "soil_moisture_pct": 41.2
}
```

## Fields

| Field | Type | Unit | Description |
| --- | --- | --- | --- |
| `device_id` | string | - | Ground device ID |
| `recorded_at` | datetime | UTC ISO8601 | Sensor collection time |
| `temperature_c` | number | Celsius | Air temperature |
| `humidity_pct` | number | % | Air humidity |
| `co2_ppm` | number | ppm | Carbon dioxide concentration |
| `light_lux` | number | lux | Light intensity |
| `soil_moisture_pct` | number | % | Soil moisture |

## Query Endpoints

```text
GET /api/sensors/latest
GET /api/sensors/readings
```

## Status

Current status: simulated data format ready; real STM32 upload not connected.

Next hardware task: align ESP8266 HTTP upload format with this JSON structure.
