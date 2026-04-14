# 导入核心库
import cv2
import matplotlib.pyplot as plt
from pix2tex import cli as latex_ocr
import os
from PIL import Image  # 新增：导入PIL库，用于格式转换
import numpy as np     # 新增：确保numpy可用

# --------------- 1. 配置路径（改成你的实际图片路径）---------------
# 注意：必须指向具体图片文件，不是文件夹！
IMG_PATH = r"D:\codeforvs\cn_ocr\images\cn_formula_test.png"  # 替换成你的图片名

# 路径检查
if not os.path.exists(IMG_PATH):
    print(f"❌ 图片路径不存在：{IMG_PATH}")
    print("请检查图片是否放在正确位置，文件名是否正确！")
    exit()
if not os.path.isfile(IMG_PATH):
    print(f"❌ 错误：{IMG_PATH} 是文件夹，不是具体图片文件！")
    exit()

# --------------- 2. 图像预处理（针对手写公式优化）---------------
def preprocess_cn_formula(img_path):
    """
    计算机网络手写公式预处理：灰度化→降噪→二值化
    返回：原始图（BGR）、预处理后的图（PIL格式，供OCR识别）
    """
    # 读取图片（OpenCV格式）
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"无法读取图片：{img_path}，请检查文件是否损坏/格式是否正确")
    
    # 灰度化
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 高斯降噪（减少手写噪点）
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    # 自适应二值化（让公式更清晰）
    thresh = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )
    
    # 关键修正：将numpy数组转换为PIL图片（供OCR识别）
    # 先把二值化图转回RGB（PIL要求3通道）
    thresh_rgb = cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB)
    # 转换为PIL格式
    thresh_pil = Image.fromarray(thresh_rgb)
    
    return img, thresh, thresh_pil

# 执行预处理
original_img, processed_img_np, processed_img_pil = preprocess_cn_formula(IMG_PATH)

# --------------- 3. 公式识别（核心：传入PIL格式图片）---------------
# 初始化LaTeX-OCR模型（已下载权重，无需重复下载）
model = latex_ocr.LatexOCR()
# 识别公式（传入PIL格式的图片）
latex_text = model(processed_img_pil)

# --------------- 4. 结果展示 ---------------
# 显示原始图和预处理后的图
plt.figure(figsize=(12, 6))
# 原始图（转换为RGB显示）
plt.subplot(1, 2, 1)
plt.imshow(cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB))
plt.title("原始手写公式图")
plt.axis("off")
# 预处理后的图（numpy格式，灰度显示）
plt.subplot(1, 2, 2)
plt.imshow(processed_img_np, cmap="gray")
plt.title("预处理后的图")
plt.axis("off")

# 打印识别结果
print("="*50)
print("📝 识别出的计算机网络公式（LaTeX格式）：")
print(latex_text)
# 公式含义匹配（针对常见网络公式）
formula_dict = {
    "C = W \\log_2(1 + S/N)": "香农公式（信道最大传输速率）",
    "总时延 = 发送时延 + 传播时延 + 处理时延 + 排队时延": "网络总时延公式",
    "吞吐量 = 数据量 / 传输时间": "网络吞吐量公式",
    "丢包率 = 丢失数据包数 / 总数据包数": "网络丢包率公式"
}
# 匹配含义（模糊匹配）
desc = "未知公式"
for key in formula_dict:
    if key in latex_text or latex_text in key:
        desc = formula_dict[key]
        break
print(f"🔍 公式含义：{desc}")
print("="*50)

# 显示图片
plt.show()