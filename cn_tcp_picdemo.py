# -*- coding: utf-8 -*-
"""
TCP三次握手主观题自动批改系统（标准答案驱动版）
核心特性：
1. 从标准答案中动态提取核心关键词/权重（无需硬编码）
2. 保留手动配置兜底（关键术语强制保留）
3. 标准答案语义特征主导评分，学生答案匹配度精准
4. 支持图表/文字混合批改，适配TCP三次握手场景
"""
from paddleocr import PaddleOCR
import jieba
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
from collections import Counter

# ========== 1. 基础配置（仅保留必选手动项） ==========
# PaddleOCR初始化
ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)

# 图片路径（修改为你的实际路径）
STANDARD_IMG_PATH = r"D:\codeforvs\cn_ocr\images/cn_tcphand4.png"  # 标准答案图片
STUDENT_IMG_PATH = r"D:\codeforvs\cn_ocr\images/cn_tcphand3.png" # 学生答案图片

# 手动强制保留的TCP核心术语（兜底，确保关键概念不遗漏）
FORCE_KEYWORDS = {"三次握手", "SYN", "ACK", "seq", "ack", "客户端", "服务端"}

# ========== 2. 核心函数1：图片文字识别 ==========
def img_to_text(img_path):
    """识别图片中的所有文字（支持图表/手写/印刷体）"""
    if not os.path.exists(img_path):
        print(f"❌ 错误：图片路径不存在 → {img_path}")
        return ""
    
    try:
        result = ocr.ocr(img_path, cls=True)
        text = ""
        for line in result[0]:
            line_text = line[1][0].strip()
            if line_text:
                text += line_text + "\n"
        final_text = text.strip()
        print(f"✅ 图片识别完成 → {img_path}")
        return final_text
    except Exception as e:
        print(f"❌ 图片识别失败 → {str(e)}")
        return ""

# ========== 3. 核心函数2：从标准答案动态提取关键词+权重 ==========
def extract_keywords_from_standard(standard_text):
    """
    从标准答案中智能提取关键词及权重：
    1. 清洗文本，拆分中英文/数字
    2. 统计词频，结合TCP术语特征计算权重
    3. 合并手动保留关键词，确保核心概念不丢失
    """
    # 步骤1：文本清洗（保留中文/英文/数字，拆分特殊字符）
    def clean_and_split(text):
        # 替换特殊符号为空格，便于拆分
        cleaned = re.sub(r"[:；，。()（）→=+]", " ", text)
        # 拆分出所有词汇（中英文/数字）
        words = re.findall(r"[a-zA-Z0-9]+|[\u4e00-\u9fa5]+", cleaned)
        # 过滤空字符串和无意义词汇
        stop_words = {"的", "了", "是", "在", "向", "发送", "回复", "进入", "状态"}
        return [word for word in words if word and word not in stop_words]
    
    # 步骤2：拆分标准答案词汇
    standard_words = clean_and_split(standard_text)
    if not standard_words:
        print("⚠️  警告：标准答案无有效词汇可提取")
        return {}, []
    
    # 步骤3：统计词频，计算基础权重
    word_count = Counter(standard_words)
    total_count = sum(word_count.values())
    base_weights = {word: count/total_count for word, count in word_count.items()}
    
    # 步骤4：TCP术语加权（核心术语权重翻倍）
    tcp_core_terms = {"SYN", "ACK", "seq", "ack", "三次握手", "ESTABLISHED", "SYN-SENT", "SYN-RCVD", "LISTEN"}
    keyword_weights = {}
    for word, weight in base_weights.items():
        # 核心TCP术语权重×3，普通术语×1.5，其他×1
        if word in tcp_core_terms or word in FORCE_KEYWORDS:
            keyword_weights[word] = weight * 3
        elif len(word) > 2 or word.isupper():  # 长词汇/大写字母（状态名）
            keyword_weights[word] = weight * 1.5
        else:
            keyword_weights[word] = weight
    
    # 步骤5：合并手动保留关键词（确保不遗漏）
    for force_word in FORCE_KEYWORDS:
        if force_word not in keyword_weights:
            keyword_weights[force_word] = 0.2  # 手动词基础权重
    
    # 步骤6：归一化权重（0-1区间）
    max_weight = max(keyword_weights.values()) if keyword_weights else 1
    normalized_weights = {word: round(weight/max_weight, 2) for word, weight in keyword_weights.items()}
    
    # 提取核心关键词列表（权重≥0.1）
    core_keywords = [word for word, weight in normalized_weights.items() if weight >= 0.1]
    
    print(f"\n📊 从标准答案提取的核心关键词（带权重）：")
    for word, weight in sorted(normalized_weights.items(), key=lambda x: x[1], reverse=True):
        print(f"  {word} → 权重：{weight}")
    
    return normalized_weights, core_keywords

# ========== 4. 核心函数3：关键词匹配评分（标准答案驱动） ==========
def keyword_score_by_standard(student_text, standard_keywords, keyword_weights):
    """
    基于标准答案提取的关键词进行匹配评分（0-6分，占60%）
    """
    # 清洗学生答案文本
    student_clean = re.sub(r"[:；，。()（）→=+]", " ", student_text).upper()
    # 转换关键词为大写（兼容大小写）
    standard_keywords_upper = {word.upper(): weight for word, weight in keyword_weights.items()}
    
    # 计算学生答案匹配的关键词权重总和
    matched_weight = 0.0
    total_standard_weight = sum(keyword_weights.values()) if keyword_weights else 1
    matched_keywords = []
    
    for word, weight in standard_keywords_upper.items():
        if word in student_clean or word.lower() in student_clean:
            matched_weight += weight
            matched_keywords.append(word)
    
    # 输出匹配结果
    print(f"\n✅ 学生答案匹配的关键词：{matched_keywords}")
    print(f"❌ 未匹配的关键词：{[w for w in standard_keywords_upper.keys() if w not in matched_keywords]}")
    
    # 转换为0-6分制
    keyword_score = round((matched_weight / total_standard_weight) * 6, 1)
    print(f"📊 关键词匹配得分：{keyword_score}/6 分（匹配率：{round(matched_weight/total_standard_weight*100, 1)}%）")
    
    return keyword_score

# ========== 5. 核心函数4：语义相似度评分（标准答案特征主导） ==========
def semantic_score_by_standard(student_text, standard_text):
    """
    基于标准答案的TF-IDF特征计算语义相似度（0-4分，占40%）
    """
    # 文本清洗
    def clean_text(text):
        return re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9]", "", text).lower()
    
    student_clean = clean_text(student_text)
    standard_clean = clean_text(standard_text)
    
    if not student_clean or not standard_clean:
        print("📊 语义相似度得分：0/4 分（文本为空）")
        return 0.0
    
    try:
        # 中文分词（基于标准答案的词汇特征）
        def preprocess(text):
            return " ".join(jieba.cut(text))
        
        # 构建TF-IDF矩阵（以标准答案为核心特征）
        vectorizer = TfidfVectorizer()
        # 先拟合标准答案，再转换学生答案（确保特征维度由标准答案决定）
        standard_tfidf = vectorizer.fit_transform([preprocess(standard_clean)])
        student_tfidf = vectorizer.transform([preprocess(student_clean)])
        
        # 计算余弦相似度
        similarity = cosine_similarity(student_tfidf, standard_tfidf)[0][0]
        semantic_score = round(similarity * 4, 1)
        
        print(f"📊 语义相似度得分：{semantic_score}/4 分（相似度：{round(similarity*100, 1)}%）")
        return semantic_score
    except Exception as e:
        print(f"📊 语义相似度得分：0/4 分（异常：{str(e)}）")
        return 0.0

# ========== 6. 综合评分 + 主程序 ==========
def main():
    print("="*80)
    print("📌 TCP三次握手主观题自动批改系统（标准答案驱动版）")
    print("✅ 关键词/评分规则均从标准答案动态提取，保留手动兜底")
    print("="*80)
    
    # Step 1：识别标准答案并提取核心信息
    print("\n🔍 步骤1：识别标准答案图片 + 提取核心特征...")
    standard_text = img_to_text(STANDARD_IMG_PATH)
    if not standard_text:
        print("❌ 标准答案识别失败，程序退出！")
        return
    print(f"📜 标准答案原文：\n{standard_text}")
    
    # 从标准答案提取关键词+权重（核心：标准答案主导）
    keyword_weights, core_keywords = extract_keywords_from_standard(standard_text)
    
    # Step 2：识别学生答案
    print("\n🔍 步骤2：识别学生答案图片...")
    student_text = img_to_text(STUDENT_IMG_PATH)
    if not student_text:
        print("❌ 学生答案识别失败，程序退出！")
        return
    print(f"✍️  学生答案原文：\n{student_text}")
    
    # Step 3：基于标准答案的关键词评分
    print("\n🔍 步骤3：标准答案关键词匹配评分...")
    kw_score = keyword_score_by_standard(student_text, core_keywords, keyword_weights)
    
    # Step 4：基于标准答案的语义相似度评分
    print("\n🔍 步骤4：标准答案语义相似度评分...")
    sem_score = semantic_score_by_standard(student_text, standard_text)
    
    # Step 5：综合评分
    total_score = round(kw_score + sem_score, 1)
    
    # Step 6：输出最终结果（突出标准答案的核心作用）
    print("\n" + "="*80)
    print(f"🎯 【最终批改结果（标准答案驱动）】")
    print(f"📜 标准答案核心特征：")
    print(f"  - 核心关键词：{core_keywords}")
    print(f"  - 关键词权重：{keyword_weights}")
    print(f"✍️  学生答案匹配情况：")
    print(f"  - 关键词得分：{kw_score}/6 分（60%）")
    print(f"  - 语义得分：{sem_score}/4 分（40%）")
    print(f"🏆 综合得分：{total_score}/10 分")
    print("="*80)

if __name__ == "__main__":
    main()