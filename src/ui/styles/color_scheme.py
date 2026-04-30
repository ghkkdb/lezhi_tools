# -*- coding: utf-8 -*-
"""
配色方案模块
============
提供统一的 UI 配色方案和样式表生成功能。

模块结构：
    - ColorScheme: 配色方案管理类
    - ColorSchemeKeys: 配色键名常量
"""
from typing import Dict


class ColorSchemeKeys:
    """
    配色键名常量
    
    定义所有可用的配色键名，便于类型检查和代码补全
    """
    PRIMARY = 'primary'
    PRIMARY_HOVER = 'primary_hover'
    PRIMARY_PRESSED = 'primary_pressed'
    SECONDARY = 'secondary'
    ACCENT = 'accent'
    SUCCESS = 'success'
    WARNING = 'warning'
    DANGER = 'danger'
    BACKGROUND = 'background'
    SURFACE = 'surface'
    SURFACE_HOVER = 'surface_hover'
    SURFACE_ELEVATED = 'surface_elevated'
    BORDER = 'border'
    BORDER_STRONG = 'border_strong'
    TEXT_PRIMARY = 'text_primary'
    TEXT_SECONDARY = 'text_secondary'
    TEXT_DISABLED = 'text_disabled'
    SHADOW = 'shadow'
    FOCUS_RING = 'focus_ring'
    NAV_BG = 'nav_bg'
    NAV_BORDER = 'nav_border'
    NAV_ACTIVE_BG = 'nav_active_bg'
    NAV_ACTIVE_TEXT = 'nav_active_text'
    CONTENT_BG = 'content_bg'
    BOTTOM_BG = 'bottom_bg'
    GROUP_BG = 'group_bg'
    INPUT_BG = 'input_bg'


class ColorScheme:
    """
    配色方案管理类
    
    现代Edge浏览器风格配色方案，清新简洁的视觉效果。
    提供颜色字典获取和全局样式表生成功能。
    
    使用示例：
        colors = ColorScheme.get_colors()
        primary_color = colors['primary']
        
        stylesheet = ColorScheme.generate_stylesheet()
        widget.setStyleSheet(stylesheet)
    """
    
    @staticmethod
    def get_colors() -> Dict[str, str]:
        """
        获取现代Edge风格配色方案
        
        Returns:
            Dict[str, str]: 配色字典，包含所有颜色定义
        """
        return {
            'primary': '#0078D4',
            'primary_hover': '#106EBE',
            'primary_pressed': '#005A9E',
            'secondary': '#6B6B6B',
            'accent': '#0078D4',
            'success': '#107C10',
            'warning': '#CA5010',
            'danger': '#D13438',
            'background': '#F3F3F3',
            'surface': '#FFFFFF',
            'surface_hover': '#F5F5F5',
            'surface_elevated': '#FAFAFA',
            'border': '#E1E1E1',
            'border_strong': '#D1D1D1',
            'text_primary': '#1A1A1A',
            'text_secondary': '#5C5C5C',
            'text_disabled': '#A0A0A0',
            'shadow': '0 2px 4px rgba(0,0,0,0.1)',
            'focus_ring': '#0078D4',
            'nav_bg': '#FFFFFF',
            'nav_border': '#E1E1E1',
            'nav_active_bg': '#0078D4',
            'nav_active_text': '#FFFFFF',
            'content_bg': '#FFFFFF',
            'bottom_bg': '#FAFAFA',
            'group_bg': '#FFFFFF',
            'input_bg': '#FFFFFF',
        }
    
    @staticmethod
    def generate_stylesheet() -> str:
        """
        生成全局样式表
        
        生成适用于整个应用程序的 QSS 样式表，
        包含 QMainWindow、QGroupBox、QPushButton、QCheckBox、
        QTextEdit、QScrollBar、QLabel、QStackedWidget 等控件的样式。
        
        Returns:
            str: QSS 样式表字符串
        """
        colors = ColorScheme.get_colors()
        
        return f"""
            QMainWindow {{
                background-color: {colors['background']};
            }}
            
            QGroupBox {{
                font-weight: 600;
                border: 1px solid {colors['border']};
                border-radius: 4px;
                margin: 0px;
                padding: 0px;
                background-color: {colors['group_bg']};
                font-size: 12px;
                color: {colors['text_primary']};
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: {colors['text_primary']};
                font-size: 12px;
                font-weight: 600;
            }}
            
            QPushButton {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border_strong']};
                border-radius: 4px;
                padding: 6px 14px;
                color: {colors['text_primary']};
                font-size: 12px;
                font-weight: 500;
            }}
            
            QPushButton:hover {{
                background-color: {colors['surface_hover']};
                border-color: {colors['primary']};
            }}
            
            QPushButton:pressed {{
                background-color: {colors['border']};
            }}
            
            QPushButton:disabled {{
                background-color: {colors['surface_elevated']};
                color: {colors['text_disabled']};
                border: 1px solid {colors['border']};
            }}
            
            QCheckBox {{
                font-size: 12px;
                spacing: 8px;
                color: {colors['text_primary']};
            }}
            
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {colors['border_strong']};
                border-radius: 3px;
                background-color: {colors['surface']};
            }}
            
            QCheckBox::indicator:unchecked {{
                background-color: {colors['surface']};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {colors['primary']};
                border-color: {colors['primary']};
            }}
            
            QCheckBox::indicator:hover {{
                border-color: {colors['primary']};
            }}
            
            QTextEdit {{
                background-color: {colors['input_bg']};
                border: 1px solid {colors['border']};
                border-radius: 4px;
                font-family: 'Consolas', 'SimSun', 'Monaco';
                font-size: 11px;
                padding: 6px;
                color: {colors['text_primary']};
                selection-background-color: {colors['primary']};
                selection-color: #FFFFFF;
            }}
            
            QTextEdit:focus {{
                border: 2px solid {colors['primary']};
            }}
            
            QScrollBar:vertical {{
                background-color: transparent;
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: rgba(0, 0, 0, 0.2);
                min-height: 30px;
                border-radius: 5px;
                margin: 1px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: rgba(0, 0, 0, 0.4);
            }}
            
            QScrollBar::handle:vertical:pressed {{
                background-color: rgba(0, 0, 0, 0.5);
            }}
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
                background-color: transparent;
            }}
            
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background-color: transparent;
            }}
            
            QScrollBar:horizontal {{
                background-color: transparent;
                height: 10px;
                margin: 0px;
                border-radius: 5px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: rgba(0, 0, 0, 0.2);
                min-width: 30px;
                border-radius: 5px;
                margin: 1px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: rgba(0, 0, 0, 0.4);
            }}
            
            QScrollBar::handle:horizontal:pressed {{
                background-color: rgba(0, 0, 0, 0.5);
            }}
            
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0px;
                background-color: transparent;
            }}
            
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {{
                background-color: transparent;
            }}
            
            QLabel {{
                color: {colors['text_primary']};
                font-size: 12px;
                background-color: transparent;
            }}
            
            QStackedWidget {{
                background-color: {colors['content_bg']};
                border: none;
            }}
        """
