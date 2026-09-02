# EXP-20260902-AUTO-REFINED-TREE-SEG-ALPHA-V02

## 实验目的

在 Review Subset 模型基础上，尝试使用更严格的 HSV + ExG 自动修标规则，过滤天空、雾和浅色背景误标，训练 Alpha V0.2。

本实验验证的问题是：自动修标能否替代人工修标。

## 数据集

| 项目 | 内容 |
| --- | --- |
| 数据集 | `AI/datasets/vegetation_v2_public_auto_refined` |
| 来源 | `vegetation_v2_public_review_subset` |
| 配置文件 | `AI/config/vegetation_v2_public_auto_refined.yaml` |
| 标注状态 | `auto_refined` |
| train | 8 张 |
| val | 3 张 |
| test | 1 张 |

数据集检查结果：通过。

## 自动修标方法

文件：

```text
AI/create_auto_refined_dataset.py
```

主要过滤条件：

- ExG/Otsu 植被初筛。
- HSV 绿色 hue 范围。
- 饱和度阈值。
- 去除低饱和高亮度区域，减少天空/雾误标。
- 绿色通道优势判断。

## 训练配置

| 项目 | 内容 |
| --- | --- |
| 基础模型 | `AI/weights/yolo26n-seg.pt` |
| epochs | 12 |
| imgsz | 416 |
| batch | 2 |
| device | CPU |
| 输出目录 | `AI/runs/segment/EXP-20260902-AUTO-REFINED-TREE-SEG-ALPHA-V02` |

## 测试集评估

| 指标 | 数值 |
| --- | ---: |
| Box Precision | 0.0067 |
| Box Recall | 0.6667 |
| Box mAP50 | 0.0283 |
| Box mAP50-95 | 0.0148 |
| Mask Precision | 0.0033 |
| Mask Recall | 0.3333 |
| Mask mAP50 | 0.0058 |
| Mask mAP50-95 | 0.0012 |
| Inference | 58.3 ms/image |

证据图：

```text
docs/evidence/0902_auto_refined_dataset/
docs/evidence/0902_auto_refined_training/
```

## 结论

自动修标后的标注总览图更干净，天空、雾和浅色背景误标有所减少。

但模型测试指标没有提升，反而低于 Review Subset 模型。说明当前自动规则过于严格，可能删掉了部分真实植被区域，导致训练目标不足。

因此，本实验结论是：

> 自动修标可以作为人工标注前的辅助检查工具，但不能替代人工修标。

当前 Demo 主模型不替换。

## 下一步

1. 保留自动修标脚本作为辅助工具。
2. 对 12 张 review subset 样例进行人工修标。
3. 人工修标后训练 Alpha V0.3。
4. 若指标和可视化明显提升，再替换 Demo 主模型。

