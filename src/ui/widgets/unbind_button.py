# -*- coding: utf-8 -*-
"""
红色叉形按钮组件
===============
支持长按拖动的红色叉形样式按钮

主要功能：
    - 显示红色叉形图标
    - 支持长按拖动触发
    - 提供视觉反馈（悬停、按下状态）
    - 状态相关的动态提示文本
"""
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QThread
from PyQt5.QtGui import QMouseEvent, QPainter, QPen, QColor, QIcon, QPixmap
from src.config import config


class UnbindButton(QPushButton):
    """
    红色叉形按钮控件
    
    信号：
        released_at: 拖动释放时触发，参数为屏幕坐标(x, y)
    """
    
    released_at = pyqtSignal(int, int)

    def __init__(self, parent=None):
        """
        初始化红色叉形按钮
        """
        super().__init__(parent)
        
        btn_size = config.ui_sizes["unbind_btn"]
        self.setFixedSize(*btn_size)
        self.setCursor(Qt.PointingHandCursor)
        
        self._tooltip_disabled = config.get_tooltip("unbind_disabled") or "未绑定窗口，无法解绑"
        self._tooltip_enabled = config.get_tooltip("unbind_enabled") or "点击解绑已绑定的窗口"
        
        self.setToolTip(self._tooltip_disabled)
        
        self.is_dragging = False
        self.drag_start_pos = None
        self.drag_threshold = 10
        self._is_running = False
        
        self._draw_icon()
    
    def set_enabled_state(self, enabled: bool):
        """
        设置启用状态并更新提示文本
        
        参数：
            enabled: 是否启用按钮
        """
        self.setEnabled(enabled)
        if enabled:
            self.setToolTip(self._tooltip_enabled)
        else:
            self.setToolTip(self._tooltip_disabled)
    
    def set_running(self, running: bool):
        """
        设置运行状态（显示警告色）
        
        参数：
            running: 是否正在运行脚本
        """
        self._is_running = running
        if running:
            self._draw_icon_running()
            self.setToolTip("脚本运行中，点击将停止脚本并解绑窗口")
        else:
            self._draw_icon()

    def _draw_icon(self):
        """
        绘制红色叉形图标
        """
        if QThread.currentThread() != self.thread():
            return
        
        btn_size = config.ui_sizes["unbind_btn"]
        pixmap = QPixmap(*btn_size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        if not painter.isActive():
            return
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen(QColor(209, 52, 56), 3)
        painter.setPen(pen)
        
        w, h = btn_size
        margin = int(w * 0.2)
        painter.drawLine(margin, margin, w - margin, h - margin)
        painter.drawLine(w - margin, margin, margin, h - margin)
        
        painter.end()
        
        self.setIcon(QIcon(pixmap))
        self.setIconSize(QSize(*btn_size))
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(209, 52, 56, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(209, 52, 56, 0.2);
            }
        """)
    
    def _draw_icon_running(self):
        """
        绘制运行状态的红色叉形图标（警告色，橙色边框）
        """
        if QThread.currentThread() != self.thread():
            return
        
        btn_size = config.ui_sizes["unbind_btn"]
        pixmap = QPixmap(*btn_size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        if not painter.isActive():
            return
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen(QColor(255, 140, 0), 3)
        painter.setPen(pen)
        
        w, h = btn_size
        margin = int(w * 0.2)
        painter.drawLine(margin, margin, w - margin, h - margin)
        painter.drawLine(w - margin, margin, margin, h - margin)
        
        painter.end()
        
        self.setIcon(QIcon(pixmap))
        self.setIconSize(QSize(*btn_size))
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 140, 0, 0.1);
                border: 1px solid rgba(255, 140, 0, 0.5);
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 140, 0, 0.2);
            }
            QPushButton:pressed {
                background-color: rgba(255, 140, 0, 0.3);
            }
        """)

    def mousePressEvent(self, event: QMouseEvent):
        """
        鼠标按下事件
        
        参数：
            event: 鼠标事件对象
        """
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
            self.is_dragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """
        鼠标移动事件
        
        参数：
            event: 鼠标事件对象
        """
        if self.drag_start_pos is not None:
            distance = (event.pos() - self.drag_start_pos).manhattanLength()
            if distance > self.drag_threshold:
                self.is_dragging = True
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        鼠标释放事件
        
        参数：
            event: 鼠标事件对象
        """
        if event.button() == Qt.LeftButton:
            if self.is_dragging:
                global_pos = self.mapToGlobal(event.pos())
                self.released_at.emit(global_pos.x(), global_pos.y())
            else:
                self.click()
            self.is_dragging = False
            self.drag_start_pos = None
        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        """鼠标进入事件：更新图标为高亮状态"""
        self._draw_icon_hover()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开事件：恢复默认图标"""
        self._draw_icon()
        super().leaveEvent(event)

    def _draw_icon_hover(self):
        """
        绘制悬停状态的红色叉形图标
        """
        if QThread.currentThread() != self.thread():
            return
        
        btn_size = config.ui_sizes["unbind_btn"]
        pixmap = QPixmap(*btn_size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        if not painter.isActive():
            return
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen(QColor(180, 40, 44), 3)
        painter.setPen(pen)
        
        w, h = btn_size
        margin = int(w * 0.2)
        painter.drawLine(margin, margin, w - margin, h - margin)
        painter.drawLine(w - margin, margin, margin, h - margin)
        
        painter.end()
        
        self.setIcon(QIcon(pixmap))
        self.setIconSize(QSize(*btn_size))
