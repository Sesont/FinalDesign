# -*- coding: utf-8 -*-
"""
计算机网络主观题自动批改系统（毕设最终版）
基于 PaddleOCR 2.7.0 实现图片文字识别，TF-IDF 实现相似度评分
适配 Python 3.9.25 + NumPy 1.26.4 + Windows CPU 环境
"""
from paddleocr import PaddleOCR
import jieba
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os

# ========== 1. 初始化配置（全局参数） ==========
# 初始化 PaddleOCR（关闭日志，避免冗余输出）
ocr = PaddleOCR(
    use_angle_cls=True,  # 开启文字方向检测
    lang='ch',           # 中文识别
    show_log=False       # 关闭调试日志
)

# 定义图片路径（可根据实际情况修改）
STANDARD_IMG_PATH = r"D:\codeforvs\cn_ocr\images/cn_tcphand3.png"  # 标准答案图片
STUDENT_IMG_PATH = r"D:\codeforvs\cn_ocr\images/tcphand1.png" # 学生答案图片

# ========== 2. 核心函数：PaddleOCR 图片转文字 ==========
def img_to_text(img_path):
    """
    功能：使用 PaddleOCR 识别图片中的文字
    参数：img_path - 图片路径（字符串）
    返回：识别后的纯文字（字符串）
    """
    # 检查图片是否存在
    if not os.path.exists(img_path):
        print(f"❌ 错误：图片路径不存在 → {img_path}")
        return ""
    
    try:
        # 执行 OCR 识别（适配 PaddleOCR 2.7.0 格式）
        result = ocr.ocr(img_path, cls=True)
        
        # 提取文字并拼接
        text = ""
        for line in result[0]:
            line_text = line[1][0].strip()  # line[1] = (文字, 置信度)
            if line_text:
                text += line_text + "\n"
        
        final_text = text.strip()
        print(f"✅ 图片识别完成 → {img_path}")
        return final_text
    except Exception as e:
        print(f"❌ 图片识别失败 → {img_path}，异常：{str(e)}")
        return ""

# ========== 3. 核心函数：TF-IDF 相似度评分 ==========
def subjective_score(student_text, standard_text):
    """
    功能：计算学生答案与标准答案的相似度，输出 0-10 分
    参数：
        student_text - 学生答案文字（字符串）
        standard_text - 标准答案文字（字符串）
    返回：
        score - 最终得分（0-10 分，保留1位小数）
        similarity - 相似度百分比（字符串）
    """
    # 文本清洗：去除标点、空格、特殊字符，统一格式
    def clean_text(text):
        # 保留中文、英文、数字，移除所有其他字符
        cleaned_text = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9]", "", text)
        # 英文转小写（避免大小写影响相似度）
        return cleaned_text.lower()
    
    # 清洗文本
    student_clean = clean_text(student_text)
    standard_clean = clean_text(standard_text)
    
    # 空文本处理
    if not student_clean or not standard_clean:
        return 0.0, "文字为空，无法评分"
    
    try:
        # 中文分词（jieba）
        def preprocess(text):
            return " ".join(jieba.cut(text))
        
        # 构建 TF-IDF 特征矩阵
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([
            preprocess(student_clean),
            preprocess(standard_clean)
        ])
        
        # 计算余弦相似度
        similarity = cosine_similarity(tfidf_matrix)[0][1]
        # 转换为 0-10 分制
        score = round(similarity * 10, 1)
        # 相似度百分比
        similarity_str = f"{similarity * 100:.1f}%"
        
        return score, similarity_str
    except Exception as e:
        print(f"❌ 评分失败，异常：{str(e)}")
        return 0.0, "评分异常"

# ========== 4. 主程序：完整批改流程 ==========
def main():
    print("="*80)
    print("📌 计算机网络主观题自动批改系统（毕设演示版）")
    print("="*80)
    
    # Step 1：识别标准答案图片
    print("\n🔍 步骤1：识别标准答案图片...")
    standard_text = img_to_text(STANDARD_IMG_PATH)
    if not standard_text:
        print("❌ 标准答案识别失败，程序退出！")
        return
    print(f"📜 标准答案：\n{standard_text}\n")
    
    # Step 2：识别学生答案图片
    print("🔍 步骤2：识别学生答案图片...")
    student_text = img_to_text(STUDENT_IMG_PATH)
    if not student_text:
        print("❌ 学生答案识别失败，程序退出！")
        return
    print(f"✍️  学生答案：\n{student_text}\n")
    
    # Step 3：自动评分
    print("🔍 步骤3：计算相似度并评分...")
    score, similarity = subjective_score(student_text, standard_text)
    
    # Step 4：输出最终结果
    print("="*80)
    print(f"🎯 【最终批改结果】")
    print(f"📜 标准答案：{standard_text}")
    print(f"✍️  学生答案：{student_text}")
    print(f"📊 相似度：{similarity}")
    print(f"🏆 最终得分：{score}/10 分")
    print("="*80)

# ========== 5. 程序入口 ==========
if __name__ == "__main__":
    main()