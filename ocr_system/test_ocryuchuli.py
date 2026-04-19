# -*- coding: utf-8 -*-
import sys
import os
import cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.base_correction import BaseCorrection

class TestOCR(BaseCorrection):
    def get_standard_rules(self): return {}
    def match_keywords(self, text_coords): return {}, 0
    def check_structure(self, text_coords): return {}, 0
    def check_detail(self, text_coords): return {}, 0
    def calculate_score(self, a,b,c): return 0

if __name__ == "__main__":
    print("=" * 60)
    print("        OCR 测试 + 显示预处理后的图片")
    print("=" * 60)

    img_path = input("请拖入图片：").strip().replace('"', "").replace("'", "")
    if not os.path.exists(img_path):
        print("文件不存在")
        sys.exit()

    ocr = TestOCR()

    # 1. 拿到预处理后的图
    processed = ocr._preprocess_image(img_path)

    # 2. 显示图片
    cv2.imshow("预处理后的图片（送给OCR）", processed)

    # 3. OCR 识别 + 合并
    text_coords, all_results = ocr.extract_text_with_coords(img_path)

    # 4. 输出结果
    print("\n识别结果：")
    for i, (text, cx, cy, bbox) in enumerate(all_results, 1):
        print(f"第{i:2d}条 | {text:20} | X={cx:4.0f} Y={cy:4.0f}")

    print("\n按任意键关闭图片退出...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()