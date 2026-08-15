# Forest-AI-Lab

# 基于无人机航拍图像的空地一体化森林碳汇监测系统

## 项目简介

本项目面向森林碳汇监测需求，设计一种融合无人机遥感、人工智能图像分析和地面环境感知的低成本监测系统。

项目通过无人机获取植被图像，利用AI模型完成植被识别与面积分析，并结合地面传感数据实现森林碳汇估算与可视化展示。

## 技术路线

```text
无人机航拍 → 图像处理 → AI植被识别 → 面积计算
                                         ↓
地面环境感知 → 空地数据融合 ─────────→ 碳汇估算 → Web系统展示
```

## 项目结构

- `AI`：人工智能算法与模型
- `STM32`：地面监测终端
- `Web`：系统展示平台
- `docs`：项目文档

## 团队

- 负责人：王思丹
- 成员：刘韵诗、梅族子

## AI第一阶段成果

- [x] Python、PyTorch、OpenCV和Ultralytics环境
- [x] 通用YOLO图片及摄像头视觉Demo
- [x] RGB绿色植被覆盖率流程基线
- [x] 数据集质量与跨集合泄漏检查
- [x] 分割模型训练、验证和预测入口
- [x] 实验台账、技术路线、接口协议和阶段验收材料
- [ ] 真实航拍数据集准备与标注
- [ ] 项目专用分割模型训练与独立测试

AI阶段资料位于 `docs/`；数据集交付规范位于 `AI/datasets/README.md`。

## AI环境安装

```powershell
py -V:3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\AI\requirements-ai.txt
python -m pip check
```

## 运行基础视觉Demo

```powershell
python .\AI\detect_image.py tree.png
python .\AI\detect_camera.py
```

摄像头窗口按小写 `q` 退出，也可在终端按 `Ctrl+C`。

## 运行森林主题植被流程基线

```powershell
python .\AI\vegetation_baseline.py tree.png --name EXP-20260815-01
```

该程序使用RGB Excess Green（ExG）验证植被提取和覆盖率统计流程，不是最终训练模型，不能代替标准NDVI。当前测试图片为插画，仅作为流程验证；正式论文实验必须使用真实航拍图、人工标注和独立测试集。

## 数据集到位后的标准流程

```powershell
python .\AI\dataset_check.py --data .\AI\config\vegetation_v1.yaml --strict
python .\AI\train_segmentation.py --data .\AI\config\vegetation_v1.yaml --device cpu --name EXP-YYYYMMDD-SEG-V1
python .\AI\evaluate_segmentation.py --model .\AI\runs\segment\EXP-YYYYMMDD-SEG-V1\weights\best.pt --split test
```

当前电脑使用CPU版PyTorch，正式训练建议使用NVIDIA GPU，并在实验记录中保存依赖、设备、随机种子和完整参数。

## 项目后续进度

- [ ] STM32采集模块
- [ ] 空地数据融合
- [ ] Web系统正式集成
- [ ] 论文实验与投稿
- [ ] 软件著作权和专利材料
- [ ] 项目结题
