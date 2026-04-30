import time
from src.utils import background_click, background_key, background_drag, find_image,find_all_images
from src.core.helpers import JN_set,DuanYou_set
from src.utils.logger import get_logger
from src.config import config
import win32gui
import win32con
from src.core.subtasks_meiri_kehuan import _handle_mai_jidan
from src.core.daily_tasks import _fuben_louji,task_richang_FB
from src.core.helpers import buy_all_buy

import src.config.settings as config

hwnd = win32gui.FindWindow("Messiah_Game",None)

# buy_all_buy(hwnd)
k = 1
n = find_all_images(hwnd,r"D:\Python\YMJH-tasks\assets\img\richang_\fuben_louji\FB_zhushou_JS.png",threshold=0.8)[0]

print(n)
if 10-n>=k:
    print("ok")
else:
    print("not ok")

# pos = find_image(hwnd, r"D:\Python\YMJH-tasks\assets\img\richang_\fuben_louji\fuben_QR.png",threshold=0.5)
# print(pos)


# while True:
#      n = _chushihua_goutu(hwnd)
#      print(n)
#      time.sleep(2)
# # JN_set(hwnd)