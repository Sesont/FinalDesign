# -*- coding: utf-8 -*-
"""
基础校正框架（所有题型通用）
【已修复OpenCV报错 + 优化OCR识别精度 + 兼容PaddleOCR输入】
"""
from abc import ABC, abstractmethod
from paddleocr import PaddleOCR
from PIL import Image
import cv2
import numpy as np
import re

class BaseCorrection(ABC):
    """基础校正抽象类（定义通用接口）"""
    def __init__(self):
        # 初始化高精度OCR（全局只初始化一次）
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang="ch",
            show_log=False,
            use_dilation=True,        # 文字膨胀，增强手写体
            det_db_unclip_ratio=1.6,   # 扩大文字检测框
            rec_batch_num=4
        )
        self.question_type = "基础题型"
        self.total_score = 10.0

    # ===================== 【核心修复+优化】图像预处理 =====================
    def _preprocess_image(self, img_path):
        """
        专为手写主观题优化的预处理，修复OpenCV报错
        1. 灰度化 2. 降噪（修复核大小为奇数） 3. 二值化 4. 对比度增强 5. 转回BGR兼容PaddleOCR
        """
        # 1. 读取原始图像（BGR格式）
        img = cv2.imread(img_path)
        if img is None:
            raise ValueError(f"无法读取图片：{img_path}")

        # 2. 转灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 3. 中值滤波去噪（修复：核大小改为3，必须为奇数）
        gray = cv2.medianBlur(gray, 3)

        # 4. 自适应二值化（黑字白底，适配手写）
        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=15,
            C=3
        )

        # 5. 膨胀让手写笔画更连续（核大小3，奇数）
        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.dilate(binary, kernel, iterations=1)

        # 6. 转回白底黑字
        binary = cv2.bitwise_not(binary)

        # 7. 【关键修复】转回3通道BGR格式，兼容PaddleOCR输入要求
        processed_img = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

        return processed_img

    # ===================== 【核心优化】高精度OCR识别（文字+坐标） =====================
    def extract_text_with_coords(self, img_path):
        """
        优化点：
        1. 自动预处理图像（修复报错）
        2. 过滤低置信度文字（<0.6 直接丢弃）
        3. 清洗乱码、标点、空格
        4. 按坐标从上到下排序（更符合阅读顺序）
        """
        try:
            # 预处理（关键！修复报错）
            processed_img = self._preprocess_image(img_path)

            # OCR识别
            result = self.ocr.ocr(processed_img, cls=True)
            if not result or len(result) == 0 or result[0] is None:
                return {}, []

            result = result[0]
            text_coords = {}
            all_results = []

            for line in result:
                bbox = line[0]          # 四点坐标
                text = line[1][0]      # 识别文字
                score = line[1][1]     # 置信度

                # ========== 过滤低置信度（避免乱识别） ==========
                if score < 0.6:
                    continue

                # ========== 文本清洗（超级关键） ==========
                text = self._clean_text(text)

                if len(text) < 1:
                    continue

                # 计算中心点
                cx = (bbox[0][0] + bbox[2][0]) / 2
                cy = (bbox[0][1] + bbox[2][1]) / 2

                text_coords[text] = (cx, cy, bbox)
                all_results.append((text, cx, cy, score))

            # ========== 按从上到下排序 ==========
            all_results = sorted(all_results, key=lambda x: x[2])

            return text_coords, all_results

        except Exception as e:
            raise Exception(f"OCR识别失败：{str(e)}")

    # ===================== 【优化】文本清洗（去掉干扰） =====================
    def _clean_text(self, text):
        """清洗干扰字符：空格、标点、表情、乱码、短字符"""
        text = text.strip()
        text = re.sub(r"\s+", "", text)                  # 去空格
        text = re.sub(r"[，。！？；：、—～·\(\)\[\]【】]", "", text)  # 去标点
        text = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fa5=]", "", text) # 保留中文/英文/数字/等号（适配TCP报文）
        return text

    # ===================== 通用方法 =====================
    def load_image(self, img_path, canvas=None):
        try:
            img = Image.open(img_path)
            if canvas:
                canvas_w = canvas.winfo_width() or 600
                canvas_h = canvas.winfo_height() or 800
                img.thumbnail((canvas_w, canvas_h), Image.Resampling.LANCZOS)
            return img
        except Exception as e:
            raise Exception(f"图片加载失败：{str(e)}")

    # ===================== 抽象方法（子类必须实现） =====================
    @abstractmethod
    def get_standard_rules(self):
        pass

    @abstractmethod
    def match_keywords(self, text_coords):
        pass

    @abstractmethod
    def check_structure(self, text_coords):
        pass

    @abstractmethod
    def check_detail(self, text_coords):
        pass

    @abstractmethod
    def calculate_score(self, kw_score, struct_score, detail_score):
        pass