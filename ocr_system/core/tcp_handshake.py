# -*- coding: utf-8 -*-
import re
from .base_correction import BaseCorrection

class TCPHandshakeCorrection(BaseCorrection):
    def __init__(self):
        super().__init__()
        self.question_type = "TCP三次握手"
        self.total_score = 10.0

    def get_allowed_chars(self):
        return {
            "en": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
            "cn": "客户端客户机服务端服务器主动打开被动打开数据传输AB",
            "symbols": "-=, +"
        }

    def get_standard_terms(self):
        return [
            "CLOSED", "LISTEN", "SYN-SENT", "SYN-RCVD", "ESTABLISHED",
            "ACK", "SYN", "主动打开", "被动打开", "数据传输", "客户端", "服务端"
        ]

    def get_protocol_type(self):
        return "TCP_THREE_WAY_HANDSHAKE"

    # ===================== 【真正生效】精准修正 =====================
    def fix_word(self, text):
        t = text.upper()

        # 1. 数字混淆：只在等号后修正 L → 1
        t = re.sub(r'ACK=L', 'ACK=1', t)
        t = re.sub(r'SYN=L', 'SYN=1', t)
        t = re.sub(r'SEQ=L', 'SEQ=1', t)
        t = re.sub(r'ACK=I', 'ACK=1', t)
        t = re.sub(r'SYN=I', 'SYN=1', t)

        # 2. 典型OCR错误（状态词）
        fix_map = {
            "LNAS": "SYN-SENT",
            "-NAS": "SYN-SENT",
            "RCVD": "SYN-RCVD",
            "LLSHED": "ESTABLISHED",
            "SHED": "ESTABLISHED",
            "SEG": "SEQ",
            "XTL": "X+1",
            "YT1": "Y+1",
            "ACK=YT1": "ACK=Y+1",
        }
        for wrong, right in fix_map.items():
            t = t.replace(wrong, right)
        return t

    # ===================== 判分用：修正后的文本 =====================
    def get_fixed_text_list(self, original_coords):
        fixed = []
        for text in original_coords.keys():
            fixed_text = self.fix_word(text)
            fixed.append(fixed_text)
        return fixed

    # ===================== 你的原有规则（完全不变） =====================
    def get_standard_rules(self):
        return {
            "keywords": {
                "subject": ["客户端", "服务端", "A", "B", "客户机", "服务器"],
                "state": ["CLOSED", "SYN-SENT", "LISTEN", "SYN-RCVD", "ESTABLISHED"],
                "packet": ["SYN=1", "ACK=1", "seq=x", "seq=y", "ack=x+1", "ack=y+1"],
                "flow": ["主动打开", "被动打开", "数据传输"]
            },
            "core_keywords": ["SYN=1", "ACK=1", "客户端", "服务端", "ESTABLISHED"],
            "state_order": {
                "client": ["CLOSED", "SYN-SENT", "ESTABLISHED"],
                "server": ["CLOSED", "LISTEN", "SYN-RCVD", "ESTABLISHED"]
            },
            "score_rules": {"keyword":4,"structure":4,"packet_detail":2}
        }

    def match_keywords(self, fixed_list):
        rules = self.get_standard_rules()
        all_text = " ".join(fixed_list).upper()
        hit = []
        miss = []
        for kw in rules["core_keywords"]:
            if kw.upper() in all_text:
                hit.append(kw)
            else:
                miss.append(kw)

        score = 0
        if any(s in all_text for s in ["客户端","客户机","服务端","服务器"]):
            score +=1
        state_hit = sum(1 for s in ["CLOSED","SYN-SENT","LISTEN","SYN-RCVD","ESTABLISHED"] if s in all_text)
        if state_hit >=3: score +=1
        packet_hit = sum(1 for p in ["SYN=1","ACK=1"] if p in all_text)
        if packet_hit >=1: score +=2
        return hit, miss, min(score,4)

    def check_structure(self, fixed_list):
        all_text = " ".join(fixed_list).upper()
        score = 0
        if "CLOSED" in all_text and "SYN-SENT" in all_text: score +=1
        if "LISTEN" in all_text and "SYN-RCVD" in all_text: score +=1
        if "SYN=1" in all_text and "ACK=1" in all_text: score +=2
        return {}, min(score,4)

    def check_detail(self, fixed_list):
        all_text = " ".join(fixed_list).upper()
        score = 0
        if "SYN=1" in all_text: score +=0.5
        if "ACK=1" in all_text: score +=0.5
        if "SEQ=X" in all_text or "ACK=X+1" in all_text: score +=0.5
        if "数据传输" in all_text: score +=0.5
        return {}, min(score,2)

    def calculate_score(self, kw, st, dt):
        return round(kw + st + dt, 1)

    # ===================== 正确返回：原始 + 修正 =====================
    def correct(self, text_coords):
        fixed_list = self.get_fixed_text_list(text_coords)
        hit, miss, kw_score = self.match_keywords(fixed_list)
        st_info, st_score = self.check_structure(fixed_list)
        dt_info, dt_score = self.check_detail(fixed_list)
        total = self.calculate_score(kw_score, st_score, dt_score)

        return {
            "question": self.question_type,
            "full_score": self.total_score,
            "score": total,
            "keyword_score": kw_score,
            "structure_score": st_score,
            "detail_score": dt_score,
            "original_words": list(text_coords.keys()),
            "fixed_for_scoring": fixed_list,
            "hit_keywords": hit,
            "miss_keywords": miss
        }