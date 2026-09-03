# 0903 V0.5 数据接收工具证据

## 本次目标

将 `campus_forest_v05` 的数据接收标准从文档要求变成可执行工具，方便负责人王思丹后续验收数据模块提交的真实校园/森林图片。

## 新增工具

### 1. 批量整理工具

```text
AI/prepare_campus_image_batch.py
```

作用：

- 读取原始图片文件夹；
- 预览 train/val/test 划分数量；
- 正式执行时统一命名为 `CAMPUS_FOREST_0001.jpg` 格式；
- 自动复制到 `campus_forest_v05/images/train|val|test`；
- 自动更新 metadata 表。

测试结果：

```text
Found 3 image(s).
Planned split:
- train: 2
- val: 0
- test: 1
Preview only. Re-run with --copy to write files.
```

说明：本次只使用预览模式验证功能，没有向正式数据集写入测试图片。

### 2. 数据接收验收工具

```text
AI/validate_campus_data_intake.py
```

作用：

- 检查图片数量是否达到 50 张起步要求；
- 检查命名是否规范；
- 检查 metadata 表是否覆盖每张图片；
- 检查来源、地点/链接、授权说明是否缺失；
- 检查 train/val/test 比例是否接近 70/15/15。

当前检查结果：

```text
total_images: 0
passed_for_intake: false
```

说明：当前 `campus_forest_v05` 是空数据集准备位，尚未接收真实图片，因此未通过接收检查是预期结果。

## 负责人价值

这一步完成后，数据模块后续交图不再只靠口头判断。负责人可以用脚本快速验收数据是否能进入 V0.5 训练流程，减少“图片收了很多但不能训练”的风险。
