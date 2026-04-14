# -*- coding: utf-8 -*-
"""
HTTP与HTTPS区别校正类
"""
import re
from .base_correction import BaseCorrection

class HTTPHTTPSCorrection(BaseCorrection):
    def __init__(self):
        super().__init__()
        self.question_type = "HTTP与HTTPS区别"
        self.total_score = 10.0

    def get_standard_rules(self):
        return {
            "keywords": {
                "diff": ["明文", "加密", "SSL", "TLS", "端口80", "端口443", "安全", "证书"],
                "core": ["HTTP", "HTTPS", "加密", "证书", "安全"]
            },
            "score_rules": {"keyword":4,"structure":4,"detail":2}
        }

    def match_keywords(self, text_coords):
        rules = self.get_standard_rules()
        match_result = {"diff":{"hit":[],"miss":[]},"core":{"hit":[],"miss":[]}}
        all_text = " ".join(text_coords.keys())
        for kw in rules["keywords"]["diff"]:
            if kw in all_text: match_result["diff"]["hit"].append(kw)
            else: match_result["diff"]["miss"].append(kw)
        kw_score = min(len(match_result["diff"]["hit"])*0.8,4)
        return match_result, round(kw_score,1)

    def check_structure(self, text_coords):
        struct_result = {
            "pos":{"pass":True,"reason":""},
            "client_state":{"pass":True,"reason":""},
            "server_state":{"pass":True,"reason":""},
            "order":{"pass":False,"reason":""}
        }
        all_text = " ".join(text_coords.keys())
        has_http = "HTTP" in all_text
        has_https = "HTTPS" in all_text
        has_ssl = "SSL" in all_text or "TLS" in all_text
        has_port = "80" in all_text or "443" in all_text

        full = has_http and has_https and has_ssl and has_port
        struct_result["order"]["pass"] = full
        struct_score = 4 if full else (2 if (has_http and has_https) else 0)
        return struct_result, struct_score

    def check_detail(self, text_coords):
        detail_result = {
            "packet1":{"pass":False,"reason":""},
            "packet2":{"pass":False,"reason":""},
            "packet3":{"pass":False,"reason":""},
            "flow":{"pass":False,"reason":""}
        }
        all_text = " ".join(text_coords.keys())
        detail_score=0
        if "加密" in all_text:
            detail_result["packet1"]["pass"]=True
            detail_score+=1
        if "证书" in all_text:
            detail_result["packet2"]["pass"]=True
            detail_score+=1
        return detail_result, min(detail_score,2)

    def calculate_score(self, kw_score, struct_score, detail_score):
        return round(kw_score+struct_score+detail_score,1)