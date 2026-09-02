# EXP-20260902-HUMAN-CORRECTED-TREE-SEG-ALPHA-V04

## 基本信息

- 负责人：王思丹
- 日期：2026-09-02
- 阶段：9月 AI Alpha 模型优化
- 任务：使用人工辅助修标后的 LabelMe 数据导回 YOLO 数据集，并训练 Alpha V0.4 分割模型

## 数据集

```text
AI/datasets/vegetation_v2_public_human_corrected_v04
```

数据来源为人工审核种子集导出的 10 个 LabelMe JSON。修标方式为：保留原始树木/森林区域，使用颜色与亮度规则辅助删除明显天空、水面、白雾和空白背景区域，再导回 YOLO 分割格式。

数据集划分：

| split | images | labels | instances |
| --- | ---: | ---: | ---: |
| train | 6 | 6 | 6 |
| val | 3 | 3 | 3 |
| test | 1 | 1 | 3 |

数据集检查结果：通过，无 errors，无 warnings。

## 训练配置

```powershell
yolo segment train model=yolo26n-seg.pt data=AI/config/vegetation_v2_public_human_corrected_v04.yaml epochs=30 imgsz=640 batch=2 device=cpu
```

说明：本轮使用真正的 `yolo26n-seg.pt` 分割权重。训练中曾发现 `yolo26n.pt` 会被识别为检测模型，因此已停止错误路线，不计入正式实验结论。

## 测试集结果

| 指标 | 结果 |
| --- | ---: |
| Box P | 0.0100 |
| Box R | 1.0000 |
| Box mAP50 | 0.3540 |
| Box mAP50-95 | 0.2380 |
| Mask P | 0.0033 |
| Mask R | 0.3330 |
| Mask mAP50 | 0.3350 |
| Mask mAP50-95 | 0.1010 |

## 预测现象

默认阈值下测试图片没有稳定检出；降低阈值后出现大量低置信度结果，说明模型确实学习到部分植被区域特征，但置信度和边界稳定性不足。

## 结论

Alpha V0.4 跑通了“LabelMe 修标—导回 YOLO—数据集检查—分割训练—测试评估”的完整闭环，是9月模型优化流程上的实质推进。

但由于当前有效样本只有 10 张，且修标仍为机器辅助初修，模型不适合替换当前 Demo 主模型。当前 Demo 仍保留 bootstrap 模型；V0.4 作为人工精修流程验证和后续扩充数据的实验记录。

## 下一步

1. 继续增加真实校园/森林图片。
2. 用 LabelMe 进行真正人工逐点精修。
3. 将样本量提升到至少 50—100 张后再训练 Alpha V0.5。
4. 保留独立测试集，避免只在训练图上展示效果。
