# 0902 Human Corrected Alpha V0.4 训练证据

## 本次产出

本目录保存 Alpha V0.4 的关键训练/评估证据。

## 文件说明

- `human_corrected_v04_confusion_matrix.png`：测试集混淆矩阵。
- `human_corrected_v04_mask_pr_curve.png`：Mask PR 曲线。
- `human_corrected_v04_test_prediction.jpg`：测试集预测可视化。

## 结论

Alpha V0.4 完成了 LabelMe 修标数据导回后的分割训练闭环。测试集 Mask mAP50 约 0.335，但默认预测阈值下结果仍不稳定，因此暂不替换 Demo 主模型。
