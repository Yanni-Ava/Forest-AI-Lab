# vegetation_v2_public 数据集说明卡

## 定位

`vegetation_v2_public` 是 9 月 AI Alpha 阶段的数据集版本。

它使用公开森林图片作为来源，并通过 ExG/Otsu 自动生成伪标注，用于训练比 8 月 bootstrap 模型更接近真实场景的树木/植被分割模型。

## 当前用途

可以用于：

- Alpha 阶段模型训练。
- 比较 bootstrap 数据和公开森林数据训练效果。
- 形成 GitHub 可追踪的数据集来源说明。
- 支撑阶段汇报中的“模型优化已推进”。

不能用于：

- 直接作为论文最终数据集。
- 证明模型已经达到可靠应用精度。
- 代替人工标注。

## 数据与标注

| 项目 | 内容 |
| --- | --- |
| 数据来源 | Wikimedia Commons 公开森林图片 |
| 标注方式 | RGB ExG + Otsu 自动伪标注 |
| 类别 | `tree` |
| 配置文件 | `AI/config/vegetation_v2_public_tree.yaml` |
| 来源说明 | `sources/public_sources.md` |
| 元数据 | `metadata.csv` |

## 后续要求

1. 替换或补充校园/实地采集图片。
2. 对伪标注结果进行人工检查。
3. 保留固定 train/val/test 划分。
4. 重新训练正式 Alpha/Beta 模型。

