# AI模块接口协议 V0.1

## 目的

本协议定义负责人AI模块与成员B的Web/系统模块之间的边界。当前通用检测接口继续保留；项目专用植被分割接口在模型V1训练完成后实现。

## 图像分析请求

- 方法：`POST`
- 建议路径：`/api/vegetation/analyze`
- 数据：`multipart/form-data`
- 字段：`file`（JPG、PNG或TIFF）、`site_id`、`captured_at`、`flight_id`。

## 标准响应

```json
{
  "analysis_id": "EXP-20260901-001",
  "model_version": "vegetation-seg-v1.0",
  "site_id": "campus-plot-01",
  "captured_at": "2026-09-01T08:30:00+08:00",
  "image": {"width": 1920, "height": 1080},
  "coverage": {
    "tree_pct": 42.1,
    "grass_pct": 31.4,
    "bare_land_pct": 12.7,
    "other_pct": 13.8,
    "vegetation_total_pct": 73.5
  },
  "inference_ms": 58.2,
  "mask_url": "/results/example-mask.png",
  "overlay_url": "/results/example-overlay.jpg",
  "warnings": []
}
```

## 错误约定

- `400`：图片损坏、缺少必需元数据。
- `413`：文件过大。
- `415`：文件格式不支持。
- `422`：字段格式或取值不合法。
- `500`：模型或结果保存失败。

错误响应统一包含 `detail` 和可选的 `error_code`。成员B不得依赖程序内部文件路径，只使用响应中的URL和字段。

## 版本原则

- 接口增加字段可以保持兼容；删除或重命名字段必须提升主版本号。
- 每个结果必须返回模型版本和分析编号。
- 百分比范围为 `0—100`，时间统一使用带时区的ISO 8601格式。
- 正式联调前由负责人和成员B共同确认一组固定测试样例。
