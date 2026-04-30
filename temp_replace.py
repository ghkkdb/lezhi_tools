# -*- coding: utf-8 -*-
"""
临时脚本：批量替换 time.sleep 为 task_controller.smart_sleep
"""
import re

file_path = r'e:\Tare_project\YMJH\src\core\daily_tasks.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 统计替换前的数量
before_count = len(re.findall(r'\btime\.sleep\(', content))
print(f'替换前: {before_count} 处 time.sleep')

# 使用正则表达式替换
# 匹配 time.sleep( 但不匹配注释中的
# 策略：逐行处理，跳过纯注释行
lines = content.split('\n')
new_lines = []
replace_count = 0

for line_num, line in enumerate(lines, 1):
    # 去除前导空格
    stripped = line.lstrip()
    
    # 如果是纯注释行，不替换
    if stripped.startswith('#'):
        new_lines.append(line)
    else:
        # 非注释行，替换 time.sleep 为 task_controller.smart_sleep
        if 'time.sleep(' in line:
            # 使用正则替换，确保是完整的 time.sleep(
            new_line = re.sub(r'\btime\.sleep\(', 'task_controller.smart_sleep(', line)
            if new_line != line:
                new_lines.append(new_line)
                replace_count += 1
                print(f'第 {line_num} 行已替换')
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

# 写回文件
new_content = '\n'.join(new_lines)
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

# 统计替换后的数量
after_count = len(re.findall(r'\btime\.sleep\(', new_content))
print(f'\n替换后: {after_count} 处 time.sleep')
print(f'成功替换: {replace_count} 处')
print('替换完成！')
