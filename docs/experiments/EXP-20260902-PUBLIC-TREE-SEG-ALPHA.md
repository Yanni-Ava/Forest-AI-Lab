# EXP-20260902-PUBLIC-TREE-SEG-ALPHA

## 实验目的

针对 9 月任务中“AI 模型优化”的要求，建立公开森林图片版本的数据集，并训练一版 Alpha 树木/植被分割模型。

本实验用于比较：只用单张 `tree.png` bootstrap 数据训练，与使用多张公开森林图片伪标注训练之间的差异。

## 数据集

| 项目 | 内容 |
| --- | --- |
| 数据集 | `AI/datasets/vegetation_v2_public` |
| 配置文件 | `AI/config/vegetation_v2_public_tree.yaml` |
| 图片来源 | Wikimedia Commons 公开森林图片 |
| 标注方式 | RGB ExG + Otsu 自动伪标注 |
| 类别 | `tree` |
| train | 12 张 |
| val | 3 张 |
| test | 3 张 |

数据集来源说明：

```text
AI/datasets/vegetation_v2_public/sources/public_sources.md
```

数据集检查结果：通过。

```powershell
.\.venv\Scripts\python.exe .\AI\dataset_check.py --data .\AI\config\vegetation_v2_public_tree.yaml --strict
```

## 训练配置

| 项目 | 内容 |
| --- | --- |
| 基础模型 | `AI/weights/yolo26n-seg.pt` |
| epochs | 15 |
| imgsz | 416 |
| batch | 2 |
| device | CPU |
| 输出目录 | `AI/runs/segment/EXP-20260902-PUBLIC-TREE-SEG-ALPHA` |

训练命令：

```powershell
.\.venv\Scripts\python.exe .\AI\train_segmentation.py --data .\AI\config\vegetation_v2_public_tree.yaml --model .\AI\weights\yolo26n-seg.pt --epochs 15 --imgsz 416 --batch 2 --device cpu --name EXP-20260902-PUBLIC-TREE-SEG-ALPHA
```

## 测试集评估

| 指标 | 数值 |
| --- | ---: |
| Box Precision | 0.0078 |
| Box Recall | 0.5833 |
| Box mAP50 | 0.0118 |
| Box mAP50-95 | 0.0070 |
| Mask Precision | 0.0022 |
| Mask Recall | 0.1667 |
| Mask mAP50 | 0.0080 |
| Mask mAP50-95 | 0.0026 |
| Inference | 31.6 ms/image |

评估结果文件：

```text
AI/runs/segment_eval/EXP-20260902-PUBLIC-TREE-SEG-ALPHA-test/metrics.json
```

## 结论

本实验完成了公开森林图片数据集构建、数据检查、模型训练和测试集评估，证明 9 月模型优化任务已经实际推进。

但测试指标明显偏低，主要原因是：

1. 公开图片视角、场景差异较大。
2. 当前标注仍是 ExG/Otsu 自动伪标注，不是人工精确标注。
3. 样本数量仍然偏少。
4. 训练轮次和 CPU 训练条件有限。

因此，本实验模型暂不替换当前 demo 的主模型。当前 demo 继续使用 `EXP-20260902-BOOTSTRAP-TREE-SEG-V1` 的权重，以保证展示稳定。

## 下一步

1. 对 `vegetation_v2_public` 进行人工标注检查。
2. 增加校园/实地采集森林图片。
3. 将 train/val/test 固定为正式数据集版本。
4. 重新训练 Alpha V0.2。
5. 将指标提升后再替换 demo 主模型。

