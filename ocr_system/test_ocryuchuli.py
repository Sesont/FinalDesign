# -*- coding: utf-8 -*-
import sys
import os
import cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.base_correction import BaseCorrection

class TestOCR(BaseCorrection):
    # 实现基类的三个通用配置方法
    def get_allowed_chars(self):
        return {
            "en": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            "cn": "客户端服务器主动打开被动打开数据传输",
            "symbols": "-="
        }

    def get_standard_terms(self):
        return [
            "CLOSED", "LISTEN", "SYN-SENT", "SYN-RCVD", "ESTABLISHED",
            "ACK", "SYN", "FIN", "SEQ", "数据传输"
        ]

    def get_protocol_type(self):
        return "TCP_TEST"

    # 你原来的抽象方法保留
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
    
    #测试base_correction
    #ocr = TestOCR()

    #测试tcp三次握手
    from core.tcp_handshake import TCPHandshakeCorrection
    ocr = TCPHandshakeCorrection()


    # 识别
    results, processed = ocr.extract_text_with_coords(img_path)

    # 显示预处理图
    if processed is not None:
        cv2.imshow("预处理后的图片（送给OCR）", processed)

    # 输出新版识别结果（带提示）
    print("\n识别结果：")
    for i, item in enumerate(results, 1):
        text = item["text"]
        cx = item["cx"]
        cy = item["cy"]
        msg = item["message"]
        print(f"第{i:2d}条 | {text:20} | X={cx:4.0f} Y={cy:4.0f} | {msg}")

    print("\n按任意键关闭图片退出...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()