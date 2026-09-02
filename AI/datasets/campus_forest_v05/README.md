# campus_forest_v05 数据集准备位

## 用途

本目录用于承接 9 月后续真实校园/森林图片，目标是训练 Alpha V0.5。

当前目录只提交规范、模板和空目录，不提交真实图片和标注文件，避免仓库过大。

## 目录结构

```text
campus_forest_v05/
  images/
    train/
    val/
    test/
  labels/
    train/
    val/
    test/
  classes.txt
  metadata_template.csv
  DATASET_CARD.md
  sources.md
```

## 数据进入标准

1. 图片主题必须与“林木、森林、校园绿地、植被覆盖”相关。
2. 每张图尽量包含清晰树冠、树干、林地或大面积植被。
3. 避免纯天空、纯道路、纯建筑、纯人物自拍、严重模糊图。
4. 保留不同光照、角度、距离和场景，避免全是同一种图。
5. 每张图片必须在 `metadata_template.csv` 中登记来源、拍摄/下载说明和是否可公开使用。

## 建议数量

- 起步验收：50 张。
- 较稳训练：100 张以上。
- 划分建议：train 70%、val 15%、test 15%。

## 当前检查状态

当前为“空数据集准备位”，尚未放入真实图片。因此直接运行数据集检查会提示 train/val/test 中没有图片，这是预期现象，不代表配置错误。

等数据同学提交图片并完成标注后，再运行：

```powershell
python .\AI\dataset_check.py --data .\AI\config\campus_forest_v05.yaml
```

届时应满足：无 errors，必要时只保留可解释的 warnings。

## 标注类别

当前只做一个类别：

```text
tree
```

后续如果扩展树种、病虫害或碳储量估计，需要另开数据集版本，不要直接混入本版本。
