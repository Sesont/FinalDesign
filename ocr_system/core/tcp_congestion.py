# -*- coding: utf-8 -*-
"""
TCP拥塞控制专属校正逻辑
【与TCP三次握手完全同结构 · 可直接运行】
"""
import re

from .base_correction import BaseCorrection

class TCPCongestionCorrection(BaseCorrection):
    """TCP拥塞控制校正类"""
    def __init__(self):
        super().__init__()
        self.question_type = "TCP拥塞控制"
        self.total_score = 10.0

    # ===================== 规则 =====================
    def get_standard_rules(self):
        return {
            "keywords": {
                "phase": ["慢开始", "拥塞避免", "快重传", "快恢复"],
                "core": ["拥塞窗口", "阈值", "cwnd", "ssthresh"],
                "behavior": ["指数增长", "线性增长", "重传", "恢复"]
            },
            "core_keywords": ["慢开始", "拥塞避免", "快重传", "快恢复", "拥塞窗口", "阈值"],
            "score_rules": {
                "keyword": 4,
                "structure": 4,
                "detail": 2
            }
        }

    # ===================== 关键词匹配 =====================
    def match_keywords(self, text_coords):
        rules = self.get_standard_rules()
        match_result = {
            "phase": {"hit": [], "miss": []},
            "core": {"hit": [], "miss": []},
            "behavior": {"hit": [], "miss": []}
        }
        all_text = " ".join(text_coords.keys())

        # 匹配阶段关键词
        for kw in rules["keywords"]["phase"]:
            if kw in all_text:
                match_result["phase"]["hit"].append(kw)
            else:
                match_result["phase"]["miss"].append(kw)

        # 匹配核心关键词
        for kw in rules["keywords"]["core"]:
            if kw in all_text:
                match_result["core"]["hit"].append(kw)
            else:
                match_result["core"]["miss"].append(kw)

        hit_count = len(match_result["phase"]["hit"]) + len(match_result["core"]["hit"])
        kw_score = min(hit_count * 0.8, 4)
        return match_result, round(kw_score, 1)

    # ===================== 结构校验（含 order，不报错） =====================
    def check_structure(self, text_coords):
        struct_result = {
            "pos": {"pass": True, "reason": "无需位置校验"},
            "client_state": {"pass": True, "reason": "无需状态校验"},
            "server_state": {"pass": True, "reason": "无需状态校验"},
            "order": {"pass": False, "reason": ""}
        }
        all_text = " ".join(text_coords.keys())
        struct_score = 0

        has_slow = "慢开始" in all_text and "拥塞避免" in all_text
        has_fast = "快重传" in all_text and "快恢复" in all_text
        full_pass = has_slow and has_fast

        struct_result["order"]["pass"] = full_pass
        if full_pass:
            struct_score = 4
            struct_result["order"]["reason"] = "核心阶段完整"
        elif has_slow or has_fast:
            struct_score = 2
            struct_result["order"]["reason"] = "部分阶段缺失"
        else:
            struct_score = 0
            struct_result["order"]["reason"] = "阶段严重缺失"

        return struct_result, struct_score

    # ===================== 细节校验 =====================
    def check_detail(self, text_coords):
        detail_result = {
            "packet1": {"pass": False, "reason": ""},
            "packet2": {"pass": False, "reason": ""},
            "packet3": {"pass": False, "reason": ""},
            "flow": {"pass": False, "reason": ""}
        }
        all_text = " ".join(text_coords.keys())
        detail_score = 0

        if "拥塞窗口" in all_text or "cwnd" in all_text:
            detail_result["packet1"]["pass"] = True
            detail_score += 1

        if "阈值" in all_text or "ssthresh" in all_text:
            detail_result["packet2"]["pass"] = True
            detail_score += 1

        return detail_result, min(detail_score, 2)

    # ===================== 计分 =====================
    def calculate_score(self, kw_score, struct_score, detail_score):
        total = kw_score + struct_score + detail_score
        return round(total, 1)