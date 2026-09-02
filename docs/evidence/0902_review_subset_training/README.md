# 2026-09-02 Review Subset 训练证据

本目录保存 `EXP-20260902-REVIEW-SUBSET-TREE-SEG-ALPHA` 的测试集评估图。

## 文件

| 文件 | 内容 |
| --- | --- |
| `review_subset_confusion_matrix.png` | 测试集混淆矩阵 |
| `review_subset_mask_pr_curve.png` | Mask PR 曲线 |
| `review_subset_test_prediction.jpg` | 测试集预测可视化 |

## 结论

筛选掉明显差伪标注样本后，Mask mAP50 相比全量公开伪标注数据有所提升，但仍不足以作为正式模型效果。

当前建议：继续人工修标，不替换 Demo 主模型。

