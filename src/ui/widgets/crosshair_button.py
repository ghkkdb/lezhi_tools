# -*- coding: utf-8 -*-
"""
瞄准镜按钮组件
==============
支持长按拖动的瞄准镜样式按钮

主要功能：
    - 显示瞄准镜样式的图标
    - 支持长按拖动到目标位置后释放触发识别
    - 提供视觉反馈（悬停、按下状态）
    - 状态相关的动态提示文本
"""
from PyQt5.QtWidgets import QPushButton, QToolTip
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QThread
from PyQt5.QtGui import QMouseEvent, QPainter, QPen, QColor, QIcon, QPixmap
from src.config import config


class CrosshairButton(QPushButton):
    """
    瞄准镜样式按钮控件
    
    信号：
        released_at: 拖动释放时触发，参数为屏幕坐标(x, y)
    """
    
    released_at = pyqtSignal(int, int)

    def __init__(self, parent=None):
        """
        初始化瞄准镜按钮
        """
        super().__init__(parent)
        
        self.setFixedSize(30, 30)
        self._tooltip_idle = config.get_tooltip("pick_idle") or "长按拖动到游戏窗口释放"
        self._tooltip_bound = config.get_tooltip("pick_bound") or "已绑定窗口，点击解绑后可重新选择"
        self._tooltip_dragging = config.get_tooltip("pick_dragging") or "拖动到目标窗口后释放"
        self._is_bound = False
        self.setToolTip(self._tooltip_idle)
        
        self.is_dragging = False
        self.drag_start_pos = None
        self.drag_threshold = 10
        
        self._draw_crosshair()
    
    def set_bound_state(self, bound: bool):
        """
        设置绑定状态并更新提示文本
        
        参数：
            bound: 是否已绑定窗口
        """
        self._is_bound = bound
        if bound:
            self.setToolTip(self._tooltip_bound)
        else:
            self.setToolTip(self._tooltip_idle)
    
    def set_disabled(self, disabled: bool):
        """
        设置按钮禁用状态
        
        参数：
            disabled: 是否禁用按钮
        """
        self.setEnabled(not disabled)
        if disabled:
            self._draw_crosshair_disabled()
        else:
            self._draw_crosshair()

    def _draw_crosshair(self):
        """
        绘制瞄准镜样式的图标（30x30像素）- 现代风格
        """
        if QThread.currentThread() != self.thread():
            return
        
        pixmap = QPixmap(30, 30)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        if not painter.isActive():
            return
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen(QColor(0, 120, 215), 2)
        painter.setPen(pen)
        
        center_x = 15
        center_y = 15
        radius = 10
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        
        painter.drawLine(2, center_y, center_x - 4, center_y)
        painter.drawLine(center_x + 4, center_y, 28, center_y)
        painter.drawLine(center_x, 2, center_x, center_y - 4)
        painter.drawLine(center_x, center_y + 4, center_x, 28)
        
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawPoint(center_x, center_y)
        
        painter.end()
        
        self.setIcon(QIcon(pixmap))
        self.setIconSize(QSize(30, 30))
    
    def _draw_crosshair_disabled(self):
        """
        绘制禁用状态的瞄准镜图标（灰色）
        """
        if QThread.currentThread() != self.thread():
            return
        
        pixmap = QPixmap(30, 30)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        if not painter.isActive():
            return
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen(QColor(128, 128, 128), 2)
        painter.setPen(pen)
        
        center_x = 15
        center_y = 15
        radius = 10
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        
        painter.drawLine(2, center_y, center_x - 4, center_y)
        painter.drawLine(center_x + 4, center_y, 28, center_y)
        painter.drawLine(center_x, 2, center_x, center_y - 4)
        painter.drawLine(center_x, center_y + 4, center_x, 28)
        
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawPoint(center_x, center_y)
        
        painter.end()
        
        self.setIcon(QIcon(pixmap))
        self.setIconSize(QSize(30, 30))

    def mousePressEvent(self, event: QMouseEvent):
        """
        鼠标按下事件
        
        参数：
            event: 鼠标事件对象
        """
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
            self.is_dragging = False
            self.setCursor(Qt.CrossCursor)
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
                if not self.is_dragging:
                    self.is_dragging = True
                global_pos = self.mapToGlobal(event.pos())
                QToolTip.showText(global_pos, self._tooltip_dragging)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        鼠标释放事件
        
        参数：
            event: 鼠标事件对象
        """
        if event.button() == Qt.LeftButton:
            QToolTip.hideText()
            if not self.isEnabled():
                self.is_dragging = False
                self.drag_start_pos = None
                self.unsetCursor()
                return
            if self.is_dragging:
                global_pos = self.mapToGlobal(event.pos())
                self.released_at.emit(global_pos.x(), global_pos.y())
            self.is_dragging = False
            self.drag_start_pos = None
            self.unsetCursor()
            if self._is_bound:
                self.setToolTip(self._tooltip_bound)
            else:
                self.setToolTip(self._tooltip_idle)
        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        """鼠标进入事件：更新图标为高亮状态"""
        self._draw_crosshair_hover()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开事件：恢复默认图标"""
        self._draw_crosshair()
        super().leaveEvent(event)

    def _draw_crosshair_hover(self):
        """
        绘制悬停状态的瞄准镜图标（高亮颜色）- 现代风格
        """
        if QThread.currentThread() != self.thread():
            return
        
        pixmap = QPixmap(30, 30)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        if not painter.isActive():
            return
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen(QColor(0, 100, 180), 2)
        painter.setPen(pen)
        
        center_x = 15
        center_y = 15
        radius = 10
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        
        painter.drawLine(2, center_y, center_x - 4, center_y)
        painter.drawLine(center_x + 4, center_y, 28, center_y)
        painter.drawLine(center_x, 2, center_x, center_y - 4)
        painter.drawLine(center_x, center_y + 4, center_x, 28)
        
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawPoint(center_x, center_y)
        
        painter.end()
        
        self.setIcon(QIcon(pixmap))
        self.setIconSize(QSize(30, 30))
