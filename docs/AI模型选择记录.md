# AI 模型选择记录

## 当前可用模型

| 模型 | 来源 | 状态 | 是否接入 Demo |
| --- | --- | --- | --- |
| 通用 YOLO26n | `AI/weights/yolo26n.pt` | 通用目标检测，可兜底 | 回退模型 |
| Bootstrap tree segmentation | `EXP-20260902-BOOTSTRAP-TREE-SEG-V1` | 展示相对稳定，已接入 API | 是 |
| Public tree segmentation Alpha | `EXP-20260902-PUBLIC-TREE-SEG-ALPHA` | 已完成训练，但测试指标偏低 | 暂不接入 |
| Review subset tree segmentation Alpha | `EXP-20260902-REVIEW-SUBSET-TREE-SEG-ALPHA` | 筛选样本后指标提升，但测试集太小且仍为伪标注 | 暂不接入 |
| Auto refined tree segmentation Alpha V0.2 | `EXP-20260902-AUTO-REFINED-TREE-SEG-ALPHA-V02` | 自动修标外观更干净，但测试指标未提升 | 暂不接入 |
| Human reviewed seed Alpha V0.3 | `EXP-20260902-HUMAN-REVIEWED-SEED-TREE-SEG-ALPHA-V03` | 人工审核种子集完成，但未逐点精修，测试指标不足 | 暂不接入 |

## 当前选择

当前 Demo 主模型继续使用：

```text
AI/runs/segment/EXP-20260902-BOOTSTRAP-TREE-SEG-V1/weights/best.pt
```

原因：

1. 已完成 API 接入验证。
2. Demo 展示更稳定。
3. Public Alpha 模型虽然数据来源更丰富，但伪标注质量不足，测试指标偏低。
4. Review subset 模型证明筛选样本有效，但还未达到稳定替换条件。
5. Auto refined V0.2 不能替代人工修标，暂不作为主模型。
6. Human reviewed seed V0.3 说明仅筛选样本仍不够，下一步需要真实人工多边形修标。

## 后续替换条件

只有当新模型满足以下条件时，才替换 Demo 主模型：

1. 使用真实图片或人工检查标注。
2. 数据集检查通过。
3. 测试集 Mask mAP50 和预测可视化明显优于当前模型。
4. Web/API 上传图片验证通过。
5. 实验记录和 GitHub 提交同步完成。
