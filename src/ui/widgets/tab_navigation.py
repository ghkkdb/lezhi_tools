# -*- coding: utf-8 -*-
"""
选项卡导航组件模块
==================
提供选项卡导航栏和选项卡按钮组件。

模块结构：
    - TabButton: 选项卡按钮组件
    - TabNavigationBar: 选项卡导航栏组件
"""
from PyQt5.QtWidgets import QPushButton, QWidget, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal, pyqtProperty

from src.config import config
from src.ui.styles.color_scheme import ColorScheme


class TabButton(QPushButton):
    """
    选项卡按钮组件
    
    特点：
        - 文本标签样式
        - 选中状态高亮显示
        - 现代Edge风格
    
    属性：
        active: 激活状态属性（支持 QSS 动画）
    """
    
    def __init__(self, text: str, parent=None):
        """
        初始化选项卡按钮
        
        Args:
            text (str): 按钮文本
            parent: 父组件
        """
        super().__init__(text, parent)
        self._is_active = False
        self._colors = ColorScheme.get_colors()
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(config.ui_sizes["tab_height"])
        self.setMinimumWidth(config.ui_sizes["tab_min_width"])
        self.setProperty("tab_button", True)
        self._update_style()
    
    def get_active(self) -> bool:
        """
        获取激活状态
        
        Returns:
            bool: 是否激活
        """
        return self._is_active
    
    def set_active(self, active: bool):
        """
        设置激活状态
        
        Args:
            active (bool): 是否激活
        """
        self._is_active = active
        self._update_style()
    
    active = pyqtProperty(bool, get_active, set_active)
    
    def _update_style(self):
        """
        更新样式
        
        根据激活状态应用不同的样式表：
        - 激活状态：主色背景，白色文字
        - 非激活状态：透明背景，灰色文字
        """
        colors = self._colors
        if self._is_active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['primary']};
                    border: none;
                    border-radius: 0px;
                    color: {colors['nav_active_text']};
                    font-size: 12px;
                    font-weight: 600;
                    padding: 4px 16px;
                }}
                QPushButton:hover {{
                    background-color: {colors['primary_hover']};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    border-bottom: 2px solid transparent;
                    color: {colors['text_secondary']};
                    font-size: 12px;
                    font-weight: 500;
                    padding: 4px 16px;
                }}
                QPushButton:hover {{
                    background-color: {colors['surface_hover']};
                    color: {colors['text_primary']};
                }}
            """)


class TabNavigationBar(QWidget):
    """
    选项卡导航栏组件
    
    特点：
        - 水平排列的文本标签选项卡
        - 当前选中选项卡高亮显示
        - 从配置动态加载导航项
        - 支持运行时添加新选项卡
    
    信号：
        currentChanged: 当前选项卡变化信号，参数为新索引
    
    属性：
        _tabs: 选项卡按钮列表
        _tab_keys: 选项卡键名到索引的映射
        _current_index: 当前选中索引
    """
    
    currentChanged = pyqtSignal(int)
    
    def __init__(self, parent=None):
        """
        初始化导航栏
        
        Args:
            parent: 父组件
        """
        super().__init__(parent)
        self._tabs = []
        self._tab_keys = {}
        self._current_index = 0
        self._colors = ColorScheme.get_colors()
        self._setup_ui()
        self._load_tabs_from_config()
    
    def _setup_ui(self):
        """
        初始化UI
        
        创建水平布局，设置导航栏样式。
        """
        self.setObjectName("tabNavigationBar")
        self.setFixedHeight(config.ui_sizes["nav_height"])
        self.setStyleSheet(f"""
            #tabNavigationBar {{
                background-color: {self._colors['nav_bg']};
                border-bottom: 1px solid {self._colors['nav_border']};
            }}
        """)
        
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(8, 0, 8, 0)
        self._layout.setSpacing(0)
        self._layout.addStretch()
    
    def _load_tabs_from_config(self):
        """
        从配置加载导航选项卡
        
        读取 config.get_nav_tabs() 返回的导航配置，
        为每个配置项创建一个选项卡。
        """
        nav_tabs = config.get_nav_tabs()
        for tab_info in nav_tabs:
            self.addTab(tab_info["name"], tab_info.get("key"))
    
    def addTab(self, text: str, key: str = None) -> int:
        """
        添加选项卡
        
        Args:
            text (str): 选项卡文本
            key (str, optional): 选项卡唯一标识。默认为 None，此时使用 text.lower() 作为键。
        
        Returns:
            int: 新添加选项卡的索引
        """
        index = len(self._tabs)
        
        if key is None:
            key = text.lower()
        
        tab = TabButton(text, self)
        tab.clicked.connect(lambda checked, idx=index: self._on_tab_clicked(idx))
        
        self._tabs.append(tab)
        self._tab_keys[key] = index
        self._layout.insertWidget(self._layout.count() - 1, tab)
        
        if index == 0:
            tab.set_active(True)
        
        return index
    
    def addTabFromConfig(self, tab_info: dict):
        """
        从配置信息添加选项卡
        
        Args:
            tab_info (dict): 选项卡配置字典，包含 name, key 等字段
        """
        self.addTab(tab_info.get("name"), tab_info.get("key"))
    
    def _on_tab_clicked(self, index: int):
        """
        选项卡点击事件处理
        
        Args:
            index (int): 被点击选项卡的索引
        """
        if index != self._current_index:
            self.setCurrentIndex(index)
    
    def setCurrentIndex(self, index: int):
        """
        设置当前选中选项卡
        
        Args:
            index (int): 目标选项卡索引
        """
        if 0 <= index < len(self._tabs):
            old_index = self._current_index
            self._current_index = index
            
            for i, tab in enumerate(self._tabs):
                tab.set_active(i == index)
            
            if old_index != index:
                self.currentChanged.emit(index)
    
    def getCurrentIndex(self) -> int:
        """
        获取当前选中索引
        
        Returns:
            int: 当前选中选项卡的索引
        """
        return self._current_index
    
    def getTabCount(self) -> int:
        """
        获取选项卡总数
        
        Returns:
            int: 选项卡数量
        """
        return len(self._tabs)
