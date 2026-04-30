# -*- coding: utf-8 -*-
import re

file_path = r'e:\Tare_project\YMJH\src\core\daily_tasks.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 统计替换前的数量
before_count = content.count('time.sleep(')
print(f'替换前: {before_count} 处 time.sleep')

# 直接全局替换
new_content = content.replace('time.sleep(', 'task_controller.smart_sleep(')

# 统计替换后的数量
after_count = new_content.count('time.sleep(')
smart_sleep_count = new_content.count('task_controller.smart_sleep(')

print(f'替换后: {after_count} 处 time.sleep')
print(f'smart_sleep: {smart_sleep_count} 处')

# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('替换完成！')
