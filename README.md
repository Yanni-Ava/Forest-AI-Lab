# Forest-AI-Lab

本项目包含本地 YOLO26 视觉识别模块、FastAPI 接口和 Vue 3 前端。

## 已实现功能

- 单张图片命令行检测：`AI/detect_image.py`
- 电脑摄像头实时检测：`AI/detect_camera.py`
- 图片上传识别 API：`AI/api_server.py`
- Vue 图片上传、浏览器摄像头拍照识别与结果展示：`Web/`（后续展示主线）
- RGB绿色植被覆盖率流程基线：`AI/vegetation_baseline.py`

AI阶段资料位于 `docs/`，包括环境配置、技术路线、实验记录模板与阶段验收记录。植被数据集交付规范位于 `AI/datasets/README.md`。

阶段材料：

- `docs/阶段验收记录_0815.md`：AI环境与基础视觉Demo验收。
- `docs/阶段验收记录_0831.md`：8月图片识别流程与AI模块V1整合验收。
- `docs/9月AI实验推进计划.md`：9月数据集、批量实验和模型优化计划。
- `docs/9月AI Alpha开发记录.md`：9月 AI Alpha Demo 开发与联调记录。
- `docs/9月负责人任务清单.md`：负责人 9 月任务拆解与完成状态。
- `docs/9月2日负责人工作记录.md`：2026-09-02 当日推进记录。
- `docs/AI模型选择记录.md`：记录当前 Demo 主模型选择和模型替换条件。
- `docs/9月模型对比阶段结论.md`：汇总多版模型训练效果和当前选择原因。
- `docs/9月人工标注规范.md`：公开森林图和后续校园图的人工修标标准。
- `docs/9月LabelMe人工精修流程.md`：LabelMe 人工修标、导回训练集和 Alpha V0.4 训练流程。
- `docs/9月数据接收与验收标准.md`：数据同学提交图片后的负责人验收标准。
- `docs/9月数据同学对接消息模板.md`：给数据模块同学的对接话术。
- `docs/9月负责人阶段验收汇总.md`：负责人9月阶段可验收成果汇总。
- `docs/9月负责人汇报口径.md`：面向老师/队友的阶段汇报话术。
- `docs/experiments/EXP-20260902-AUTO-REFINED-TREE-SEG-ALPHA-V02.md`：自动修标 Alpha V0.2 训练实验记录。
- `docs/experiments/EXP-20260902-HUMAN-REVIEWED-SEED-TREE-SEG-ALPHA-V03.md`：人工审核种子集 Alpha V0.3 训练实验记录。
- `docs/experiments/EXP-20260902-HUMAN-CORRECTED-TREE-SEG-ALPHA-V04.md`：LabelMe 修标导回后的 Alpha V0.4 训练实验记录。
- `docs/Web展示主线说明_V0.1.md`：明确 Vue + FastAPI 为后续系统展示主线。
- `STM32/docs/sensor_data_protocol_v0.1.md`：地面传感器模拟数据协议。
- `AI/experiment_registry.csv`：实验总台账。

AI模块V1工具：

- `AI/dataset_check.py`：检查数据损坏、漏标、类别/坐标错误和跨集合重复。
- `AI/train_segmentation.py`：训练植被分割基线。
- `AI/evaluate_segmentation.py`：在验证集或独立测试集导出指标。
- `AI/predict_segmentation.py`：使用训练权重完成图片、视频或摄像头推理。
- `AI/run_batch_experiment.py`：批量生成检测结果、植被覆盖率和实验汇总。
- `AI/create_bootstrap_vegetation_dataset.py`：在真实标注不足时生成伪标注数据，用于训练流程验证。
- `AI/export_yolo_to_labelme.py`：将 YOLO 分割标注导出为 LabelMe 可人工编辑任务。
- `AI/import_labelme_to_yolo.py`：将人工修正后的 LabelMe 标注导回 YOLO 训练集。
- `AI/visualize_labelme_tasks.py`：生成 LabelMe 修标任务总览图，便于快速检查。
- `AI/experiment_registry.csv`：实验总台账。

## 启动视觉 API

在项目根目录执行：

```powershell
.\.venv\Scripts\python.exe .\AI\api_server.py
```

正式网页：`http://127.0.0.1:8000`  
接口文档：`http://127.0.0.1:8000/docs`

`Web/dist` 已由 FastAPI 直接提供，因此日常使用只需启动这一条 Python 命令。

进入网页后可选择“上传图片”或“使用摄像头”。摄像头模式需要允许浏览器访问摄像头，然后点击“识别当前画面”。

本地如果存在 `AI/runs/segment/EXP-20260902-BOOTSTRAP-TREE-SEG-V1/weights/best.pt`，API 会优先使用这版 bootstrap 树木分割模型；如果不存在，则自动退回 `AI/weights/yolo26n.pt` 通用检测模型，保证 demo 仍可运行。

当前 Alpha Demo 已在图片识别结果中加入 RGB 植被覆盖率估计，并返回植被叠加图地址。

项目展示主线统一为 Vue + FastAPI。Streamlit 页面仅作为早期原型材料保留，不作为后续主线系统。

## 前端开发模式（可选）

安装 Node.js 20.19+ 或 22.12+，然后在 `Web` 目录执行：

```powershell
pnpm install
pnpm dev
```

开发网页地址：`http://127.0.0.1:5173`。修改完成后运行 `pnpm build`，正式网页会更新到 8000 端口。

## 运行图片检测

```powershell
python .\AI\detect_image.py bus.jpg
```

图片可放入 `AI/input/`，结果保存到 `AI/runs/`。

## 运行森林主题植被基线

```powershell
python .\AI\vegetation_baseline.py tree.png --name EXP-20260815-01
```

该程序使用RGB Excess Green（ExG）验证植被提取和覆盖率统计流程，不是最终训练模型，也不能代替标准NDVI。正式论文实验必须使用真实航拍图、人工标注和独立测试集。

## 数据集到位后的标准流程

```powershell
python .\AI\dataset_check.py --data .\AI\config\vegetation_v1.yaml --strict
python .\AI\train_segmentation.py --data .\AI\config\vegetation_v1.yaml --device cpu --name EXP-YYYYMMDD-SEG-V1
python .\AI\evaluate_segmentation.py --model .\AI\runs\segment\EXP-YYYYMMDD-SEG-V1\weights\best.pt --split test
```

当前电脑使用CPU版PyTorch。正式训练建议换用NVIDIA GPU环境，并在实验记录中保存依赖、设备、随机种子和完整参数。

## 运行摄像头检测

```powershell
python .\AI\detect_camera.py
```

点击摄像头窗口后按小写 `q` 退出；也可以在终端按 `Ctrl+C`。
