# -*- coding: utf-8 -*-

"""
辅助功能模块
============
提供游戏辅助操作的工具函数

主要功能：
    - win_gb: 关闭意外窗口
    - wp_gb: 关闭小物品窗口
    - zhd: 打开活动界面
    - TuiLIKaShi_set: 脱离卡死
    - DuanYou_set: 端游设置
    - TuiDui_set: 退队功能
    - baoguo_manSet: 包裹满处理
    - baogou_jsSet: 包裹解锁
    - JN_set: 前往金陵
"""
import time
import random
import win32gui
from src.utils import background_click, background_key, background_drag, find_image
from src.utils.logger import get_logger
from src.config import config
from .controller import task_controller

logger = get_logger('helpers')

def win_gb(
    hwnd: int,
    templates: list | str | None = None,
    roi: list | None = None,
    max_attempts: int = 2,
    wait_time: float = 1,
    threshold: float = 0.8,
    max_loop_time: float = 60
) -> int:
    """
    持续查找并关闭所有匹配的意外窗口。
    优化逻辑：无弹窗时仅查询1次极速放行；发现弹窗后，重试次数提升至 max_attempts 确保清理干净。

    参数：
        hwnd: 窗口句柄
        templates: 模板图片路径列表或单个路径
        roi: 查找区域 [x, y, width, height]
        max_attempts: 发现弹窗后，确保清理干净的最大连续未找到次数
        wait_time: 每次查找间隔时间（秒）
        threshold: 匹配阈值（0-1）
        max_loop_time: 最大循环时间（秒），防止无限循环

    返回：
        int: 关闭的窗口数量
    """
    if not win32gui.IsWindow(hwnd):
        logger.warning("无效的窗口句柄")
        return 0

    # 默认模板初始化
    if templates is None:
        templates = [
            config.get_img_path("chushihua_/gb_xwp.png"),
            config.get_img_path("chushihua_/gb_mryg.png"),
            config.get_img_path("chushihua_/gb_3.png")
        ]
    elif isinstance(templates, str):
        templates = [templates]

    closed_count = 0
    consecutive_not_found = 0
    start_time = time.time()
    
    # 初始只进行 1 轮查询
    current_max_attempts = 1 

    try:
        while consecutive_not_found < current_max_attempts:
            task_controller.smart_sleep(1)
            # 点击0，0，确保窗口响应
            background_click(hwnd, 0, 0, button="left", delay=60)
            task_controller.smart_sleep(0.1)

            task_controller.check_status()
            # 外层防卡死超时判断
            if time.time() - start_time > max_loop_time:
                logger.warning("关闭窗口超时，退出循环")
                break

            found_in_this_round = False
            
            for template_path in templates:
                pos_gb = find_image(hwnd, template_path, roi=roi, threshold=threshold)

                # 发现弹窗（将原来的 while 改为 if，点一次就换下一个模板，防止死磕）
                if pos_gb is not None:
                    found_in_this_round = True
                    
                    # 关键逻辑：一旦发现弹窗，说明环境不干净，将查询次数提升至传入的 max_attempts
                    current_max_attempts = max_attempts 

                    logger.debug(f"发现意外窗口 (已关闭: {closed_count})")
                    
                    # 注意：如果底层的 delay 是秒，这里的 60 会导致立刻超时。如果是毫秒则没问题。
                    background_click(hwnd, pos_gb[0], pos_gb[1], button="left", delay=60)
                    closed_count += 1
                    task_controller.smart_sleep(0.5) # 点击后的短暂缓冲

            # 轮询结果结算
            if found_in_this_round:
                # 本轮有收获，连续未找到次数清零，继续下一轮扫荡
                consecutive_not_found = 0
            else:
                # 本轮无收获，增加未找到次数
                consecutive_not_found += 1
                # 如果还没达到最大允许的未找到次数，等待 wait_time 后再找
                if consecutive_not_found < current_max_attempts:
                    task_controller.smart_sleep(wait_time)

        return closed_count

    except Exception as e:
        logger.error(f"关闭意外窗口时出错: {str(e)}", exc_info=True)
        return closed_count


def wp_gb(hwnd, log_signal=None):
    """
    关闭小物品窗口

    参数：
        hwnd: 窗口句柄
        log_signal: 日志信号对象（已弃用）
    """
    for i in range(5):
        pos_gb_xwp = find_image(
            hwnd,
            config.get_img_path("chushihua_/gb_xwp.png"),
            roi=[500, 140, 430, 360],
            threshold=0.8
        )
        task_controller.smart_sleep(1)
        if pos_gb_xwp is not None:
            logger.debug("意外窗口关闭")
            background_click(hwnd, pos_gb_xwp[0], pos_gb_xwp[1], button="left", delay=60)
    return False


def zhd(hwnd):
    """
    打开活动界面

    Args:
        hwnd: 窗口句柄
    """
    win_gb(hwnd)

    task_controller.check_status()
    background_key(hwnd, 'B')
    task_controller.smart_sleep(1)
    
    pos = find_image(hwnd, config.get_img_path("chushihua_/hdsz.png"), threshold=0.8)
    if pos is None:
        return False
    
    background_click(hwnd, pos[0], pos[1], button="left", delay=60)
    task_controller.smart_sleep(1)
    
    pos_hd = find_image(hwnd, config.get_img_path("chushihua_/hd.png"), threshold=0.8)
    if pos_hd is None:
        return False
    
    background_click(hwnd, pos_hd[0], pos_hd[1], button="left", delay=60)
    task_controller.smart_sleep(2)
    
    pos_hdqd = find_image(hwnd, config.get_img_path("chushihua_/hdqd.png"), threshold=0.8)
    if pos_hdqd is None:
        return False
    
    logger.debug("进入活动界面")
    task_controller.smart_sleep(2)
    return True


def TuiLIKaShi_set(hwnd, pos=None):
    """
    脱离卡死功能

    Args:
        hwnd: 窗口句柄
        pos: 图像检测位置（可选，由装饰器回调传入）

    Returns:
        bool: 始终返回 True
    """
    win_gb(hwnd)
    logger.debug("脱离卡死")
    
    task_controller.check_status()
    pos_1 = find_image(hwnd, config.get_img_path("chushihua_/kashi.png"), roi=[900, 460, 40, 40], threshold=0.8)
    
    if pos_1 is None:
        logger.debug("未找到卡死风车按钮")
        return False
    
    
    background_click(hwnd, pos_1[0], pos_1[1], button="left", delay=60)
    task_controller.smart_sleep(2)

    # pos_2 = find_image(hwnd, config.get_img_path("chushihua_/tlks.png"), roi=[860, 380, 40, 40], threshold=0.8)
    pos_2 = find_image(hwnd, config.get_img_path("chushihua_/tlks.png"), threshold=0.8)
    if pos_2 is None:
        logger.debug("未找到脱离卡死按钮")
        return False
    
    background_click(hwnd, pos_2[0], pos_2[1], button="left", delay=60)
    # background_click(hwnd, 918, 437, button="left", delay=60)
    task_controller.smart_sleep(2)
    
    pos_3 = find_image(hwnd, config.get_img_path("chushihua_/ksqueding.png"), roi=[560, 320, 120, 60], threshold=0.8)
    if pos_3 is None:
        logger.debug("未找到确认脱离卡死按钮")
        return False
    
    background_click(hwnd, pos_3[0], pos_3[1], button="left", delay=60)
    task_controller.smart_sleep(2)
    return True


def DuanYou_set(hwnd):
    """
    端游设置功能

    Args:
        hwnd: 窗口句柄

    Returns:
        bool: 始终返回 True
    """
    win_gb(hwnd)
    task_controller.check_status()
    background_key(hwnd, 'Esc')
    task_controller.smart_sleep(2)
    
    jm2_pos = find_image(hwnd, config.get_img_path("chushihua_/jmms_2.png"), threshold=0.8)
    print(jm2_pos)
    
    if jm2_pos is not None:
        background_click(hwnd, jm2_pos[0], jm2_pos[1], button="left", delay=60)
        task_controller.smart_sleep(1)
        background_click(hwnd, 599, 232, button="left", delay=60)
        task_controller.smart_sleep(1)
        background_click(hwnd, 474, 347, button="left", delay=60)
        task_controller.smart_sleep(1)
    task_controller.smart_sleep(2)
    pos = find_image(hwnd, config.get_img_path("chushihua_/dyms.png"), threshold=0.8)
    if pos is not None:
        background_click(hwnd, 521, 423, button="left", delay=60)
        task_controller.smart_sleep(1)
        win_gb(hwnd)
        task_controller.smart_sleep(3)
    
    return True


def TuiDui_set(hwnd):
    """
    退队功能

    Args:
        hwnd: 窗口句柄

    Returns:
        bool: 始终返回 True
    """
    win_gb(hwnd)
    task_controller.check_status()
    background_key(hwnd, 'T')
    task_controller.smart_sleep(2)
    
    pos = find_image(hwnd, config.get_img_path("chushihua_/tuidui.png"), threshold=0.8)
    if pos is None:
        win_gb(hwnd)
        return True
    
    logger.debug("退队")
    background_click(hwnd, pos[0], pos[1], button="left", delay=60)
    task_controller.smart_sleep(1)
    logger.debug("确认退队")
    background_click(hwnd, 619, 352, button="left", delay=60)
    task_controller.smart_sleep(1)
    win_gb(hwnd)
    return True


def baoguo_manSet(hwnd):
    """
    处理包裹满提示

    Args:
        hwnd: 窗口句柄

    Returns:
        bool: 是否处理了包裹满提示
    """
    pos_full = find_image(
        hwnd,
        config.get_img_path("chushihua_/baogou.png"),
        roi=[620, 320, 100, 100],
        threshold=0.7
    )
    if pos_full is None:
        return True
    
    background_click(hwnd, pos_full[0], pos_full[1], button="left", delay=60)
    task_controller.smart_sleep(1)
    
    pos_claim = find_image(hwnd, config.get_img_path("chushihua_/baogou_lq.png"), threshold=0.8)
    if pos_claim is None:
        return False
    
    background_click(hwnd, pos_claim[0], pos_claim[1], button="left", delay=60)
    task_controller.smart_sleep(3)
    background_click(hwnd, 621, 352, button="left", delay=60)
    task_controller.smart_sleep(1)
    
    return True


def baogou_jsSet(hwnd):
    """
    解锁包裹格子

    Args:
        hwnd: 窗口句柄
    """
    background_key(hwnd, 'B')
    task_controller.smart_sleep(1)
    
    pos_set = find_image(hwnd, config.get_img_path("chushihua_/hdsz.png"), threshold=0.8)
    if pos_set is None:
        return
    
    while True:
        task_controller.check_status()
        background_drag(hwnd, 641, 394, 641, 94, drag_duration=1)
        task_controller.smart_sleep(1)
        
        pos_unlock = find_image(hwnd, config.get_img_path("chushihua_/baogou_jies.png"), threshold=0.8)
        if pos_unlock is None:
            continue
        
        background_click(hwnd, pos_unlock[0], pos_unlock[1], button="left", delay=60)
        task_controller.smart_sleep(2)
        background_click(hwnd, 615, 352, button="left", delay=60)
        task_controller.smart_sleep(1)
        background_click(hwnd, 499, 402, button="left", delay=60)
        task_controller.smart_sleep(2)
        background_click(hwnd, 615, 352, button="left", delay=60)
        task_controller.smart_sleep(1)
        win_gb(hwnd)
        break


# 前往金陵功能
def JN_set(hwnd, timeout=80):
    """
    前往金陵功能

    Args:
        hwnd: 窗口句柄
        timeout: 超时时间（秒），默认60秒

    Returns:
        bool: 成功返回 True，超时返回 False
    """
    logger.info("前往金陵...")
    start_time = time.time()

    task_controller.smart_sleep(2)

    win_gb(hwnd)
    TuiLIKaShi_set(hwnd)

    background_key(hwnd, 'M')
    logger.debug("打开地图")
    task_controller.smart_sleep(3)

    # 判断当前位置是否为金陵
    pos_dwqd = find_image(hwnd, config.get_img_path("chushihua_/M_dwqd.png"), roi=[0, 460, 140, 40], threshold=0.8)
    if pos_dwqd is not None:
        logger.info(f"确定当前位置--[金陵]")
        return True

    pos_shijie = find_image(hwnd, config.get_img_path("chushihua_/M_shijie.png"), threshold=0.8)
    if pos_shijie is None:
        logger.warning("未找到世界地图")
        return False
    
    background_click(hwnd, pos_shijie[0], pos_shijie[1], button="left", delay=60)
    task_controller.smart_sleep(2)
    logger.debug("点击世界地图")

    pos_jN = find_image(hwnd, config.get_img_path("chushihua_/M_jN.png"), threshold=0.8)
    if pos_jN is None:
        logger.warning("未找到地图中金陵")
        return False
    
    background_click(hwnd, pos_jN[0], pos_jN[1], button="left", delay=60)
    task_controller.smart_sleep(2)
    logger.debug("点击金陵")

    background_click(hwnd, 476,303, button="left", delay=0)
    logger.debug("前往挂机点")
    task_controller.smart_sleep(10)

    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            logger.warning(f"前往金陵超时，已等待 {timeout} 秒")
            return False

        task_controller.check_status()

        pos_dwqd = find_image(hwnd, config.get_img_path("chushihua_/M_dwqd.png"), roi=[0, 460, 140, 40], threshold=0.8)
        # pos_dwqd2 = find_image(hwnd, config.get_img_path("chushihua_/M_dwqd_2.png"), roi=[438, 294, 48, 85], threshold=0.8)
        # if pos_dwqd is not None and pos_dwqd2 is not None:
        if pos_dwqd is not None:
            logger.info(f"确定当前位置--[金陵]")
            background_key(hwnd, 'M')
            task_controller.smart_sleep(2)
            return True
        else:
            background_key(hwnd, 'M')
            logger.debug("未到金陵")
            task_controller.smart_sleep(7)


def reset_game_state(hwnd):
    """
    重置游戏状态到安全状态
    
    当上下文失效时调用此函数，尝试将游戏恢复到可继续执行的状态。
    使用固定短延迟而非 smart_sleep，避免嵌套异常。
    
    参数：
        hwnd: 窗口句柄
        
    返回：
        bool: 重置是否成功
        
    注意：
        - 执行时间不超过 5 秒
        - 不包含复杂的图像识别或循环等待
        - 只执行最基础的恢复操作（按 ESC 键返回）
    """
    try:
        if not win32gui.IsWindow(hwnd):
            logger.warning("重置游戏状态失败：窗口句柄无效")
            return False
        
        logger.info("正在重置游戏状态...")
        
        for _ in range(3):
            background_key(hwnd, 'Esc')
            time.sleep(0.3)
        
        win_gb(hwnd, max_attempts=2, max_loop_time=2)
        
        time.sleep(0.5)
        
        logger.success("游戏状态重置完成")
        return True
        
    except Exception as e:
        logger.error(f"重置游戏状态时发生错误: {str(e)}")
        return False

# 购买时包裹满了
def buy_baogou_man(hwnd):
    '''
    购买时包裹满了，尝试重置包裹
    '''
    if find_image(hwnd, config.get_img_path("richang_/baogou_man.png"), threshold=0.8):
        logger.warning("包裹满了")
        win_gb(hwnd)
        if not baoguo_manSet(hwnd):
            baogou_jsSet(hwnd)
            return True
        else:
            return True
    return False

# 开启全服购买
def buy_all_buy(hwnd):
    '''
    开启全服购买
    '''
    pos_jiaoyi = find_image(hwnd, config.get_img_path("chushihua_/jiaoyi.png"), threshold=0.8)
    if pos_jiaoyi is None:
        logger.warning("未找到交易")
        return False
    
    logger.debug("点击交易")
    background_click(hwnd, pos_jiaoyi[0], pos_jiaoyi[1], button="left", delay=60)
    task_controller.smart_sleep(2)

    # 点击装备培养按钮
    pos_quanfu_zbqy = find_image(hwnd, config.get_img_path("chushihua_/quanfu_zbqy.png"), threshold=0.8)
    if pos_quanfu_zbqy is None:
        logger.warning("进入交易界面异常")
        return False

    logger.debug("点击装备培养按钮")
    background_click(hwnd, pos_quanfu_zbqy[0], pos_quanfu_zbqy[1], button="left", delay=60)
    task_controller.smart_sleep(2)

    for _ in range(3):
        # 检查是否已开启全服购买
        pos_qd = find_image(hwnd, config.get_img_path("chushihua_/quanfukaiqi_QD.png"), threshold=0.8)
        #未开启全服购买
        if pos_qd is None:
            pos_quanfuanniu = find_image(hwnd, config.get_img_path("chushihua_/quanfuanniu.png"), threshold=0.8)
            logger.debug("点击开启全服购买按钮")
            background_click(hwnd, pos_quanfuanniu[0], pos_quanfuanniu[1], button="left", delay=60)
            task_controller.smart_sleep(2)
        # 已开启全服购买
        else:
            logger.debug("全服交易已开启！")
            win_gb(hwnd)
            return True
