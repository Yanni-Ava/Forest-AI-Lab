# EXP-20260902-REVIEW-SUBSET-TREE-SEG-ALPHA

## 实验目的

在 `vegetation_v2_public` 全量公开森林伪标注数据训练效果偏低后，先对伪标注总览图进行质量检查，筛出较适合人工修标的样例，形成 review subset，再训练一版模型。

本实验用于验证：剔除明显差标注样本后，模型训练结果是否更稳定。

## 数据集

| 项目 | 内容 |
| --- | --- |
| 原始数据集 | `AI/datasets/vegetation_v2_public` |
| 子集数据集 | `AI/datasets/vegetation_v2_public_review_subset` |
| 人工检查表 | `AI/datasets/vegetation_v2_public/manual_review_v0.1.csv` |
| 配置文件 | `AI/config/vegetation_v2_public_review_subset.yaml` |
| 类别 | `tree` |
| train | 8 张 |
| val | 3 张 |
| test | 1 张 |

数据集检查结果：通过。

```powershell
.\.venv\Scripts\python.exe .\AI\dataset_check.py --data .\AI\config\vegetation_v2_public_review_subset.yaml --strict
```

## 训练配置

| 项目 | 内容 |
| --- | --- |
| 基础模型 | `AI/weights/yolo26n-seg.pt` |
| epochs | 12 |
| imgsz | 416 |
| batch | 2 |
| device | CPU |
| 输出目录 | `AI/runs/segment/EXP-20260902-REVIEW-SUBSET-TREE-SEG-ALPHA` |

训练命令：

```powershell
.\.venv\Scripts\python.exe .\AI\train_segmentation.py --data .\AI\config\vegetation_v2_public_review_subset.yaml --model .\AI\weights\yolo26n-seg.pt --epochs 12 --imgsz 416 --batch 2 --device cpu --name EXP-20260902-REVIEW-SUBSET-TREE-SEG-ALPHA
```

## 测试集评估

| 指标 | 数值 |
| --- | ---: |
| Box Precision | 0.0067 |
| Box Recall | 0.3333 |
| Box mAP50 | 0.1667 |
| Box mAP50-95 | 0.1359 |
| Mask Precision | 0.0033 |
| Mask Recall | 0.1667 |
| Mask mAP50 | 0.1650 |
| Mask mAP50-95 | 0.0860 |
| Inference | 51.4 ms/image |

评估结果文件：

```text
AI/runs/segment_eval/EXP-20260902-REVIEW-SUBSET-TREE-SEG-ALPHA-test/metrics.json
```

证据图：

```text
docs/evidence/0902_review_subset_training/
```

## 结论

相比 `EXP-20260902-PUBLIC-TREE-SEG-ALPHA`，筛选后的 review subset 模型测试集 Mask mAP50 从约 0.008 提升到约 0.165，说明剔除明显差伪标注样本后，模型结果有改善。

但该结果仍不足以替换 Demo 主模型，原因是：

1. test 图片数量只有 1 张，指标不够稳定。
2. 标签仍是伪标注，不是人工精标。
3. 预测可视化仍存在大量重复检测。

因此当前结论是：筛选样本有效，但下一步必须进行人工修标，而不是继续盲目增加训练轮次。

## 下一步

1. 对 review subset 中 12 张样例进行人工修标。
2. 将修标后的标签状态改为 `human_checked`。
3. 重新训练 Alpha V0.2。
4. 与 bootstrap 模型、public 全量模型、review subset 模型做三方对比。

