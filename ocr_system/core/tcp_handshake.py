# -*- coding: utf-8 -*-
"""
TCP三次握手专属校正逻辑
继承BaseCorrection，实现TCP专属方法
适配新版 base_correction（通用白名单 + 术语库 + 协议类型）
"""
import re
from .base_correction import BaseCorrection

class TCPHandshakeCorrection(BaseCorrection):
    """TCP三次握手校正类"""
    def __init__(self):
        super().__init__()
        self.question_type = "TCP三次握手"
        self.total_score = 10.0

    # ===================== 新版基类必须实现的 3 个通用接口 =====================
    def get_allowed_chars(self):
        """
        【本题型允许出现的合法字符】
        不在里面的中文 → 标记非法
        """
        return {
            "en": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
            "cn": "客户端服务端主动打开被动打开数据传输AB",
            "symbols": "-="
        }

    def get_standard_terms(self):
        """
        【本题型标准术语库】
        用于识别提示：接近某个标准词
        """
        return [
            "CLOSED",
            "LISTEN",
            "SYN-SENT",
            "SYN-RCVD",
            "ESTABLISHED",
            "ACK",
            "SYN",
            "FIN",
            "SEQ",
            "主动打开",
            "被动打开",
            "数据传输",
            "客户端",
            "服务端"
        ]

    def get_protocol_type(self):
        return "TCP三次握手"

    # ===================== 你原来的 TCP 专属规则（完全不动） =====================
    def get_standard_rules(self):
        """TCP三次握手专属规则"""
        return {
            "keywords": {
                "subject": ["客户端", "服务端", "A", "B"],
                "state": ["CLOSED", "SYN-SENT", "LISTEN", "SYN-RCVD", "ESTABLISHED"],
                "packet": ["SYN=1", "ACK=1", "seq=x", "seq=y", "ack=x+1", "ack=y+1"],
                "flow": ["主动打开", "被动打开", "数据传输"]
            },
            "core_keywords": ["SYN=1", "ACK=1", "客户端", "服务端", "ESTABLISHED"],
            "state_order": {
                "client": ["CLOSED", "SYN-SENT", "ESTABLISHED"],
                "server": ["CLOSED", "LISTEN", "SYN-RCVD", "ESTABLISHED"]
            },
            "packet_order": [
                "SYN=1,seq=x",
                "SYN=1,ACK=1,seq=y,ack=x+1",
                "ACK=1,seq=x+1,ack=y+1"
            ],
            "score_rules": {
                "keyword": 4,
                "structure": 4,
                "packet_detail": 2
            }
        }

    # ===================== 你原来的判分逻辑（完全不动） =====================
    def match_keywords(self, text_coords):
        rules = self.get_standard_rules()
        match_result = {
            "subject": {"hit": [], "miss": []},
            "state": {"hit": [], "miss": []},
            "packet": {"hit": [], "miss": []},
            "flow": {"hit": [], "miss": []},
            "core": {"hit": [], "miss": []}
        }
        all_text = " ".join(text_coords.keys()).upper()

        for kw in rules["core_keywords"]:
            if kw in all_text or re.search(kw.replace("=", "\="), all_text):
                match_result["core"]["hit"].append(kw)
            else:
                match_result["core"]["miss"].append(kw)

        for key in ["subject", "state", "packet", "flow"]:
            for kw in rules["keywords"][key]:
                if kw in all_text or re.search(kw.replace("=", "\="), all_text):
                    match_result[key]["hit"].append(kw)
                else:
                    match_result[key]["miss"].append(kw)

        keyword_score = 0
        if len(match_result["subject"]["hit"]) >= 1:
            keyword_score += 1
        if len(match_result["state"]["hit"]) >= 3:
            keyword_score += 1
        packet_hit = len(match_result["packet"]["hit"])
        if packet_hit >= 2:
            keyword_score += 2
        elif packet_hit == 1:
            keyword_score += 1

        return match_result, min(keyword_score, 4)

    def check_structure(self, text_coords):
        rules = self.get_standard_rules()
        struct_result = {
            "pos": {"pass": False, "reason": ""},
            "client_state": {"pass": False, "reason": ""},
            "server_state": {"pass": False, "reason": ""},
            "packet_order": {"pass": False, "reason": ""}
        }
        struct_score = 0

        client_x = [x for text, (x, y, bbox) in text_coords.items() if any(kw in text for kw in ["客户端", "A"])]
        server_x = [x for text, (x, y, bbox) in text_coords.items() if any(kw in text for kw in ["服务端", "B"])]
        if client_x and server_x:
            avg_client_x = sum(client_x) / len(client_x)
            avg_server_x = sum(server_x) / len(server_x)
            if avg_client_x < avg_server_x:
                struct_result["pos"]["pass"] = True
                struct_score += 1
            else:
                struct_result["pos"]["reason"] = "客户端在右，服务端在左"
        else:
            struct_result["pos"]["reason"] = "未识别到客户端/服务端"

        client_states = [(text, y) for text, (x, y, bbox) in text_coords.items() if text in rules["state_order"]["client"]]
        if len(client_states) >= 3:
            sorted_states = sorted(client_states, key=lambda s: s[1])
            sorted_text = [s[0] for s in sorted_states]
            if sorted_text == rules["state_order"]["client"]:
                struct_result["client_state"]["pass"] = True
                struct_score += 1
            else:
                struct_result["client_state"]["reason"] = f"顺序错误：{sorted_text}"
        else:
            struct_result["client_state"]["reason"] = f"状态数不足：{len(client_states)}"

        server_states = [(text, y) for text, (x, y, bbox) in text_coords.items() if text in rules["state_order"]["server"]]
        if len(server_states) >= 4:
            sorted_states = sorted(server_states, key=lambda s: s[1])
            sorted_text = [s[0] for s in sorted_states]
            if sorted_text == rules["state_order"]["server"]:
                struct_result["server_state"]["pass"] = True
                struct_score += 1
            else:
                struct_result["server_state"]["reason"] = f"顺序错误：{sorted_text}"
        else:
            struct_result["server_state"]["reason"] = f"状态数不足：{len(server_states)}"

        packets = [(text, y) for text, (x, y, bbox) in text_coords.items() if any(kw in text for kw in ["SYN=1", "ACK=1", "seq=", "ack="])]
        if len(packets) >= 3:
            sorted_packets = sorted(packets, key=lambda p: p[1])
            if "SYN=1" in sorted_packets[0][0] and "ACK=1" in sorted_packets[-1][0]:
                struct_result["packet_order"]["pass"] = True
                struct_score += 1
            else:
                struct_result["packet_order"]["reason"] = f"顺序错误：{[p[0] for p in sorted_packets]}"
        else:
            struct_result["packet_order"]["reason"] = f"报文数不足：{len(packets)}"

        return struct_result, min(struct_score, 4)

    def check_detail(self, text_coords):
        rules = self.get_standard_rules()
        detail_result = {
            "packet1": {"pass": False, "reason": ""},
            "packet2": {"pass": False, "reason": ""},
            "packet3": {"pass": False, "reason": ""},
            "flow": {"pass": False, "reason": ""}
        }
        detail_score = 0
        all_text = " ".join(text_coords.keys())

        if "SYN=1" in all_text and "seq=x" in all_text:
            detail_result["packet1"]["pass"] = True
            detail_score += 0.5
        else:
            detail_result["packet1"]["reason"] = "缺失SYN=1或seq=x"

        if all(kw in all_text for kw in ["SYN=1", "ACK=1", "ack=x+1"]):
            detail_result["packet2"]["pass"] = True
            detail_score += 0.5
        else:
            detail_result["packet2"]["reason"] = "缺失SYN=1/ACK=1/ack=x+1"

        if "ACK=1" in all_text and "ack=y+1" in all_text:
            detail_result["packet3"]["pass"] = True
            detail_score += 0.5
        else:
            detail_result["packet3"]["reason"] = "缺失ACK=1或ack=y+1"

        if any(kw in all_text for kw in ["数据传输", "数据通信"]):
            detail_result["flow"]["pass"] = True
            detail_score += 0.5
        else:
            detail_result["flow"]["reason"] = "未识别到数据传输"

        return detail_result, min(detail_score, 2)

    def calculate_score(self, kw_score, struct_score, detail_score):
        total = kw_score + struct_score + detail_score
        return round(total, 1)