# EXP-20260902-BOOTSTRAP-TREE-SEG-V1

## 实验目的

针对“尚未训练可靠森林专用模型”的不足，先建立一个可运行的 YOLO 分割模型训练流程。

本实验使用现有 `tree.png` 自动生成伪标注 bootstrap 数据集，并训练单类 `tree` 分割模型。该实验用于证明训练链路、权重产出和评估流程已经跑通，不作为正式论文模型精度。

## 数据集

| 项目 | 内容 |
| --- | --- |
| 数据目录 | `AI/datasets/vegetation_v1` |
| 生成脚本 | `AI/create_bootstrap_vegetation_dataset.py` |
| 标注方式 | ExG + Otsu 自动伪标注 |
| 类别 | `tree` |
| train | 8 张 |
| val | 2 张 |
| test | 2 张 |

数据集检查命令：

```powershell
.\.venv\Scripts\python.exe .\AI\dataset_check.py --data .\AI\config\vegetation_bootstrap_tree.yaml --strict
```

检查结果：通过。图片、标签和类别 ID 均可被训练程序读取。

## 训练配置

| 项目 | 内容 |
| --- | --- |
| 基础模型 | `AI/weights/yolo26n-seg.pt` |
| 配置文件 | `AI/config/vegetation_bootstrap_tree.yaml` |
| epochs | 20 |
| imgsz | 416 |
| batch | 2 |
| device | CPU |
| 输出目录 | `AI/runs/segment/EXP-20260902-BOOTSTRAP-TREE-SEG-V1` |

训练命令：

```powershell
.\.venv\Scripts\python.exe .\AI\train_segmentation.py --data .\AI\config\vegetation_bootstrap_tree.yaml --model .\AI\weights\yolo26n-seg.pt --epochs 20 --imgsz 416 --batch 2 --device cpu --name EXP-20260902-BOOTSTRAP-TREE-SEG-V1
```

## 评估结果

测试集评估结果：

| 指标 | 数值 |
| --- | ---: |
| Box Precision | 0.015 |
| Box Recall | 0.900 |
| Box mAP50 | 0.356 |
| Box mAP50-95 | 0.224 |
| Mask Precision | 0.015 |
| Mask Recall | 0.900 |
| Mask mAP50 | 0.355 |
| Mask mAP50-95 | 0.213 |
| Inference | 23.1 ms/image |

权重文件：

```text
AI/runs/segment/EXP-20260902-BOOTSTRAP-TREE-SEG-V1/weights/best.pt
AI/runs/segment/EXP-20260902-BOOTSTRAP-TREE-SEG-V1/weights/last.pt
```

评估结果文件：

```text
AI/runs/segment_eval/EXP-20260902-BOOTSTRAP-TREE-SEG-V1-test/metrics.json
```

## 结论

已完成从数据集生成、数据检查、模型训练、权重保存到测试集评估的完整训练链路。

当前模型仍存在明显不足：数据来自单张图片的伪标注增强，样本数量少，泛化能力不足，预测展示不稳定。因此该模型只能作为训练流程证明，不能作为正式森林植被识别模型。

补充验证：使用训练后的 `best.pt` 对 `AI/input/tree.png` 做推理时，低置信度阈值可输出检测结果，但会出现大量重复/误检，说明当前权重已经具备可运行性，但仍需要真实标注数据和阈值优化后才能用于正式展示。

## Demo 接入

已将本实验产出的 `best.pt` 接入 `AI/api_server.py`：

- 本地存在该权重时，API 优先使用 bootstrap 树木分割模型。
- 权重不存在时，API 自动回退到通用 `yolo26n.pt`，避免队友拉取代码后 demo 无法启动。
- 前端 Vue demo 仍调用原 `/detect` 接口，不需要修改前端调用方式。
- 本地接口验证通过：`/api/health` 返回 `model=best.pt`，上传 `tree.png` 返回 `detection_count=20`。

## 下一步

1. 接入真实 `dataset_v1` 或校园/公开森林图片。
2. 用人工标注替代伪标注。
3. 扩充类别或先固定单类 `tree/vegetation`。
4. 在真实 test 集上重新训练并记录正式指标。
