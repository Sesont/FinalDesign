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

    def fix_word(self, text):
        t = str(text).upper()
        t = re.sub(r'ACK=L', 'ACK=1', t)
        t = re.sub(r'SYN=L', 'SYN=1', t)
        t = re.sub(r'SEQ=L', 'SEQ=1', t)
        t = re.sub(r'ACK=I', 'ACK=1', t)
        t = re.sub(r'SYN=I', 'SYN=1', t)

        fix_map = {
            "LNAS": "SYN-SENT",
            "-NAS": "SYN-SENT",
            "RCVD": "SYN-RCVD",
            "LLSHED": "ESTABLISHED",
            "SHED": "ESTABLISHED",
            "SEG": "SEQ",
            "XTL": "X+1",
            "YT1": "Y+1",
        }
        for wrong, right in fix_map.items():
            t = t.replace(wrong, right)
        return t

    def extract_text_list(self, ocr_items):
        texts = []
        for item in ocr_items:
            if isinstance(item, dict) and "text" in item:
                texts.append(item["text"])
            else:
                texts.append(str(item))
        return texts

    def get_standard_rules(self):
        return {
            "keywords": {
                "subject": ["客户端", "服务端", "A", "B"],
                "state": ["CLOSED","SYN-SENT","LISTEN","SYN-RCVD","ESTABLISHED"],
                "packet": ["SYN=1", "ACK=1"],
            },
            "core_keywords": ["SYN=1", "ACK=1", "客户端", "服务端", "ESTABLISHED"],
        }

    def match_keywords(self, ocr_items):
        text_list = self.extract_text_list(ocr_items)
        fixed = [self.fix_word(t) for t in text_list]
        all_text = " ".join(fixed).upper()
        rules = self.get_standard_rules()
        
        hit = []
        miss = []
        for kw in rules["core_keywords"]:
            if kw.upper() in all_text:
                hit.append(kw)
            else:
                miss.append(kw)

        score = 0
        if any(s in all_text for s in ["客户端", "客户机", "服务端", "服务器"]):
            score +=1
        state_hit = sum(1 for s in ["CLOSED","SYN-SENT","ESTABLISHED"] if s in all_text)
        if state_hit >=2:
            score +=1
        if "SYN=1" in all_text: score +=1
        if "ACK=1" in all_text: score +=1
        return hit, miss, round(min(score,4),1), text_list, fixed

    def check_structure(self, ocr_items):
        text_list = self.extract_text_list(ocr_items)
        fixed = [self.fix_word(t) for t in text_list]
        all_text = " ".join(fixed).upper()
        score = 0
        log = []
        if "CLOSED" in all_text:
            score +=1
            log.append("✓ 存在CLOSED状态")
        if "SYN-SENT" in all_text:
            score +=1
            log.append("✓ 存在SYN-SENT状态")
        if "SYN-RCVD" in all_text:
            score +=1
            log.append("✓ 存在SYN-RCVD状态")
        if "ESTABLISHED" in all_text:
            score +=1
            log.append("✓ 存在ESTABLISHED状态")
        return {"log": log}, round(min(score,4),1)

    def check_detail(self, ocr_items):
        text_list = self.extract_text_list(ocr_items)
        fixed = [self.fix_word(t) for t in text_list]
        all_text = " ".join(fixed).upper()
        score = 0
        log = []
        if "SYN=1" in all_text:
            score +=0.5
            log.append("✓ SYN=1报文")
        if "ACK=1" in all_text:
            score +=0.5
            log.append("✓ ACK=1报文")
        if "SEQ=X" in all_text or "ACK=X+1" in all_text:
            score +=0.5
            log.append("✓ 序号/确认号格式正确")
        if "数据传输" in all_text:
            score +=0.5
            log.append("✓ 包含数据传输阶段")
        return {"log": log}, round(min(score,2),1)

    def calculate_score(self, kw, st, dt):
        return round(kw + st + dt, 1)

    def correct(self, ocr_items):
        hit, miss, kw, original_text, fixed_text = self.match_keywords(ocr_items)
        st_info, st = self.check_structure(ocr_items)
        dt_info, dt = self.check_detail(ocr_items)
        total = self.calculate_score(kw, st, dt)

        return {
            "score": total,
            "keyword_score": kw,
            "structure_score": st,
            "detail_score": dt,
            "hit_keywords": hit,
            "miss_keywords": miss,
            "original_text": original_text,
            "fixed_text": fixed_text,
            "structure_log": st_info["log"],
            "detail_log": dt_info["log"]
        }