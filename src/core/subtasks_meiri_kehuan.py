# -*- coding: utf-8 -*-
"""
每日可换子任务处理模块
====================
管理每日可换任务的所有子任务处理函数

主要功能：
    - 子任务处理函数映射
    - 统一的子任务执行入口
    - 占位实现，便于后续扩展
"""
import time
from src.utils import background_click, background_key, background_drag, find_image
from src.utils.logger import get_logger
from src.config import config
from .helpers import win_gb, wp_gb, zhd, baoguo_manSet, buy_baogou_man
from .controller import task_controller, TaskStoppedException, ContextExpiredException, TargetNotFoundError
from .recovery import with_retry

logger = get_logger('subtasks_meiri_kehuan')


def execute_subtask(hwnd, subtask_name: str) -> bool:
    """
    执行单个每日可换子任务
    
    参数：
        hwnd: 窗口句柄
        subtask_name: 子任务名称
    
    返回：
        bool: 执行是否成功
    """
    handler = SUBTASK_HANDLERS.get(subtask_name)
    if handler:
        try:
            return handler(hwnd)
        except TaskStoppedException:
            raise
        except ContextExpiredException:
            raise
        except Exception as e:
            logger.error(f"子任务 [{subtask_name}] 执行异常: {e}", exc_info=True)
            return False
    else:
        logger.warning(f"子任务 [{subtask_name}] 未找到处理函数")
        return False


def _subtask_not_implemented(hwnd, subtask_name: str) -> bool:
    """
    未实现的子任务占位处理
    
    参数：
        hwnd: 窗口句柄
        subtask_name: 子任务名称
    
    返回：
        bool: 始终返回 False
    """
    logger.warning(f"子任务 [{subtask_name}] 暂未实现")
    task_controller.smart_sleep(0.5)
    return False


@with_retry(max_retries=3, recovery_func=win_gb)
def _handle_meiri_qiandao(hwnd) -> bool:
    """
    每日签到子任务
    
    参数：
        hwnd: 窗口句柄
    
    返回：
        bool: 执行是否成功
    """
    task_name = "每日签到"
    logger.info(f"正在处理: {task_name}")
    
    background_key(hwnd, 'B')
    task_controller.smart_sleep(1)

    pos_hdsz = find_image(hwnd, config.get_img_path("chushihua_/hdsz.png"), threshold=0.8)
    if pos_hdsz is None:
        raise TargetNotFoundError("未找到活动设置图标")
    
    background_click(hwnd, pos_hdsz[0], pos_hdsz[1], button="left", delay=60)
    task_controller.smart_sleep(2)

    fuli_chazhao = True
    下滑查找 = 5
    for i in range(1, 下滑查找 + 1):
        task_controller.smart_sleep(1)
        background_drag(hwnd, 884, 441, 884, 50, drag_duration=0.5)
        task_controller.smart_sleep(2)
        pos_fuli = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_fuli.png"), threshold=0.8)
        if pos_fuli is None:
            continue
        else:
            background_click(hwnd, pos_fuli[0], pos_fuli[1], button="left", delay=60)
            task_controller.smart_sleep(3)
            background_click(hwnd, 336, 323, button="left", delay=60)
            task_controller.smart_sleep(3)
            fuli_chazhao = False
            break
        
    if fuli_chazhao:
        raise TargetNotFoundError("未找到福利图标")
    
    pos_qiandao = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_qiandao.png"), threshold=0.8)
    if pos_qiandao is None:
        raise TargetNotFoundError("未找到签到图标")
    
    task_controller.smart_sleep(2)
    # 点击签到礼盒
    background_click(hwnd, 134, 351, button="left", delay=60)

    
    logger.info(f"{task_name}任务执行成功")
    task_controller.smart_sleep(1)
    return True


@with_retry(max_retries=3, recovery_func=win_gb)
def _handle_meiri_jianghuli(hwnd) -> bool:
    """
    每日江湖礼子任务
    
    参数：
        hwnd: 窗口句柄
    
    返回：
        bool: 执行是否成功
    """
    task_name = "每日江湖礼"
    logger.info(f"正在处理: {task_name}")
    
    background_key(hwnd, 'B')
    task_controller.smart_sleep(1)

    pos_hdsz = find_image(hwnd, config.get_img_path("chushihua_/hdsz.png"), threshold=0.8)
    if pos_hdsz is None:
        raise TargetNotFoundError("未找到活动设置图标")
    
    background_click(hwnd, pos_hdsz[0], pos_hdsz[1], button="left", delay=60)
    task_controller.smart_sleep(2)

    fuli_chazhao = True
    下滑查找 = 5
    for i in range(1, 下滑查找 + 1):
        task_controller.smart_sleep(1)
        background_drag(hwnd, 884, 441, 884, 50, drag_duration=0.5)
        task_controller.smart_sleep(2)
        pos_fuli = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_fuli.png"), threshold=0.8)
        if pos_fuli is None:
            continue
        else:
            background_click(hwnd, pos_fuli[0], pos_fuli[1], button="left", delay=60)
            task_controller.smart_sleep(3)
            background_click(hwnd, 787, 408, button="left", delay=60)
            task_controller.smart_sleep(3)
            fuli_chazhao = False
            break
        
    if fuli_chazhao:
        raise TargetNotFoundError("未找到福利图标")
    
    pos_jianghuli_lq = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_jhllq.png"), threshold=0.8)
    if pos_jianghuli_lq is None:
        logger.info("今日江湖礼暂不可领取")
        task_controller.smart_sleep(2)
        return True
    
    background_click(hwnd, pos_jianghuli_lq[0], pos_jianghuli_lq[1], button="left", delay=60)
    task_controller.smart_sleep(3)
    logger.info(f"{task_name}任务执行成功")
    return True


@with_retry(max_retries=3, recovery_func=win_gb)
def _handle_meiri_zaixianli(hwnd) -> bool:
    """
    每日在线礼子任务
    
    参数：
        hwnd: 窗口句柄
    
    返回：
        bool: 执行是否成功
    """
    task_name = "每日在线礼"
    logger.info(f"正在处理: {task_name}")
    
    background_key(hwnd, 'B')
    task_controller.smart_sleep(1)

    pos_hdsz = find_image(hwnd, config.get_img_path("chushihua_/hdsz.png"), threshold=0.8)
    if pos_hdsz is None:
        raise TargetNotFoundError("未找到活动设置图标")
    
    background_click(hwnd, pos_hdsz[0], pos_hdsz[1], button="left", delay=60)
    task_controller.smart_sleep(2)

    fuli_chazhao = True
    下滑查找 = 5
    for i in range(1, 下滑查找 + 1):
        task_controller.smart_sleep(1)
        background_drag(hwnd, 884, 441, 884, 50, drag_duration=0.5)
        task_controller.smart_sleep(2)
        pos_fuli = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_fuli.png"), threshold=0.8)
        if pos_fuli is None:
            continue
        else:
            background_click(hwnd, pos_fuli[0], pos_fuli[1], button="left", delay=60)
            task_controller.smart_sleep(3)
            background_click(hwnd, 226, 425, button="left", delay=60)
            task_controller.smart_sleep(1)
            logger.info(f"{task_name}任务执行成功")
            task_controller.smart_sleep(2)
            return True
        
    raise TargetNotFoundError("未找到福利图标")


@with_retry(max_retries=3, recovery_func=win_gb)
def _handle_meiri_huikuli(hwnd) -> bool:
    """
    每日回馈礼子任务
    
    参数：
        hwnd: 窗口句柄
    
    返回：
        bool: 执行是否成功
    """
    task_name = "每日回馈礼"
    logger.info(f"正在处理: {task_name}")
    
    pos_tehu = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_tehu.png"), roi=[749,7,123,60], threshold=0.8)
    if pos_tehu is None:
        background_click(hwnd, 862, 16, button="left", delay=60)
        task_controller.smart_sleep(3)
        raise TargetNotFoundError("未找到回馈礼图标")
    
    task_controller.smart_sleep(1)
    background_click(hwnd, pos_tehu[0], pos_tehu[1], button="left", delay=60)
    task_controller.smart_sleep(3)
    
    pos_tehu_2 = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_tehu_2.png"), roi=[0,0,160,60], threshold=0.8)
    if pos_tehu_2 is None:
        raise TargetNotFoundError("未进入特惠页面")
    
    pos_zhouka = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_zhouka.png"), threshold=0.8)
    if pos_zhouka is None:
        raise TargetNotFoundError("未找到周卡图标")
    
    background_click(hwnd, pos_zhouka[0], pos_zhouka[1], button="left", delay=60)
    task_controller.smart_sleep(5)

    pos_tehuiLB = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_tehuiLB.png"), threshold=0.8)
    if pos_tehuiLB is not None:
        background_click(hwnd, pos_tehuiLB[0], pos_tehuiLB[1], button="left", delay=60)
        task_controller.smart_sleep(2)
        logger.info(f"{task_name}任务执行成功")
        return True

@with_retry(max_retries=3, recovery_func=win_gb)
def _handle_meiri_maiyinpiao(hwnd) -> bool:
    """
    每日买银票子任务
    
    参数：
        hwnd: 窗口句柄
    
    返回：
        bool: 执行是否成功
    """
    task_name = "每日买银票"
    logger.info(f"正在处理: {task_name}")
    
    baoguo_manSet(hwnd)

    background_key(hwnd, 'B')
    task_controller.smart_sleep(1)

    pos_hdsz = find_image(hwnd, config.get_img_path("chushihua_/hdsz.png"), threshold=0.8)
    if pos_hdsz is None:
        raise TargetNotFoundError("未找到活动设置图标")
    
    background_click(hwnd, pos_hdsz[0], pos_hdsz[1], button="left", delay=60)
    task_controller.smart_sleep(2)

    pos_zhenbaoge = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_zhenbaoge.png"), threshold=0.8)
    if pos_zhenbaoge is None:
        raise TargetNotFoundError("未找到珍宝阁图标")
    
    background_click(hwnd, pos_zhenbaoge[0], pos_zhenbaoge[1], button="left", delay=60)
    task_controller.smart_sleep(3)
    background_click(hwnd, 879, 306, button="left", delay=60)
    task_controller.smart_sleep(2)

    pos_yingpiaoLH = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_yingpiaoLH.png"), roi=(49, 105, 500, 370), threshold=0.8)
    if pos_yingpiaoLH is None:
        raise TargetNotFoundError("未找到银票礼盒图标")
    
    background_click(hwnd, pos_yingpiaoLH[0], pos_yingpiaoLH[1], button="left", delay=60)
    task_controller.smart_sleep(3)
    background_click(hwnd, 691, 409, button="left", delay=60)
    task_controller.smart_sleep(2)
    for i in range(2):
        background_click(hwnd, 718, 347, button="left", action="double", delay=60)
        task_controller.smart_sleep(1)
    background_click(hwnd, 684, 462, button="left", action="double", delay=60)
    background_click(hwnd, 684, 462, button="left", action="double", delay=60)
    if buy_baogou_man(hwnd):
        raise TargetNotFoundError("购买失败，包裹满了")
    task_controller.smart_sleep(3)

    pos_yingliangBZ = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_yingliangBZ.png"), threshold=0.8)
    if pos_yingliangBZ is not None:
        logger.info("银两不足，无法购买")
        task_controller.smart_sleep(2)
        background_click(hwnd, 316, 351, button="left", delay=60)
        logger.info(f"{task_name}任务执行成功")
        return False
    
    task_controller.smart_sleep(2)
    logger.info(f"{task_name}任务执行成功")
    return True


@with_retry(max_retries=3, recovery_func=win_gb)
def _handle_mai_jidan(hwnd) -> bool:
    """
    买鸡蛋子任务
    
    参数：
        hwnd: 窗口句柄
    
    返回：
        bool: 执行是否成功
    """
    task_name = "买鸡蛋"
    logger.info(f"正在处理: {task_name}")
    
    baoguo_manSet(hwnd)

    background_key(hwnd, 'B')
    task_controller.smart_sleep(1)

    pos_hdsz = find_image(hwnd, config.get_img_path("chushihua_/hdsz.png"), threshold=0.8)
    if pos_hdsz is None:
        raise TargetNotFoundError("未找到活动设置图标")
    
    background_click(hwnd, pos_hdsz[0], pos_hdsz[1], button="left", delay=60)
    task_controller.smart_sleep(2)

    pos_zhenbaoge = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_zhenbaoge.png"), threshold=0.8)
    if pos_zhenbaoge is None:
        raise TargetNotFoundError("未找到珍宝阁图标")
    
    background_click(hwnd, pos_zhenbaoge[0], pos_zhenbaoge[1], button="left", delay=60)
    task_controller.smart_sleep(3)
    background_click(hwnd, 879, 433, button="left", delay=60)
    task_controller.smart_sleep(3)
    pos_yijiBS = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_yijiBS.png"), threshold=0.8)
    if pos_yijiBS is not None:
        background_click(hwnd, 156, 131, button="left", delay=60)
        task_controller.smart_sleep(5)
    
    jianghuZ_path = [
        config.get_img_path("richang_/meiriduihuan/MRDH_jianghuZH.png"),
        config.get_img_path("richang_/meiriduihuan/MRDH_jianghuZH_2.png"),
    ] 
    pos_jianghuZH = find_image(hwnd, jianghuZ_path, threshold=0.8)
    if pos_jianghuZH is None:
        raise TargetNotFoundError("未找到江湖杂货图标")
    
    background_click(hwnd, pos_jianghuZH[0], pos_jianghuZH[1], button="left", delay=60)
    task_controller.smart_sleep(3)
    
    for count in range(10):
        pos_YKjidan = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_YKjidan.png"), roi=(259, 106, 250, 360), threshold=0.8)
        if pos_YKjidan:
            background_click(hwnd, pos_YKjidan[0], pos_YKjidan[1])
            task_controller.smart_sleep(1)
            background_click(hwnd, 664, 401, button="left", delay=60)
            task_controller.smart_sleep(2)
            for _ in range(2):
                background_click(hwnd, 697, 337, button="left", action="double", delay=60)
                task_controller.smart_sleep(1)
            background_click(hwnd, 664, 455, button="left", action="double", delay=60)
            background_click(hwnd, 664, 455, button="left", action="double", delay=60)
            task_controller.smart_sleep(1)
            if buy_baogou_man(hwnd):
                raise TargetNotFoundError("购买失败，包裹满了")
            task_controller.smart_sleep(2)
            logger.info(f"{task_name}任务执行成功")
            return True
        elif count == 9:
            raise TargetNotFoundError("未找到鸡蛋图标")
        else:
            background_drag(hwnd, 387, 318, 387, 208, drag_duration=0.5)
            task_controller.smart_sleep(1)
    
    return False


@with_retry(max_retries=3, recovery_func=win_gb)
def _handle_suntou_maoyan(hwnd) -> bool:
    """
    榫头卯眼子任务
    
    参数：
        hwnd: 窗口句柄
    
    返回：
        bool: 执行是否成功
    """
    task_name = "榫头卯眼"
    logger.info(f"正在处理: {task_name}")
    
    baoguo_manSet(hwnd)

    background_key(hwnd, 'B')
    task_controller.smart_sleep(1)

    pos_hdsz = find_image(hwnd, config.get_img_path("chushihua_/hdsz.png"), threshold=0.8)
    if pos_hdsz is None:
        raise TargetNotFoundError("未找到活动设置图标")
    
    background_click(hwnd, pos_hdsz[0], pos_hdsz[1], button="left", delay=60)
    task_controller.smart_sleep(2)

    pos_zhenbaoge = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_zhenbaoge.png"), threshold=0.8)
    if pos_zhenbaoge is None:
        raise TargetNotFoundError("未找到珍宝阁图标")
    
    background_click(hwnd, pos_zhenbaoge[0], pos_zhenbaoge[1], button="left", delay=60)
    task_controller.smart_sleep(3)
    background_click(hwnd, 879, 433, button="left", delay=60)
    task_controller.smart_sleep(3)
    pos_yijiBS = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_yijiBS.png"), threshold=0.8)
    if pos_yijiBS is not None:
        background_click(hwnd, 156, 131, button="left", delay=60)
        task_controller.smart_sleep(5)
    
    jianghuZ_path = [
        config.get_img_path("richang_/meiriduihuan/MRDH_jianghuZH.png"),
        config.get_img_path("richang_/meiriduihuan/MRDH_jianghuZH_2.png"),
    ] 
    pos_jianghuZH = find_image(hwnd, jianghuZ_path, threshold=0.8)
    if pos_jianghuZH is None:
        raise TargetNotFoundError("未找到江湖杂货图标")
    
    background_click(hwnd, pos_jianghuZH[0], pos_jianghuZH[1], button="left", delay=60)
    task_controller.smart_sleep(3)
    
    for count in range(10):
        pos_suntouMY = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_suntouMY.png"), roi=(259, 106, 250, 360), threshold=0.8)
        if pos_suntouMY:
            background_click(hwnd, pos_suntouMY[0], pos_suntouMY[1])
            task_controller.smart_sleep(1)
            background_click(hwnd, 664, 401, button="left", delay=60)
            task_controller.smart_sleep(2)
            for _ in range(2):
                background_click(hwnd, 697, 337, button="left", action="double", delay=60)
                task_controller.smart_sleep(1)
            background_click(hwnd, 664, 455, button="left", action="double", delay=60)
            background_click(hwnd, 664, 455, button="left", action="double", delay=60)
            task_controller.smart_sleep(1)
            if buy_baogou_man(hwnd):
                raise TargetNotFoundError("购买失败，包裹满了")
            task_controller.smart_sleep(2)
            logger.info(f"{task_name}任务执行成功")
            return True
        elif count == 9:
            raise TargetNotFoundError("未找到榫头卯眼图标")
        else:
            background_drag(hwnd, 387, 318, 387, 208, drag_duration=0.5)
            task_controller.smart_sleep(1)
    
    return False


def _handle_duihuan_wujingzhi(hwnd) -> bool:
    """
    兑换武经志子任务
    
    参数：
        hwnd: 窗口句柄
    
    返回：
        bool: 执行是否成功
    """
    return _subtask_not_implemented(hwnd, "兑换武经志")


def _handle_xiaohonghua_lihe(hwnd) -> bool:
    """
    小红花礼盒子任务
    
    参数：
        hwnd: 窗口句柄
    
    返回：
        bool: 执行是否成功
    """
    return _subtask_not_implemented(hwnd, "小红花礼盒")


def _handle_goumai_tongdouzi(hwnd) -> bool:
    """
    购买铜豆子子任务
    
    参数：
        hwnd: 窗口句柄
    
    返回：
        bool: 执行是否成功
    """
    return _subtask_not_implemented(hwnd, "购买铜豆子")


def _handle_gongji_huantongban(hwnd) -> bool:
    """
    功绩换铜板子任务
    
    参数：
        hwnd: 窗口句柄
    
    返回：
        bool: 执行是否成功
    """
    return _subtask_not_implemented(hwnd, "功绩换铜板")


def _handle_hangdang_juehuo(hwnd) -> bool:
    """
    行当绝活子任务
    
    参数：
        hwnd: 窗口句柄
    
    返回：
        bool: 执行是否成功
    """
    return _subtask_not_implemented(hwnd, "行当绝活")


@with_retry(max_retries=3, recovery_func=win_gb)
def _handle_bitong_mapi(hwnd) -> bool:
    """
    碧铜马坯子任务
    
    参数：
        hwnd: 窗口句柄
    
    返回：
        bool: 执行是否成功
    """
    task_name = "碧铜马坯"
    logger.info(f"正在处理: {task_name}")
    
    baoguo_manSet(hwnd)

    background_key(hwnd, 'B')
    task_controller.smart_sleep(1)

    pos_hdsz = find_image(hwnd, config.get_img_path("chushihua_/hdsz.png"), threshold=0.8)
    if pos_hdsz is None:
        raise TargetNotFoundError("未找到活动设置图标")
    
    background_click(hwnd, pos_hdsz[0], pos_hdsz[1], button="left", delay=60)
    task_controller.smart_sleep(2)

    pos_zhenbaoge = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_zhenbaoge.png"), threshold=0.8)
    if pos_zhenbaoge is None:
        raise TargetNotFoundError("未找到珍宝阁图标")
    
    background_click(hwnd, pos_zhenbaoge[0], pos_zhenbaoge[1], button="left", delay=60)
    task_controller.smart_sleep(3)
    background_click(hwnd, 879, 433, button="left", delay=60)
    task_controller.smart_sleep(3)
    pos_yijiBS = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_yijiBS.png"), threshold=0.8)
    if pos_yijiBS is not None:
        background_click(hwnd, 156, 131, button="left", delay=60)
        task_controller.smart_sleep(5)
    
    background_drag(hwnd, 162, 443, 162, 0, drag_duration=0.5)
    task_controller.smart_sleep(1)
    
    gudongCL_path = [
        config.get_img_path("richang_/meiriduihuan/MRDH_gudongCL.png"),
        config.get_img_path("richang_/meiriduihuan/MRDH_gudongCL2.png"),
    ] 
    pos_gudongCL = find_image(hwnd, gudongCL_path, threshold=0.8)
    if pos_gudongCL is None:
        raise TargetNotFoundError("未找到古董材料图标")
    
    background_click(hwnd, pos_gudongCL[0], pos_gudongCL[1], button="left", delay=60)
    task_controller.smart_sleep(3)
    
    for count in range(10):
        pos_bitongMP = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_bitongMP.png"), roi=(259, 106, 250, 360), threshold=0.8)
        if pos_bitongMP:
            background_click(hwnd, pos_bitongMP[0], pos_bitongMP[1])
            task_controller.smart_sleep(1)
            background_click(hwnd, 664, 401, button="left", delay=60)
            task_controller.smart_sleep(2)
            for _ in range(2):
                background_click(hwnd, 697, 337, button="left", action="double", delay=60)
                task_controller.smart_sleep(1)
            background_click(hwnd, 664, 455, button="left", action="double", delay=60)
            background_click(hwnd, 664, 455, button="left", action="double", delay=60)
            task_controller.smart_sleep(1)
            if buy_baogou_man(hwnd):
                raise TargetNotFoundError("购买失败，包裹满了")
            task_controller.smart_sleep(2)
            logger.info(f"{task_name}任务执行成功")
            return True
        elif count == 9:
            raise TargetNotFoundError("未找到碧铜马坯图标")
    
    return False


@with_retry(max_retries=3, recovery_func=win_gb)
def _handle_mai_wuyuejianpi(hwnd) -> bool:
    """
    买吴越剑坯子任务
    
    参数：
        hwnd: 窗口句柄
    
    返回：
        bool: 执行是否成功
    """
    task_name = "买吴越剑坯"
    logger.info(f"正在处理: {task_name}")
    
    baoguo_manSet(hwnd)

    background_key(hwnd, 'B')
    task_controller.smart_sleep(1)

    pos_hdsz = find_image(hwnd, config.get_img_path("chushihua_/hdsz.png"), threshold=0.8)
    if pos_hdsz is None:
        raise TargetNotFoundError("未找到活动设置图标")
    
    background_click(hwnd, pos_hdsz[0], pos_hdsz[1], button="left", delay=60)
    task_controller.smart_sleep(2)

    pos_zhenbaoge = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_zhenbaoge.png"), threshold=0.8)
    if pos_zhenbaoge is None:
        raise TargetNotFoundError("未找到珍宝阁图标")
    
    background_click(hwnd, pos_zhenbaoge[0], pos_zhenbaoge[1], button="left", delay=60)
    task_controller.smart_sleep(3)
    background_click(hwnd, 879, 306, button="left", delay=60)
    task_controller.smart_sleep(2)
    background_click(hwnd, 218, 122, button="left", delay=60)
    task_controller.smart_sleep(2)
    background_click(hwnd, 222, 207, button="left", delay=60)
    task_controller.smart_sleep(2)

    pos_wuyueJP = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_wuyueJP.png"), roi=(49, 105, 500, 370), threshold=0.8)
    if pos_wuyueJP is None:
        raise TargetNotFoundError("未找到吴越剑坯图标")
    
    background_click(hwnd, pos_wuyueJP[0], pos_wuyueJP[1], button="left", delay=60)
    task_controller.smart_sleep(3)
    background_click(hwnd, 691, 409, button="left", delay=60)
    task_controller.smart_sleep(2)
    for i in range(2):
        background_click(hwnd, 718, 347, button="left", action="double", delay=60)
        task_controller.smart_sleep(1)
    background_click(hwnd, 684, 462, button="left", action="double", delay=60)
    background_click(hwnd, 684, 462, button="left", action="double", delay=60)
    if buy_baogou_man(hwnd):
        raise TargetNotFoundError("购买失败，包裹满了")
    task_controller.smart_sleep(3)

    pos_yingliangBZ = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_yingliangBZ.png"), threshold=0.8)
    if pos_yingliangBZ is not None:
        logger.info("银两不足，无法购买")
        task_controller.smart_sleep(2)
        background_click(hwnd, 316, 351, button="left", delay=60)
        logger.info(f"{task_name}任务执行成功")
        return False
    
    task_controller.smart_sleep(2)
    logger.info(f"{task_name}任务执行成功")
    return True


@with_retry(max_retries=3, recovery_func=win_gb)
def _handle_mai_baigongdingpi(hwnd) -> bool:
    """
    买白公鼎坯子任务
    
    参数：
        hwnd: 窗口句柄
    
    返回：
        bool: 执行是否成功
    """
    task_name = "买白公鼎坯"
    logger.info(f"正在处理: {task_name}")
    
    baoguo_manSet(hwnd)

    background_key(hwnd, 'B')
    task_controller.smart_sleep(1)

    pos_hdsz = find_image(hwnd, config.get_img_path("chushihua_/hdsz.png"), threshold=0.8)
    if pos_hdsz is None:
        raise TargetNotFoundError("未找到活动设置图标")
    
    background_click(hwnd, pos_hdsz[0], pos_hdsz[1], button="left", delay=60)
    task_controller.smart_sleep(2)

    pos_zhenbaoge = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_zhenbaoge.png"), threshold=0.8)
    if pos_zhenbaoge is None:
        raise TargetNotFoundError("未找到珍宝阁图标")
    
    background_click(hwnd, pos_zhenbaoge[0], pos_zhenbaoge[1], button="left", delay=60)
    task_controller.smart_sleep(3)
    background_click(hwnd, 879, 306, button="left", delay=60)
    task_controller.smart_sleep(2)
    background_click(hwnd, 218, 122, button="left", delay=60)
    task_controller.smart_sleep(2)
    background_click(hwnd, 222, 207, button="left", delay=60)
    task_controller.smart_sleep(2)

    pos_baigongDP = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_baigongDP.png"), roi=(49, 105, 500, 370), threshold=0.8)
    if pos_baigongDP is None:
        raise TargetNotFoundError("未找到白公鼎坯图标")
    
    background_click(hwnd, pos_baigongDP[0], pos_baigongDP[1], button="left", delay=60)
    task_controller.smart_sleep(3)
    background_click(hwnd, 691, 409, button="left", delay=60)
    task_controller.smart_sleep(2)
    for i in range(2):
        background_click(hwnd, 718, 347, button="left", action="double", delay=60)
        task_controller.smart_sleep(1)
    background_click(hwnd, 684, 462, button="left", action="double", delay=60)
    background_click(hwnd, 684, 462, button="left", action="double", delay=60)
    if buy_baogou_man(hwnd):
        raise TargetNotFoundError("购买失败，包裹满了")
    task_controller.smart_sleep(3)

    pos_yingliangBZ = find_image(hwnd, config.get_img_path("richang_/meiriduihuan/MRDH_yingliangBZ.png"), threshold=0.8)
    if pos_yingliangBZ is not None:
        logger.info("银两不足，无法购买")
        task_controller.smart_sleep(2)
        background_click(hwnd, 316, 351, button="left", delay=60)
        logger.info(f"{task_name}任务执行成功")
        return False
    
    task_controller.smart_sleep(2)
    logger.info(f"{task_name}任务执行成功")
    return True


def _handle_duihuan_jinfangxiu(hwnd) -> bool:
    """
    兑换锦芳绣子任务
    
    参数：
        hwnd: 窗口句柄
    
    返回：
        bool: 执行是否成功
    """
    return _subtask_not_implemented(hwnd, "兑换锦芳绣")


def _handle_mai_xingyingxinde(hwnd) -> bool:
    """
    买形影心得子任务
    
    参数：
        hwnd: 窗口句柄
    
    返回：
        bool: 执行是否成功
    """
    return _subtask_not_implemented(hwnd, "买形影心得")


def _handle_huan_gaojicuishi(hwnd) -> bool:
    """
    换高级萃石子任务
    
    参数：
        hwnd: 窗口句柄
    
    返回：
        bool: 执行是否成功
    """
    return _subtask_not_implemented(hwnd, "换高级萃石")


SUBTASK_HANDLERS = {
    "每日签到": _handle_meiri_qiandao,
    "每日江湖礼": _handle_meiri_jianghuli,
    "每日在线礼": _handle_meiri_zaixianli,
    "每日回馈礼": _handle_meiri_huikuli,
    "每日买银票": _handle_meiri_maiyinpiao,
    "买鸡蛋": _handle_mai_jidan,
    "榫头卯眼": _handle_suntou_maoyan,
    "兑换武经志": _handle_duihuan_wujingzhi,
    "小红花礼盒": _handle_xiaohonghua_lihe,
    "购买铜豆子": _handle_goumai_tongdouzi,
    "功绩换铜板": _handle_gongji_huantongban,
    "行当绝活": _handle_hangdang_juehuo,
    "碧铜马坯": _handle_bitong_mapi,
    "买吴越剑坯": _handle_mai_wuyuejianpi,
    "买白公鼎坯": _handle_mai_baigongdingpi,
    "兑换锦芳绣": _handle_duihuan_jinfangxiu,
    "买形影心得": _handle_mai_xingyingxinde,
    "换高级萃石": _handle_huan_gaojicuishi,
}
