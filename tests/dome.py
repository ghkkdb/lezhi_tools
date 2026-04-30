import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import config
from src.utils import background_click,bind_window,find_image
import time
import random
from src.utils import background_click, background_key, background_drag, find_image
from src.config import config


hwnd = bind_window(class_name=config.class_name)
# 截图
# img = capture_window(hwnd,'img/test.jpg')
# win_gb(hwnd)
# baoguo_manSet(hwnd)
background_click(hwnd, 235, 469, button="left", delay=60)

pos_yaoqianshu_open = find_image(hwnd, config.get_img_path(
    "./richang_/yaoqianshu/yaoqianshu_open.png"), roi=[140, 360, 120, 80], threshold=0.8)

time.sleep(1)
# task_chaguan(hwnd)

# pos_yun_zhsr = find_image(hwnd, "img/richang_/keye_yun_3.png",threshold=0.8)
# if pos_yun_zhsr is not None:
#     background_click(hwnd, 629, 420, button="left", delay=60)
#     time.sleep(1)

# while True:
#     pos_xuqiu = find_image(hwnd, "img/richang_/xuqiu.png",threshold=0.8)
#     if pos_xuqiu is not None:
#             last_action_time = time.time()
#             # log_signal.emit(" [INFO] 课业需求购买中...")
#             background_click(hwnd, 404, 142, button="left", delay=60)
#             time.sleep(2)
#             pos_gomai = find_image(hwnd, "img/richang_/keye_gomai.png",threshold=0.8)
#             if pos_gomai is not None:
#                 # log_signal.emit(" [INFO] 课业购买中...")
#                 background_click(hwnd, pos_gomai[0], pos_gomai[1], button="left", delay=60)
#                 time.sleep(1)
#                 background_click(hwnd, 618, 353, button="left", delay=60)
#                 time.sleep(1)
#                 pos_baogou_man = find_image(hwnd, "img/richang_/baogou_man.png",threshold=0.8)
#                 if pos_baogou_man is not None:
#                     # log_signal.emit(" [INFO] 包裹满了")
#                     print("包裹满了")
#                     win_gb(hwnd)
# task_bangpai(hwnd)


# pos_jieshu = find_image(hwnd, "img/richang_/keye_jieshu.png",threshold=0.8)
# # background_click(hwnd, pos_keye5[0], pos_keye5[1], button="left", delay=60)
# background_click(hwnd, 663, 354, button="left", delay=60)
# time.sleep(2)
# win_gb(hwnd)
# task_keye(hwnd)
# pos_keye5 = find_image(hwnd, "img/richang_/keye_5.png",threshold=0.5)
# pos_canwu = find_image(hwnd, "img/richang_/keye_canwu.png",threshold=0.8)

# hwnd = init_Game_set()


# win_gb(hwnd)

# DuanYou_set(hwnd)

# TuiLIKaShi_set(hwnd)

# TuiDui_set(hwnd)

# task_gua(hwnd)



# pos = find_image(hwnd, "img/chushihua_/kashi.png", roi=[900,460,40,40],threshold=0.7)



# for i in range(30):
#     pos = find_image(hwnd, "img/tuichu.png", roi=[900,120,40,40],threshold=0.7)
#     if pos is not None:
#         background_click(hwnd, pos[0], pos[1], button="left", delay=60)
#         print('退出副本！')
#         break
#     else:
#         print('未找到退出按钮！')

# for i in range(30):
#     pos = find_image(hwnd, "img/lk.png",roi=[560,320,120,60], threshold=0.5)
#     if pos is not None:
#         background_click(hwnd, pos[0], pos[1], button="left", delay=60)
#         print('确定退出副本！')
#         break