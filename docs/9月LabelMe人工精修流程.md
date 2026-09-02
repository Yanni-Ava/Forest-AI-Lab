# 9月 LabelMe 人工精修流程

## 目的

当前 Alpha 模型已经能完成基础林木/植被识别演示，但公开图片自动生成的标注质量仍不稳定。9月下一步不是继续盲目训练，而是建立“人工修标—导回训练—再次训练—对比评估”的闭环。

本流程对应负责人王思丹的任务：AI模型优化、实验流程整理、Web联调和GitHub规范提交。

## 当前已经准备好的内容

- 可人工编辑的 LabelMe 标注任务：`AI/annotation_tasks/vegetation_alpha_v04_labelme`
- YOLO 标注转 LabelMe 工具：`AI/export_yolo_to_labelme.py`
- LabelMe 标注导回 YOLO 工具：`AI/import_labelme_to_yolo.py`
- 导回后的训练配置：`AI/config/vegetation_v2_public_human_corrected_v04.yaml`

## 人工修标怎么做

1. 打开 LabelMe。
2. 选择一个 JSON 文件，例如：`AI/annotation_tasks/vegetation_alpha_v04_labelme/train/VEG_PUBLIC_0001.json`
3. 检查多边形是否真正覆盖树木或植被区域。
4. 如果多边形偏到天空、道路、建筑、河面等位置，就手动拖点修正。
5. 如果某个标注完全错误，就删除这个形状。
6. 如果明显漏掉大块树冠或林地，就新增 polygon，标签写 `tree`。
7. 保存 JSON。

## 导回训练集

人工修完后，在项目根目录执行：

```powershell
python .\AI\import_labelme_to_yolo.py
```

导回后会生成：

```text
AI/datasets/vegetation_v2_public_human_corrected_v04
```

该目录用于下一轮训练。

## 质量检查

导回后先检查数据集结构：

```powershell
python .\AI\dataset_check.py --data .\AI\config\vegetation_v2_public_human_corrected_v04.yaml
```

确认图片、标签、类别和划分都正常后，再训练 Alpha V0.4。

## 训练建议

```powershell
yolo segment train model=AI/weights/yolo26n.pt data=AI/config/vegetation_v2_public_human_corrected_v04.yaml epochs=30 imgsz=640 batch=2 device=cpu project=AI/runs/segment name=EXP-20260902-HUMAN-CORRECTED-TREE-SEG-ALPHA-V04
```

## 验收口径

这一步的意义是：项目已经从“能跑通 Demo”进入“有数据闭环的模型优化阶段”。即使 V0.4 训练结果暂时不一定最好，也能证明项目具备持续优化能力，符合9月“AI Alpha版本开发与实验记录整理”的要求。
