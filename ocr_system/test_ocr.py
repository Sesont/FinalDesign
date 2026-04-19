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
    print("  输出：文本 + 中心点坐标 + 四点bbox坐标")
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

    print("\n✅ 最终识别结果（已合并 + 完整坐标）：")
    print("-" * 70)
    for idx, item in enumerate(all_results):
        text = item[0]
        cx = item[1]
        cy = item[2]
        bbox = item[3]
        
        print(f"第 {idx+1} 条")
        print(f"  文本：{text}")
        print(f"  中心坐标：X = {cx:.1f}  |  Y = {cy:.1f}")
        print(f"  四点坐标：{bbox}")
        print("-" * 70)

    print("\n✅ 测试完成！")