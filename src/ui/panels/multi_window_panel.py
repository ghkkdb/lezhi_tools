# -*- coding: utf-8 -*-
"""
多开控制面板
============
多开页只负责窗口绑定、选择已保存任务方案、独立启停和分窗口日志。
具体任务勾选与参数配置仍由“日常任务”页保存为任务方案。
"""
from typing import Callable, Dict, List, Optional, Tuple

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)
from PyQt5.QtGui import QImage, QPixmap

from src.config import config
from src.core.state_manager import ButtonState
from src.core.worker import ScriptWorker
from src.ui.panels.log_panel import LogPanel
from src.ui.widgets import UnbindButton
from src.utils.win_api import release_tracked_inputs


class WindowLogDialog(QDialog):
    """单个多开窗口的专属日志窗口。"""

    def __init__(self, title: str, colors: Dict[str, str], parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(640, 360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        self.log_panel = LogPanel(colors)
        layout.addWidget(self.log_panel)

    def append_message(self, message: str):
        self.log_panel.append_message(message)


class MultiWindowSlotPanel(QFrame):
    """一个动态窗口槽位。"""

    status_changed = pyqtSignal()
    unbound = pyqtSignal(object)

    def __init__(
        self,
        slot_index: int,
        hwnd: int,
        img,
        colors: Dict[str, str],
        unlock_callback: Optional[Callable[[int], None]] = None,
        parent=None
    ):
        super().__init__(parent)
        self.slot_index = slot_index
        self.slot_name = f"窗口{slot_index}"
        self._colors = colors
        self._worker: Optional[ScriptWorker] = None
        self._bound_hwnd: Optional[int] = hwnd
        self._button_state = ButtonState.IDLE
        self._log_dialog: Optional[WindowLogDialog] = None
        self._preview_img = img
        self._unlock_callback = unlock_callback

        self._setup_ui()

    @property
    def bound_hwnd(self) -> Optional[int]:
        return self._bound_hwnd

    @property
    def context_label(self) -> Optional[str]:
        if not self._bound_hwnd:
            return None
        return f"{self.slot_name}:{self._bound_hwnd}"

    @property
    def is_running(self) -> bool:
        return bool(self._worker and self._worker.isRunning())

    @property
    def is_bound(self) -> bool:
        return self._bound_hwnd is not None

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors['surface']};
                border: 1px solid {self._colors['border']};
                border-radius: 4px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self.title_label = QLabel(self.slot_name)
        self.title_label.setFixedWidth(54)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(
            f"font-weight: 600; color: {self._colors['text_primary']}; border: none;"
        )
        layout.addWidget(self.title_label)

        self.unbind_btn = UnbindButton()
        self.unbind_btn.set_enabled_state(True)
        self.unbind_btn.clicked.connect(self._unbind_window)
        layout.addWidget(self.unbind_btn)

        self.preview_label = QLabel("未绑定角色")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedSize(90, 30)
        self.preview_label.setStyleSheet(
            f"background-color: {self._colors['surface_elevated']}; "
            f"border: 1px solid {self._colors['border']}; border-radius: 4px; "
            f"color: {self._colors['text_secondary']}; font-size: 9pt;"
        )
        self._set_preview_image(self._preview_img)
        layout.addWidget(self.preview_label)

        self.start_btn = QPushButton("开始执行")
        self.start_btn.setFixedSize(85, 30)
        self.start_btn.clicked.connect(self._on_start_clicked)
        layout.addWidget(self.start_btn)

        self.pause_btn = QPushButton("暂停运行")
        self.pause_btn.setFixedSize(85, 30)
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self._on_pause_clicked)
        layout.addWidget(self.pause_btn)

        scheme_layout = QVBoxLayout()
        scheme_layout.setSpacing(4)
        scheme_label = QLabel("任务方案")
        scheme_label.setStyleSheet(
            f"color: {self._colors['text_secondary']}; border: none;"
        )
        self.config_combo = QComboBox()
        self.config_combo.setFixedWidth(90)
        self.refresh_config_names()
        self.config_combo.currentTextChanged.connect(lambda _: self._update_status_label())
        scheme_layout.addWidget(scheme_label)
        scheme_layout.addWidget(self.config_combo)
        layout.addLayout(scheme_layout)

        self.status_label = QLabel("")
        self.status_label.setTextFormat(Qt.RichText)
        self.status_label.setMinimumWidth(250)
        self.status_label.setStyleSheet(
            f"color: {self._colors['text_secondary']}; border: none;"
        )
        layout.addWidget(self.status_label, stretch=1)

        self.open_log_btn = QPushButton("日志")
        self.open_log_btn.setFixedWidth(56)
        self.open_log_btn.clicked.connect(lambda _checked=False: self._ensure_log_dialog(show=True))
        layout.addWidget(self.open_log_btn)

        self._update_status_label()

    def refresh_config_names(self):
        current = self.config_combo.currentText() if hasattr(self, "config_combo") else ""
        names = config.get_config_names()
        self.config_combo.blockSignals(True)
        self.config_combo.clear()
        self.config_combo.addItems(names)
        if current in names:
            self.config_combo.setCurrentText(current)
        self.config_combo.blockSignals(False)

    def set_slot_index(self, slot_index: int):
        self.slot_index = slot_index
        self.slot_name = f"窗口{slot_index}"
        self.title_label.setText(self.slot_name)
        self._update_status_label()

    def _set_button_state(self, state: str):
        self._button_state = state
        self._sync_buttons()
        self._update_status_label()
        self.status_changed.emit()

    def _sync_buttons(self):
        if self._button_state == ButtonState.IDLE:
            self.start_btn.setText("开始执行")
            self.start_btn.setEnabled(True)
            self.start_btn.setStyleSheet("")
            self.pause_btn.setText("暂停运行")
            self.pause_btn.setEnabled(False)
            self.pause_btn.setStyleSheet("")
            self.unbind_btn.set_running(False)
        elif self._button_state == ButtonState.RUNNING:
            self.start_btn.setText("强制停止")
            self.start_btn.setEnabled(True)
            self.start_btn.setStyleSheet(f"background-color: {self._colors['danger']}; color: white;")
            self.pause_btn.setText("暂停运行")
            self.pause_btn.setEnabled(True)
            self.pause_btn.setStyleSheet("")
            self.unbind_btn.set_running(True)
        elif self._button_state == ButtonState.PAUSED:
            self.start_btn.setText("强制停止")
            self.start_btn.setEnabled(True)
            self.start_btn.setStyleSheet(f"background-color: {self._colors['danger']}; color: white;")
            self.pause_btn.setText("继续运行")
            self.pause_btn.setEnabled(True)
            self.pause_btn.setStyleSheet(f"background-color: {self._colors['success']}; color: white;")
            self.unbind_btn.set_running(True)
        elif self._button_state == ButtonState.STOPPING:
            self.start_btn.setText("正在停止...")
            self.start_btn.setEnabled(False)
            self.start_btn.setStyleSheet(f"background-color: {self._colors['secondary']}; color: white;")
            self.pause_btn.setText("暂停运行")
            self.pause_btn.setEnabled(False)
            self.pause_btn.setStyleSheet("")

    def _set_preview_image(self, img):
        if img is None:
            return
        qimg = QImage(img.tobytes(), img.width, img.height, img.width * 3, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self.preview_label.setPixmap(
            pixmap.scaled(90, 30, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        )

    def _on_start_clicked(self):
        if self._worker and self._worker.isRunning():
            self._stop_worker()
            return

        if not self._bound_hwnd:
            self._append_local_log(f"[{self.slot_name}] 请先绑定游戏窗口")
            return

        selected, task_params = self._load_selected_config()
        if not selected:
            self._append_local_log(f"[{self.slot_name}] 当前任务方案没有勾选任务")
            return

        self._ensure_log_dialog(show=True)
        self._log_dialog.log_panel.clear()

        context = self.context_label
        self._worker = ScriptWorker(selected, self._bound_hwnd, task_params, context)
        self._worker.finished_sig.connect(self._on_worker_finished)
        self._worker.task_completed.connect(self._on_task_completed)
        self._set_button_state(ButtonState.RUNNING)
        self._worker.start()
        self._append_local_log(
            f"[{self.slot_name}] 使用方案 [{self.config_combo.currentText()}] 启动: "
            f"{', '.join(selected)}"
        )

    def _load_selected_config(self) -> Tuple[List[str], Dict[str, Dict]]:
        config_name = self.config_combo.currentText()
        config_data = config.load_config(config_name) if config_name else None
        if not config_data:
            return [], {}

        checked_tasks = config_data.get("checked_tasks", [])
        raw_params = config_data.get("task_params", {})
        mapped_params: Dict[str, Dict] = {}
        for task_name, params in raw_params.items():
            mapped_params[task_name] = {}
            for param_name, value in params.items():
                mapped_params[task_name][param_name] = config.get_task_mapped_param(
                    task_name, param_name, value
                )
        return checked_tasks, mapped_params

    def _stop_worker(self):
        if self._worker and self._worker.isRunning():
            self._set_button_state(ButtonState.STOPPING)
            self._worker.stop()
            self._append_local_log(f"[{self.slot_name}] 正在停止任务...")

    def _on_pause_clicked(self):
        if not self._worker or not self._worker.isRunning():
            return

        if self._button_state == ButtonState.RUNNING:
            self._worker.pause()
            self._set_button_state(ButtonState.PAUSED)
            self._append_local_log(f"[{self.slot_name}] 任务已暂停")
        elif self._button_state == ButtonState.PAUSED:
            try:
                self._worker.resume()
                self._set_button_state(ButtonState.RUNNING)
                self._append_local_log(f"[{self.slot_name}] 任务已继续")
            except Exception as exc:
                self._append_local_log(f"[{self.slot_name}] 继续失败: {exc}")

    def _on_worker_finished(self):
        self._set_button_state(ButtonState.IDLE)
        self._append_local_log(f"[{self.slot_name}] 当前任务线程已结束")

    def _on_task_completed(self, task_name: str, result):
        if result:
            self._append_local_log(f"[{self.slot_name}] 任务 [{task_name}] 执行完成")
        else:
            self._append_local_log(f"[{self.slot_name}] 任务 [{task_name}] 执行失败或被中止")

    def _unbind_window(self):
        if self._worker and self._worker.isRunning():
            self._stop_worker()
            if not self._worker.wait(500):
                self._append_local_log(f"[{self.slot_name}] 线程退出超时，强制终止")
                self._worker.terminate()
                self._worker.wait()

        if self._bound_hwnd:
            release_tracked_inputs(self._bound_hwnd)
            if self._unlock_callback:
                self._unlock_callback(self._bound_hwnd)

        self._bound_hwnd = None
        self._set_button_state(ButtonState.IDLE)
        self._update_status_label()
        self._append_local_log(f"[{self.slot_name}] 已解除窗口绑定")
        self.status_changed.emit()
        self.unbound.emit(self)

    def _ensure_log_dialog(self, show: bool = True):
        if self._log_dialog is None:
            title = f"{self.slot_name} 日志"
            if self._bound_hwnd:
                title = f"{self.slot_name} 日志 - {self._bound_hwnd}"
            self._log_dialog = WindowLogDialog(title, self._colors, self)
        if show:
            self._log_dialog.setWindowModality(Qt.NonModal)
            self._log_dialog.show()
            self._log_dialog.setWindowState(
                self._log_dialog.windowState() & ~Qt.WindowMinimized
            )
            self._log_dialog.raise_()
            self._log_dialog.activateWindow()
        return self._log_dialog

    def _append_local_log(self, message: str):
        if self._log_dialog is not None:
            self._log_dialog.append_message(message)

    def append_external_log(self, message: str) -> bool:
        if self.context_label and f"[{self.context_label}]" in message:
            self._ensure_log_dialog(show=False).append_message(message)
            return True
        return False

    def _update_status_label(self):
        hwnd_text = str(self._bound_hwnd) if self._bound_hwnd else "未绑定"
        state_text = {
            ButtonState.IDLE: "空闲",
            ButtonState.RUNNING: "运行中",
            ButtonState.PAUSED: "已暂停",
            ButtonState.STOPPING: "停止中",
        }.get(self._button_state, self._button_state)
        state_color = {
            ButtonState.IDLE: self._colors['text_secondary'],
            ButtonState.RUNNING: self._colors['success'],
            ButtonState.PAUSED: self._colors['warning'],
            ButtonState.STOPPING: self._colors['danger'],
        }.get(self._button_state, self._colors['text_secondary'])
        self.status_label.setStyleSheet(
            f"color: {self._colors['text_secondary']}; border: none;"
        )
        self.status_label.setText(
            f"句柄: {hwnd_text} | 状态: "
            f"<span style='color:{state_color}; font-weight:600;'>{state_text}</span>"
            f" | 方案: {self.config_combo.currentText()}"
        )

    def status_summary(self) -> str:
        hwnd_text = str(self._bound_hwnd) if self._bound_hwnd else "未绑定"
        state_text = {
            ButtonState.IDLE: "空闲",
            ButtonState.RUNNING: "运行中",
            ButtonState.PAUSED: "已暂停",
            ButtonState.STOPPING: "停止中",
        }.get(self._button_state, self._button_state)
        return f"{self.slot_name}: {hwnd_text} | {state_text} | {self.config_combo.currentText()}"

    def shutdown(self):
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            if not self._worker.wait(500):
                self._worker.terminate()
                self._worker.wait()
        if self._bound_hwnd:
            release_tracked_inputs(self._bound_hwnd)
            if self._unlock_callback:
                self._unlock_callback(self._bound_hwnd)


class MultiWindowControlPage(QWidget):
    """动态多开控制页。"""

    status_changed = pyqtSignal()

    def __init__(
        self,
        colors: Dict[str, str],
        unlock_callback: Optional[Callable[[int], None]] = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors
        self._unlock_callback = unlock_callback
        self._slots: List[MultiWindowSlotPanel] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QHBoxLayout()
        title = QLabel("多开控制")
        title.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {self._colors['text_primary']};"
        )
        header.addWidget(title)
        header.addStretch()

        self.refresh_btn = QPushButton("刷新方案")
        self.refresh_btn.setFixedWidth(80)
        self.refresh_btn.clicked.connect(self.refresh_config_names)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.container = QWidget()
        self.rows_layout = QVBoxLayout(self.container)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(8)
        self.rows_layout.addStretch()
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, stretch=1)

    @property
    def bound_count(self) -> int:
        return sum(1 for slot in self._slots if slot.is_bound)

    def add_window(self, hwnd: int, img) -> bool:
        if self.has_window(hwnd):
            return False
        slot = MultiWindowSlotPanel(
            len(self._slots) + 1,
            hwnd,
            img,
            self._colors,
            self._unlock_callback,
            self
        )
        slot.status_changed.connect(self.status_changed.emit)
        slot.unbound.connect(self._remove_slot)
        self._slots.append(slot)
        self.rows_layout.insertWidget(self.rows_layout.count() - 1, slot)
        self.status_changed.emit()
        return True

    def _remove_slot(self, slot: MultiWindowSlotPanel):
        if slot not in self._slots:
            return

        self._slots.remove(slot)
        self.rows_layout.removeWidget(slot)
        slot.setParent(None)
        slot.deleteLater()

        for index, existing_slot in enumerate(self._slots, start=1):
            existing_slot.set_slot_index(index)

        self.status_changed.emit()

    def has_window(self, hwnd: int) -> bool:
        return any(slot.is_bound and slot.bound_hwnd == hwnd for slot in self._slots)

    def refresh_config_names(self):
        for slot in self._slots:
            slot.refresh_config_names()
        self.status_changed.emit()

    def append_log(self, message: str) -> bool:
        consumed = False
        for slot in self._slots:
            consumed = slot.append_external_log(message) or consumed
        return consumed

    def status_lines(self) -> List[str]:
        bound_slots = [slot for slot in self._slots if slot.is_bound]
        if not bound_slots:
            return ["多开控制: 暂无绑定窗口"]
        return [slot.status_summary() for slot in bound_slots]

    def shutdown(self):
        for slot in self._slots:
            slot.shutdown()
