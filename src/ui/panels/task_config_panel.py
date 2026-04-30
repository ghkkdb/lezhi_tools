# -*- coding: utf-8 -*-
"""
任务配置面板模块
================
提供任务配置的显示和管理功能

模块结构：
    TaskConfigPanel: 右侧任务配置面板，显示任务配置管理区和各任务的详细配置项
    MultiColumnCheckboxGroup: 多列复选框组控件

架构特点：
    - 扁平化控件存储：所有交互控件统一存储在一维字典 _flat_widgets 中
    - 递归渲染调度器：_build_ui_node 根据配置类型分发渲染任务
    - O(1) 数据读写：直接遍历扁平字典，无需递归
"""
from pathlib import Path

from PyQt5.QtWidgets import (QScrollArea, QWidget, QVBoxLayout, QHBoxLayout,
                             QGridLayout, QLabel, QPushButton, QCheckBox,
                             QComboBox, QLineEdit, QSpinBox, QFrame, QGroupBox,
                             QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap

from src.config import config
from src.utils.logger import get_logger


class MultiColumnCheckboxGroup(QWidget):
    """
    多列复选框组控件
    
    用于显示多列布局的复选框组，支持分组配置
    
    信号：
        state_changed: 复选框状态变化信号 (checkbox_name, checked, group_name)
    
    属性：
        checkboxes: 复选框字典 {group_name: {checkbox_name: QCheckBox}}
    """
    
    state_changed = pyqtSignal(str, bool, str)
    
    def __init__(self, groups_config: list, parent=None):
        """
        初始化多列复选框组
        
        Args:
            groups_config (list): 分组配置列表，格式：
                [
                    {"name": "组名", "items": ["项1", "项2", ...]},
                    ...
                ]
            parent: 父组件
        """
        super().__init__(parent)
        self.checkboxes = {}
        self._setup_ui(groups_config)
    
    def _setup_ui(self, groups_config: list):
        """
        初始化UI
        
        Args:
            groups_config (list): 分组配置列表
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        for group in groups_config:
            group_name = group.get("name", "")
            items = group.get("items", [])
            
            self.checkboxes[group_name] = {}
            
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)
            
            for item_name in items:
                cb = QCheckBox(item_name)
                cb.setChecked(True)
                cb.stateChanged.connect(
                    lambda state, name=item_name, gname=group_name: 
                    self._on_checkbox_changed(name, state, gname)
                )
                row_layout.addWidget(cb)
                self.checkboxes[group_name][item_name] = cb
            
            row_layout.addStretch()
            layout.addWidget(row_widget)
    
    def _on_checkbox_changed(self, checkbox_name: str, state: int, group_name: str):
        """
        复选框状态变化处理
        
        Args:
            checkbox_name (str): 复选框名称
            state (int): 勾选状态
            group_name (str): 分组名称
        """
        checked = state == Qt.Checked
        self.state_changed.emit(checkbox_name, checked, group_name)
    
    def get_checked_items(self) -> dict:
        """
        获取所有勾选的项目
        
        Returns:
            dict: {group_name: [checked_item_names]}
        """
        result = {}
        for group_name, items in self.checkboxes.items():
            result[group_name] = [
                name for name, cb in items.items() if cb.isChecked()
            ]
        return result
    
    def set_checked_items(self, items_dict: dict):
        """
        设置勾选的项目
        
        Args:
            items_dict (dict): {group_name: [item_names]}
        """
        for group_name, item_names in items_dict.items():
            if group_name in self.checkboxes:
                for name, cb in self.checkboxes[group_name].items():
                    cb.blockSignals(True)
                    cb.setChecked(name in item_names)
                    cb.blockSignals(False)
    
    def get_state(self) -> dict:
        """
        获取当前状态（供外部调用）
        
        Returns:
            dict: {checkbox_name: checked}
        """
        state = {}
        for group_name, items in self.checkboxes.items():
            for name, cb in items.items():
                state[name] = cb.isChecked()
        return state
    
    def set_state(self, state: dict):
        """
        设置当前状态（供外部调用）
        
        Args:
            state (dict): {checkbox_name: checked}
        """
        for group_name, items in self.checkboxes.items():
            for name, cb in items.items():
                if name in state:
                    cb.blockSignals(True)
                    cb.setChecked(state[name])
                    cb.blockSignals(False)


class TaskConfigPanel(QScrollArea):
    """
    右侧任务配置面板
    
    显示任务配置管理区和各任务的详细配置项
    
    架构特点：
        - _flat_widgets: 扁平化控件存储 {task_name: {field_name: widget}}
        - _section_frames: 任务区域帧存储 {task_name: QFrame}
        - _task_to_shared_config: 任务名到共享配置名的映射 {"任务名": "共享配置名"}
        - O(1) 复杂度的数据读写
    
    信号：
        config_changed: 配置变化信号
    
    属性：
        _task_list_panel: 任务列表面板引用
        _flat_widgets: 扁平化控件字典 {task_name: {field_name: widget}}
        _section_frames: 任务区域字典 {task_name: QFrame}
        _task_to_shared_config: 任务到共享配置的映射字典
    """
    
    config_changed = pyqtSignal()
    
    def __init__(self, task_list_panel, colors: dict, parent=None):
        """
        初始化任务配置面板
        
        Args:
            task_list_panel: 任务列表面板引用
            colors (dict): 配色方案字典
            parent: 父组件
        """
        super().__init__(parent)
        self._colors = colors
        self._task_list_panel = task_list_panel
        self._flat_widgets = {}
        self._section_frames = {}
        self._task_to_shared_config = {}
        self._logger = get_logger('TaskConfigPanel')
        self._setup_ui()
    
    def _setup_ui(self):
        """
        初始化UI
        
        创建滚动区域、配置管理区和任务配置区域
        """
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setFixedWidth(550)
        self.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self._colors['surface']};
                border: 1px solid {self._colors['border']};
                border-radius: 4px;
            }}
        """)
        
        container = QWidget()
        self.setWidget(container)
        
        self._main_layout = QVBoxLayout(container)
        self._main_layout.setContentsMargins(8, 8, 8, 8)
        self._main_layout.setSpacing(8)
        
        self._create_config_manager()
        self._create_task_configs()
        
        self._main_layout.addStretch()
    
    def _create_config_manager(self):
        """
        创建配置管理区
        
        包含配置下拉框、保存按钮和删除按钮
        """
        manager_frame = QFrame()
        manager_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors['surface_elevated']};
                border: 1px solid {self._colors['border']};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        
        manager_layout = QVBoxLayout(manager_frame)
        manager_layout.setContentsMargins(8, 8, 8, 8)
        manager_layout.setSpacing(8)
        
        title_label = QLabel("任务方案配置")
        title_label.setStyleSheet(f"""
            font-weight: 600;
            font-size: 13px;
            color: {self._colors['text_primary']};
        """)
        manager_layout.addWidget(title_label)
        
        config_row = QHBoxLayout()
        config_row.setSpacing(8)
        
        self.config_combo = QComboBox()
        self.config_combo.setMinimumWidth(150)
        self.config_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {self._colors['border_strong']};
                border-radius: 4px;
                padding: 4px 8px;
                background-color: {self._colors['surface']};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """)
        self.config_combo.currentTextChanged.connect(self._on_config_selected)
        self.config_combo.currentIndexChanged.connect(self._on_config_index_changed)
        config_row.addWidget(self.config_combo)
        
        self.save_btn = QPushButton("保存")
        self.save_btn.setFixedWidth(60)
        self.save_btn.clicked.connect(self._on_save_config)
        config_row.addWidget(self.save_btn)
        
        self.delete_btn = QPushButton("删除")
        self.delete_btn.setFixedWidth(60)
        self.delete_btn.clicked.connect(self._on_delete_config)
        config_row.addWidget(self.delete_btn)
        
        config_row.addStretch()
        manager_layout.addLayout(config_row)
        
        self._main_layout.addWidget(manager_frame)
        self._refresh_config_list()
    
    def _create_task_configs(self):
        """
        创建任务配置区域
        
        遍历所有日常任务，为每个任务创建配置区域
        支持任务组（列表）水平排列
        支持共享配置继承机制：
            - 共享配置只渲染一次（如"组队配置"）
            - 继承的任务（如"日常副本"）不重复创建配置区域
            - 只在 _section_frames 中建立映射关系供跳转使用
        """
        created_shared = set()
        
        for task_item in config.daily_tasks:
            if isinstance(task_item, list):
                self._create_task_group_row(task_item, created_shared)
            else:
                if not config.has_task_config(task_item):
                    continue
                
                shared_name = config.task_definition.get_shared_config_name(task_item)
                
                if shared_name and shared_name not in created_shared:
                    section = self._create_task_section(shared_name)
                    self._section_frames[shared_name] = section
                    self._main_layout.addWidget(section)
                    created_shared.add(shared_name)
                    self._task_to_shared_config[task_item] = shared_name
                elif shared_name:
                    self._task_to_shared_config[task_item] = shared_name
                else:
                    section = self._create_task_section(task_item)
                    self._section_frames[task_item] = section
                    self._main_layout.addWidget(section)
    
    def _create_task_group_row(self, task_names: list, created_shared: set = None):
        """
        创建任务组行（多个任务水平排列）
        
        Args:
            task_names (list): 任务名称列表
            created_shared (set): 已创建的共享配置集合
        """
        if created_shared is None:
            created_shared = set()
        
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)
        
        for task_name in task_names:
            if not config.has_task_config(task_name):
                continue
            
            shared_name = config.task_definition.get_shared_config_name(task_name)
            
            if shared_name and shared_name not in created_shared:
                section = self._create_task_section(shared_name)
                self._section_frames[shared_name] = section
                row_layout.addWidget(section)
                created_shared.add(shared_name)
                self._task_to_shared_config[task_name] = shared_name
            elif shared_name:
                self._task_to_shared_config[task_name] = shared_name
            else:
                section = self._create_task_section(task_name)
                self._section_frames[task_name] = section
                row_layout.addWidget(section)
        
        row_layout.addStretch()
        self._main_layout.addWidget(row_widget)
    
    def _create_task_section(self, task_name: str) -> QFrame:
        """
        创建单个任务的配置区域
        
        Args:
            task_name (str): 任务名称
            
        Returns:
            QFrame: 配置区域组件
        """
        frame = QFrame()
        frame.setObjectName(f"section_{task_name}")
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors['surface']};
                border: 1px solid {self._colors['border']};
                border-radius: 4px;
            }}
        """)
        
        task_def = config.task_config_definitions.get(task_name, {})
        
        if "section_width" in task_def:
            frame.setFixedWidth(task_def["section_width"])
        if "section_max_width" in task_def:
            frame.setMaximumWidth(task_def["section_max_width"])
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        title_label = QLabel(f"【{task_name}】")
        title_label.setStyleSheet(f"""
            font-weight: 600;
            font-size: 12px;
            color: {self._colors['primary']};
        """)
        layout.addWidget(title_label)
        
        self._flat_widgets[task_name] = {}
        
        fields = task_def.get("fields", [])
        
        for field in fields:
            ui_element = self._build_ui_node(field, task_name)
            if ui_element is not None:
                if isinstance(ui_element, QWidget):
                    layout.addWidget(ui_element)
                elif isinstance(ui_element, QHBoxLayout):
                    layout.addLayout(ui_element)
        
        return frame
    
    def _build_ui_node(self, node_config: dict, task_name: str, in_row: bool = False):
        """
        核心渲染调度器
        
        根据配置类型分发渲染任务到对应的 build 方法
        
        Args:
            node_config (dict): 节点配置字典
            task_name (str): 任务名称
            in_row (bool): 是否在 row 容器内部，用于控制 stretch 行为
            
        Returns:
            QWidget/QHBoxLayout/None: 渲染结果
        """
        node_type = node_config.get("type", "dropdown")
        
        if node_type == "group":
            return self._build_group(node_config, task_name)
        elif node_type == "row":
            return self._build_row(node_config, task_name)
        elif node_type == "columns":
            return self._build_columns(node_config, task_name)
        elif node_type == "label":
            return self._create_label_field(node_config)
        else:
            return self._build_interactive_field(node_config, task_name, in_row)
    
    def _build_group(self, field: dict, task_name: str) -> QGroupBox:
        """
        构建分组容器
        
        将多个控件垂直排列在一个分组中。
        注意：group 内禁止嵌套子 group。
        
        Args:
            field (dict): 字段配置字典
            task_name (str): 任务名称
            
        Returns:
            QGroupBox: 分组容器
        """
        group_box = QGroupBox(field.get("label", ""))
        group_box.setStyleSheet(f"""
            QGroupBox {{
                font-weight: 600;
                color: {self._colors['text_primary']};
                border: none;
                margin-top: 0px;
                padding-top: 0px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 0px;
                padding: 0 4px;
            }}
        """)
        
        group_layout = QVBoxLayout(group_box)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(4)
        
        fields = field.get("fields", [])
        
        for sub_field in fields:
            sub_type = sub_field.get("type", "dropdown")
            
            if sub_type == "group":
                raise ValueError("group 内禁止嵌套子 group")
            
            ui_element = self._build_ui_node(sub_field, task_name)
            if ui_element is not None:
                if isinstance(ui_element, QWidget):
                    group_layout.addWidget(ui_element)
                elif isinstance(ui_element, QHBoxLayout):
                    group_layout.addLayout(ui_element)
        
        return group_box
    
    def _build_row(self, field: dict, task_name: str) -> QWidget:
        """
        构建行布局容器
        
        将多个控件水平排列在一行中。
        注意：row 内禁止嵌套 row 或 group 类型。
        
        Args:
            field (dict): 字段配置字典
            task_name (str): 任务名称
            
        Returns:
            QWidget: 行容器
        """
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)
        
        items = field.get("items", [])
        layout_align = field.get("layout_align", "left")
        
        for item in items:
            item_type = item.get("type", "dropdown")
            
            if item_type in ("row", "group"):
                raise ValueError(f"row 内禁止嵌套 {item_type} 类型")
            
            ui_element = self._build_ui_node(item, task_name, in_row=True)
            if ui_element is not None:
                if isinstance(ui_element, QWidget):
                    if "width" in item:
                        ui_element.setFixedWidth(item["width"])
                    row_layout.addWidget(ui_element)
                elif isinstance(ui_element, QHBoxLayout):
                    row_layout.addLayout(ui_element)
        
        if layout_align == "left":
            row_layout.addStretch()
        
        return row_widget
    
    def _build_columns(self, field: dict, task_name: str) -> QWidget:
        """
        构建多列布局容器
        
        将控件按指定列数排列，每列垂直排列。
        
        Args:
            field (dict): 字段配置字典，包含：
                - items: 控件列表
                - columns: 列数（默认5）
                - column_spacing: 列间距（默认16）
                - row_spacing: 行间距（默认4）
            task_name (str): 任务名称
            
        Returns:
            QWidget: 多列容器
        """
        columns_widget = QWidget()
        main_layout = QHBoxLayout(columns_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        items = field.get("items", [])
        col_count = field.get("columns", 5)
        col_spacing = field.get("column_spacing", 16)
        row_spacing = field.get("row_spacing", 4)
        
        main_layout.setSpacing(col_spacing)
        
        items_per_col = (len(items) + col_count - 1) // col_count
        
        col_layouts = []
        for col_idx in range(col_count):
            col_widget = QWidget()
            col_layout = QVBoxLayout(col_widget)
            col_layout.setContentsMargins(0, 0, 0, 0)
            col_layout.setSpacing(row_spacing)
            col_layouts.append(col_layout)
            main_layout.addWidget(col_widget)
        
        for idx, item in enumerate(items):
            col_idx = idx // items_per_col
            if col_idx >= col_count:
                col_idx = col_count - 1
            
            item_type = item.get("type", "dropdown")
            if item_type in ("row", "group", "columns"):
                raise ValueError(f"columns 内禁止嵌套 {item_type} 类型")
            
            ui_element = self._build_ui_node(item, task_name, in_row=True)
            if ui_element is not None:
                if isinstance(ui_element, QWidget):
                    col_layouts[col_idx].addWidget(ui_element)
                elif isinstance(ui_element, QHBoxLayout):
                    col_layouts[col_idx].addLayout(ui_element)
        
        for col_layout in col_layouts:
            col_layout.addStretch()
        
        main_layout.addStretch()
        
        return columns_widget
    
    def _build_interactive_field(self, field: dict, task_name: str, in_row: bool = False):
        """
        构建交互控件
        
        根据字段类型创建对应的控件实例，并存储到扁平字典中。
        核心逻辑：所有交互控件统一存储到 _flat_widgets[task_name][field_name]
        
        Args:
            field (dict): 字段配置字典
            task_name (str): 任务名称
            in_row (bool): 是否在 row 容器内部，为 True 时不添加 stretch
            
        Returns:
            QWidget/QHBoxLayout: 控件或布局容器
        """
        field_type = field.get("type", "dropdown")
        field_name = field.get("name")
        
        widget = None
        
        if field_type == "dropdown":
            combo = QComboBox()
            options = field.get("options", [])
            if options:
                combo.addItems(options)
            combo.setCurrentText(field.get("default", ""))
            combo.setStyleSheet(f"""
                QComboBox {{
                    border: 1px solid {self._colors['border_strong']};
                    border-radius: 4px;
                    padding: 4px 8px;
                    min-width: 100px;
                }}
            """)
            combo.currentTextChanged.connect(lambda _, tn=task_name: self._on_field_changed(tn))
            widget = combo
        
        elif field_type == "text":
            line_edit = QLineEdit()
            line_edit.setText(field.get("default", ""))
            line_edit.setPlaceholderText(field.get("placeholder", ""))
            line_edit.setStyleSheet(f"""
                QLineEdit {{
                    border: 1px solid {self._colors['border_strong']};
                    border-radius: 4px;
                    padding: 4px 8px;
                    min-width: 100px;
                }}
            """)
            line_edit.textChanged.connect(lambda _, tn=task_name: self._on_field_changed(tn))
            widget = line_edit
        
        elif field_type == "number":
            spinbox = QSpinBox()
            spinbox.setValue(int(field.get("default", 0)))
            if "min" in field:
                spinbox.setMinimum(int(field["min"]))
            if "max" in field:
                spinbox.setMaximum(int(field["max"]))
            if "step" in field:
                spinbox.setSingleStep(int(field["step"]))
            spinbox.setStyleSheet(f"""
                QSpinBox {{
                    border: 1px solid {self._colors['border_strong']};
                    border-radius: 4px;
                    padding: 4px 8px;
                    min-width: 80px;
                }}
            """)
            spinbox.valueChanged.connect(lambda _, tn=task_name: self._on_field_changed(tn))
            widget = spinbox
        
        elif field_type == "checkbox":
            checkbox_text = field.get("label", "")
            checkbox = QCheckBox(checkbox_text)
            default_val = field.get("default", False)
            if isinstance(default_val, str):
                default_val = default_val.lower() in ('true', '1', 'yes')
            checkbox.setChecked(bool(default_val))
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    spacing: 6px;
                    color: {self._colors['text_primary']};
                }}
                QCheckBox::indicator {{
                    width: 16px;
                    height: 16px;
                }}
            """)
            checkbox.stateChanged.connect(lambda _, tn=task_name: self._on_field_changed(tn))
            widget = checkbox
        
        elif field_type == "checkbox_group":
            groups_config = field.get("groups", [])
            checkbox_group = MultiColumnCheckboxGroup(groups_config)
            checkbox_group.state_changed.connect(lambda _, __, ___, tn=task_name: self._on_field_changed(tn))
            widget = checkbox_group
        
        if widget is None:
            return None
        
        if field_name:
            if field_name in self._flat_widgets[task_name]:
                raise ValueError(
                    f"配置解析错误: 任务 [{task_name}] 中存在重复的字段名 [{field_name}]，"
                    f"请检查配置定义，确保每个字段的 name 属性唯一"
                )
            self._flat_widgets[task_name][field_name] = widget
        
        if field_type == "checkbox":
            return widget
        
        if field.get("label"):
            field_layout = QHBoxLayout()
            field_layout.setSpacing(8)
            
            label = QLabel(field["label"])
            label.setStyleSheet(f"color: {self._colors['text_primary']};")
            field_layout.addWidget(label)
            
            if "width" in field:
                widget.setFixedWidth(field["width"])
            field_layout.addWidget(widget)
            
            if not in_row:
                field_layout.addStretch()
            
            return field_layout
        
        return widget
    
    def _create_label_field(self, field: dict) -> QLabel:
        """
        创建静态标签控件
        
        支持图片显示和文本显示两种模式。
        图片路径使用 pathlib 处理，确保 Windows 兼容性。
        
        Args:
            field (dict): 字段配置字典
            
        Returns:
            QLabel: 标签控件
        """
        label_widget = QLabel()
        
        if "image" in field:
            image_path = Path(config.get_img_path(field["image"]))
            if image_path.exists():
                pixmap = QPixmap(str(image_path))
                if "size" in field:
                    size = field["size"]
                    pixmap = pixmap.scaled(size[0], size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label_widget.setPixmap(pixmap)
            else:
                label_widget.setText("[图片缺失]")
                label_widget.setStyleSheet(f"color: {self._colors['text_secondary']}; font-style: italic;")
        else:
            label_widget.setText(field.get("text", ""))
            
            style = field.get("style", "normal")
            style_colors = {
                "normal": self._colors['text_primary'],
                "info": self._colors['primary'],
                "warning": self._colors['warning'],
                "success": self._colors['success'],
                "danger": self._colors['danger']
            }
            color = style_colors.get(style, self._colors['text_primary'])
            label_widget.setStyleSheet(f"color: {color};")
        
        if "width" in field:
            label_widget.setFixedWidth(field["width"])
        
        return label_widget
    
    def _on_field_changed(self, task_name: str):
        """
        配置字段变化处理
        
        Args:
            task_name (str): 任务名称
        """
        self.config_changed.emit()
    
    def _refresh_config_list(self):
        """刷新配置列表"""
        self.config_combo.blockSignals(True)
        current_text = self.config_combo.currentText()
        self.config_combo.clear()
        
        config_names = config.get_config_names()
        self.config_combo.addItems(config_names)
        
        if current_text and current_text in config_names:
            self.config_combo.setCurrentText(current_text)
        
        self.config_combo.blockSignals(False)
    
    def _on_config_selected(self, config_name: str):
        """
        配置选择处理
        
        Args:
            config_name (str): 配置名称
        """
        if not config_name:
            return
        
        config_data = config.load_config(config_name)
        if config_data:
            self._apply_config_data(config_data)
    
    def _on_config_index_changed(self, index: int):
        """
        配置索引变化处理（支持单配置方案切换）
        
        Args:
            index (int): 选中索引
        """
        if index < 0:
            return
        
        config_name = self.config_combo.itemText(index)
        if config_name:
            config_data = config.load_config(config_name)
            if config_data:
                self._apply_config_data(config_data)
    
    def _apply_config_data(self, config_data: dict):
        """
        应用配置数据到UI
        
        Args:
            config_data (dict): 配置数据字典
        """
        checked_tasks = config_data.get("checked_tasks", [])
        task_params = config_data.get("task_params", {})
        
        self._task_list_panel.set_checked_tasks(checked_tasks)
        self._apply_task_params(task_params)
    
    def _on_save_config(self):
        """保存配置处理"""
        text, ok = QInputDialog.getText(
            self, "保存配置", "请输入配置名称:"
        )
        
        if ok and text:
            config_name = text.strip()
            if not config_name:
                QMessageBox.warning(self, "警告", "配置名称不能为空")
                return
            
            checked_tasks = self._task_list_panel.get_checked_tasks()
            task_params = self._get_all_task_params()
            
            config.save_config(config_name, checked_tasks, task_params)
            self._refresh_config_list()
            
            self.config_combo.blockSignals(True)
            self.config_combo.setCurrentText(config_name)
            self.config_combo.blockSignals(False)
            
            config_data = {
                "checked_tasks": checked_tasks,
                "task_params": task_params
            }
            self._apply_config_data(config_data)
            
            QMessageBox.information(self, "成功", f"配置 '{config_name}' 保存成功")
    
    def _on_delete_config(self):
        """删除配置处理"""
        config_name = self.config_combo.currentText()
        if not config_name:
            QMessageBox.warning(self, "警告", "请先选择要删除的配置")
            return
        
        if config.is_default_config(config_name):
            QMessageBox.warning(self, "警告", "默认配置不能删除")
            return
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除配置 '{config_name}' 吗?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if config.delete_config(config_name):
                self._refresh_config_list()
                self._reset_to_defaults()
                QMessageBox.information(self, "成功", f"配置 '{config_name}' 已删除")
            else:
                QMessageBox.warning(self, "失败", "删除配置失败")
    
    def _get_all_task_params(self) -> dict:
        """
        获取所有任务参数
        
        直接遍历扁平字典，O(1) 单控件访问
        
        Returns:
            dict: 任务参数字典
        """
        params = {}
        for task_name, widgets in self._flat_widgets.items():
            params[task_name] = {}
            for field_name, widget in widgets.items():
                params[task_name][field_name] = self._get_widget_value(widget)
        return params
    
    def _get_widget_value(self, widget):
        """
        获取控件值
        
        优先检测自定义复合组件的状态管理接口
        
        Args:
            widget: 控件实例
            
        Returns:
            any: 控件值
        """
        if hasattr(widget, 'get_state'):
            return widget.get_state()
        elif isinstance(widget, QComboBox):
            return widget.currentText()
        elif isinstance(widget, QLineEdit):
            return widget.text()
        elif isinstance(widget, QSpinBox):
            return widget.value()
        elif isinstance(widget, QCheckBox):
            return widget.isChecked()
        return None
    
    def _set_widget_value(self, widget, value):
        """
        设置控件值
        
        优先检测自定义复合组件的状态管理接口
        
        Args:
            widget: 控件实例
            value: 要设置的值
        """
        if hasattr(widget, 'set_state'):
            widget.set_state(value)
        elif isinstance(widget, QComboBox):
            widget.setCurrentText(str(value))
        elif isinstance(widget, QLineEdit):
            widget.setText(str(value))
        elif isinstance(widget, QSpinBox):
            widget.setValue(int(value))
        elif isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))
    
    def _apply_task_params(self, task_params: dict):
        """
        应用任务参数
        
        直接遍历扁平字典，O(1) 单控件访问
        使用 blockSignals 防止信号风暴
        
        Args:
            task_params (dict): 任务参数字典
        """
        for task_name, params in task_params.items():
            if task_name not in self._flat_widgets:
                continue
            
            widgets = self._flat_widgets[task_name]
            for field_name, widget in widgets.items():
                if field_name in params:
                    widget.blockSignals(True)
                    self._set_widget_value(widget, params[field_name])
                    widget.blockSignals(False)
    
    def _reset_to_defaults(self):
        """重置为默认值"""
        for task_name, widgets in self._flat_widgets.items():
            task_def = config.task_config_definitions.get(task_name, {})
            fields = task_def.get("fields", [])
            
            default_params = {}
            for field in fields:
                field_name = field.get("name")
                if field_name and field_name in widgets:
                    default_params[field_name] = field.get("default", "")
            
            for field_name, widget in widgets.items():
                if field_name in default_params:
                    widget.blockSignals(True)
                    self._set_widget_value(widget, default_params[field_name])
                    widget.blockSignals(False)
        
        self._task_list_panel.set_checked_tasks([])
    
    def scroll_to_task(self, task_name: str):
        """
        滚动到指定任务的配置区域
        
        滚动后会临时高亮显示该区域边框，2秒后恢复。
        支持共享配置：如果任务继承自共享配置，则跳转到共享配置区域。
        
        Args:
            task_name (str): 任务名称
        """
        actual_name = self._task_to_shared_config.get(task_name, task_name)
        
        if actual_name not in self._section_frames:
            return
        
        section = self._section_frames[actual_name]
        self.ensureWidgetVisible(section)
        
        section.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors['surface']};
                border: 2px solid {self._colors['primary']};
                border-radius: 4px;
            }}
        """)
        
        QTimer.singleShot(2000, lambda: section.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors['surface']};
                border: 1px solid {self._colors['border']};
                border-radius: 4px;
            }}
        """))
    
    def get_task_param(self, task_name: str, param_name: str):
        """
        获取指定任务的参数值
        
        支持共享配置：如果任务继承自共享配置，则从共享配置中获取参数值。
        
        Args:
            task_name (str): 任务名称
            param_name (str): 参数名称
            
        Returns:
            any: 参数值，如果任务或参数不存在则返回 None
        """
        actual_name = self._task_to_shared_config.get(task_name, task_name)
        
        if actual_name not in self._flat_widgets:
            return None
        
        if param_name not in self._flat_widgets[actual_name]:
            return None
        
        widget = self._flat_widgets[actual_name][param_name]
        return self._get_widget_value(widget)
    
    def load_last_config(self):
        """加载最近使用的配置"""
        config_name, config_data = config.get_last_used_config()
        
        if config_name and config_data:
            self.config_combo.blockSignals(True)
            self.config_combo.setCurrentText(config_name)
            self.config_combo.blockSignals(False)
            
            self._apply_config_data(config_data)
    
    def set_all_config_checkboxes(self, task_name: str, checked: bool):
        """
        设置任务所有配置复选框状态
        
        支持共享配置：如果任务继承自共享配置，则设置共享配置中的复选框。
        
        Args:
            task_name (str): 任务名称
            checked (bool): 是否勾选
        """
        actual_name = self._task_to_shared_config.get(task_name, task_name)
        
        if actual_name not in self._flat_widgets:
            return
        
        for widget in self._flat_widgets[actual_name].values():
            if isinstance(widget, QCheckBox):
                widget.setChecked(checked)
    
    def set_specific_config_checkboxes(self, task_name: str, result_dict: dict):
        """
        根据结果字典精准设置配置复选框状态
        
        成功的子项取消勾选，失败的子项保持勾选状态。
        支持共享配置：如果任务继承自共享配置，则设置共享配置中的复选框。
        
        Args:
            task_name (str): 任务名称
            result_dict (dict): {"子项名": True/False, ...}，True 表示成功
        """
        actual_name = self._task_to_shared_config.get(task_name, task_name)
        
        if actual_name not in self._flat_widgets:
            return
        
        widgets = self._flat_widgets[actual_name]
        logger = get_logger('UI')
        
        for checkbox_name, success in result_dict.items():
            if success and checkbox_name in widgets:
                widget = widgets[checkbox_name]
                if isinstance(widget, QCheckBox):
                    widget.setChecked(False)
                else:
                    logger.warning(f"任务 [{task_name}] 返回的子项 [{checkbox_name}] 不是复选框")
            elif success:
                logger.warning(f"任务 [{task_name}] 返回的子项 [{checkbox_name}] 在 UI 中未找到对应复选框")
    
    def has_config_checkboxes(self, task_name: str) -> bool:
        """
        检查任务是否有配置复选框
        
        仅检查 QCheckBox 类型控件，忽略 QComboBox、QLineEdit、QSpinBox
        支持共享配置：如果任务继承自共享配置，则检查共享配置中的复选框。
        
        Args:
            task_name (str): 任务名称
            
        Returns:
            bool: 是否存在至少一个 QCheckBox
        """
        actual_name = self._task_to_shared_config.get(task_name, task_name)
        
        if actual_name not in self._flat_widgets:
            return False
        
        for widget in self._flat_widgets[actual_name].values():
            if isinstance(widget, QCheckBox):
                return True
        return False
    
    def are_all_config_checkboxes_unchecked(self, task_name: str) -> bool:
        """
        检查任务的所有配置复选框是否都未勾选
        
        当复选框总数为 0 时，返回 True（表示"没有需要保持勾选的项"）
        支持共享配置：如果任务继承自共享配置，则检查共享配置中的复选框。
        
        Args:
            task_name (str): 任务名称
            
        Returns:
            bool: 所有复选框是否都未勾选
        """
        actual_name = self._task_to_shared_config.get(task_name, task_name)
        
        if actual_name not in self._flat_widgets:
            return True
        
        for widget in self._flat_widgets[actual_name].values():
            if isinstance(widget, QCheckBox) and widget.isChecked():
                return False
        return True
    
    def get_flattened_task_params(self, task_name: str) -> dict:
        """
        获取扁平化的任务参数（全量提取）
        
        直接遍历扁平字典，O(1) 单控件访问
        支持共享配置：如果任务继承自共享配置，则获取共享配置的参数。
        
        Args:
            task_name (str): 任务名称
            
        Returns:
            dict: 扁平化的参数字典
        """
        actual_name = self._task_to_shared_config.get(task_name, task_name)
        
        if actual_name not in self._flat_widgets:
            return {}
        
        params = {}
        for field_name, widget in self._flat_widgets[actual_name].items():
            params[field_name] = self._get_widget_value(widget)
        return params
