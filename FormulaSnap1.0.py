import sys
import base64
import os
import time
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QMessageBox, 
                            QVBoxLayout, QWidget, QPushButton, QShortcut)
from PyQt5.QtCore import Qt, QRect, QPoint, QObject, pyqtSignal, QRectF, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QColor, QScreen, QKeySequence, QPainterPath
import keyboard
import logging
import platform
from PIL import Image
import numpy as np

# ==================== 配置部分 ====================
# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Kimi API 配置
KIMI_API_KEY = "sk-OFXYS6uoTqKyINHuoPoph6zBQ2yiDHoc4gRBUbNZAB1QdT6J"
KIMI_API_URL = "https://api.moonshot.cn/v1/chat/completions"

# ==================== 主程序 ====================
# 截图窗口
class ScreenshotWindow(QMainWindow):
    # 当窗口关闭时发送携带截图路径的信号
    closed = pyqtSignal(str)

    # 初始化
    def __init__(self):
        super().__init__()
        logger.info("初始化截图窗口")
        
        # 设置窗口为无边框（Qt.FramelessWindowHint）
        # 置顶（Qt.WindowStaysOnTopHint）
        # 透明背景（Qt.WA_TranslucentBackground）
        # 全屏（Qt.WindowFullScreen）
        self.setWindowTitle("公式截图工具")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowState(Qt.WindowFullScreen)

        # 设置鼠标起止点
        self.begin = QPoint()
        self.end = QPoint()

        # 储存屏幕快照
        self.screenshot = None

        # 获取屏幕对象和像素缩放比，适配高DPI显示器
        self.screen = QApplication.primaryScreen()
        self.device_pixel_ratio = self.screen.devicePixelRatio()
        self.screen_geometry = self.screen.geometry()

    # 显示事件
    def showEvent(self, event):
        """在窗口显示时捕获屏幕快照"""
        try:
            if self.screen:
                self.screenshot = self.screen.grabWindow(0)
                size = self.screenshot.size()
                logger.info(f"已捕获新屏幕快照，分辨率: ({size.width()}, {size.height()}), 缩放: {self.device_pixel_ratio}")
            else:
                logger.error("无法获取屏幕对象")
                self.screenshot = QPixmap()
            self.begin = QPoint()
            self.end = QPoint()
            super().showEvent(event)
        except Exception as e:
            logger.error(f"截图窗口初始化失败: {e}")
            QMessageBox.critical(None, "错误", f"无法显示截图窗口: {str(e)}")
            self.close()

    # 绘制事件
    def paintEvent(self, event):
        """绘制半透明背景和选区框"""

        # 获取绘制区域
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 检测截图是否有效
        if self.screenshot and not self.screenshot.isNull():
            painter.drawPixmap(self.rect(), self.screenshot)
        # 如果截图无效，绘制空白背景
        else:
            logger.warning("截图无效，绘制空白背景")
            painter.fillRect(self.rect(), QColor(0, 0, 0, 150))
            return

        # 检查选区是否有效
        if not self.begin.isNull() and not self.end.isNull():
            # 绘制选区矩形框
            # 使用 normalized() 方法确保矩形坐标正确
            rect = QRect(self.begin, self.end).normalized()
            path = QPainterPath()
            # 创建遮罩路径，避免选区外的区域被遮挡
            path.addRect(QRectF(self.rect()))
            path.addRect(QRectF(rect))
            painter.setPen(Qt.NoPen)
            painter.fillPath(path, QColor(0, 0, 0, 150))
            painter.setPen(QColor(255, 0, 0, 255))
            painter.drawRect(rect)
        else:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 150))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.begin = event.pos()
            self.end = self.begin
            logger.info(f"鼠标按下: {self.begin}")
            self.update()

    def mouseMoveEvent(self, event):
        if not self.begin.isNull():
            self.end = event.pos()
            logger.debug(f"鼠标移动: {self.end}")
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.end = event.pos()
            logger.info(f"鼠标释放: {self.end}")
            if self.begin != self.end and not self.begin.isNull() and not self.end.isNull():
                try:
                    screenshot_path = self.capture_selection()
                    self.hide()
                    QApplication.processEvents()
                    QTimer.singleShot(0, lambda: self.closed.emit(screenshot_path))
                except Exception as e:
                    logger.error(f"截图保存失败: {e}")
                    QMessageBox.critical(None, "错误", f"截图无效: {str(e)}")
            else:
                logger.warning("无效选区，未保存截图")
                QMessageBox.warning(None, "提示", "请拖选有效区域完成截图")
            self.close()
            logger.info("截图窗口已关闭")

    def capture_selection(self):
        """捕获选区并保存截图"""
        try:
            rect = QRect(self.begin, self.end).normalized()
            logger.info(f"选区矩形: {rect}")
            if not self.screen_geometry.contains(rect):
                raise Exception("选区超出屏幕范围")
            if rect.width() < 10 or rect.height() < 10:
                raise Exception("选区太小，请选择更大的区域")
            scaled_rect = QRect(
                int(rect.left() * self.device_pixel_ratio),
                int(rect.top() * self.device_pixel_ratio),
                int(rect.width() * self.device_pixel_ratio),
                int(rect.height() * self.device_pixel_ratio)
            )
            logger.info(f"缩放后矩形: {scaled_rect}")
            cropped = self.screenshot.copy(scaled_rect)
            os.makedirs("screenshots", exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join("screenshots", f"formula_screenshot_{timestamp}.png")
            cropped.save(save_path, "PNG")
            with Image.open(save_path) as img:
                logger.info(f"截图尺寸: {img.size}")
                img_array = np.array(img)
                if img_array.std() < 1:
                    raise Exception("截图内容为空或全黑")
                if img.size[0] < 500:
                    logger.warning("截图宽度低于500像素，可能影响识别")
                logger.info(f"截图像素均值: {img_array.mean():.2f}, 方差: {img_array.std():.2f}")
            logger.info(f"截图已保存到: {save_path}")
            return save_path
        except Exception as e:
            logger.error(f"截图失败: {e}")
            raise

class ResultWindow(QWidget):
    def __init__(self, latex):
        super().__init__()
        self.setWindowTitle("公式识别结果")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setGeometry(300, 300, 400, 200)
        layout = QVBoxLayout()
        self.code_label = QLabel(f"LaTeX代码:\n{latex}")
        self.code_label.setStyleSheet("""
            font-family: 'Courier New', monospace;
            font-size: 12pt;
            padding: 10px;
            background-color: #f0f0f0;
            border: 1px solid #ccc;
        """)
        layout.addWidget(self.code_label)
        copy_btn = QPushButton("复制到剪贴板")
        copy_btn.setStyleSheet("""
            QPushButton {
                padding: 8px;
                font-size: 11pt;
                background-color: #4CAF50;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        copy_btn.clicked.connect(lambda: self.copy_to_clipboard(latex))
        layout.addWidget(copy_btn)
        self.setLayout(layout)

    def copy_to_clipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "成功", "LaTeX代码已复制！")

class FormulaSnapApp(QObject):
    def __init__(self):
        super().__init__()
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        self.app = QApplication(sys.argv)
        self.screenshot_window = None
        self.result_window = None
        
        self.hotkey_parent = QMainWindow()
        self.hotkey_parent.setWindowTitle("FormulaSnap")
        self.hotkey_parent.resize(1, 1)
        self.hotkey_parent.show()
        
        self.app.setApplicationName("FormulaSnap")
        self.app.setApplicationVersion("1.0")
        self.setup_hotkeys()

    def setup_hotkeys(self):
        """设置热键监听方案"""
        try:
            shortcut = QShortcut(QKeySequence("Ctrl+Alt+S"), self.hotkey_parent)
            shortcut.activated.connect(self.show_screenshot_window)
            logger.info("Qt热键注册成功 (Ctrl+Alt+S)")
            
            backup_shortcut = QShortcut(QKeySequence("Ctrl+Alt+Q"), self.hotkey_parent)
            backup_shortcut.activated.connect(self.show_screenshot_window)
            logger.info("Qt备用热键注册成功 (Ctrl+Alt+Q)")
        except Exception as e:
            logger.warning(f"Qt热键注册失败: {e}, 尝试使用keyboard库")
            try:
                keyboard.add_hotkey("ctrl+alt+s", self.show_screenshot_window)
                logger.info("keyboard热键注册成功 (Ctrl+Alt+S, 需要管理员权限)")
                keyboard.add_hotkey("ctrl+alt+q", self.show_screenshot_window)
                logger.info("keyboard备用热键注册成功 (Ctrl+Alt+Q, 需要管理员权限)")
            except Exception as e:
                logger.error(f"所有热键方案均失败: {e}")
                QMessageBox.critical(None, "错误", 
                    "无法注册热键！\n"
                    "可能原因：\n"
                    "1. 请以管理员权限运行程序\n"
                    "2. 热键已被其他程序占用\n"
                    "3. 系统不支持全局热键\n"
                    "请尝试使用 Ctrl+Alt+Q 或检查其他程序"
                )

    def show_screenshot_window(self):
        """显示截图窗口"""
        logger.info("热键被触发")
        try:
            if self.screenshot_window is None:
                logger.info("正在创建截图窗口")
                self.screenshot_window = ScreenshotWindow()
                self.screenshot_window.closed.connect(self.process_screenshot)
                logger.info("正在显示截图窗口")
                self.screenshot_window.show()
                self.screenshot_window.raise_()
                self.screenshot_window.activateWindow()
                logger.info("截图窗口已显示")
            else:
                logger.warning("截图窗口已存在，忽略重复触发")
        except Exception as e:
            logger.error(f"显示截图窗口失败: {e}", exc_info=True)
            self.screenshot_window = None
            QMessageBox.critical(None, "错误", f"无法启动截图工具: {str(e)}")

    def process_screenshot(self, screenshot_path):
        """处理截图并识别公式"""
        try:
            if os.path.exists(screenshot_path):
                latex = self.recognize_formula(screenshot_path)
                self.show_result(latex)
            else:
                logger.warning("未找到截图文件")
                raise Exception("截图文件不存在")
        except Exception as e:
            logger.error(f"处理截图失败: {e}")
            QMessageBox.critical(None, "错误", f"公式识别失败: {str(e)}")
        finally:
            self.screenshot_window = None

    def recognize_formula(self, image_path):
        """调用 Kimi API 识别公式"""
        try:
            with Image.open(image_path) as img:
                if img.size[0] * img.size[1] < 100:
                    raise Exception("截图尺寸太小")
                img_array = np.array(img)
                if img_array.std() < 1:
                    raise Exception("截图内容为空或全黑")
                if img.size[0] < 500:
                    logger.warning("截图宽度低于500像素，可能影响识别")
                logger.info(f"截图尺寸: {img.size}, 像素均值: {img_array.mean():.2f}, 方差: {img_array.std():.2f}")
            
            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")
            logger.info(f"图片base64长度: {len(img_b64)}")
            if len(img_b64) < 1000:
                raise Exception("图片base64编码过短，可能无效")
            if len(img_b64) > 1000000:
                raise Exception("图片base64编码过长，Kimi API 可能不支持")
            
            headers = {
                "Authorization": f"Bearer {KIMI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "moonshot-v1-8k-vision-preview",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "你是 Kimi，由 Moonshot AI 提供的人工智能助手，擅长处理数学任务。"
                            "任务：仅识别图像中的数学公式，输出纯 LaTeX 代码（例如 \\frac{a}{b}、\\sum 等），"
                            "不包含 \\documentclass、\\begin{document}、\\text、注释、链接或任何非公式内容。"
                            "支持分数、上下标、多行公式等复杂结构。"
                            "若图像无公式或无法识别，返回空字符串。"
                        )
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_b64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": (
                                    "提取图像中的数学公式（如分数、上下标），返回纯 LaTeX 代码，无包装或文本。"
                                    "若无公式，返回空字符串。"
                                )
                            }
                        ]
                    }
                ],
                "temperature": 0.3
            }
            logger.info(f"发送 Kimi API 请求...")
            response = requests.post(KIMI_API_URL, json=payload, headers=headers, timeout=30)
            try:
                response.raise_for_status()
            except requests.HTTPError as e:
                logger.error(f"Kimi API 响应: {response.text}")
                raise
            result = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            logger.info(f"Kimi识别结果: {result}")
            
            if not result:
                logger.warning("Kimi识别结果为空，可能图像不含公式或无法识别")
                return ""
            if (
                any(c in result for c in ["\\frac", "^", "_", "\\sum", "\\int"]) and
                not any(w in result.lower() for w in ["http", "reference", "moonshot", "text", "sorry"]) and
                "\\text" not in result
            ):
                if len(result) < 30 or result in ["\\frac{a}{b}", "\\frac{x}{y}", "x^2"]:
                    logger.warning("Kimi识别结果过于简单，可能误识别")
                    return ""
                logger.info("Kimi识别结果为LaTeX公式")
                return result
            logger.warning(f"Kimi识别结果无效，可能是非公式内容: {result}")
            return ""
        except Exception as e:
            logger.error(f"Kimi API调用失败: {e}")
            raise Exception(
                f"识别服务错误: {str(e)}\n"
                "可能原因：\n"
                "- Kimi API 密钥无效或无图像权限，请确认。\n"
                "- 公式图像被内容审查拒绝，请确保公式清晰、无无关内容。\n"
                "- 网络连接问题，请重试。\n"
                "建议：\n"
                "- 公式字体>=14pt，截图宽度>=500像素，背景对比度高。\n"
                "- 仅截取公式区域，避免文字或链接。\n"
                "- 测试简单公式（如 x^2+y^2=1）确认问题。\n"
                "- 联系支持：support@moonshot.cn"
            )

    def show_result(self, latex):
        """显示识别结果窗口"""
        if not latex:
            message = (
                "未识别到公式，可能公式太复杂、图像不清晰或被Kimi审查拒绝。\n"
                "建议：\n"
                "- 确保公式字体>=14pt，截图宽度>=500像素，背景对比度高。\n"
                "- 仅截取公式区域，避免无关内容。\n"
                "- 测试简单公式（如 x^2+y^2=1）。\n"
                "- 联系支持：support@moonshot.cn"
            )
        else:
            message = latex
        self.result_window = ResultWindow(message)
        self.result_window.show()

def main():
    try:
        if not KIMI_API_KEY:
            raise Exception("请配置有效的 Kimi API 密钥")
        app = FormulaSnapApp()
        logger.info("程序启动成功，使用Ctrl+Alt+S或Ctrl+Alt+Q截图")
        sys.exit(app.app.exec_())
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        QMessageBox.critical(None, "致命错误", 
            f"程序无法启动:\n{str(e)}\n\n"
            "可能原因：\n"
            "1. 缺少依赖库 (pip install pyqt5 keyboard pillow numpy requests)\n"
            "2. 系统不兼容\n"
            "3. Kimi 密钥未配置"
        )

if __name__ == "__main__":
    main()