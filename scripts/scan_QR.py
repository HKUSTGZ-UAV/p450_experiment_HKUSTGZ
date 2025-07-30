import cv2
import os
import numpy as np
from qreader import QReader

# 初始化 QReader
qreader = QReader()

# 文件夹路径
image_folder = os.path.expanduser("~/fly_1/")
image_extensions = ('.jpg', '.jpeg', '.png')

# 图像裁剪和增强
# def crop_and_enhance(image, scale=4.0):
#     # 图像放大 + 灰度 + 自适应阈值
#     h, w = image.shape[:2]
#     zoomed = cv2.resize(image, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_CUBIC)
#     gray = cv2.cvtColor(zoomed, cv2.COLOR_BGR2GRAY)
#     enhanced = cv2.adaptiveThreshold(gray, 255,
#                                      cv2.ADAPTIVE_THRESH_MEAN_C,
#                                      cv2.THRESH_BINARY, 11, 2)
#     return enhanced
def crop_and_enhance(image, scale=5.0, block_size=21, C=5):
    h, w = image.shape[:2]
    zoomed = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(zoomed, cv2.COLOR_BGR2GRAY)

    # 可选：锐化
    kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    sharpened = cv2.filter2D(gray, -1, kernel)

    enhanced = cv2.adaptiveThreshold(sharpened, 255,
                                     cv2.ADAPTIVE_THRESH_MEAN_C,
                                     cv2.THRESH_BINARY,
                                     block_size, C)
    return enhanced


# 遍历图像文件
for filename in sorted(os.listdir(image_folder)):
    if not filename.lower().endswith(image_extensions):
        continue

    image_path = os.path.join(image_folder, filename)
    image = cv2.imread(image_path)
    if image is None:
        print(f"[跳过] 无法读取图像: {filename}")
        continue

    print(f"\n[•] 图像: {filename}")

    # 原图尝试识别
    decoded = qreader.detect_and_decode(image)
    if decoded:
        for i, data in enumerate(decoded):
            print(f"   ➤ 第{i+1}个二维码识别内容: {data}")
        continue

    # 放大增强图像后再尝试
    enhanced = crop_and_enhance(image)
    decoded_enhanced = qreader.detect_and_decode(enhanced)
    if decoded_enhanced:
        for i, data in enumerate(decoded_enhanced):
            print(f"   ➤ 第{i+1}个二维码【放大增强】识别内容: {data}")
    else:
        print(f"   × 放大增强后仍未检测到二维码")
