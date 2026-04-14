# -*- coding: utf-8 -*-
"""
子网划分与IP计算校正类
"""
import re
from .base_correction import BaseCorrection

class SubnetCorrection(BaseCorrection):
    def __init__(self):
        super().__init__()
        self.question_type = "子网划分/IP计算"
        self.total_score = 10.0

    def get_standard_rules(self):
        return {
            "keywords": {
                "terms": ["子网掩码", "网段", "主机位", "网络位", "广播地址", "可用IP", "CIDR", "/24"],
                "calc": ["借位", "子网数", "主机数", "划分"]
            },
            "score_rules": {"keyword":4,"structure":4,"detail":2}
        }

    def match_keywords(self, text_coords):
        rules = self.get_standard_rules()
        match_result = {"terms":{"hit":[],"miss":[]},"calc":{"hit":[],"miss":[]}}
        all_text = " ".join(text_coords.keys())
        hit = 0
        for k in ["子网掩码","网段","可用IP","广播","主机数","网络位"]:
            if k in all_text: hit +=1
        kw_score = min(hit*0.8,4)
        return match_result, round(kw_score,1)

    def check_structure(self, text_coords):
        struct_result = {
            "pos":{"pass":True,"reason":""},
            "client_state":{"pass":True,"reason":""},
            "server_state":{"pass":True,"reason":""},
            "order":{"pass":False,"reason":""}
        }
        all_text = " ".join(text_coords.keys())
        has_mask = "子网掩码" in all_text
        has_ip = "IP" in all_text or "网段" in all_text
        has_calc = "主机数" in all_text or "子网数" in all_text

        full = has_mask and has_ip and has_calc
        struct_result["order"]["pass"]=full
        struct_score=4 if full else 2
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
        if "广播地址" in all_text:
            detail_result["packet1"]["pass"]=True
            detail_score+=1
        if "可用主机" in all_text:
            detail_result["packet2"]["pass"]=True
            detail_score+=1
        return detail_result, min(detail_score,2)

    def calculate_score(self, kw_score, struct_score, detail_score):
        return round(kw_score+struct_score+detail_score,1)