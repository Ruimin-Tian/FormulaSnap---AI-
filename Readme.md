# FormulaSnap - 数学公式截图识别工具

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)
![License](https://img.shields.io/badge/License-MIT-orange.svg)

FormulaSnap 是一款基于 PyQt5 和 Kimi API 的数学公式截图识别工具，能够将屏幕上的数学公式转换为 LaTeX 代码。

## 功能特性

- 🖥️ 全屏截图功能，支持选区截图
- ✨ 高DPI屏幕适配
- 🔥 双热键支持 (Ctrl+Alt+S 或 Ctrl+Alt+Q)
- 📋 自动复制识别结果到剪贴板
- 🧠 基于 Kimi AI 的精准公式识别
- 📁 自动保存截图到 screenshots 文件夹

## 安装与使用

### 依赖安装

```bash
pip install pyqt5 keyboard pillow numpy requests
```

### 运行程序

```bash
python formula_snap.py
```

### 使用方法

1. 按下 `Ctrl+Alt+S` 或 `Ctrl+Alt+Q` 启动截图工具
2. 鼠标拖选需要识别的公式区域
3. 释放鼠标自动识别
4. 结果窗口显示 LaTeX 代码并可复制

## 配置说明

在代码中修改以下配置：

```python
# Kimi API 配置
KIMI_API_KEY = "sk-your-api-key-here"  # 替换为你的Kimi API密钥
```

## 常见问题

### 识别失败可能原因

1. 截图区域太小（建议宽度≥500像素）
2. 公式字体太小（建议≥14pt）
3. 背景对比度不足
4. 截图包含非公式内容
5. Kimi API 密钥无效或配额不足

### 热键无效解决方案

1. 以管理员权限运行程序
2. 检查热键是否被其他程序占用
3. 尝试备用热键 `Ctrl+Alt+Q`

## 开发说明

- 主程序类: `FormulaSnapApp`
- 截图窗口: `ScreenshotWindow`
- 结果窗口: `ResultWindow`
- 日志系统: Python `logging` 模块

## 许可证

MIT License

## 支持与反馈

如有任何问题或建议，请联系: 19947645815@163.com

---

> 提示：为了获得最佳识别效果，请确保公式清晰、背景对比度高，并仅截取公式区域。