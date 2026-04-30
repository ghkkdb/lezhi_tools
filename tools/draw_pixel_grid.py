# -*- coding: utf-8 -*-
"""
像素网格绘制工具
================
在截图上绘制坐标网格，辅助定位界面元素

主要功能：
    - draw_pixel_grid: 在图片上绘制像素网格
"""
from PIL import Image, ImageDraw, ImageFont


def draw_pixel_grid(image_path, grid_size=50, output_path="grid_image.png"):
    """
    在图片上绘制像素网格，仅在X轴/Y轴标注像素坐标，左上角为(0,0)

    参数：
        image_path: 原始图片路径
        grid_size: 网格大小（每个网格的像素宽/高，默认50像素）
        output_path: 带网格的图片保存路径
    """
    try:
        img = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(f"加载图片失败：{e}")
        return
    
    draw = ImageDraw.Draw(img)
    img_width, img_height = img.size
    print(f"图片原始尺寸：宽 {img_width} 像素，高 {img_height} 像素")

    try:
        font = ImageFont.truetype("simhei.ttf", 12)
    except:
        try:
            font = ImageFont.truetype("/Library/Fonts/Arial Unicode.ttf", 12)
        except:
            font = ImageFont.load_default(size=12)

    for x in range(0, img_width + 1, grid_size):
        draw.line([(x, 0), (x, img_height)], fill=(255, 0, 0, 128), width=1)

    for y in range(0, img_height + 1, grid_size):
        draw.line([(0, y), (img_width, y)], fill=(255, 0, 0, 128), width=1)

    for x in range(0, img_width + 1, grid_size):
        text = f"{x}"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        draw.text((x - text_width / 2, 2), text, fill=(255, 255, 255, 255), font=font)

    for y in range(0, img_height + 1, grid_size):
        text = f"{y}"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_height = text_bbox[3] - text_bbox[1]
        draw.text((2, y - text_height / 2), text, fill=(255, 255, 255, 255), font=font)

    img.save(output_path)
    img.show()
    print(f"带网格的图片已保存至：{output_path}")


if __name__ == "__main__":
    IMAGE_PATH = "assets/img/test.jpg"
    GRID_SIZE = 20
    
    draw_pixel_grid(
        image_path=IMAGE_PATH,
        grid_size=GRID_SIZE,
        output_path="assets/img/marked_image.png"
    )
