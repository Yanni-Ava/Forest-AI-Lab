# 2026-09-02 标注质量检查证据

本目录保存 `vegetation_v2_public` 的伪标注可视化检查材料。

## 文件

| 文件 | 内容 |
| --- | --- |
| `vegetation_v2_public_label_contact_sheet.jpg` | 18 张公开森林图片伪标注总览图 |
| `vegetation_v2_public_review_index.csv` | 自动生成的标注检查索引 |

## 检查结论

公开森林图片数据集可以继续作为 Alpha 阶段训练基础，但当前伪标注不能直接作为正式论文数据。

主要问题：

- 雾天/天空区域容易被误标。
- 部分航拍图裸地边界粗糙。
- 自动阈值生成的多边形需要人工检查。

优先人工修标样例见：

```text
AI/datasets/vegetation_v2_public/manual_review_v0.1.csv
```

人工标注规范见：

```text
docs/9月人工标注规范.md
```

