# -*- coding: utf-8 -*-
import sys
import os
import cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("=" * 60)
    print("        TCP 三次握手 手写智能批改系统")
    print("=" * 60)

    img_path = input("请拖入图片：").strip().replace('"', "").replace("'", "")
    if not os.path.exists(img_path):
        print("文件不存在")
        sys.exit()

    from core.tcp_handshake import TCPHandshakeCorrection
    ocr = TCPHandshakeCorrection()

    results, processed = ocr.extract_text_with_coords(img_path)

    # ===================== 【自动缩放图片】 =====================
    if processed is not None:
        h, w = processed.shape[:2]
        max_h = 720   # 你可以改：800 / 900 / 1080
        scale = max_h / h
        new_w = int(w * scale)
        new_h = int(h * scale)
        resized = cv2.resize(processed, (new_w, new_h))
        cv2.imshow("预处理后的图片", resized)

    # ===================== 原始识别结果 =====================
    print("\n【原始识别结果】")
    for i, item in enumerate(results, 1):
        text = item["text"]
        cx = item["cx"]
        cy = item["cy"]
        msg = item["message"]
        print(f"第{i:2d}条 | {text:20} | X={cx:4.0f} Y={cy:4.0f} | {msg}")

    text_coords = {item["text"]: (item["cx"], item["cy"], item["bbox"]) for item in results}
    report = ocr.correct(text_coords)

    # ===================== 最终输出 =====================
    print("\n" + "="*70)
    print(f"📝 题目：{report['question']}")
    print(f"🔍 原始识别词汇：{report['original_words']}")
    print(f"✅ 判分修正词汇：{report['fixed_for_scoring']}")
    print(f"🎯 命中关键词：{report['hit_keywords']}")
    print(f"❌ 遗漏关键词：{report['miss_keywords']}")
    print("-"*70)
    print(f"🔸 关键词得分：{report['keyword_score']}/4")
    print(f"🔸 结构得分：{report['structure_score']}/4")
    print(f"🔸 细节得分：{report['detail_score']}/2")
    print(f"🏆 最终总分：{report['score']} / {report['full_score']}")
    print("="*70)

    print("\n按任意键关闭窗口退出...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()