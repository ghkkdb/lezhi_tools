# -*- coding: utf-8 -*-
"""
任务配置定义模块
================
管理任务配置项的定义和验证逻辑

支持配置继承机制：
    - 任务可通过 "extends" 字段继承共享配置
    - 共享配置只渲染一次，多个任务共享同一个配置区域
    - 点击任务列表中的任务会跳转到对应的共享配置区域
"""
from typing import Dict, Any, List, Optional


class TaskDefinitionConfig:
    """
    任务配置定义类
    
    专门管理任务配置项的定义、验证和参数处理
    
    属性：
        definitions: 任务配置定义字典
        shared_configs: 共享配置名列表
        
    方法：
        has_task_config: 检查任务是否有配置项
        get_task_default_params: 获取任务的默认参数
        get_task_mapped_param: 获取映射后的参数值
        get_shared_config_name: 获取任务继承的共享配置名
        is_shared_config: 检查配置名是否为共享配置
    """
    
    def __init__(self):
        """初始化任务配置定义"""
        self.definitions: Dict[str, Dict[str, Any]] = {}
        self.shared_configs: List[str] = []
        self._init_definitions()
        self._validate_definitions()
    
    def _init_definitions(self) -> None:
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
            - columns: 多列布局容器，垂直排列多行复选框
        
        嵌套约束：
            - row 内部仅允许基础控件或 label，禁止嵌套 row 或 group
            - group 内部允许基础控件、label 和 row，禁止嵌套子 group
        """
        self.definitions = {
            "每日可换": {
                "fields": [
                    {
                        "name": "checkbox_columns",
                        "type": "columns",
                        "columns": 5,
                        "column_spacing": 20,
                        "row_spacing": 4,
                        "items": [
                            {"name": "每日签到", "type": "checkbox", "label": "每日签到", "default": False},
                            {"name": "每日江湖礼", "type": "checkbox", "label": "每日江湖礼", "default": False},
                            {"name": "每日在线礼", "type": "checkbox", "label": "每日在线礼", "default": False},
                            {"name": "每日回馈礼", "type": "checkbox", "label": "每日回馈礼", "default": False},
                            {"name": "每日买银票", "type": "checkbox", "label": "每日买银票", "default": False},
                            {"name": "买鸡蛋", "type": "checkbox", "label": "买鸡蛋", "default": False},
                            {"name": "榫头卯眼", "type": "checkbox", "label": "榫头卯眼", "default": False},
                            {"name": "兑换武经志", "type": "checkbox", "label": "兑换武经志", "default": False},
                            {"name": "小红花礼盒", "type": "checkbox", "label": "小红花礼盒", "default": False},
                            {"name": "购买铜豆子", "type": "checkbox", "label": "购买铜豆子", "default": False},
                            {"name": "功绩换铜板", "type": "checkbox", "label": "功绩换铜板", "default": False},
                            {"name": "行当绝活", "type": "checkbox", "label": "行当绝活", "default": False},
                            {"name": "碧铜马坯", "type": "checkbox", "label": "碧铜马坯", "default": False},
                            {"name": "买吴越剑坯", "type": "checkbox", "label": "买吴越剑坯", "default": False},
                            {"name": "买白公鼎坯", "type": "checkbox", "label": "买白公鼎坯", "default": False},
                            {"name": "兑换锦芳绣", "type": "checkbox", "label": "兑换锦芳绣", "default": False},
                            {"name": "买形影心得", "type": "checkbox", "label": "买形影心得", "default": False},
                            {"name": "换高级萃石", "type": "checkbox", "label": "换高级萃石", "default": False},
                        ]
                    },
                    {
                        "name": "提示信息",
                        "type": "label",
                        "text": "提示：只执行勾选的内容，请在左侧任务列表勾选每日可换总开关",
                        "style": "info"
                    }
                ]
            },
            "摇钱树": {
                "section_width": 260, 
                "fields": [
                    {
                        "name": "choice_row",
                        "type": "row",
                        "items": [
                            {
                                "name": "choice",
                                "type": "dropdown",
                                "label": "摇树方式",
                                "options": ["轻轻摇【免费】", "用力摇【2000】", "全力摇【6000】"],
                                "default": "轻轻摇【免费】",
                                "value_map": {
                                    "轻轻摇【免费】": 1,
                                    "用力摇【2000】": 0,
                                    "全力摇【6000】": 2
                                }
                            }
                        ]
                    }
                ]
            },
            "华山论剑1v1": {
                "section_width": 260, 
                "fields": [
                    {
                        "name": "config_row",
                        "type": "row",
                        "items": [
                            {
                                "name": "count",
                                "type": "number",
                                "label": "论剑次数",
                                "default": 1,
                                "min": 1,
                                "max": 999
                            },
                            {
                                "name": "quick_exit",
                                "type": "checkbox",
                                "label": "秒退",
                                "default": True
                            }
                        ]
                    }
                ]
            },
            "聚义平冤": {
                "section_width": 260, 
                "fields": [
                    {
                        "name": "config_row",
                        "type": "row",
                        "items": [
                            {
                                "name": "mode",
                                "type": "dropdown",
                                "label": "完成方式",
                                "options": ["发布悬赏", "脚本完成"],
                                "default": "发布悬赏",
                            }
                        ]
                    }
                ]
            },
            "江湖行商": {
                "section_width": 260, 
                "fields": [
                    {
                        "name": "config_row",
                        "type": "row",
                        "items": [
                            {
                                "name": "mode",
                                "type": "dropdown",
                                "label": "完成方式",
                                "options": ["发布悬赏", "脚本完成"],
                                "default": "发布悬赏",
                            }
                        ]
                    }
                ]
            },
            "江湖英雄榜": {
                "section_width": 260, 
                "fields": [
                    {
                        "name": "config_row",
                        "type": "row",
                        "items": [
                            {
                                "name": "count",
                                "type": "number",
                                "label": "次数",
                                "default": 1,
                                "min": 1,
                                "max": 999
                            },
                            {
                                "name": "quick_exit",
                                "type": "checkbox",
                                "label": "秒退",
                                "default": True
                            }
                        ]
                    }
                ]
            },
            "寻访佳园": {
                "section_width": 260, 
                "fields": [
                    {
                        "name": "count",
                        "type": "number",
                        "label": "次数",
                        "default": 5,
                        "min": 1,
                        "max": 20
                    }
                ]
            },
            "华山论剑3v3": {
                "section_width": 260, 
                "fields": [
                    {
                        "name": "config_row",
                        "type": "row",
                        "items": [
                            {
                                "name": "count",
                                "type": "number",
                                "label": "次数",
                                "default": 1,
                                "min": 1,
                                "max": 10
                            },
                            {
                                "name": "quick_exit",
                                "type": "checkbox",
                                "label": "秒退",
                                "default": True
                            }
                        ]
                    }
                ]
            },
            "帮派捐献": {
                "section_width": 260, 
                "fields": [
                    {
                        "name": "donate_row",
                        "type": "row",
                        "items": [
                            {
                                "name": "捐献铜币",
                                "type": "checkbox",
                                "label": "铜币",
                                "default": True
                            },
                            {
                                "name": "捐献银两",
                                "type": "checkbox",
                                "label": "银两",
                                "default": False
                            },
                            {
                                "name": "捐献元宝",
                                "type": "checkbox",
                                "label": "元宝",
                                "default": False
                            }
                        ]
                    }
                ]
            },
            "组队配置": {
                "is_shared": True,
                # "section_width": 520,
                "fields": [
                    {
                        "name": "mode_row",
                        "type": "row",
                        "items": [
                            {
                                "name": "team_mode",
                                "type": "dropdown",
                                "label": "组队方式",
                                "options": ["队长组队", "队员混队"],
                                "default": "队长组队",
                                "value_map": {
                                    "队长组队": "leader",
                                    "队员混队": "member"
                                }
                            },
                            {
                                "name": "team_size",
                                "type": "dropdown",
                                "label": "组队人数",
                                "options": ["1人", "2人", "3人", "4人", "5人", "6人", "7人", "8人", "9人", "10人"],
                                "default": "1人",
                                "value_map": {
                                    "1人": 1, "2人": 2, "3人": 3, "4人": 4, "5人": 5,
                                    "6人": 6, "7人": 7, "8人": 8, "9人": 9, "10人": 10
                                }
                            }
                        ]
                    },
                    {
                        "name": "options_row",
                        "type": "row",
                        "items": [
                            {
                                "name": "season_shout",
                                "type": "checkbox",
                                "label": "赛季喊话",
                                "default": False
                            },
                            {
                                "name": "xiuwei_limit",
                                "type": "text",
                                "label": "修为限制",
                                "default": "",
                                "placeholder": "如：100000",
                                "width": 100
                            }
                        ]
                    }
                ]
            },
            "日常副本": {"extends": "组队配置"},
            "副本悬赏": {"extends": "组队配置"},
        }

        self._init_shared_configs()
    
    def _init_shared_configs(self) -> None:
        """
        初始化共享配置列表
        
        遍历所有配置定义，识别标记为 is_shared=True 的共享配置
        """
        self.shared_configs = []
        for config_name, config_def in self.definitions.items():
            if config_def.get("is_shared", False):
                self.shared_configs.append(config_name)
    
    def _validate_definitions(self) -> None:
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
            """验证 row 内的 items"""
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
            """验证 group 内的 fields"""
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
            """验证顶层字段列表"""
            for idx, field in enumerate(fields):
                field_type = field.get("type", "")
                field_path = f"任务[{task_name}].fields[{idx}]"
                
                if field_type == "row":
                    items = field.get("items", [])
                    validate_row_items(items, field_path)
                
                elif field_type == "group":
                    group_fields = field.get("fields", [])
                    validate_group_fields(group_fields, field_path)
        
        for task_name, task_def in self.definitions.items():
            if "extends" in task_def:
                continue
            fields = task_def.get("fields", [])
            validate_fields(fields, task_name)
    
    def get_shared_config_name(self, task_name: str) -> Optional[str]:
        """
        获取任务继承的共享配置名
        
        参数：
            task_name: 任务名称
            
        返回：
            Optional[str]: 共享配置名，如果没有继承则返回 None
        """
        if task_name not in self.definitions:
            return None
        
        task_def = self.definitions[task_name]
        if "extends" in task_def:
            return task_def["extends"]
        return None
    
    def is_shared_config(self, config_name: str) -> bool:
        """
        检查配置名是否为共享配置
        
        参数：
            config_name: 配置名称
            
        返回：
            bool: 是否为共享配置
        """
        return config_name in self.shared_configs
    
    def has_task_config(self, task_name: str) -> bool:
        """
        检查任务是否有配置项
        
        参数：
            task_name: 任务名称
            
        返回：
            bool: 是否有配置项
        """
        return task_name in self.definitions
    
    def get_task_default_params(self, task_name: str) -> dict:
        """
        获取任务的默认参数
        
        支持共享配置继承：如果任务继承自共享配置，则获取共享配置的默认参数。
        
        参数：
            task_name: 任务名称
            
        返回：
            dict: 默认参数字典
        """
        actual_name = self.get_shared_config_name(task_name) or task_name
        
        if actual_name not in self.definitions:
            return {}
        
        task_def = self.definitions[actual_name]
        return self._extract_default_params(task_def.get("fields", []))
    
    def get_task_mapped_param(self, task_name: str, param_name: str, value: Any) -> Any:
        """
        获取映射后的参数值
        
        支持共享配置继承：如果任务继承自共享配置，则使用共享配置的映射规则。
        
        参数：
            task_name: 任务名称
            param_name: 参数名称
            value: 原始值
            
        返回：
            Any: 映射后的值
        """
        actual_name = self.get_shared_config_name(task_name) or task_name
        
        if actual_name not in self.definitions:
            return value
        
        task_def = self.definitions[actual_name]
        return self._get_mapped_param_from_fields(task_def.get("fields", []), param_name, value)
    
    def _get_mapped_param_from_fields(self, fields: list, param_name: str, value: Any) -> Any:
        """
        从字段列表中获取映射后的参数值
        
        参数：
            fields: 字段列表
            param_name: 参数名称
            value: 原始值
            
        返回：
            Any: 映射后的值
        """
        for field in fields:
            field_type = field.get("type", "dropdown")
            
            if field_type == "row":
                items = field.get("items", [])
                result = self._get_mapped_param_from_fields(items, param_name, value)
                if result != value:
                    return result
            elif field_type == "group":
                sub_fields = field.get("fields", [])
                result = self._get_mapped_param_from_fields(sub_fields, param_name, value)
                if result != value:
                    return result
            elif field_type == "columns":
                items = field.get("items", [])
                result = self._get_mapped_param_from_fields(items, param_name, value)
                if result != value:
                    return result
            elif field.get("name") == param_name and "value_map" in field:
                return field["value_map"].get(value, value)
        
        return value
    
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
