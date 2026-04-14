# -*- coding: utf-8 -*-
import sys
import os

# 自动加入项目根路径，解决导入错误
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.base_correction import BaseCorrection

# 创建测试类（必须实现抽象方法才能运行）
class TestOCR(BaseCorrection):
    def get_standard_rules(self):
        return {}
    def match_keywords(self, text_coords):
        return {}, 0
    def check_structure(self, text_coords):
        return {}, 0
    def check_detail(self, text_coords):
        return {}, 0
    def calculate_score(self, kw, st, dt):
        return 0

if __name__ == "__main__":
    print("==============================================")
    print("     测试 base_correction.py OCR 识别结果")
    print("  功能：末尾带 - 自动合并下一行文字")
    print("==============================================\n")

    # 输入图片路径
    img_path = input("请拖入图片：").strip().replace('"', "").replace("'", "")

    if not os.path.exists(img_path):
        print("❌ 文件不存在")
        sys.exit()

    # 初始化
    ocr = TestOCR()

    # 调用你真实的 OCR 函数
    text_coords, all_results = ocr.extract_text_with_coords(img_path)

    print("\n✅ 最终识别结果（已合并）：")
    for item in all_results:
        text = item[0]
        print(f"→ {text}")

    print("\n✅ 测试完成！")