# -*- coding: utf-8 -*-
"""
基础校正框架（所有题型通用）
【已优化：带 - 自动粘合下一行文字，解决 SYN- SENT / SY- NSENT 问题】
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
        # 手写题专用 OCR 参数
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang="ch",
            show_log=False,
            use_dilation=True,
            det_db_unclip_ratio=2.2,
            det_limit_side_len=1280,
            det_db_score_mode="slow",
            drop_score=0.4,
            rec_batch_num=4
        )
        self.question_type = "基础题型"
        self.total_score = 10.0

    def _preprocess_image(self, img_path):
        img = cv2.imread(img_path)
        if img is None:
            raise ValueError(f"无法读取图片：{img_path}")

        h, w = img.shape[:2]
        if h < 600 or w < 800:
            img = cv2.resize(img, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)

        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=21,
            C=4
        )

        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.dilate(binary, kernel, iterations=1)
        binary = cv2.bitwise_not(binary)
        processed_img = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

        return processed_img

    def extract_text_with_coords(self, img_path):
        try:
            processed_img = self._preprocess_image(img_path)
            result = self.ocr.ocr(processed_img, cls=True)

            if not result or len(result) == 0 or result[0] is None:
                return {}, []

            result = result[0]
            items = []

            for line in result:
                bbox = line[0]
                text = line[1][0]
                score = line[1][1]

                if score < 0.45:
                    continue

                text = self._clean_text(text)
                if not text:
                    continue

                # 取框的四个点
                x1, y1 = bbox[0]
                x2, y2 = bbox[1]
                x3, y3 = bbox[2]
                x4, y4 = bbox[3]

                # 计算中心点
                cx = (x1 + x3) / 2
                cy = (y1 + y3) / 2

                # 保存：文本, 中心点x, 中心点y, 框
                items.append((text, cx, cy, bbox))

            # ===================== 🔥 最终正确合并规则 =====================
            # 1. 只有 末尾以 "-" 结尾
            # 2. 且 下一行在垂直方向很近
            # 3. 同一行左右的内容 绝不合并
            merged = []
            skip_next = False
            for i in range(len(items)):
                if skip_next:
                    skip_next = False
                    continue

                text1, cx1, cy1, bbox1 = items[i]

                # ----------------------- 核心修复：只合并 【末尾- + 下一行】 -----------------------
                if text1.endswith("-") and i + 1 < len(items):
                    text2, cx2, cy2, bbox2 = items[i+1]

                    # 垂直距离近（真正是换行），水平可以随便
                    delta_y = abs(cy2 - cy1)
                    if delta_y < 40:  # 行间距小 = 是上下关系
                        # 合并！
                        combined = text1 + text2
                        merged.append((combined, cx1, cy1, bbox1))
                        skip_next = True
                        continue

                # 不满足合并条件，直接加入
                merged.append(items[i])

            # 构建结果
            text_coords = {}
            all_results = []
            for text, cx, cy, bbox in merged:
                text_coords[text] = (cx, cy, bbox)
                all_results.append((text, cx, cy, 1.0))

            return text_coords, all_results

        except Exception as e:
            raise Exception(f"OCR识别失败：{str(e)}")


    def _clean_text(self, text):
        text = text.strip()
        text = re.sub(r"\s+", "", text)
        text = re.sub(r"[，。！？；：、—～·\(\)\[\]【】]", "", text)
        text = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fa5\-]", "", text)
        return text

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