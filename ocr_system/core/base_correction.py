# -*- coding: utf-8 -*-
"""
基础校正框架（所有题型通用）
【终极双遍历合并版：支持隔行合并、只保留合并结果、自动生成坐标】
"""
from abc import ABC, abstractmethod
from paddleocr import PaddleOCR
from PIL import Image
import cv2
import numpy as np
import re

class BaseCorrection(ABC):
    def __init__(self):
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
        gray = cv2.GaussianBlur(gray, (3, 3), 0)#高斯模糊调小

        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=21,
            C=4
        )

        kernel = np.ones((1, 1), np.uint8)#膨胀变细
        binary = cv2.dilate(binary, kernel, iterations=1)
        binary = cv2.bitwise_not(binary)
        processed_img = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

        return processed_img

    def extract_text_with_coords(self, img_path):
        try:
            processed_img = self._preprocess_image(img_path)
            result = self.ocr.ocr(processed_img, cls=True)
            if not result: return {}, []
            result = result[0]

            # ========== 第一次遍历：正常提取 ==========
            items = []
            for line in result:
                bbox = line[0]
                text = line[1][0]
                score = line[1][1]
                if score < 0.45: continue
                text = self._clean_text(text)
                if not text: continue

                x1, y1 = bbox[0]
                x3, y3 = bbox[2]
                cx = (x1 + x3) / 2
                cy = (y1 + y3) / 2
                items.append([text, cx, cy, bbox])

            # ========== 第二次遍历：全局合并（你要的功能） ==========
            merged = []
            skip = set()
            n = len(items)

            for i in range(n):
                if i in skip: continue
                t1, cx1, cy1, b1 = items[i]

                # 寻找以“-”结尾的，向后3行找同列匹配
                best_match = -1
                min_dx = 999

                if t1.endswith("-"):
                    for j in range(i+1, min(i+4, n)):
                        if j in skip: continue
                        t2, cx2, cy2, b2 = items[j]
                        dx = abs(cx2 - cx1)
                        dy = abs(cy2 - cy1)
                        if dx < 100 and dy < 120:  # 同列、接近
                            if dx < min_dx:
                                min_dx = dx
                                best_match = j

                # 找到就合并
                if best_match != -1:
                    t2, cx2, cy2, b2 = items[best_match]
                     # ✅ 保留 `-`，直接拼接
                    new_text = t1 + t2  

                    # 合并坐标
                    x_min = min(b1[0][0], b2[0][0])
                    y_min = min(b1[0][1], b2[0][1])
                    x_max = max(b1[2][0], b2[2][0])
                    y_max = max(b1[2][1], b2[2][1])
                    new_bbox = [[x_min,y_min],[x_max,y_min],[x_max,y_max],[x_min,y_max]]
                    new_cx = (x_min+x_max)/2
                    new_cy = (y_min+y_max)/2

                    merged.append([new_text, new_cx, new_cy, new_bbox])
                    skip.add(i)
                    skip.add(best_match)
                    continue

                merged.append([t1, cx1, cy1, b1])

            # 构建输出
            text_coords = {}
            all_results = []
            for item in merged:
                t, cx, cy, bbox = item
                text_coords[t] = (cx, cy, bbox)
                all_results.append((t, cx, cy, bbox))

            return text_coords, all_results

        except Exception as e:
            raise Exception(f"OCR识别失败：{str(e)}")

    def _clean_text(self, text):
        text = text.strip()
        text = re.sub(r"\s+", "", text)
        text = re.sub(r"[，。！？；：、—～·\(\)\[\]【】]", "", text)
        text = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fa5\-\=]", "", text)
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
    def get_standard_rules(self): pass
    @abstractmethod
    def match_keywords(self, text_coords): pass
    @abstractmethod
    def check_structure(self, text_coords): pass
    @abstractmethod
    def check_detail(self, text_coords): pass
    @abstractmethod
    def calculate_score(self, kw_score, struct_score, detail_score): pass