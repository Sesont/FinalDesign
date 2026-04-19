# -*- coding: utf-8 -*-
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.base_correction import BaseCorrection

class TestOCR(BaseCorrection):
    # 必须实现的三个通用配置方法
    def get_allowed_chars(self):
        return {
            "en": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
            "cn": "客户端服务器主动打开被动打开数据传输",
            "symbols": "-="
        }

    def get_standard_terms(self):
        return [
            "CLOSED", "LISTEN", "SYN-SENT", "SYN-RCVD", "ESTABLISHED",
            "ACK", "SYN", "FIN", "SEQ"
        ]

    def get_protocol_type(self):
        return "TCP_TEST"

    # 你原本保留的抽象方法
    def get_standard_rules(self): return {}
    def match_keywords(self, text_coords): return {}, 0
    def check_structure(self, text_coords): return {}, 0
    def check_detail(self, text_coords): return {}, 0
    def calculate_score(self, a,b,c): return 0

if __name__ == "__main__":
    print("==============================================")
    print("     测试 base_correction.py OCR 识别结果")
    print("  功能：末尾带 - 自动合并下一行文字")
    print("  输出：文本 + 中心点坐标 + 四点bbox坐标")
    print("==============================================\n")

    img_path = input("请拖入图片：").strip().replace('"', "").replace("'", "")

    if not os.path.exists(img_path):
        print("❌ 文件不存在")
        sys.exit()

    ocr = TestOCR()
    # 新版 base 返回：results, processed_img
    results, processed_img = ocr.extract_text_with_coords(img_path)

    print("\n✅ 最终识别结果（已合并 + 完整坐标）：")
    print("-" * 70)
    
    for idx, item in enumerate(results):
        text = item["text"]
        cx = item["cx"]
        cy = item["cy"]
        bbox = item["bbox"]
        
        print(f"第 {idx+1} 条")
        print(f"  文本：{text}")
        print(f"  中心坐标：X = {cx:.1f}  |  Y = {cy:.1f}")
        print(f"  四点坐标：{bbox}")
        print("-" * 70)

    print("\n✅ 测试完成！")