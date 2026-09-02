# EXP-20260902-HUMAN-REVIEWED-SEED-TREE-SEG-ALPHA-V03

## 实验目的

在完成自动修标和伪标注质量检查后，进一步筛选人工审核通过的种子样本，建立 `human_reviewed_seed` 数据集，并训练 Alpha V0.3。

本实验验证的问题是：只靠筛选较干净样本，是否足以显著提升模型效果。

## 数据集

| 项目 | 内容 |
| --- | --- |
| 数据集 | `AI/datasets/vegetation_v2_public_human_reviewed_seed` |
| 来源 | `vegetation_v2_public_auto_refined` |
| 配置文件 | `AI/config/vegetation_v2_public_human_reviewed_seed.yaml` |
| 标注状态 | `human_reviewed_auto_label` |
| train | 6 张 |
| val | 3 张 |
| test | 1 张 |

说明：该数据集是人工审核种子集，不是最终人工精标数据集。它保留了视觉上较可用的自动修标标签，但边界仍未逐点精修。

数据集检查结果：通过。

## 训练配置

| 项目 | 内容 |
| --- | --- |
| 基础模型 | `AI/weights/yolo26n-seg.pt` |
| epochs | 15 |
| imgsz | 416 |
| batch | 2 |
| device | CPU |
| 输出目录 | `AI/runs/segment/EXP-20260902-HUMAN-REVIEWED-SEED-TREE-SEG-ALPHA-V03` |

## 测试集评估

| 指标 | 数值 |
| --- | ---: |
| Box Precision | 0.0033 |
| Box Recall | 0.3333 |
| Box mAP50 | 0.0073 |
| Box mAP50-95 | 0.0019 |
| Mask Precision | 0.0000 |
| Mask Recall | 0.0000 |
| Mask mAP50 | 0.0000 |
| Mask mAP50-95 | 0.0000 |
| Inference | 46.1 ms/image |

证据图：

```text
docs/evidence/0902_human_reviewed_seed/
docs/evidence/0902_human_reviewed_seed_training/
```

## 结论

人工审核种子集完成后，数据质量在视觉上比原始伪标注更清晰，但训练结果没有达到替换 Demo 主模型的标准。

这说明：当前问题不只是“挑出好图”，还需要真正逐点修正分割边界，并增加测试集数量。否则模型会在少量样本上不稳定。

当前 Demo 主模型不替换。

## 下一步

1. 使用标注工具对 10—20 张图片进行真实人工多边形修标。
2. 避免把天空、雾、裸地和道路标入 `tree`。
3. 将标签状态改为 `human_corrected`。
4. 训练 Alpha V0.4。
5. 扩大 test 集后再判断是否替换 Demo 主模型。

