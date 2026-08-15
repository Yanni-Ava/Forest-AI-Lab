# AI环境配置与复现说明

## 当前验证环境

- 操作系统：Windows
- Python：3.12.10
- PyTorch：2.13.0（CPU）
- TorchVision：0.28.0
- OpenCV：5.0.0
- Ultralytics：8.4.120
- NumPy：2.4.4
- 项目虚拟环境：`D:\Forest-AI-Lab\.venv`

当前电脑使用 AMD Radeon 780M 核显，PyTorch 采用 CPU 版本。该环境适合开发、推理和小规模验证；正式分割模型训练建议使用实验室或云端 NVIDIA GPU，并在实验记录中单独记录训练设备。

## 安装与验证

在项目根目录执行：

```powershell
py -V:3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\AI\requirements-ai.txt
python --version
python -m pip --version
python -c "import torch, cv2, ultralytics; print(torch.__version__, cv2.__version__, ultralytics.__version__)"
```

若 PowerShell 阻止激活脚本，可对当前终端临时执行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 已验证功能

- 通用YOLO图片目标检测。
- 电脑摄像头实时检测。
- RGB绿色植被覆盖率基线程序。

## 复现原则

1. 每次实验记录Python、模型、依赖、设备和随机种子。
2. 训练权重与大数据集不提交Git，记录其文件哈希和保存位置。
3. 不覆盖旧实验目录；每次实验使用唯一编号。
4. 论文图表必须能追溯到具体实验目录和指标文件。
