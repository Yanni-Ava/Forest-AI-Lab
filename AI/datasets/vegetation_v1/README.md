# vegetation_v1 Dataset Handoff

This folder defines the first vegetation dataset handoff format for September work.

It is a structure and metadata template, not a completed training dataset yet.
Real images and labels should be added after field collection or dataset cleaning.

## Directory Structure

```text
vegetation_v1/
  images/
    train/
    val/
    test/
  labels/
    train/
    val/
    test/
  sources/
  classes.txt
  metadata_template.csv
```

## Classes

The current V1 segmentation classes are:

```text
0 tree
1 grass
2 bare_land
3 other
```

Keep this order consistent with `AI/config/vegetation_v1.yaml`.

## Label Format

Use YOLO segmentation labels:

```text
class_id x1 y1 x2 y2 x3 y3 ...
```

All coordinates must be normalized to `[0, 1]`.

For example:

```text
0 0.1200 0.2500 0.1800 0.2600 0.2000 0.4200 0.1100 0.4100
```

## Handoff Requirements

Before training, the dataset must include:

- Real image files in `images/train`, `images/val`, and `images/test`.
- Matching label files in `labels/train`, `labels/val`, and `labels/test`.
- A filled `metadata.csv` based on `metadata_template.csv`.
- Source notes under `sources/`.
- No duplicate images across train/val/test.
- No unclear class names or mixed task definitions.

## Quality Check

From the project root:

```powershell
.\.venv\Scripts\python.exe .\AI\dataset_check.py --data .\AI\config\vegetation_v1.yaml --strict
```

The check must pass before formal model training.
