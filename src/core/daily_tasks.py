# -*- coding: utf-8 -*-
"""
日常任务模块
============
实现游戏日常任务的自动化执行

主要功能：
    - init_game_set: 初始化游戏设置
    - task_gua: 每日一卦任务
    - task_keye: 课业任务
    - task_bangpai: 帮派任务
    - task_chaguan: 茶馆说书任务
"""
import time
import random
from src.utils import background_click, background_key, background_drag, find_image,find_all_images
from src.utils.logger import get_logger, LogLevel
from src.config import config
from .helpers import (
    win_gb, wp_gb, zhd, TuiLIKaShi_set, DuanYou_set,
    TuiDui_set, baoguo_manSet, baogou_jsSet, JN_set,buy_all_buy
)
from .controller import task_controller, TaskStoppedException, ContextExpiredException, TargetNotFoundError,GameStuckException
from .recovery import with_retry,on_images_detected,on_map_transition
from .subtasks_meiri_kehuan import execute_subtask as _execute_subtask_kehuan
from .task_registry import register_task

logger = get_logger('daily_tasks')

EXECUTABLE_SUBTASKS = [
    "每日签到", "每日江湖礼", "每日在线礼", "每日回馈礼",
    "每日买银票", "买鸡蛋",
    "榫头卯眼", "兑换武经志", "小红花礼盒", "购买铜豆子", "功绩换铜板", "行当绝活",
    "碧铜马坯", "买吴越剑坯", "买白公鼎坯", "兑换锦芳绣", "买形影心得", "换高级萃石"
]


class LogSignalAdapter:
    """
    日志信号适配器
    
    将新的日志系统适配为兼容旧版 log_signal 接口，
    用于渐进式迁移，避免一次性修改所有调用点
    """
    
    def __init__(self, module_name: str = 'daily_tasks'):
        """
        初始化适配器
        
        参数：
            module_name: 模块名称
        """
        self._logger = get_logger(module_name)
    
    def emit(self, message: str):
        """
        发送日志消息（兼容旧版接口）
        
        参数：
            message: 日志消息
        """
        level = self._parse_level(message)
        self._logger._log(level, self._clean_message(message))
    
    def _parse_level(self, message: str) -> LogLevel:
        """
        解析日志级别
        
        参数：
            message: 原始日志消息
            
        返回：
            LogLevel: 日志级别
        """
        if '[OK]' in message or '✅' in message:
            return LogLevel.SUCCESS
        elif '[ERROR]' in message or '❌' in message:
            return LogLevel.ERROR
        elif '[WARN]' in message or '⚠️' in message:
            return LogLevel.WARNING
        elif '[INFO]' in message or 'ℹ️' in message:
            return LogLevel.INFO
        elif '==>' in message:
            return LogLevel.INFO
        else:
            return LogLevel.INFO
    
    def _clean_message(self, message: str) -> str:
        """
        清理日志消息中的级别标记
        
        参数：
            message: 原始消息
            
        返回：
            str: 清理后的消息
        """
        message = message.replace('[OK]', '').replace('[INFO]', '')
        message = message.replace('[ERROR]', '').replace('[WARN]', '')
        message = message.replace('✅', '').replace('❌', '').replace('⚠️', '')
        message = message.replace('==>', '').strip()
        return message

def init_game_set(hwnd):
    """
    初始化游戏窗口设置

    参数：
        hwnd: 窗口句柄
    """
    try:
        logger.success("游戏窗口绑定成功")
        logger.info("开始初始化设置...")
        win_gb(hwnd)

        logger.info("开始端游设置...")
        if DuanYou_set(hwnd):
            logger.success("端游设置完成")

        JN_set(hwnd)

        logger.info("开始退队...")
        if TuiDui_set(hwnd):
            logger.success("退队完成")

        logger.info("开始脱离卡死...")
        if TuiLIKaShi_set(hwnd):
            logger.success("脱离卡死完成")
        return hwnd

    except Exception as e:
        logger.error(f"初始化失败: {str(e)}", exc_info=True)
        return None

@register_task("每日一卦")
@with_retry(max_retries=6, recovery_func=win_gb)
@on_map_transition(interval=2.0) 
def task_gua(hwnd):
    """
    每日一卦任务
    
    参数：
        hwnd: 窗口句柄
        log_signal: 日志信号对象（可选，已弃用）
    
    返回：
        bool: 任务执行结果
    """
    logger.info("正在处理: 每日一卦")
    for _ in range(2):
        win_gb(hwnd)
        zhd(hwnd)
        background_click(hwnd, 521, 476, button="left", delay=60)
        task_controller.smart_sleep(1)

        pos = find_image(hwnd, config.get_img_path("richang_/mryg.png"), threshold=0.8)
        if pos is None:
            logger.success("每日一挂已完成")
            return True
        
        background_click(hwnd, 319, 290, button="left", delay=60)

        max_find_attempts = 6
        npc_found = False
        
        for i in range(max_find_attempts):
            pos_smbg = find_image(hwnd, config.get_img_path("richang_/smbg.png"), threshold=0.8)
            if pos_smbg is None:
                logger.debug(f"每日一挂寻路中... ({i + 1}/{max_find_attempts})")
                task_controller.smart_sleep(10)
            else:
                background_click(hwnd, pos_smbg[0], pos_smbg[1], button="left", delay=60)
                task_controller.smart_sleep(1)
                background_click(hwnd, pos_smbg[0], pos_smbg[1], button="left", delay=60)
                npc_found = True
                break

        if not npc_found:
            raise TargetNotFoundError("寻路超时，未能找到算命卜卦NPC")

        task_controller.smart_sleep(3)

        pos_ttym = find_image(hwnd, config.get_img_path("richang_/ttym.png"), threshold=0.8)
        if pos_ttym is None:
            raise TargetNotFoundError("未能找到[听天由命]按钮")

        background_click(hwnd, pos_ttym[0], pos_ttym[1], button="left", delay=60)
        task_controller.smart_sleep(3)
        background_click(hwnd, 730, 398, button="left", delay=60)
        task_controller.smart_sleep(10)

        pos_jsgx = find_image(hwnd, config.get_img_path("richang_/jsgx.png"), threshold=0.8)
        if pos_jsgx is None:
            raise TargetNotFoundError("未能找到[接受卦象]按钮")

        background_click(hwnd, pos_jsgx[0], pos_jsgx[1], button="left", delay=60)
        task_controller.smart_sleep(3)
        background_click(hwnd, 626, 355, button="left", delay=60)
        task_controller.smart_sleep(2)

def _keye_louji(hwnd):
    """
    课业任务过程逻辑（内部函数）- 性能优化版
    """
    last_action_time = time.time()
    stuck_count = 0  # 卡死计数器
    
    # 提前缓存图片路径，避免在循环中反复调用 config.get_img_path
    img_tijiao = config.get_img_path("richang_/keye_tijiao.png")
    img_jieshu = config.get_img_path("richang_/keye_jieshu.png")
    img_keye5 = config.get_img_path("richang_/keye_5.png")
    img_yun_zhsr = config.get_img_path("richang_/keye_yun_3.png")
    img_gomai = config.get_img_path("richang_/keye_gomai.png")
    img_xuqiu = config.get_img_path("richang_/xuqiu.png")
    img_bofa = config.get_img_path("richang_/keye_bofa.png")
    img_ymdt = config.get_img_path("richang_/keye_ym_dt.png")
    img_yun_1 = config.get_img_path("richang_/keye_yun_1.png")
    img_yun_2 = config.get_img_path("richang_/keye_yun_2.png")
    img_shiyong = config.get_img_path("richang_/keye_shiyong.png")
    img_xiayilun = config.get_img_path("richang_/keye_xiayilun.png")
    img_qw = config.get_img_path("richang_/keye_qw.png")

    while True: # 改为无限循环，通过内部 return 退出
        task_controller.check_status()
        baoguo_manSet(hwnd)
        action_taken = False # 记录本轮是否执行了任何操作

        # 【核心优化】按顺序查找，找到一个就立马执行并 continue 进入下一轮，绝不浪费 CPU 去找不需要的图
        
        pos_tijiao = find_image(hwnd, img_tijiao, threshold=0.8)
        if pos_tijiao:
            logger.info("课业任务道具提交")
            background_click(hwnd, pos_tijiao[0], pos_tijiao[1], button="left", delay=60)
            task_controller.smart_sleep(10)
            action_taken = True
            
        elif pos_jieshu := find_image(hwnd, img_jieshu, threshold=0.8):
            logger.info("课业任务已结束")
            background_click(hwnd, 663, 354, button="left", delay=60)
            task_controller.smart_sleep(3)
            wp_gb(hwnd)
            return True # 代表这一轮课业顺利完成
        
        elif pos_shiyong := find_image(hwnd, img_shiyong, threshold=0.8):
            logger.info("课业任务道具使用中...")
            background_click(hwnd, pos_shiyong[0], pos_shiyong[1], button="left", delay=60)
            task_controller.smart_sleep(3)
            action_taken = True

        elif find_image(hwnd, img_yun_zhsr, threshold=0.8):
            logger.info("云梦杂货商人购买...")
            background_click(hwnd, 629, 420, button="left", delay=60)
            task_controller.smart_sleep(1)
            action_taken = True

        elif pos_gomai := find_image(hwnd, img_gomai, threshold=0.8):
            logger.info("课业购买中...")
            background_click(hwnd, pos_gomai[0], pos_gomai[1], button="left", delay=60)
            task_controller.smart_sleep(1)
            background_click(hwnd, 618, 353, button="left", delay=60)
            task_controller.smart_sleep(1)
            if find_image(hwnd, config.get_img_path("richang_/baogou_man.png"), threshold=0.8):
                logger.warning("包裹满了")
                win_gb(hwnd)
                if not baoguo_manSet(hwnd): baogou_jsSet(hwnd)
            action_taken = True

        elif find_image(hwnd, img_xuqiu, threshold=0.8):
            if not find_image(hwnd, config.get_img_path("richang_/keye_zhahuogomai.png"), roi=[540, 300, 400, 200], threshold=0.8):
                logger.info("课业需求购买中...")
                background_click(hwnd, 404, 142, button="left", delay=60)
                task_controller.smart_sleep(2)
                if pos_g := find_image(hwnd, img_gomai, threshold=0.8):
                    background_click(hwnd, pos_g[0], pos_g[1], button="left", delay=60)
                    task_controller.smart_sleep(1)
                    background_click(hwnd, 618, 353, button="left", delay=60)
                    task_controller.smart_sleep(1)
                    if find_image(hwnd, config.get_img_path("richang_/baogou_man.png"), threshold=0.8):
                        win_gb(hwnd)
                        if not baoguo_manSet(hwnd): baogou_jsSet(hwnd)
            action_taken = True

        elif find_image(hwnd, img_bofa, threshold=0.8):
            logger.info("课业对话中...")
            background_click(hwnd, 618, 353, button="left", delay=60)
            task_controller.smart_sleep(3)
            action_taken = True

        elif find_image(hwnd, img_ymdt, threshold=0.8):
            logger.info("云梦答题中...")
            win_gb(hwnd)
            task_controller.smart_sleep(2)
            action_taken = True

        elif pos_yun_1 := find_image(hwnd, img_yun_1, threshold=0.8):
            background_click(hwnd, pos_yun_1[0], pos_yun_1[1], button="left", delay=60)
            task_controller.smart_sleep(1)
            if pos_yun_1_1 := find_image(hwnd, config.get_img_path("richang_/keye_yun_1_1.png"), threshold=0.8):
                for _ in range(4): # 简化连续点击4次的逻辑
                    background_click(hwnd, pos_yun_1_1[0], pos_yun_1_1[1], button="left", delay=60)
                    task_controller.smart_sleep(2)
            action_taken = True

        elif pos_yun_2 := find_image(hwnd, img_yun_2, threshold=0.8):
            background_click(hwnd, pos_yun_2[0], pos_yun_2[1], button="left", delay=60)
            task_controller.smart_sleep(2)
            if pos_yun_2_1 := find_image(hwnd, config.get_img_path("richang_/keye_yun_2_1.png"), threshold=0.8):
                background_click(hwnd, pos_yun_2_1[0], pos_yun_2_1[1], button="left", delay=60)
                task_controller.smart_sleep(2)
            action_taken = True

        elif find_image(hwnd, img_xiayilun, threshold=0.8):
            logger.info("课业任务下一轮")
            background_click(hwnd, 316, 354, button="left", delay=60)
            task_controller.smart_sleep(3)
            wp_gb(hwnd)
            return True # 完成一小轮，返回True让外层继续接取下一轮
        
        elif pos_keye5 := find_image(hwnd, img_keye5, roi=[20, 120, 160, 160], threshold=0.6):
            logger.info("课业继续中...")
            background_click(hwnd, pos_keye5[0], pos_keye5[1], button="left", delay=60)
            task_controller.smart_sleep(8)
            # 购买逻辑保持不变
            if pos_buy_1 := find_image(hwnd, config.get_img_path("richang_/buy_1.png"), threshold=0.8):
                logger.info("课业任务道具1购买...")
                background_click(hwnd, pos_buy_1[0], pos_buy_1[1], button="left", delay=60)
                task_controller.smart_sleep(2)
            elif pos_buy_2 := find_image(hwnd, config.get_img_path("richang_/buy_2.png"), threshold=0.8):
                logger.info("课业任务道具2购买...")
                background_click(hwnd, pos_buy_2[0], pos_buy_2[1], button="left", delay=60)
                task_controller.smart_sleep(2)
                if pos_buy_2_1 := find_image(hwnd, config.get_img_path("richang_/buy_2_1.png"), threshold=0.8):
                    background_click(hwnd, pos_buy_2_1[0], pos_buy_2_1[1], button="left", delay=60)
                    task_controller.smart_sleep(2)
                    win_gb(hwnd)
            action_taken = True

        # 如果上面所有的分支都没有触发，说明可能卡住了或者在跑路中
        if action_taken:
            last_action_time = time.time() # 有动作，更新时间
            stuck_count = 0 # 有动作说明没卡死，计数器清零
        else:
            # 如果连续 15 秒没有任何有效动作，进行兜底检查
            if time.time() - last_action_time >= 15:
                logger.debug("空闲15秒，进行课业任务完成检测...")
                win_gb(hwnd)
                zhd(hwnd)
                background_click(hwnd, 145, 478, button="left", delay=60)
                task_controller.smart_sleep(1)
                
                if not find_image(hwnd, img_qw, roi=[120, 160, 80, 80], threshold=0.8):
                    logger.success("活动菜单显示课业任务已完成")
                    win_gb(hwnd)
                    return True
                else:
                    stuck_count += 1 #卡死次数 +1
                    logger.info("课业任务仍在进行中，关闭菜单继续...")
                    win_gb(hwnd)
                    last_action_time = time.time()
                    task_controller.smart_sleep(1)
                    if stuck_count >= 4:
                        raise GameStuckException("课业任务内部流程卡死超过45秒")

@register_task("课业任务")
@with_retry(max_retries=6, recovery_func=win_gb)
@on_map_transition(interval=2.0) 
def task_keye(hwnd, log_signal=None):
    """
    课业任务主控逻辑
    
    参数：
        hwnd: 窗口句柄
        log_signal: 日志信号对象（可选，已弃用）
    
    返回：
        bool: 任务执行结果
    """
    logger.info("正在处理: 课业任务")
    win_gb(hwnd)
    buy_all_buy(hwnd)
    baoguo_manSet(hwnd)
    
    pos_jh_renwu = find_image(hwnd, config.get_img_path("richang_/jh_renwu.png"), threshold=0.8)
    pos_un_renwu = find_image(hwnd, config.get_img_path("richang_/un_renwu.png"), threshold=0.8)
    if pos_jh_renwu:
        logger.debug("找到JH江湖图标")
        background_click(hwnd, 99, 128, button="left", delay=60)
        task_controller.smart_sleep(3)
        background_drag(hwnd, 133, 182, 133, 300, drag_duration=0.5)
    elif pos_un_renwu:
        logger.debug("找到任务图标")
        background_click(hwnd, pos_un_renwu[0], pos_un_renwu[1], button="left", delay=60)
        task_controller.smart_sleep(3)
        background_click(hwnd, 99, 128, button="left", delay=60)
        task_controller.smart_sleep(3)
        background_drag(hwnd, 133, 182, 133, 300, drag_duration=1)
        task_controller.smart_sleep(3)
    
    pos_keye5 = find_image(hwnd, config.get_img_path("richang_/keye_5.png"), roi=[20, 120, 160, 160], threshold=0.6)
    if pos_keye5:
        logger.info("检测到未完成的课业，直接继续...")
        background_click(hwnd, pos_keye5[0], pos_keye5[1], button="left", delay=60)
        _keye_louji(hwnd) 

    for _ in range(3):
        zhd(hwnd)
        background_click(hwnd, 145, 478, button="left", delay=60)
        task_controller.smart_sleep(1)
        pos_qw = find_image(hwnd, config.get_img_path("richang_/keye_qw.png"), roi=[120, 160, 80, 80], threshold=0.8)
        pos_jh = find_image(hwnd, config.get_img_path("richang_/jh_jh.png"), roi=[100, 440, 80, 60], threshold=0.8)
        task_controller.smart_sleep(1)

        if pos_qw is None:
            logger.success("活动菜单显示课业任务已完成")
            win_gb(hwnd)
            return True

        if pos_qw and pos_jh:
            background_click(hwnd, 154, 193, button="left", delay=60)
            task_controller.smart_sleep(2)
            background_click(hwnd, 216, 344, button="left", delay=60)

            max_find_attempts = 12
            pathfinding_success = False
            
            for i in range(max_find_attempts):
                pos_canwu = find_image(hwnd, config.get_img_path("richang_/keye_canwu.png"), threshold=0.8)
                pos_keye = find_image(hwnd, config.get_img_path("richang_/keye.png"), threshold=0.8)
                
                if pos_keye is None and pos_canwu is None:
                    logger.debug(f"课业任务寻路中... ({i+1}/{max_find_attempts})")
                    task_controller.smart_sleep(10)
                else:
                    pathfinding_success = True
                    if pos_canwu:
                        logger.info("课业禅悟接取中...")
                        background_click(hwnd, pos_canwu[0], pos_canwu[1], button="left", delay=60)
                        task_controller.smart_sleep(1)
                        background_click(hwnd, 819, 323, button="left", delay=60)
                        task_controller.smart_sleep(2)
                    else:
                        logger.info("课业任务接取中...")
                        background_click(hwnd, pos_keye[0], pos_keye[1], button="left", delay=60)
                        task_controller.smart_sleep(1)
                        background_click(hwnd, pos_keye[0], pos_keye[1], button="left", delay=60)
                        task_controller.smart_sleep(2)
                    
                    pos_yijiequ = find_image(hwnd, config.get_img_path("richang_/keye_yijiequ.png"), threshold=0.8)
                    if pos_yijiequ:
                        logger.info("课业任务已接取...")
                        win_gb(hwnd)
                    else:
                        background_click(hwnd, 471, 240, button="left", delay=60)
                        task_controller.smart_sleep(2)
                    break # 成功接取，跳出寻路循环

            if not pathfinding_success:
                raise TargetNotFoundError("课业接取寻路超时")

            _keye_louji(hwnd)

    logger.error("课业任务执行次数超限，强制退出以防死循环")
    return False

def _bangpai_louji(hwnd, log_signal=None):
    """
    帮派任务过程逻辑（内部函数） - 性能优化版
    """
    last_action_time = time.time()
    stuck_count = 0  # <--- 新增：卡死计数器
    # 提前缓存图片路径，避免循环内频繁读取配置
    img_tijiao = config.get_img_path("richang_/keye_tijiao.png")
    img_wc = config.get_img_path("richang_/bangpairenwu_wc.png")
    img_xiayilun = config.get_img_path("richang_/bangpai_xiayilun.png")
    img_keye5 = config.get_img_path("richang_/keye_5.png")
    img_bofa = config.get_img_path("richang_/keye_bofa.png")
    img_gomai = config.get_img_path("richang_/keye_gomai.png")
    img_xuqiu = config.get_img_path("richang_/xuqiu.png")
    img_qh = config.get_img_path("richang_/keye_quehe.png")
    img_qw = config.get_img_path("richang_/bprw_qw.png")
    
    while True:
        task_controller.check_status()
        baoguo_manSet(hwnd)
        action_taken = False

        # 【核心优化】按优先级短路查找，一旦命中立即执行并进入下一轮，极大降低 CPU 占用
        
        pos_tijiao = find_image(hwnd, img_tijiao, threshold=0.8)
        if pos_tijiao:
            logger.info("帮派任务道具提交")
            background_click(hwnd, pos_tijiao[0], pos_tijiao[1], button="left", delay=60)
            task_controller.smart_sleep(10)
            action_taken = True
            
        elif pos_wc := find_image(hwnd, img_wc, threshold=0.8):
            logger.info("帮派任务已结束")
            background_click(hwnd, pos_wc[0], pos_wc[1], button="left", delay=60)
            task_controller.smart_sleep(3)
            win_gb(hwnd)
            return True  # 返回 True 代表本轮任务圆满完成
            
        elif pos_xiayilun := find_image(hwnd, img_xiayilun, threshold=0.8):
            logger.info("帮派任务下一轮")
            background_click(hwnd, 316, 354, button="left", delay=60)
            task_controller.smart_sleep(3)
            background_click(hwnd, 316, 354, button="left", delay=60)
            task_controller.smart_sleep(1)
            wp_gb(hwnd)
            return True  # 准备进入下一小环，向外层返回成功

        elif find_image(hwnd, img_bofa, threshold=0.8):
            logger.info("帮派任务对话中...")
            background_click(hwnd, 618, 353, button="left", delay=60)
            task_controller.smart_sleep(3)
            action_taken = True

        elif pos_gomai := find_image(hwnd, img_gomai, threshold=0.8):
            logger.info("帮派任务购买中...")
            background_click(hwnd, pos_gomai[0], pos_gomai[1], button="left", delay=60)
            task_controller.smart_sleep(1)
            background_click(hwnd, 618, 353, button="left", delay=60)
            task_controller.smart_sleep(1)
            if find_image(hwnd, config.get_img_path("richang_/baogou_man.png"), threshold=0.8):
                logger.warning("包裹满了")
                win_gb(hwnd)
                if not baoguo_manSet(hwnd): baogou_jsSet(hwnd)
            action_taken = True

        elif find_image(hwnd, img_xuqiu, threshold=0.8):
            logger.info("帮派需求购买中...")
            background_click(hwnd, 404, 142, button="left", delay=60)
            task_controller.smart_sleep(2)
            if pos_g := find_image(hwnd, img_gomai, threshold=0.8):
                logger.info("帮派购买中...")
                background_click(hwnd, pos_g[0], pos_g[1], button="left", delay=60)
                task_controller.smart_sleep(1)
                background_click(hwnd, 618, 353, button="left", delay=60)
                task_controller.smart_sleep(1)
                if find_image(hwnd, config.get_img_path("richang_/baogou_man.png"), threshold=0.8):
                    logger.warning("包裹满了")
                    win_gb(hwnd)
                    if not baoguo_manSet(hwnd): baogou_jsSet(hwnd)
            action_taken = True

        elif pos_qh := find_image(hwnd, img_qh, threshold=0.8):
            logger.warning("帮派任务道具缺货...")
            background_click(hwnd, 564, 343, button="left", delay=60)
            task_controller.smart_sleep(3)
            if pos_quanfu := find_image(hwnd, config.get_img_path("richang_/quan_fu.png"), threshold=0.8):
                logger.info("帮派任务道具缺货,全服购买...")
                background_click(hwnd, pos_quanfu[0], pos_quanfu[1], button="left", delay=60)
                task_controller.smart_sleep(3)
            else:
                logger.error("帮派任务道具全服缺货,任务结束")
                return False  # 无法继续，返回 False 报错退出
            action_taken = True
        # 只要任务没完成基本常在
        elif pos_keye5 := find_image(hwnd, img_keye5, roi=[20, 120, 160, 160], threshold=0.6):
            logger.info("帮派任务继续中...")
            background_click(hwnd, pos_keye5[0], pos_keye5[1], button="left", delay=60)
            task_controller.smart_sleep(8)
            # 内部购买逻辑
            if pos_buy_1 := find_image(hwnd, config.get_img_path("richang_/buy_1.png"), threshold=0.8):
                logger.info("帮派任务道具购买...")
                background_click(hwnd, pos_buy_1[0], pos_buy_1[1], button="left", delay=60)
                task_controller.smart_sleep(2)
            elif pos_buy_2 := find_image(hwnd, config.get_img_path("richang_/buy_2.png"), threshold=0.8):
                background_click(hwnd, pos_buy_2[0], pos_buy_2[1], button="left", delay=60)
                task_controller.smart_sleep(2)
                if pos_buy_2_1 := find_image(hwnd, config.get_img_path("richang_/buy_2_1.png"), threshold=0.8):
                    background_click(hwnd, pos_buy_2_1[0], pos_buy_2_1[1], button="left", delay=60)
                    task_controller.smart_sleep(2)
                    win_gb(hwnd)
            action_taken = True
        
        # 兜底：如果 15 秒没有任何操作，检测是否任务已自动完成
        if action_taken:
            last_action_time = time.time()
            stuck_count = 0  # <--- 新增：有动作说明没卡死，计数器清零
        else:
            if time.time() - last_action_time >= 15:
                logger.debug("空闲15秒，帮派任务完成检测...")
                win_gb(hwnd)
                zhd(hwnd)
                background_click(hwnd, 235, 469, button="left", delay=60)
                task_controller.smart_sleep(1)
                
                if not find_image(hwnd, img_qw, roi=[100, 180, 100, 100], threshold=0.8):
                    logger.success("活动菜单显示帮派任务已完成")
                    win_gb(hwnd)
                    return True  # 确定完成
                else:
                    stuck_count += 1  # <--- 新增：卡死次数 +1
                    logger.info("帮派任务仍在进行中，关闭菜单继续...")
                    win_gb(hwnd)
                    last_action_time = time.time()
                    task_controller.smart_sleep(1)
                    # <--- 新增：连续 4 次（60秒）都没进展，直接抛出异常，召唤装饰器！
                    if stuck_count >= 4:
                        raise GameStuckException("课业任务内部流程卡死超过45秒")

@register_task("帮派任务")
@with_retry(max_retries=6, recovery_func=win_gb)
@on_map_transition(interval=2.0) 
def task_bangpai(hwnd):
    """
    帮派任务主控逻辑
    """
    logger.info("正在处理: 帮派任务")
    win_gb(hwnd)
    buy_all_buy(hwnd)
    baoguo_manSet(hwnd)
    
    # 1. 检查断线或界面重置后的任务恢复
    pos_jh_renwu = find_image(hwnd, config.get_img_path("richang_/jh_renwu.png"), threshold=0.8)
    pos_un_renwu = find_image(hwnd, config.get_img_path("richang_/un_renwu.png"), threshold=0.8)
    if pos_jh_renwu:
        background_click(hwnd, 99, 128, button="left", delay=60)
        task_controller.smart_sleep(3)
        background_drag(hwnd, 133, 182, 133, 300, drag_duration=0.5)
    elif pos_un_renwu:
        background_click(hwnd, pos_un_renwu[0], pos_un_renwu[1], button="left", delay=60)
        task_controller.smart_sleep(3)
        background_click(hwnd, 99, 128, button="left", delay=60)
        task_controller.smart_sleep(3)
        background_drag(hwnd, 133, 182, 133, 300, drag_duration=0.5)
        task_controller.smart_sleep(3)

    pos_keye5 = find_image(hwnd, config.get_img_path("richang_/keye_5.png"), roi=[20, 120, 160, 160], threshold=0.6)
    if pos_keye5:
        logger.info("检测到进行中的帮派任务，直接继续...")
        background_click(hwnd, pos_keye5[0], pos_keye5[1], button="left", delay=60)
        _bangpai_louji(hwnd)

    # 2. 正常接取任务流程
    for _ in range(3):
        zhd(hwnd)
        background_click(hwnd, 235, 469, button="left", delay=60)
        task_controller.smart_sleep(1)
        pos_qw = find_image(hwnd, config.get_img_path("richang_/bprw_qw.png"), roi=[100, 180, 100, 100], threshold=0.8)

        if pos_qw is None:
            logger.success("帮派任务已完成")
            win_gb(hwnd)
            # JN_set(hwnd)
            return True  # 任务彻底清空，返回成功
            
        # 准备前往接取
        background_click(hwnd, 163, 223, button="left", delay=60)
        task_controller.smart_sleep(5)
            
        # 检查是否加入帮派
        if find_image(hwnd, config.get_img_path("richang_/bangpai_lb.png"), threshold=0.8):
            logger.warning("未加入帮派！任务结束")
            win_gb(hwnd)
            JN_set(hwnd)
            return False  # 特殊失败状态

        # 3. 【核心优化】寻路加入超时机制，最多等 120 秒
        max_find_attempts = 12
        pathfinding_success = False
            
        for i in range(max_find_attempts):
            pos_bangpai = find_image(hwnd, config.get_img_path("richang_/bprw.png"), roi=[700, 280, 200, 80], threshold=0.8)
            if pos_bangpai is None:
                logger.debug(f"帮派任务寻路中... ({i+1}/{max_find_attempts})")
                task_controller.smart_sleep(10)
            else:
                logger.info("帮派任务接取中...")
                background_click(hwnd, pos_bangpai[0], pos_bangpai[1], button="left", delay=60)
                task_controller.smart_sleep(1)
                background_click(hwnd, pos_bangpai[0], pos_bangpai[1], button="left", delay=60)
                task_controller.smart_sleep(2)
                pathfinding_success = True
                break

        if not pathfinding_success:
            raise TargetNotFoundError("帮派接取寻路超时")

        # 4. 进入内部执行逻辑
        _bangpai_louji(hwnd)
        # JN_set(hwnd)
    return True

@register_task("茶馆说书")
@with_retry(max_retries=6, recovery_func=win_gb)
@on_map_transition(interval=2.0) 
def task_chaguan(hwnd):
    """
    茶馆说书任务
    
    参数：
        hwnd: 窗口句柄
    
    返回：
        bool: 任务执行结果
    """
    logger.info("正在处理: 茶馆说书")
    win_gb(hwnd)

    zhd(hwnd)
    background_click(hwnd, 145, 478, button="left", delay=60)
    task_controller.smart_sleep(1)
    pos_chaguan_qw = find_image(hwnd, config.get_img_path("richang_/chaguan_qw.png"), roi=[140, 360, 120, 80], threshold=0.8)

    if pos_chaguan_qw is None:
        logger.success("茶馆说书已完成")
        win_gb(hwnd)
        return True
    
    background_click(hwnd, pos_chaguan_qw[0], pos_chaguan_qw[1], button="left", delay=60)

    max_find_attempts = 12
    pathfinding_success = False
    
    for i in range(max_find_attempts):
        pos_chaguan_jr = find_image(hwnd, config.get_img_path("richang_/chaguan_jr.png"), threshold=0.8)
        if pos_chaguan_jr is None:
            logger.debug(f"茶馆寻路中... ({i + 1}/{max_find_attempts})")
            task_controller.smart_sleep(10)
        else:
            logger.info("找到茶馆入口，正在进入...")
            background_click(hwnd, pos_chaguan_jr[0], pos_chaguan_jr[1], button="left", delay=60)
            task_controller.smart_sleep(10)
            pathfinding_success = True
            break

    if not pathfinding_success:
        raise TargetNotFoundError("茶馆寻路超时，未能找到茶馆入口")

    pos_chaguan_qr = find_image(hwnd, config.get_img_path("richang_/chaguan_qr.png"), roi=[0, 0, 100, 80], threshold=0.8)
    if pos_chaguan_qr is None:
        raise TargetNotFoundError("未能确认进入茶馆场景")

    logger.info("已成功进入茶馆，开始答题...")

    idle_timeout = 30 
    last_action_time = time.time()
    finished_chaguan = False

    while time.time() - last_action_time < idle_timeout:
        task_controller.check_status()
        pos_chaguan_tc = find_image(hwnd, config.get_img_path("richang_/chaguan_tc.png"), threshold=0.8)
        if pos_chaguan_tc is not None:
            logger.info("茶馆说书结束，正在退出...")
            background_click(hwnd, 0, 0, button="left", delay=60)
            task_controller.smart_sleep(3)
            background_click(hwnd, pos_chaguan_tc[0], pos_chaguan_tc[1], button="left", delay=60)
            task_controller.smart_sleep(3)
            TuiLIKaShi_set(hwnd)
            finished_chaguan = True
            break

        pos_chaguan_dttime = find_image(hwnd, config.get_img_path("richang_/chaguan_dttime.png"), threshold=0.7)
        if pos_chaguan_dttime is not None:
            logger.info("茶馆答题中...")
            pos_DaTi = random.choices(config.chaguan_dt, weights=config.chaguan_dt_weights, k=1)[0]
            task_controller.smart_sleep(2)
            background_click(hwnd, pos_DaTi[0], pos_DaTi[1], button="left", delay=60)
            task_controller.smart_sleep(3)
            last_action_time = time.time()
            continue

        task_controller.smart_sleep(1)

    if not finished_chaguan:
        raise GameStuckException("茶馆答题过程异常卡顿或超时")

    logger.success("茶馆说书已完成")
    return True

@register_task("每日可换")
def task_meiri_kehuan(hwnd, task_params=None):
    """
    每日可换任务
    
    参数：
        hwnd: 窗口句柄
        task_params: 扁平化的配置参数字典
    
    返回：
        dict: {"子项名": True/False, ...}
    """
    logger.info("正在处理: 每日可换任务")
    
    if task_params is None:
        task_params = {}
    
    logger.debug(f"每日可换参数: {task_params}")
    
    results = {}
    for subtask_name in EXECUTABLE_SUBTASKS:
        if task_params.get(subtask_name) is True:
            results[subtask_name] = False
    
    if not results:
        logger.info("每日可换：无勾选的子任务")
        return True
    
    for subtask_name in results.keys():
        try:
            win_gb(hwnd)
            success = _execute_meiri_subtask(hwnd, subtask_name)
            results[subtask_name] = success
            if success:
                logger.success(f"每日可换 [{subtask_name}] 执行成功")
            else:
                logger.warning(f"每日可换 [{subtask_name}] 执行失败")
        except TaskStoppedException:
            raise
        except ContextExpiredException:
            raise
        except Exception as e:
            logger.error(f"每日可换子任务 [{subtask_name}] 执行异常: {e}", exc_info=True)
            results[subtask_name] = False
    
    return results

def _execute_meiri_subtask(hwnd, subtask_name: str) -> bool:
    """
    执行单个每日可换子任务
    
    参数：
        hwnd: 窗口句柄
        subtask_name: 子任务名称
    
    返回：
        bool: 执行是否成功
    """
    return _execute_subtask_kehuan(hwnd, subtask_name)

@register_task("摇钱树")
@with_retry(max_retries=3, recovery_func=win_gb)
@on_map_transition(interval=2.0) 
def task_bangpai_yao(hwnd, task_params=None):
    """
    摇钱树任务
    
    参数：
        hwnd: 窗口句柄
        task_params: 扁平化的配置参数字典
            - choice: 摇树方式 ("轻轻摇"/"用力摇"/"全力摇")
    
    返回：
        bool: 任务执行结果
    """
    logger.info("正在处理: 摇钱树任务")

    if task_params is None:
        task_params = {}

    logger.debug(task_params)
    
    choice_text = task_params.get("choice", "轻轻摇")
    choice_map = {"轻轻摇": 1, "用力摇": 0, "全力摇": 2}
    choice = choice_map.get(choice_text, 1)

    for _ in range(2):
        win_gb(hwnd)
        zhd(hwnd)
        
        background_click(hwnd, config.bangpai_btn[0], config.bangpai_btn[1], button="left", delay=60)
        task_controller.smart_sleep(1)
            
        pos_yaoqianshu_open = find_image(hwnd, config.get_img_path("richang_/yaoqianshu/yaoqianshu_open.png"), threshold=0.8)
        if pos_yaoqianshu_open is None:
            logger.success("摇钱树任务完成 (活动入口已消失)")
            win_gb(hwnd)
            return True  

        background_click(hwnd, pos_yaoqianshu_open[0], pos_yaoqianshu_open[1], button="left", delay=60)
        task_controller.smart_sleep(1)
            
        pos_yaoqianshu_qw = find_image(hwnd, config.get_img_path("richang_/yaoqianshu/yaoqianshu_qw.png"), threshold=0.8)
        if pos_yaoqianshu_qw is None:
            logger.success("摇钱树任务完成 (未开启)")
            win_gb(hwnd)
            return False

        background_click(hwnd, pos_yaoqianshu_qw[0], pos_yaoqianshu_qw[1], button="left", delay=60)
        task_controller.smart_sleep(3)
            
        max_find_attempts = 12
        pathfinding_success = False
            
        for i in range(max_find_attempts):
            pos_yaoqianshu_xl = find_image(hwnd, config.get_img_path("richang_/yaoqianshu/yaoqianshu_xl.png"), threshold=0.8)
            if pos_yaoqianshu_xl is None:
                logger.debug(f"摇钱树寻路中... ({i+1}/{max_find_attempts})")
                task_controller.smart_sleep(5)
            else:
                pathfinding_success = True
                break
                    
        if not pathfinding_success:
            raise TargetNotFoundError("摇钱树寻路超时，未能找到摇钱树")
                
        logger.info("到达摇钱树，准备摇树")
        option = config.yaoqianshu_options.get(choice, config.yaoqianshu_options[1])
        coord = option["coord"]
        name = option["name"]
        
        task_controller.smart_sleep(1)
        background_click(hwnd, coord[0], coord[1], button="left", delay=60)
        logger.info(f"摇钱树执行动作: {name}")
        task_controller.smart_sleep(5)
        
        logger.debug("本次摇树动作结束，准备返回活动界面确认是否完成")

    raise GameStuckException("摇钱树任务循环次数超限")
        
@register_task("山河器")
@with_retry(max_retries=3, recovery_func=win_gb)
@on_map_transition(interval=2.0) 
def task_shanheqi(hwnd):
    """
    山河器任务
    
    参数：
        hwnd: 窗口句柄
    
    返回：
        bool: 任务执行结果
    """
    logger.info("正在处理: 山河器任务")
    
    timeout_pick = 120
    win_gb(hwnd)
    background_key(hwnd, 'B')
    task_controller.smart_sleep(1)
    
    pos_hdsz = find_image(hwnd, config.get_img_path("chushihua_/hdsz.png"), threshold=0.8)
    if pos_hdsz is None:
        raise TargetNotFoundError("未找到活动设置")
        
    background_click(hwnd, pos_hdsz[0], pos_hdsz[1], button="left", delay=60)
    task_controller.smart_sleep(2)
    
    pos_zshq = find_image(hwnd, config.get_img_path("richang_/shanheqi/shanheqi_01.png"), threshold=0.8)
    if pos_zshq is None:
        logger.info("山河器未开启 (未找到入口标记)")
        background_click(hwnd, 100, 100, button="left", delay=60)
        task_controller.smart_sleep(2)
        logger.success("山河器任务已跳过/结束")
        win_gb(hwnd)
        return False

    background_click(hwnd, pos_zshq[0], pos_zshq[1], button="left", delay=60)
    task_controller.smart_sleep(3)
    
    pos_shanheqi_wf = find_image(hwnd, config.get_img_path("richang_/shanheqi/shanheqi_wf.png"), threshold=0.8)
    if pos_shanheqi_wf is not None:
        logger.info("关闭规则页面")
        background_click(hwnd, 871, 414, button="left", delay=60)
        task_controller.smart_sleep(3)

    pos_ts_1 = find_image(hwnd, config.get_img_path("richang_/shanheqi/shanheqi_ts_1.png"), threshold=0.6)
    pos_ts_2 = find_image(hwnd, config.get_img_path("richang_/shanheqi/shanheqi_ts_2.png"), threshold=0.6)
    target_pos = pos_ts_1 if pos_ts_1 is not None else pos_ts_2

    if target_pos is None:
        pos_mf = find_image(hwnd, config.get_img_path("richang_/shanheqi/shanheqi_mf.png"), threshold=0.8)
        if pos_mf is not None:
            logger.info("山河器免费搜索")
            background_click(hwnd, pos_mf[0], pos_mf[1], button="left", delay=60)
            task_controller.smart_sleep(5)
            background_click(hwnd, 475, 235, button="left", delay=60)
            task_controller.smart_sleep(10)
            
            search_timeout = 15
            search_start = time.time()
            while time.time() - search_start < search_timeout:
                task_controller.check_status()
                pos_ts_1 = find_image(hwnd, config.get_img_path("richang_/shanheqi/shanheqi_ts_1.png"), threshold=0.6)
                pos_ts_2 = find_image(hwnd, config.get_img_path("richang_/shanheqi/shanheqi_ts_2.png"), threshold=0.6)
                target_pos = pos_ts_1 if pos_ts_1 is not None else pos_ts_2
                
                if target_pos is not None:
                    break
                task_controller.smart_sleep(1)
        else:
            logger.success("山河器任务结束 (无免费次数)")
            task_controller.smart_sleep(1)
            win_gb(hwnd)
            return True
        
    if target_pos is not None:
        logger.info("山河器探索点击")
        background_click(hwnd, target_pos[0], target_pos[1], button="left", delay=60)
    else:
        task_controller.smart_sleep(1)
        raise TargetNotFoundError("前往探索目标未找到")

    logger.info("山河器探索中，等待拾取...")
    start_time = time.time()

    pickup_success = False
    while time.time() - start_time < timeout_pick:
        task_controller.check_status()
        pos_pick = find_image(hwnd, config.get_img_path("richang_/shanheqi/shanheqi_shiqu_1.png"), threshold=0.8)
        if pos_pick is not None:
            logger.info("发现山河器，正在拾取...")
            background_click(hwnd, pos_pick[0], pos_pick[1], button="left", delay=60)
            task_controller.smart_sleep(10)
            if find_image(hwnd,config.get_img_path("richang_/shanheqi/shanheqi_houde.png"),threshold=0.8) is not None:
                background_click(hwnd, 0, 0, button="left", delay=60)
                logger.info("关闭奖励界面成功")
            else:
                raise TargetNotFoundError("未找到完成山河器拾取标识")
            task_controller.smart_sleep(5)
            pos_mf = find_image(hwnd, config.get_img_path("richang_/shanheqi/shanheqi_mf.png"), threshold=0.8)
            pos_ts_1 = find_image(hwnd, config.get_img_path("richang_/shanheqi/shanheqi_ts_1.png"), threshold=0.6)
            pos_ts_2 = find_image(hwnd, config.get_img_path("richang_/shanheqi/shanheqi_ts_2.png"), threshold=0.6)
            if pos_mf is None and pos_ts_1 is None and pos_ts_2 is None:
                logger.info("已完成所有免费搜索")
                win_gb(hwnd)
                return True
            else:
                raise TargetNotFoundError("未找到完成标识")

    if not pickup_success:
        raise GameStuckException("山河器拾取超时(1分钟)")
            
BANGPAI_JUANXIAN_SUBTASKS = ["捐献铜币", "捐献银两", "捐献元宝"]

@register_task("帮派捐献")
@with_retry(max_retries=6, recovery_func=win_gb)
def task_bangpai_JX(hwnd, task_params=None):
    """
    帮派捐献任务
    
    参数：
        hwnd: 窗口句柄
        task_params: 扁平化的配置参数字典
            - 捐献铜币: bool
            - 捐献银两: bool
            - 捐献元宝: bool
    
    返回：
        dict: {"捐献铜币": True/False, "捐献银两": True/False, "捐献元宝": True/False}
    """
    logger.info("正在处理: 帮派捐献任务")
    
    if task_params is None:
        task_params = {}
        
    logger.debug(task_params)

    results = {}
    for subtask_name in BANGPAI_JUANXIAN_SUBTASKS:
        if task_params.get(subtask_name) is True:
            results[subtask_name] = False
    
    if not results:
        logger.info("帮派捐献：无勾选的子任务")
        return True
    
    win_gb(hwnd)

    background_key(hwnd, 'B')
    task_controller.smart_sleep(2)

    pos_hdsz = find_image(hwnd, config.get_img_path("chushihua_/hdsz.png"), threshold=0.8)
    
    if pos_hdsz is None:
        raise TargetNotFoundError("未找到活动设置")
        
    background_click(hwnd, pos_hdsz[0], pos_hdsz[1], button="left", delay=60)
    logger.debug("点击活动设置")
    task_controller.smart_sleep(2)
    
    pos_bangpai = find_image(hwnd, config.get_img_path("richang_/bangpai_JX/bangpai.png"), threshold=0.8)
    if pos_bangpai is None:
        raise TargetNotFoundError("未找到帮派")
    
    background_click(hwnd, pos_bangpai[0], pos_bangpai[1], button="left", delay=60)
    logger.debug("点击帮派")
    task_controller.smart_sleep(2)

    pos_bangpai_FL = find_image(hwnd, config.get_img_path("richang_/bangpai_JX/bangbai_FL.png"), threshold=0.8)
    if pos_bangpai_FL is None:
        raise TargetNotFoundError("未找到帮派福利")
    
    background_click(hwnd, pos_bangpai_FL[0], pos_bangpai_FL[1], button="left", delay=60)
    logger.debug("点击帮派福利")
    task_controller.smart_sleep(2)
    
    pos_bangpai_JX = find_image(hwnd, config.get_img_path("richang_/bangpai_JX/bangpai_JX.png"), threshold=0.8)
    if pos_bangpai_JX is None:
        raise TargetNotFoundError("未找到帮派捐献")
    
    background_click(hwnd, pos_bangpai_JX[0], pos_bangpai_JX[1], button="left", delay=60)
    logger.debug("点击帮派捐献")
    task_controller.smart_sleep(2)

    pos_bangpai_JX_2 = find_image(hwnd, config.get_img_path("richang_/bangpai_JX/bangpai_JX_2.png"), threshold=0.8)
    if pos_bangpai_JX_2 is None:
        raise TargetNotFoundError("未进入帮派捐献界面")
    task_controller.smart_sleep(2)

    if "捐献铜币" in results:
        try:
            for _ in range(3):
                logger.info("捐献铜币")
                background_click(hwnd, 203, 390, button="left", delay=60)
                task_controller.smart_sleep(2)
                background_click(hwnd, 622, 354, button="left", delay=60)
                task_controller.smart_sleep(2)
            logger.success("捐献铜币完成")
            pos_TQ_end = find_image(hwnd, config.get_img_path("richang_/bangpai_JX/JX_end.png"), roi=(176, 375, 88, 28), threshold=0.8)
            if pos_TQ_end is not None:
                results["捐献铜币"] = True
            else:
                logger.warning("未找到捐献铜币结束标识")
        except TaskStoppedException:
            raise
        except Exception as e:
            logger.error(f"捐献铜币执行异常: {e}", exc_info=True)
        task_controller.smart_sleep(2)
    
    if "捐献银两" in results:
        try:
            for _ in range(3):
                logger.info("捐献银两")
                background_click(hwnd, 466, 391, button="left", delay=60)
                task_controller.smart_sleep(2)
                background_click(hwnd, 622, 354, button="left", delay=60)
                task_controller.smart_sleep(2)
            logger.success("捐献银两完成")
            pos_YL_end = find_image(hwnd, config.get_img_path("richang_/bangpai_JX/JX_end.png"), roi=(418, 377, 88, 28), threshold=0.8)
            if pos_YL_end is not None:
                results["捐献银两"] = True
            else:
                logger.warning("未找到捐献银两结束标识")
        except TaskStoppedException:
            raise
        except Exception as e:
            logger.error(f"捐献银两执行异常: {e}", exc_info=True)
        task_controller.smart_sleep(2)
    
    if "捐献元宝" in results:
        try:
            for _ in range(3):
                logger.info("捐献元宝")
                background_click(hwnd, 700, 392, button="left", delay=60)
                task_controller.smart_sleep(2)
                background_click(hwnd, 622, 354, button="left", delay=60)
                task_controller.smart_sleep(2)
            logger.success("捐献元宝完成")
            pos_YB_end = find_image(hwnd, config.get_img_path("richang_/bangpai_JX/JX_end.png"), roi=(655, 373, 88, 28), threshold=0.8)
            if pos_YB_end is not None:
                results["捐献元宝"] = True
            else:
                logger.warning("未找到捐献元宝结束标识")
        except TaskStoppedException:
            raise
        except Exception as e:
            logger.error(f"捐献元宝执行异常: {e}", exc_info=True)
        task_controller.smart_sleep(2)
    
    logger.success("帮派捐献任务完成")
    win_gb(hwnd)
    return True

# 弹窗处理
def FB_tiaogou(hwnd, pos):
    """处理剧情跳过（可重复触发）"""
    logger.info("跳过剧情")
    background_click(hwnd, pos[0], pos[1], button="left", delay=60)
    
@on_images_detected([
    {   
        # 跳过剧情
        "image_path": "richang_/fuben_louji/FB_tiaogou.png",
        "action": FB_tiaogou,
        "threshold": 0.8,
        "once": False
    },{
        # 无法寻路脱离卡死
        "image_path": "richang_/fuben_louji/FB_wufaxunlu.png",
        "action": TuiLIKaShi_set,
        "threshold": 0.8,
        "once": False
    }
], interval=1.0)
def _fuben_louji(hwnd,task_params=None):
    # 退本退队
    TBTD = False

    while True:

        pos_FB_tuichu = find_image(hwnd, config.get_img_path("richang_/fuben_louji/FB_tuichu.png"), threshold=0.8)
        if pos_FB_tuichu is not None:
            task_controller.smart_sleep(2)
            background_click(hwnd,0,0,button="left",action="double", delay=60)
            logger.debug("跳过奖励确定")
            task_controller.smart_sleep(2)

            pos_FU_TB_anniu = find_image(hwnd, config.get_img_path("richang_/fuben_louji/FB_TB_anniu.png"), threshold=0.8)
            if pos_FU_TB_anniu is not None:
                background_click(hwnd, pos_FU_TB_anniu[0], pos_FU_TB_anniu[1], button="left", delay=60)
                logger.debug("点击退出副本")
                task_controller.smart_sleep(3)

            if TBTD == False:
                pos_FB_LKFB = find_image(hwnd, config.get_img_path("richang_/fuben_louji/FB_LKFB.png"), threshold=0.8)
                if pos_FB_LKFB is None:
                    raise TargetNotFoundError("未找到离开副本按钮")
                background_click(hwnd, pos_FB_LKFB[0], pos_FB_LKFB[1], button="left", delay=60)
                logger.debug("离开副本")
                task_controller.smart_sleep(2)
            else:
                pos_FB_TBTD = find_image(hwnd, config.get_img_path("richang_/fuben_louji/FB_TBTD.png"), threshold=0.8)
                if pos_FB_TBTD is None:
                    raise TargetNotFoundError("未找到退本退队按钮")
                background_click(hwnd, pos_FB_TBTD[0], pos_FB_TBTD[1], button="left", delay=60)
                logger.debug("退本退队")
                task_controller.smart_sleep(2)

            return True
        
        task_controller.smart_sleep(2)
        pos_fuben_QR = find_image(hwnd, config.get_img_path("richang_/fuben_louji/fuben_QR.png"),roi=[14,132,100,50], threshold=0.8)
        if pos_fuben_QR is not None:
            background_click(hwnd, pos_fuben_QR[0], pos_fuben_QR[1], button="left", delay=60)
            logger.debug("点击副本任务")
            task_controller.smart_sleep(20)

        # pos_zhandou = find_image(hwnd, config.get_img_path("richang_/fuben_louji/FB_tongji_ZD.png"), threshold=0.8)
        # if pos_zhandou is not None:
        #     logger.debug("自动战斗")
        #     background_key(hwnd, "Q")
        #     task_controller.smart_sleep(2)
            
        
@register_task("日常副本")
@with_retry(max_retries=6, recovery_func=win_gb)
@on_map_transition(interval=2.0) 
def task_richang_FB(hwnd, task_params=None):
    """
    日常副本任务
    
    参数：
        hwnd: 窗口句柄
    
    返回：
        bool: 任务执行结果
    """
    
    
    logger.info("正在处理: 日常副本任务")
    if task_params is None:
        task_params = {}

    logger.debug(task_params)

    team_mode = task_params.get("team_mode", "leader")
    team_size = task_params.get("team_size", 1)
    season_shout = task_params.get("season_shout", False)
    xiuwei_limit = task_params.get("xiuwei_limit", "")

    if team_mode == "member":
        team_size = 0

    if xiuwei_limit == "":
        xiuwei_limit = 0
    else:
        xiuwei_limit = int(xiuwei_limit)
    
    logger.info(f"日常副本 - 模式:{team_mode}, 人数:{team_size}, 是否喊话:{season_shout},修为限制:{xiuwei_limit}")

    JN_set(hwnd)

    win_gb(hwnd)
    # 退队
    TuiDui_set(hwnd)
    if team_mode == "leader":
        background_key(hwnd, "T")
        task_controller.smart_sleep(4)

        pos_jiandui = find_image(hwnd, config.get_img_path("richang_/fuben_louji/FB_jiandui.png"), threshold=0.8)
        if pos_jiandui is  None:
            raise TargetNotFoundError("未进入组队界面")
        
        background_click(hwnd, pos_jiandui[0], pos_jiandui[1], button="left", delay=60)
        logger.debug("创建队伍")
        task_controller.smart_sleep(2)

        pos_DA_mubiao = find_image(hwnd, config.get_img_path("richang_/fuben_louji/FB_dabenmubiao.png"), threshold=0.8)
        if pos_DA_mubiao is  None:
            raise TargetNotFoundError("未找到日常副本队伍目标")
        
        background_click(hwnd, pos_DA_mubiao[0], pos_DA_mubiao[1], button="left", delay=60)
        logger.debug("选择日常副本队伍目标")
        task_controller.smart_sleep(2)

        pos_JH_jishi = find_image(hwnd, config.get_img_path("richang_/fuben_louji/FB_jianghujishi.png"), threshold=0.8)
        if pos_JH_jishi is  None:
            raise TargetNotFoundError("未找到江湖纪事按钮")
        
        background_click(hwnd, pos_JH_jishi[0], pos_JH_jishi[1], button="left", delay=60)
        logger.debug("点击江湖纪事")
        task_controller.smart_sleep(2)

        pos_RC_fuben = find_image(hwnd, config.get_img_path("richang_/fuben_louji/FB_richang.png"), threshold=0.8)
        if pos_RC_fuben is  None:
            raise TargetNotFoundError("未找到日常副本按钮")
        
        background_click(hwnd, pos_RC_fuben[0], pos_RC_fuben[1], button="left", delay=60)
        logger.debug("点击日常副本")
        task_controller.smart_sleep(2)
        # 默认确定日常副本
        background_click(hwnd, 250, 385, button="left", delay=60)
        task_controller.smart_sleep(2)
        # 确定开本组队
        background_click(hwnd, 618, 353, button="left", delay=60)
        task_controller.smart_sleep(2)

        # 等待组队人数符合设置人数
        start_time = time.time()

        while True:
            # 计时
            current_time = time.time()
            if current_time - start_time >= 180:
                logger.error("等待组队人数超时")
                raise TimeoutError("等待组队人数超时")
            
            # 切换赛季喊话按钮
            pos_qiehuan = find_image(hwnd, config.get_img_path("richang_/fuben_louji/qiehuan.png"), threshold=0.8)
            # 是否切换赛季喊话
            if season_shout == True:
                # 当前是否是赛季喊话
                pos_saiji = find_image(hwnd, config.get_img_path("richang_/fuben_louji/hanhua.png"), threshold=0.8)
                # 不是则切换赛季喊话
                if pos_saiji is None:
                    # 找切换按钮
                    background_click(hwnd, pos_qiehuan[0], pos_qiehuan[1], button="left", delay=60)
                    logger.debug("切换赛季喊话")
                    task_controller.smart_sleep(3)
                    # 第一次切换需要确定切换
                    pos_qiehuan_QD = find_image(hwnd, config.get_img_path("richang_/fuben_louji/pos_qiehuan_QD.png"), threshold=0.8)
                    if pos_qiehuan_QD is not None:
                        background_click(hwnd, pos_qiehuan_QD[0], pos_qiehuan_QD[1], button="left", delay=60)
                        logger.debug("切换赛季喊话确认")
                        task_controller.smart_sleep(2)
            
            # 有切换按钮说明可以点击喊话了
            pos_hanhua_LB = find_image(hwnd, config.get_img_path("richang_/fuben_louji/hanhua_LB.png"), threshold=0.8)
            if pos_qiehuan is not None and pos_hanhua_LB is not None:
                background_click(hwnd, pos_hanhua_LB[0], pos_hanhua_LB[1], button="left", delay=60)
                logger.debug("赛季喊话中")
                task_controller.smart_sleep(3)
            
            # 等待组队人数符合设置人数
            renshu_count = find_all_images(hwnd,config.get_img_path("richang_/fuben_louji/FB_zhushou_JS.png"),threshold=0.8)[0]
            if 10-renshu_count>=team_size:
                logger.info(f"组队人数符合设置人数: {team_size}")
                task_controller.smart_sleep(2)
                break
            else:
                logger.info(f"当前组队人数: {10-renshu_count}, 未达到设置人数: {team_size}, 已等待: {int(current_time - start_time)}秒")
                task_controller.smart_sleep(2)
                
        pos_FB_ruben = find_image(hwnd, config.get_img_path("richang_/fuben_louji/FB_ruben.png"), threshold=0.8)
        if pos_FB_ruben is None:
            raise TargetNotFoundError("未找到日常进入副本按钮")
            
        background_click(hwnd, pos_FB_ruben[0], pos_FB_ruben[1], button="left", delay=60)
        logger.debug("进入副本")
        task_controller.smart_sleep(2)

        pos_FB_ruben_QD = find_image(hwnd, config.get_img_path("richang_/fuben_louji/FB_ruben_QD.png"), threshold=0.8)
        if pos_FB_ruben_QD is None:
            raise TargetNotFoundError("未找到日常进入副本确认按钮")
        
        background_click(hwnd, pos_FB_ruben_QD[0], pos_FB_ruben_QD[1], button="left", delay=60)
        logger.debug("进入副本确认")
        task_controller.smart_sleep(2)

        pos_FB_QTJR = find_image(hwnd, config.get_img_path("richang_/fuben_louji/FB_QTJR.png"), threshold=0.8)
        if pos_FB_QTJR is not None:
            background_click(hwnd, pos_FB_QTJR[0], pos_FB_QTJR[1], button="left", delay=60)
            logger.debug("点击全体进入")
            task_controller.smart_sleep(2)

        # 进入副本逻辑
        _fuben_louji(hwnd)

        task_controller.smart_sleep(3)
        win_gb(hwnd)

    return True


@with_retry(max_retries=6, recovery_func=win_gb)
@on_map_transition(interval=2.0) 
@register_task("华山论剑1V1")
def task_lunjian(hwnd,task_params=None):
    """
    华山论剑1V1任务
    参数：
        hwnd: 窗口句柄
        task_params: 任务参数字典，默认 None
    """
    logger.info("正在处理: 华山论剑1V1")

    if task_params is None:
        task_params = {}
        
    logger.debug(task_params)

    count = task_params.get("count", 1)
    quick_exit = task_params.get("quick_exit", False)
    #前往金陵
    JN_set(hwnd)
    # 退队
    TuiDui_set

    for i in range(count):
        # 关闭
        win_gb(hwnd)
        # 打开活动
        zhd(hwnd)
        # 点击纷争
        background_click(hwnd, 337, 470, button="left", delay=60)
        logger.debug("点击纷争")
        task_controller.smart_sleep(2)

        pos_1V1_qd = find_image(hwnd, config.get_img_path("richang_/fuben_louji/1V1_qd.png"), threshold=0.8)
        if pos_1V1_qd is None:
            raise TargetNotFoundError("未找到论剑1v1按钮")
        background_click(hwnd, pos_1V1_qd[0], pos_1V1_qd[1], button="left", delay=60)
        logger.debug("点击论剑1v1")
        task_controller.smart_sleep(2)

        # 判断是否在匹配中
        pos_1V1_ppz = find_image(hwnd, config.get_img_path("richang_/fuben_louji/1v1_ppz.png"), threshold=0.8)
        # 不在
        if pos_1V1_ppz is None:
            # 点击匹配
            background_click(hwnd, 682, 412, button="left", delay=60)
        
        background_click(hwnd, pos_1V1_ppz[0], pos_1V1_ppz[1], button="left", delay=60)
        logger.debug("点击论剑1v1确认")
        task_controller.smart_sleep(2)


        


