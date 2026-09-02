# 8月阶段验收证据包

本目录用于集中保存 8 月 AI 模块阶段验收可直接展示的证据材料。

## 证据清单

| 文件 | 证明内容 |
| --- | --- |
| `vegetation_overlay_EXP-20260815-01.jpg` | RGB 植被覆盖率流程已能生成覆盖区域叠加图 |
| `vegetation_mask_EXP-20260815-01.png` | RGB 植被覆盖率流程已能生成二值掩膜 |
| `api_demo_result_latest.jpg` | API/Web demo 能输出识别结果图 |
| `bootstrap_tree_confusion_matrix.png` | bootstrap 分割模型已完成测试集评估 |
| `bootstrap_tree_mask_pr_curve.png` | bootstrap 分割模型已生成 Mask PR 曲线 |
| `bootstrap_tree_val_prediction.jpg` | bootstrap 分割模型已输出预测可视化 |

## 8月验收口径

可表述为：

> 8 月已完成 AI 模块 V1：图片输入、基础识别、植被覆盖率分析、结果保存、API 接口和 Web 展示链路均已跑通；同时完成 bootstrap 分割训练流程验证，产出初版权重并接入 demo。

不建议表述为：

> 已完成可靠森林专用识别模型。

原因：当前训练数据仍是 bootstrap 伪标注数据，正式论文指标需要真实图片和人工标注数据支撑。

