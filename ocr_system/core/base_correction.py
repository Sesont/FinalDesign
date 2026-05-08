# -*- coding: utf-8 -*-
"""
计网手写识别基类
通用预处理、OCR、文本分析、坐标合并
"""
from abc import ABC, abstractmethod
from paddleocr import PaddleOCR
import cv2
import numpy as np
import re

class BaseCorrection(ABC):
    def __init__(self):
        # OCR初始化（通用印刷/手写体模型）
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang="ch",
            show_log=False,
            det_db_unclip_ratio=2.0,
            det_limit_side_len=1200,
            drop_score=0.4
        )

    # ----------------------【1. 通用配置接口：子类必须实现】----------------------
    @abstractmethod
    def get_allowed_chars(self):
        return {
            "en": "",
            "cn": "",
            "symbols": ""
        }

    @abstractmethod
    def get_standard_terms(self):
        return []

    @abstractmethod
    def get_protocol_type(self):
        return "UNKNOWN"

    # ----------------------【2. 图像预处理】----------------------
    def _preprocess_image(self, img_path):
        img = cv2.imread(img_path)
        if img is None:
            raise ValueError("图片读取失败")

        h, w = img.shape[:2]
        if max(h, w) < 800:
            img = cv2.resize(img, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (1, 1), 0)

        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=19,
            C=3
        )

        kernel = np.ones((1, 1), np.uint8)
        thin_img = cv2.dilate(binary, kernel, iterations=1)

        result = cv2.bitwise_not(thin_img)
        return cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

    # ----------------------【3. 文本智能分析】----------------------
    def analyze_text(self, text):
        text = text.strip()
        allowed = self.get_allowed_chars()
        standards = self.get_standard_terms()
        result = {
            "valid": True,
            "illegal_cn": False,
            "similar_term": None,
            "message": "识别正常"
        }

        cn_chars = re.findall(r"[\u4e00-\u9fa5]", text)
        allowed_cn = allowed.get("cn", "")
        for c in cn_chars:
            if c not in allowed_cn and len(cn_chars) > 0:
                result["valid"] = False
                result["illegal_cn"] = True
                result["message"] = "包含无关中文，可能识别错误"
                return result

        best_match = None
        min_dist = 999
        text_len = len(text)
        if text_len >= 2:
            sorted_terms = sorted(standards, key=lambda x: len(x), reverse=True)
            for term in sorted_terms:
                if text_len >= 6 and len(term) <= 3:
                    continue
                term_len = len(term)
                if abs(term_len - text_len) > 3:
                    continue
                t1 = text.replace('-', '').replace('=', '').upper()
                t2 = term.replace('-', '').replace('=', '').upper()
                dist = abs(len(t1) - len(t2))
                min_len = min(len(t1), len(t2))
                for i in range(min_len):
                    if t1[i] != t2[i]:
                        dist += 1
                if dist < min_dist:
                    min_dist = dist
                    best_match = term
            if best_match and min_dist <= 2:
                result["similar_term"] = best_match
                result["message"] = f"接近标准术语: {best_match}"

        return result

    # ----------------------【4. OCR识别 + 坐标合并】----------------------
    def extract_text_with_coords(self, img_path):
        try:
            processed = self._preprocess_image(img_path)
            ocr_results = self.ocr.ocr(processed, cls=True)
            if not ocr_results or len(ocr_results) == 0:
                return [], processed

            items = []
            for line in ocr_results[0]:
                bbox = line[0]
                text = str(line[1][0]).strip()
                score = float(line[1][1])

                if score < 0.4 or len(text) < 1:
                    continue

                clean_text = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fa5\-=, ]", "", text)
                if len(clean_text) < 1:
                    continue

                x1, y1 = bbox[0]
                x3, y3 = bbox[2]
                cx = round((x1 + x3) / 2, 1)
                cy = round((y1 + y3) / 2, 1)

                analyze = self.analyze_text(clean_text)

                items.append({
                    "text": clean_text,
                    "cx": cx,
                    "cy": cy,
                    "bbox": bbox,
                    "confidence": round(score, 2),
                    "valid": analyze["valid"],
                    "message": analyze["message"],
                    "similar_term": analyze["similar_term"]
                })

            merged = self._merge_items(items)
            for item in merged:
                analyze = self.analyze_text(item["text"])
                item["valid"] = analyze["valid"]
                item["message"] = analyze["message"]
                item["similar_term"] = analyze["similar_term"]
            return merged, processed

        except Exception as e:
            print(f"识别异常: {str(e)}")
            return [], None

    def _merge_items(self, items):
        if len(items) < 2:
            return items

        merged = []
        skip_idx = set()
        n = len(items)

        for i in range(n):
            if i in skip_idx:
                continue

            current = items[i]
            text1 = current["text"]
            cx1 = current["cx"]
            cy1 = current["cy"]
            bbox1 = current["bbox"]

            if text1.endswith("-"):
                for j in range(i + 1, min(i + 3, n)):
                    if j in skip_idx:
                        continue

                    target = items[j]
                    text2 = target["text"]
                    cx2 = target["cx"]
                    bbox2 = target["bbox"]

                    if abs(cx2 - cx1) < 100:
                        new_text = text1 + text2

                        x_min = min(bbox1[0][0], bbox2[0][0])
                        y_min = min(bbox1[0][1], bbox2[0][1])
                        x_max = max(bbox1[2][0], bbox2[2][0])
                        y_max = max(bbox1[2][1], bbox2[2][1])

                        new_bbox = [
                            [x_min, y_min],
                            [x_max, y_min],
                            [x_max, y_max],
                            [x_min, y_max]
                        ]

                        new_cx = (x_min + x_max) / 2
                        new_cy = (y_min + y_max) / 2

                        new_item = current.copy()
                        new_item["text"] = new_text
                        new_item["cx"] = new_cx
                        new_item["cy"] = new_cy
                        new_item["bbox"] = new_bbox

                        merged.append(new_item)

                        skip_idx.add(i)
                        skip_idx.add(j)
                        break
                continue

            merged.append(current)

        return merged

    def load_image(self, img_path, canvas=None):
        # 修复界面图片加载报错
        img = cv2.imread(img_path)
        return img