# -*- coding: utf-8 -*-
"""
交换机与路由器区别校正类
"""
import re
from .base_correction import BaseCorrection

class SwitchRouterCorrection(BaseCorrection):
    def __init__(self):
        super().__init__()
        self.question_type = "交换机vs路由器"
        self.total_score = 10.0

    def get_standard_rules(self):
        return {
            "keywords": {
                "layer": ["数据链路层", "网络层"],
                "address": ["MAC地址", "IP地址"],
                "func": ["局域网转发", "跨网段", "路由选择", "冲突域", "广播域"]
            },
            "score_rules": {"keyword":4,"structure":4,"detail":2}
        }

    def match_keywords(self, text_coords):
        rules = self.get_standard_rules()
        match_result = {"layer":{"hit":[],"miss":[]},"address":{"hit":[],"miss":[]},"func":{"hit":[],"miss":[]}}
        all_text = " ".join(text_coords.keys())
        hit = 0
        for k in ["交换机","路由器","MAC","IP","链路层","网络层"]:
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
        has_switch = "交换机" in all_text
        has_router = "路由器" in all_text
        has_mac = "MAC" in all_text
        has_ip = "IP" in all_text

        full = has_switch and has_router and has_mac and has_ip
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
        if "局域网" in all_text:
            detail_result["packet1"]["pass"]=True
            detail_score+=1
        if "跨网段" in all_text or "路由" in all_text:
            detail_result["packet2"]["pass"]=True
            detail_score+=1
        return detail_result, min(detail_score,2)

    def calculate_score(self, kw_score, struct_score, detail_score):
        return round(kw_score+struct_score+detail_score,1)