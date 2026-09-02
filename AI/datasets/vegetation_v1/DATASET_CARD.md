# vegetation_v1 数据集说明卡

## 当前状态

`vegetation_v1` 当前是 bootstrap 训练集，不是正式论文数据集。

它的作用是：在真实人工标注数据还没到位前，先把“图片整理、YOLO 分割标注格式、数据检查、模型训练、评估输出”这一整条流程跑通。

## 数据来源

| 项目 | 内容 |
| --- | --- |
| 原始样例 | `AI/input/tree.png` |
| 生成方式 | 脚本自动增强 + ExG/Otsu 伪标注 |
| 生成脚本 | `AI/create_bootstrap_vegetation_dataset.py` |
| 元数据 | `AI/datasets/vegetation_v1/metadata.csv` |
| 来源说明 | `AI/datasets/vegetation_v1/sources/bootstrap_source.md` |

## 数据规模

| 划分 | 图片数 | 标注状态 |
| --- | ---: | --- |
| train | 8 | pseudo_label |
| val | 2 | pseudo_label |
| test | 2 | pseudo_label |

## 类别设置

当前 bootstrap 模型只训练一个类别：

```text
0 tree
```

正式数据集计划保留更完整类别表：

```text
0 tree
1 grass
2 bare_land
3 other
```

## 适用范围

可以用于：

- 验证 YOLO 分割训练流程。
- 验证数据目录和标注格式是否可用。
- 产出初版权重，接入 API/Web demo。
- 作为 8 月阶段“模型训练链路跑通”的证据。

不能用于：

- 证明森林专用模型已经可靠。
- 作为论文正式精度。
- 直接支撑树种识别、病虫害识别等细分结论。

## 已完成检查

已使用数据集检查脚本通过严格检查：

```powershell
.\.venv\Scripts\python.exe .\AI\dataset_check.py --data .\AI\config\vegetation_bootstrap_tree.yaml --strict
```

检查内容包括：

- 图片和标签是否一一对应。
- 类别 ID 是否越界。
- YOLO 分割坐标是否有效。
- train/val/test 是否可被训练程序读取。

## 后续替换要求

进入正式模型训练前，需要用真实数据替换当前 bootstrap 数据：

1. 收集校园或公开森林图片。
2. 对树冠/植被区域进行人工标注。
3. 形成固定 train/val/test 划分。
4. 重新运行数据集检查。
5. 使用同一训练脚本训练正式模型。

