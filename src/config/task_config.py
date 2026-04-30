# -*- coding: utf-8 -*-
"""
任务配置模块
============
管理游戏任务相关的配置参数
"""
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Union, Any


@dataclass
class TaskConfig:
    """
    任务配置类
    
    管理游戏任务的配置参数
    
    属性：
        daily_tasks: 日常任务列表
        chaguan_dt: 茶馆答题选项坐标
        chaguan_dt_weights: 答题选项权重
        bangpai_btn: 帮派按钮坐标
        yaoqianshu_options: 摇钱树选项配置
    """
    daily_tasks: List[Union[str, List[str]]] = field(default_factory=lambda: [
            "每日可换","山河器","每日一卦", "茶馆说书", 
            "课业任务", "帮派任务",["门客设宴", "破阵设宴"],["帮派捐献","摇钱树"],
            ["华山论剑1v1", "华山论剑3v3"],["寻访佳园","江湖英雄榜"],"日常副本", "副本悬赏",
            ["聚义平冤", "江湖行商"],"天下宗师","剑取楼兰日常",
             "万象拍照","坐观万象",
        ])
    
    chaguan_dt: List[Tuple[int, int]] = field(default_factory=lambda: [
        (908, 248), (908, 314), (908, 377), (908, 439)
    ])
    
    chaguan_dt_weights: List[float] = field(default_factory=lambda: [
        0.35, 0.35, 0.2, 0.1
    ])
    
    bangpai_btn: Tuple[int, int] = (235, 469)
    
    yaoqianshu_options: Dict[int, Dict[str, Any]] = field(default_factory=lambda: {
        0: {"name": "用力摇", "coord": (620, 301)},
        1: {"name": "轻轻摇", "coord": (633, 258)},
        2: {"name": "全力", "coord": (659, 208)}
    })
