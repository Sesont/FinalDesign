# -*- coding: utf-8 -*-
"""
DNS解析过程校正类
"""
import re
from .base_correction import BaseCorrection

class DNSResolveCorrection(BaseCorrection):
    def __init__(self):
        super().__init__()
        self.question_type = "DNS解析过程"
        self.total_score = 10.0

    def get_standard_rules(self):
        return {
            "keywords": {
                "steps": ["递归查询", "迭代查询", "本地DNS", "根DNS", "顶级域DNS", "权威DNS"],
                "core": ["域名", "IP地址", "缓存", "主机"]
            },
            "score_rules": {"keyword":4,"structure":4,"detail":2}
        }

    def match_keywords(self, text_coords):
        rules = self.get_standard_rules()
        match_result = {"steps":{"hit":[],"miss":[]},"core":{"hit":[],"miss":[]}}
        all_text = " ".join(text_coords.keys())
        for kw in rules["keywords"]["steps"]:
            if kw in all_text: match_result["steps"]["hit"].append(kw)
            else: match_result["steps"]["miss"].append(kw)
        kw_score = min(len(match_result["steps"]["hit"])*0.8,4)
        return match_result, round(kw_score,1)

    def check_structure(self, text_coords):
        struct_result = {
            "pos":{"pass":True,"reason":""},
            "client_state":{"pass":True,"reason":""},
            "server_state":{"pass":True,"reason":""},
            "order":{"pass":False,"reason":""}
        }
        all_text = " ".join(text_coords.keys())
        has_recur = "递归查询" in all_text
        has_iter = "迭代查询" in all_text
        has_dns = "本地DNS" in all_text and "根DNS" in all_text

        if has_recur and has_iter and has_dns:
            struct_result["order"]["pass"]=True
            struct_score=4
        else:
            struct_score=2 if (has_recur or has_iter or has_dns) else 0
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
        if "域名转IP" in all_text or "IP地址" in all_text:
            detail_result["packet1"]["pass"]=True
            detail_score+=1
        if "缓存" in all_text:
            detail_result["packet2"]["pass"]=True
            detail_score+=1
        return detail_result, min(detail_score,2)

    def calculate_score(self, kw_score, struct_score, detail_score):
        return round(kw_score+struct_score+detail_score,1)