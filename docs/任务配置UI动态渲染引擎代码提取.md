# 任务配置 UI 动态渲染引擎 - 核心代码提取

> 本文档用于配合外部架构师的优化方案，提取了三个核心部分的完整代码片段。

---

## 目录

1. [任务配置数据结构](#1-任务配置数据结构)
2. [UI 动态渲染逻辑](#2-ui-动态渲染逻辑)
3. [参数的提取与回填逻辑](#3-参数的提取与回填逻辑)

---

## 1. 任务配置数据结构

**文件位置**: `src/config/settings.py`

### 1.1 最复杂的任务配置：`每日可换`

该配置包含完整的 `group`（分组）、`row`（同行排列）、`label`（提示说明）嵌套布局结构：

```python
"每日可换": {
    "fields": [
        {
            "name": "1_group",
            "type": "group",
            "fields": [
                {
                    "name": "1_row",
                    "type": "row",
                    "items": [
                        {
                            "name": "每日签到",
                            "type": "checkbox",
                            "label": "每日签到",
                            "default": False
                        },
                        {
                            "name": "每日江湖礼",
                            "type": "checkbox",
                            "label": "每日江湖礼",
                            "default": False
                        },
                        {
                            "name": "每日在线礼",
                            "type": "checkbox",
                            "label": "每日在线礼",
                            "default": False
                        },
                        {
                            "name": "每日回馈礼",
                            "type": "checkbox",
                            "label": "每日回馈礼",
                            "default": False
                        },
                        {
                            "name": "每日买银票",
                            "type": "checkbox",
                            "label": "每日买银票",
                            "default": False
                        },
                         {
                            "name": "买鸡蛋",
                            "type": "checkbox",
                            "label": "买鸡蛋",
                            "default": False
                        },
                    ]
                }
            ]
        },
        {
            "name": "2_group",
            "type": "group",
            "fields": [
                {
                    "name": "2_row",
                    "type": "row",
                    "items": [
                        {
                            "name": "榫头卯眼",
                            "type": "checkbox",
                            "label": "榫头卯眼",
                            "default": False
                        },
                        {
                            "name": "兑换武经志",
                            "type": "checkbox",
                            "label": "兑换武经志",
                            "default": False
                        },
                        {
                            "name": "小红花礼盒",
                            "type": "checkbox",
                            "label": "小红花礼盒",
                            "default": False
                        },
                        {
                            "name": "购买铜豆子",
                            "type": "checkbox",
                            "label": "购买铜豆子",
                            "default": False
                        },
                        {
                            "name": "功绩换铜板",
                            "type": "checkbox",
                            "label": "功绩换铜板",
                            "default": False
                        },
                        {
                            "name": "行当绝活",
                            "type": "checkbox",
                            "label": "行当绝活",
                            "default": False
                        }
                        
                    ]
                }
            ]
        },
        {
            "name": "3_group",
            "type": "group",
            "fields": [
                {
                    "name": "3_row",
                    "type": "row",
                    "items": [
                        {
                            "name": "碧铜马坯",
                            "type": "checkbox",
                            "label": "碧铜马坯",
                            "default": False
                        },
                        {
                            "name": "买吴越剑坯",
                            "type": "checkbox",
                            "label": "买吴越剑坯",
                            "default": False
                        },
                        {
                            "name": "买白公鼎坯",
                            "type": "checkbox",
                            "label": "买白公鼎坯",
                            "default": False
                        },
                        {
                            "name": "兑换锦芳绣",
                            "type": "checkbox",
                            "label": "兑换锦芳绣",
                            "default": False
                        },
                        {
                            "name": "买形影心得",
                            "type": "checkbox",
                            "label": "买形影心得",
                            "default": False
                        },
                        {
                            "name": "换高级萃石",
                            "type": "checkbox",
                            "label": "换高级萃石",
                            "default": False
                        }
                    ]
                }
            ]
        },
        {
            "name": "提示信息",
            "type": "label",
            "text": "提示：只执行勾选的内容",
            "style": "info"
        }
    ]
},
```

### 1.2 另一个复杂任务：`摇钱树`

该配置展示了 `row` 内混合 `dropdown` 和 `label` 的用法：

```python
"摇钱树": {
    "fields": [
        {
            "name": "choice_row",
            "type": "row",
            "items": [
                {
                    "name": "choice",
                    "type": "dropdown",
                    "label": "摇树方式",
                    "options": ["轻轻摇", "用力摇", "全力摇"],
                    "default": "轻轻摇",
                    "value_map": {
                        "轻轻摇": 1,
                        "用力摇": 0,
                        "全力摇": 2
                    }
                },
                {
                    "name": "choice_hint",
                    "type": "label",
                    "text": "轻轻摇【免费】、用力摇【5000】、【全力摇1W】",
                    "style": "info"
                }
            ]
        }
    ]
},
```

### 1.3 配置定义初始化函数

```python
def _init_task_config_definitions(self):
    """
    初始化任务配置定义
    
    定义哪些任务有配置项，以及配置项的类型和选项
    
    支持的字段类型：
        - dropdown: 下拉选择框，需要 options 和 value_map
        - text: 文本输入框，需要 default
        - number: 数字输入框，需要 default，可选 min/max/step
        - checkbox: 复选框，需要 default (True/False)
        - spinbox: 数字微调框，需要 default, min, max, step
        - label: 静态标签，用于显示不可编辑的文本或图片
        - row: 行布局容器，水平排列多个控件
        - group: 分组容器，带标题的分组
    
    嵌套约束：
        - row 内部仅允许基础控件或 label，禁止嵌套 row 或 group
        - group 内部允许基础控件、label 和 row，禁止嵌套子 group
    """
    self.task_config_definitions = {
        # ... 配置定义 ...
    }
```

### 1.4 默认参数递归提取函数

```python
def _extract_default_params(self, fields: list) -> dict:
    """
    递归提取字段的默认参数值
    
    参数：
        fields: 字段列表
        
    返回：
        dict: 默认参数字典
    """
    params = {}
    for field in fields:
        field_type = field.get("type", "dropdown")
        
        if field_type == "row":
            items = field.get("items", [])
            params.update(self._extract_default_params(items))
        elif field_type == "group":
            sub_fields = field.get("fields", [])
            params.update(self._extract_default_params(sub_fields))
        elif field_type not in ("label",):
            params[field["name"]] = field.get("default", "")
    
    return params
```

### 1.5 嵌套约束验证函数

```python
def _validate_task_config_definitions(self):
    """
    验证任务配置定义的嵌套约束
    
    检查配置定义是否符合嵌套规则：
        - row 内部仅允许基础控件或 label，禁止嵌套 row 或 group
        - group 内部允许基础控件、label 和 row，禁止嵌套子 group
    
    Raises:
        ValueError: 当配置违反嵌套约束时抛出
    """
    BASIC_TYPES = {"dropdown", "text", "number", "checkbox", "checkbox_group", "spinbox", "label"}
    
    def validate_row_items(items: list, parent_path: str):
        """
        验证 row 内的 items
        
        Args:
            items: row 内的控件列表
            parent_path: 父级路径，用于错误提示
        
        Raises:
            ValueError: 当发现非法嵌套时抛出
        """
        for idx, item in enumerate(items):
            item_type = item.get("type", "")
            item_path = f"{parent_path}.items[{idx}]"
            
            if item_type == "row":
                raise ValueError(
                    f"嵌套约束违规: {item_path} - row 内部禁止嵌套 row"
                )
            if item_type == "group":
                raise ValueError(
                    f"嵌套约束违规: {item_path} - row 内部禁止嵌套 group"
                )
    
    def validate_group_fields(fields: list, parent_path: str):
        """
        验证 group 内的 fields
        
        Args:
            fields: group 内的字段列表
            parent_path: 父级路径，用于错误提示
        
        Raises:
            ValueError: 当发现非法嵌套时抛出
        """
        for idx, field in enumerate(fields):
            field_type = field.get("type", "")
            field_path = f"{parent_path}.fields[{idx}]"
            
            if field_type == "group":
                raise ValueError(
                    f"嵌套约束违规: {field_path} - group 内部禁止嵌套子 group"
                )
            
            if field_type == "row":
                items = field.get("items", [])
                validate_row_items(items, field_path)
    
    def validate_fields(fields: list, task_name: str):
        """
        验证顶层字段列表
        
        Args:
            fields: 字段列表
            task_name: 任务名称
        
        Raises:
            ValueError: 当发现非法嵌套时抛出
        """
        for idx, field in enumerate(fields):
            field_type = field.get("type", "")
            field_path = f"任务[{task_name}].fields[{idx}]"
            
            if field_type == "row":
                items = field.get("items", [])
                validate_row_items(items, field_path)
            
            elif field_type == "group":
                group_fields = field.get("fields", [])
                validate_group_fields(group_fields, field_path)
    
    for task_name, task_def in self.task_config_definitions.items():
        fields = task_def.get("fields", [])
        validate_fields(fields, task_name)
```

---

## 2. UI 动态渲染逻辑

**文件位置**: `src/ui/panels/task_config_panel.py`

### 2.1 `_create_task_section` 函数（主渲染入口）

```python
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
    
    task_def = config.task_config_definitions.get(task_name, {})
    fields = task_def.get("fields", [])
    
    self._config_widgets[task_name] = {}
    
    for field in fields:
        field_type = field.get("type", "dropdown")
        
        if field_type in ("label", "row", "group", "checkbox_group"):
            if field_type == "label":
                label_widget = self._create_label_field(field)
                layout.addWidget(label_widget)
            elif field_type == "row":
                row_widget = self._create_row_field(field, task_name)
                layout.addWidget(row_widget)
            elif field_type == "group":
                group_widget = self._create_group_field(field, task_name)
                layout.addWidget(group_widget)
            elif field_type == "checkbox_group":
                groups_config = field.get("groups", [])
                checkbox_group = MultiColumnCheckboxGroup(groups_config)
                checkbox_group.state_changed.connect(lambda _, __, ___, tn=task_name: self._on_field_changed(tn))
                layout.addWidget(checkbox_group)
                self._config_widgets[task_name][field["name"]] = checkbox_group
            continue
        
        field_layout = QHBoxLayout()
        field_layout.setSpacing(8)
        
        label = QLabel(field["label"] + ":")
        label.setStyleSheet(f"color: {self._colors['text_primary']};")
        field_layout.addWidget(label)
        
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
            field_layout.addWidget(combo)
            self._config_widgets[task_name][field["name"]] = combo
        
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
            field_layout.addWidget(line_edit)
            self._config_widgets[task_name][field["name"]] = line_edit
        
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
            field_layout.addWidget(spinbox)
            self._config_widgets[task_name][field["name"]] = spinbox
        
        elif field_type == "checkbox":
            checkbox = QCheckBox()
            checkbox.setChecked(field.get("default", False))
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    spacing: 4px;
                }}
            """)
            checkbox.stateChanged.connect(lambda _, tn=task_name: self._on_field_changed(tn))
            field_layout.addWidget(checkbox)
            self._config_widgets[task_name][field["name"]] = checkbox
        
        field_layout.addStretch()
        layout.addLayout(field_layout)
    
    return frame
```

### 2.2 `_create_label_field` 函数

```python
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
```

### 2.3 `_create_row_field` 函数

```python
def _create_row_field(self, field: dict, task_name: str) -> QWidget:
    """
    创建行布局容器
    
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
    
    row_widget_key = field.get("name", f"row_{id(field)}")
    self._config_widgets[task_name][row_widget_key] = {}
    
    for item in items:
        item_type = item.get("type", "dropdown")
        
        if item_type in ("row", "group"):
            raise ValueError(f"row 内禁止嵌套 {item_type} 类型")
        
        if item_type == "checkbox":
            checkbox_text = item.get("label", "")
            checkbox = QCheckBox(checkbox_text)
            default_val = item.get("default", False)
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
            row_layout.addWidget(checkbox)
            if item.get("name"):
                self._config_widgets[task_name][row_widget_key][item["name"]] = checkbox
        else:
            if item.get("label"):
                item_label = QLabel(item["label"])
                item_label.setStyleSheet(f"color: {self._colors['text_primary']};")
                row_layout.addWidget(item_label)
            
            widget = self._create_field_widget(item, item_type, task_name)
            if widget:
                if "width" in item:
                    widget.setFixedWidth(item["width"])
                row_layout.addWidget(widget)
                if item.get("name"):
                    self._config_widgets[task_name][row_widget_key][item["name"]] = widget
    
    if layout_align == "left":
        row_layout.addStretch()
    
    return row_widget
```

### 2.4 `_create_group_field` 函数

```python
def _create_group_field(self, field: dict, task_name: str) -> QGroupBox:
    """
    创建分组容器
    
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
    
    group_widget_key = field.get("name", f"group_{id(field)}")
    self._config_widgets[task_name][group_widget_key] = {}
    
    for sub_field in fields:
        sub_type = sub_field.get("type", "dropdown")
        
        if sub_type == "group":
            raise ValueError("group 内禁止嵌套子 group")
        
        if sub_type == "row":
            row_widget = self._create_row_field(sub_field, task_name)
            group_layout.addWidget(row_widget)
        elif sub_type == "label":
            label_widget = self._create_label_field(sub_field)
            group_layout.addWidget(label_widget)
        else:
            field_layout = QHBoxLayout()
            field_layout.setSpacing(8)
            
            if sub_field.get("label"):
                sub_label = QLabel(sub_field["label"])
                sub_label.setStyleSheet(f"color: {self._colors['text_primary']};")
                field_layout.addWidget(sub_label)
            
            widget = self._create_field_widget(sub_field, sub_type, task_name)
            if widget:
                field_layout.addWidget(widget)
                if sub_field.get("name"):
                    self._config_widgets[task_name][group_widget_key][sub_field["name"]] = widget
            
            field_layout.addStretch()
            group_layout.addLayout(field_layout)
    
    return group_box
```

### 2.5 `_create_field_widget` 函数

```python
def _create_field_widget(self, field: dict, field_type: str, task_name: str):
    """
    创建字段控件
    
    根据字段类型创建对应的控件实例。
    支持的类型：dropdown, text, number, checkbox, label
    
    Args:
        field (dict): 字段配置字典
        field_type (str): 字段类型
        task_name (str): 任务名称
        
    Returns:
        QWidget: 控件实例，如果类型不支持则返回 None
    """
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
        if field.get("name"):
            self._config_widgets[task_name][field["name"]] = combo
        return combo
    
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
        if field.get("name"):
            self._config_widgets[task_name][field["name"]] = line_edit
        return line_edit
    
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
        if field.get("name"):
            self._config_widgets[task_name][field["name"]] = spinbox
        return spinbox
    
    elif field_type == "checkbox":
        checkbox = QCheckBox()
        default_val = field.get("default", False)
        if isinstance(default_val, str):
            default_val = default_val.lower() in ('true', '1', 'yes')
        checkbox.setChecked(bool(default_val))
        checkbox.setStyleSheet(f"""
            QCheckBox {{
                spacing: 4px;
            }}
        """)
        checkbox.stateChanged.connect(lambda _, tn=task_name: self._on_field_changed(tn))
        if field.get("name"):
            self._config_widgets[task_name][field["name"]] = checkbox
        return checkbox
    
    elif field_type == "label":
        return self._create_label_field(field)
    
    return None
```

---

## 3. 参数的提取与回填逻辑

**文件位置**: `src/ui/panels/task_config_panel.py`

### 3.1 `_get_all_task_params` 函数（获取所有任务参数）

```python
def _get_all_task_params(self) -> dict:
    """
    获取所有任务参数
    
    Returns:
        dict: 任务参数字典
    """
    params = {}
    for task_name, widgets in self._config_widgets.items():
        params[task_name] = self._extract_params_from_widgets(widgets)
    return params
```

### 3.2 `_extract_params_from_widgets` 函数（递归提取）

```python
def _extract_params_from_widgets(self, widgets: dict) -> dict:
    """
    从控件字典中提取参数值（支持嵌套结构）
    
    Args:
        widgets (dict): 控件字典
        
    Returns:
        dict: 参数字典
    """
    params = {}
    for field_name, widget in widgets.items():
        if isinstance(widget, dict):
            params.update(self._extract_params_from_widgets(widget))
        elif isinstance(widget, QComboBox):
            params[field_name] = widget.currentText()
        elif isinstance(widget, QLineEdit):
            params[field_name] = widget.text()
        elif isinstance(widget, QSpinBox):
            params[field_name] = widget.value()
        elif isinstance(widget, QCheckBox):
            params[field_name] = widget.isChecked()
    return params
```

### 3.3 `_apply_task_params` 函数（应用任务参数）

```python
def _apply_task_params(self, task_params: dict):
    """
    应用任务参数
    
    Args:
        task_params (dict): 任务参数字典
    """
    for task_name, params in task_params.items():
        if task_name not in self._config_widgets:
            continue
        self._apply_params_to_widgets(self._config_widgets[task_name], params)
```

### 3.4 `_apply_params_to_widgets` 函数（递归回填）

```python
def _apply_params_to_widgets(self, widgets: dict, params: dict):
    """
    将参数应用到控件（支持嵌套结构）
    
    Args:
        widgets (dict): 控件字典
        params (dict): 参数字典
    """
    for field_name, widget in widgets.items():
        if isinstance(widget, dict):
            self._apply_params_to_widgets(widget, params)
        elif field_name in params:
            widget.blockSignals(True)
            if isinstance(widget, QComboBox):
                widget.setCurrentText(str(params[field_name]))
            elif isinstance(widget, QLineEdit):
                widget.setText(str(params[field_name]))
            elif isinstance(widget, QSpinBox):
                widget.setValue(int(params[field_name]))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(params[field_name]))
            widget.blockSignals(False)
```

### 3.5 `get_flattened_task_params` 函数（扁平化提取入口）

```python
def get_flattened_task_params(self, task_name: str) -> dict:
    """
    获取扁平化的任务参数（全量提取）
    
    将嵌套的 group/row 结构扁平化为简单的 {name: value} 字典
    提取所有具备交互能力的基础控件的值
    
    Args:
        task_name (str): 任务名称
        
    Returns:
        dict: 扁平化的参数字典
    """
    if task_name not in self._config_widgets:
        return {}
    
    flattened = {}
    self._flatten_params(self._config_widgets[task_name], flattened)
    return flattened
```

### 3.6 `_flatten_params` 函数（递归扁平化）

```python
def _flatten_params(self, widgets: dict, result: dict):
    """
    递归扁平化参数（全量提取）
    
    提取所有基础控件类型：QCheckBox、QComboBox、QLineEdit、QSpinBox
    
    Args:
        widgets (dict): 控件字典
        result (dict): 结果字典
    """
    for field_name, widget in widgets.items():
        if isinstance(widget, dict):
            self._flatten_params(widget, result)
        elif isinstance(widget, QCheckBox):
            result[field_name] = widget.isChecked()
        elif isinstance(widget, QComboBox):
            result[field_name] = widget.currentText()
        elif isinstance(widget, QLineEdit):
            result[field_name] = widget.text()
        elif isinstance(widget, QSpinBox):
            result[field_name] = widget.value()
```

---

## 附录：数据结构示意图

### 配置字典嵌套结构

```
task_config_definitions
├── "每日可换"
│   └── fields: [...]
│       ├── group (1_group)
│       │   └── fields: [...]
│       │       └── row (1_row)
│       │           └── items: [checkbox, checkbox, ...]
│       ├── group (2_group)
│       │   └── ...
│       ├── group (3_group)
│       │   └── ...
│       └── label (提示信息)
├── "摇钱树"
│   └── fields: [...]
│       └── row (choice_row)
│           └── items: [dropdown, label]
└── ...
```

### 控件存储结构

```
_config_widgets
├── "每日可换"
│   ├── "1_group" (dict)
│   │   └── "1_row" (dict)
│   │       ├── "每日签到" -> QCheckBox
│   │       ├── "每日江湖礼" -> QCheckBox
│   │       └── ...
│   ├── "2_group" (dict)
│   │   └── ...
│   └── "3_group" (dict)
│       └── ...
├── "摇钱树"
│   └── "choice_row" (dict)
│       ├── "choice" -> QComboBox
│       └── "choice_hint" -> QLabel (不存储值)
└── ...
```

---

> 文档生成时间：2026-03-12
