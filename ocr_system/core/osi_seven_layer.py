# -*- coding: utf-8 -*-
"""
OSI七层模型专属校正逻辑
继承BaseCorrection，实现OSI题型的专属方法
"""
import re
from .base_correction import BaseCorrection

class OSISevenLayerCorrection(BaseCorrection):
    """OSI七层模型校正类"""
    def __init__(self):
        super().__init__()
        # 重写题型名称
        self.question_type = "OSI七层模型"
        # 重写总分（可自定义）
        self.total_score = 10.0

    # ===================== OSI专属规则 =====================
    def get_standard_rules(self):
        """获取OSI七层模型专属规则"""
        return {
            "keywords": {
                # 七层名称（中文+英文）
                "layers": [
                    "物理层", "Physical Layer",
                    "数据链路层", "Data Link Layer",
                    "网络层", "Network Layer",
                    "传输层", "Transport Layer",
                    "会话层", "Session Layer",
                    "表示层", "Presentation Layer",
                    "应用层", "Application Layer"
                ],
                # 每层核心功能关键词
                "functions": [
                    "比特流", "物理介质", "网卡", "双绞线",  # 物理层
                    "帧", "MAC地址", "交换机", "差错检测",    # 数据链路层
                    "分组", "IP地址", "路由器", "路由选择",    # 网络层
                    "段", "端口号", "TCP", "UDP",             # 传输层
                    "会话建立", "会话管理", "同步",            # 会话层
                    "数据加密", "格式转换", "解压缩",          # 表示层
                    "应用程序", "HTTP", "FTP", "DNS"          # 应用层
                ],
                # 层序关键词
                "order": ["从上到下", "从下到上", "第一层", "第七层"]
            },
            # 核心关键词（必须识别的）
            "core_keywords": ["物理层", "数据链路层", "网络层", "传输层", "会话层", "表示层", "应用层"],
            # 七层顺序规则（从下到上）
            "layer_order": [
                "物理层", 
                "数据链路层", 
                "网络层", 
                "传输层", 
                "会话层", 
                "表示层", 
                "应用层"
            ],
            "score_rules": {
                "keyword": 5,   # 关键词完整性（5分）
                "structure": 3, # 层序正确性（3分）
                "detail": 2     # 功能匹配度（2分）
            }
        }

    # ===================== OSI专属校验 =====================
    def match_keywords(self, text_coords):
        """OSI关键词匹配（5分）"""
        rules = self.get_standard_rules()
        match_result = {
            "layers": {"hit": [], "miss": []},      # 七层名称
            "functions": {"hit": [], "miss": []},   # 核心功能
            "core": {"hit": [], "miss": []}         # 核心关键词
        }
        all_text = " ".join(text_coords.keys()).upper()

        # 核心关键词匹配（七层名称）
        for kw in rules["core_keywords"]:
            if kw in all_text or re.search(kw, all_text):
                match_result["core"]["hit"].append(kw)
            else:
                match_result["core"]["miss"].append(kw)

        # 分层关键词匹配
        # 1. 七层名称匹配
        for kw in rules["keywords"]["layers"]:
            if kw.upper() in all_text or re.search(kw, all_text, re.IGNORECASE):
                match_result["layers"]["hit"].append(kw)
            else:
                match_result["layers"]["miss"].append(kw)
        
        # 2. 功能关键词匹配
        for kw in rules["keywords"]["functions"]:
            if kw in all_text or re.search(kw, all_text):
                match_result["functions"]["hit"].append(kw)
            else:
                match_result["functions"]["miss"].append(kw)

        # 计算关键词得分（0-5分）
        keyword_score = 0
        # 每识别1层名称得0.5分（满分3.5分）
        layer_hit_count = len([k for k in match_result["layers"]["hit"] if k in rules["core_keywords"]])
        keyword_score += min(layer_hit_count * 0.5, 3.5)
        # 每识别2个功能关键词得0.5分（满分1.5分）
        func_hit_count = len(match_result["functions"]["hit"])
        keyword_score += min(func_hit_count // 2 * 0.5, 1.5)

        return match_result, round(keyword_score, 1)

    def check_structure(self, text_coords):
        """OSI层序校验（3分）"""
        rules = self.get_standard_rules()
        struct_result = {
            "order": {"pass": False, "reason": ""},    # 层序正确性
            "direction": {"pass": False, "reason": ""} # 顺序方向（从下到上/从上到下）
        }
        struct_score = 0

        # 1. 提取所有七层名称的坐标（y坐标决定上下顺序）
        layer_coords = {}
        for text, (x, y, bbox) in text_coords.items():
            if text in rules["core_keywords"]:
                layer_coords[text] = y

        # 2. 校验层序（至少识别4层才校验）
        if len(layer_coords) >= 4:
            # 按y坐标排序（y越小越靠上）
            sorted_layers = sorted(layer_coords.items(), key=lambda x: x[1])
            sorted_layer_names = [layer[0] for layer in sorted_layers]
            
            # 验证是否符合「从下到上=物理层→应用层」或「从上到下=应用层→物理层」
            # 方式1：从下到上（物理层在最下，y最大）
            is_bottom_up = all([
                sorted_layer_names[i] == rules["layer_order"][i] 
                for i in range(len(sorted_layer_names))
            ])
            # 方式2：从上到下（应用层在最上，y最小）
            is_top_down = all([
                sorted_layer_names[i] == rules["layer_order"][::-1][i] 
                for i in range(len(sorted_layer_names))
            ])

            if is_bottom_up or is_top_down:
                struct_result["order"]["pass"] = True
                struct_score += 2  # 层序正确得2分
                struct_result["order"]["reason"] = f"顺序正确：{sorted_layer_names}"
            else:
                struct_result["order"]["reason"] = f"顺序错误，正确应为：{rules['layer_order']}（从下到上）"
            
            # 3. 校验顺序方向描述
            all_text = " ".join(text_coords.keys())
            if "从下到上" in all_text or "从上到下" in all_text:
                struct_result["direction"]["pass"] = True
                struct_score += 1  # 方向描述正确得1分
                struct_result["direction"]["reason"] = "包含顺序方向描述（从下到上/从上到下）"
            else:
                struct_result["direction"]["reason"] = "未识别到顺序方向描述"
        else:
            struct_result["order"]["reason"] = f"识别到的层数不足：{len(layer_coords)}层（需至少4层）"
            struct_result["direction"]["reason"] = "层数不足，无法校验方向"

        return struct_result, min(struct_score, 3)

    def check_detail(self, text_coords):
        """OSI功能细节校验（2分）"""
        rules = self.get_standard_rules()
        detail_result = {
            "physical": {"pass": False, "reason": ""},    # 物理层功能
            "data_link": {"pass": False, "reason": ""},   # 数据链路层功能
            "network": {"pass": False, "reason": ""},     # 网络层功能
            "transport": {"pass": False, "reason": ""}    # 传输层功能
        }
        detail_score = 0
        all_text = " ".join(text_coords.keys())

        # 1. 物理层功能（0.5分）
        if any(kw in all_text for kw in ["比特流", "物理介质", "网卡", "双绞线"]):
            detail_result["physical"]["pass"] = True
            detail_score += 0.5
        else:
            detail_result["physical"]["reason"] = "未识别到物理层核心功能（比特流/物理介质等）"

        # 2. 数据链路层功能（0.5分）
        if any(kw in all_text for kw in ["帧", "MAC地址", "交换机", "差错检测"]):
            detail_result["data_link"]["pass"] = True
            detail_score += 0.5
        else:
            detail_result["data_link"]["reason"] = "未识别到数据链路层核心功能（帧/MAC地址等）"

        # 3. 网络层功能（0.5分）
        if any(kw in all_text for kw in ["分组", "IP地址", "路由器", "路由选择"]):
            detail_result["network"]["pass"] = True
            detail_score += 0.5
        else:
            detail_result["network"]["reason"] = "未识别到网络层核心功能（IP地址/路由器等）"

        # 4. 传输层功能（0.5分）
        if any(kw in all_text for kw in ["段", "端口号", "TCP", "UDP"]):
            detail_result["transport"]["pass"] = True
            detail_score += 0.5
        else:
            detail_result["transport"]["reason"] = "未识别到传输层核心功能（TCP/UDP/端口号等）"

        return detail_result, min(detail_score, 2)

    def calculate_score(self, kw_score, struct_score, detail_score):
        """OSI评分计算（总分=关键词+结构+细节）"""
        total = kw_score + struct_score + detail_score
        return round(total, 1)