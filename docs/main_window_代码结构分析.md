# main_window.py 代码结构分析报告

> 分析日期：2026-03-09
> 文件路径：`src/ui/main_window.py`
> 总行数：**2156 行**

---

## 📊 总体概览

```
┌─────────────────────────────────────────────────────────────┐
│                    main_window.py 2156 行                    │
├─────────────────────────────────────────────────────────────┤
│  ████████████████████████████████████████ TaskConfigPanel   │
│  ████████████████████████████████████████ (996行, 46.2%)    │
│                                                              │
│  ██████████████████████████ ClassicScriptUI (549行, 25.5%)  │
│                                                              │
│  ████████████ ColorScheme (225行, 10.4%)                    │
│                                                              │
│  其他 4 个小类 (~186行, 8.6%)                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 内部类分布（按行数占比排序）

### 1. TaskConfigPanel — 最大"罪魁祸首" ⚠️

| 属性 | 值 |
|------|-----|
| 起止行 | 600-1596 |
| 行数 | **~996 行** |
| 占比 | **46.2%** |
| 职责 | 动态表单生成、配置管理、参数提取/应用 |

**问题分析**：这是一个巨型类，包含动态表单生成、配置管理、参数提取/应用等复杂逻辑，严重违反单一职责原则。

---

### 2. ClassicScriptUI — 主界面类

| 属性 | 值 |
|------|-----|
| 起止行 | 1599-2148 |
| 行数 | ~549 行 |
| 占比 | 25.5% |
| 职责 | 主窗口管理、信号连接、任务执行控制 |

---

### 3. ColorScheme — 配色方案类

| 属性 | 值 |
|------|-----|
| 起止行 | 38-263 |
| 行数 | ~225 行 |
| 占比 | 10.4% |
| 职责 | 颜色定义、QSS 样式表生成 |

**问题分析**：内嵌大量 QSS 样式字符串（约 170 行），可外置到 `.qss` 文件。

---

### 4. TaskListPanel — 任务列表面板

| 属性 | 值 |
|------|-----|
| 起止行 | 467-597 |
| 行数 | ~130 行 |
| 占比 | 6.0% |
| 职责 | 任务复选框列表显示 |

---

### 5. TabNavigationBar — 选项卡导航栏

| 属性 | 值 |
|------|-----|
| 起止行 | 344-464 |
| 行数 | ~120 行 |
| 占比 | 5.6% |
| 职责 | 选项卡导航控制 |

---

### 6. TabButton — 选项卡按钮

| 属性 | 值 |
|------|-----|
| 起止行 | 265-341 |
| 行数 | ~76 行 |
| 占比 | 3.5% |
| 职责 | 单个选项卡按钮样式 |

---

## 📋 TaskConfigPanel 内部方法清单

### UI 构建方法（巨型方法）

| 方法名 | 起始行 | 行数 | 职责 |
|--------|--------|------|------|
| `_create_task_section()` | 723 | ~137 | 创建单个任务配置区域 |
| `_create_field_widget()` | 1042 | ~89 | 创建字段控件 |
| `_create_row_field()` | 904 | ~68 | 创建行布局容器 |
| `_create_group_field()` | 974 | ~66 | 创建分组容器 |
| `_create_config_manager()` | 653 | ~58 | 创建配置管理区 |
| `_create_label_field()` | 862 | ~40 | 创建静态标签控件 |

### 配置操作逻辑

| 方法名 | 职责 |
|--------|------|
| `_on_save_config()` | 保存配置 |
| `_on_delete_config()` | 删除配置 |
| `_on_config_selected()` | 配置选择处理 |
| `_on_config_index_changed()` | 配置索引变化处理 |
| `_refresh_config_list()` | 刷新配置列表 |
| `_apply_config_data()` | 应用配置数据到 UI |
| `_reset_to_defaults()` | 重置为默认值 |
| `load_last_config()` | 加载最近使用的配置 |

### 参数提取/应用方法

| 方法名 | 职责 |
|--------|------|
| `_get_all_task_params()` | 获取所有任务参数 |
| `_extract_params_from_widgets()` | 从控件字典提取参数值 |
| `_apply_task_params()` | 应用任务参数 |
| `_apply_params_to_widgets()` | 将参数应用到控件 |
| `get_task_param()` | 获取指定任务的参数值 |
| `get_flattened_task_params()` | 获取扁平化的任务参数 |
| `_flatten_params()` | 递归扁平化参数 |

### 复选框状态管理方法

| 方法名 | 职责 |
|--------|------|
| `set_all_config_checkboxes()` | 设置任务所有配置复选框状态 |
| `set_specific_config_checkboxes()` | 根据结果字典精准设置复选框 |
| `has_config_checkboxes()` | 检查任务是否有配置复选框 |
| `are_all_config_checkboxes_unchecked()` | 检查所有复选框是否未勾选 |

---

## 📋 ClassicScriptUI 核心视图方法

| 方法名 | 起始行 | 行数 | 职责 |
|--------|--------|------|------|
| `init_ui()` | 1689 | ~85 | 初始化用户界面 |
| `_create_daily_page()` | 1855 | ~27 | 创建日常任务配置页面 |
| `_create_placeholder_page()` | 1833 | ~21 | 创建占位页面 |
| `_create_menu_bar()` | 1785 | ~28 | 创建菜单栏 |

---

## 🎯 重构优先级建议

| 优先级 | 问题 | 行数 | 建议方案 |
|--------|------|------|----------|
| 🔴 高 | **TaskConfigPanel 类过大** | 996 行 | 拆分到独立模块 `src/ui/panels/task_config_panel.py` |
| 🟡 中 | ColorScheme 样式字符串 | 170 行 | 外置到 `.qss` 文件 |
| 🟢 低 | TaskListPanel 可独立 | 130 行 | 移至 `src/ui/panels/task_list_panel.py` |
| 🟢 低 | TabButton/TabNavigationBar | 196 行 | 移至 `src/ui/widgets/tab_widgets.py` |

---

## 💡 下一步重构计划

### Phase 4：拆分 TaskConfigPanel（最大收益）

**目标结构**：

```
src/ui/panels/
├── __init__.py
├── bottom_panel.py        ✅ 已完成
├── log_panel.py           ✅ 已完成
├── task_list_panel.py     🆕 待创建
└── task_config_panel.py   🆕 待创建（最大收益）
```

**预期收益**：

- main_window.py 从 2156 行减少到约 1100 行
- TaskConfigPanel 独立维护，职责清晰
- 便于单元测试和复用

---

## 📈 重构进度追踪

| 阶段 | 任务 | 状态 | 行数变化 |
|------|------|------|----------|
| Phase 1 | 提取 ScriptWorker | ✅ 完成 | - |
| Phase 2 | 创建 StateManager/ConfigManager | ✅ 完成 | - |
| Phase 3 | 提取 BottomControlPanel/LogPanel | ✅ 完成 | 2309 → 2156 行 |
| Phase 4 | 提取 TaskConfigPanel | ⏳ 待执行 | 预计 2156 → ~1100 行 |
| Phase 5 | 提取其他小组件 | ⏳ 待执行 | 预计 ~900 行 |

---

## 📝 备注

本文档用于记录 `main_window.py` 的代码结构分析结果，为后续重构提供决策依据。
