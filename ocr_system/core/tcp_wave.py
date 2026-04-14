# -*- coding: utf-8 -*-
"""
TCP四次挥手专属校正逻辑（与三次握手100%同结构，含order键，解决KeyError）
"""
import re

from .base_correction import BaseCorrection

class TCPWaveCorrection(BaseCorrection):
    """TCP四次挥手校正类"""
    def __init__(self):
        super().__init__()
        self.question_type = "TCP四次挥手"
        self.total_score = 10.0

    def get_standard_rules(self):
        """TCP四次挥手专属规则"""
        return {
            "keywords": {
                "subject": ["客户端", "服务端", "A", "B"],
                "state": ["CLOSED", "FIN_WAIT", "TIME_WAIT", "CLOSE_WAIT", "LAST_ACK", "ESTABLISHED"],
                "packet": ["FIN=1", "ACK=1", "seq=x", "seq=y", "ack=x+1", "ack=y+1"],
                "flow": ["主动关闭", "被动关闭", "连接释放"]
            },
            "core_keywords": ["FIN=1", "ACK=1", "客户端", "服务端", "TIME_WAIT"],
            "state_order": {
                "client": ["ESTABLISHED", "FIN_WAIT", "TIME_WAIT", "CLOSED"],
                "server": ["ESTABLISHED", "CLOSE_WAIT", "LAST_ACK", "CLOSED"]
            },
            "packet_order": [
                "FIN=1,seq=x",
                "ACK=1,ack=x+1",
                "FIN=1,seq=y",
                "ACK=1,ack=y+1"
            ],
            "score_rules": {
                "keyword": 4,
                "structure": 4,
                "packet_detail": 2
            }
        }

    def match_keywords(self, text_coords):
        """TCP四次挥手关键词匹配（4分）"""
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
        """TCP四次挥手结构校验（4分，保留order键，解决KeyError）"""
        rules = self.get_standard_rules()
        struct_result = {
            "pos": {"pass": False, "reason": ""},
            "client_state": {"pass": False, "reason": ""},
            "server_state": {"pass": False, "reason": ""},
            "order": {"pass": False, "reason": ""}
        }
        struct_score = 0

        # 1. 客户端/服务端位置
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

        # 2. 客户端状态顺序
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

        # 3. 服务端状态顺序
        server_states = [(text, y) for text, (x, y, bbox) in text_coords.items() if text in rules["state_order"]["server"]]
        if len(server_states) >= 3:
            sorted_states = sorted(server_states, key=lambda s: s[1])
            sorted_text = [s[0] for s in sorted_states]
            if sorted_text == rules["state_order"]["server"]:
                struct_result["server_state"]["pass"] = True
                struct_score += 1
            else:
                struct_result["server_state"]["reason"] = f"顺序错误：{sorted_text}"
        else:
            struct_result["server_state"]["reason"] = f"状态数不足：{len(server_states)}"

        # 4. 报文顺序（对应order键，与三次握手结构完全一致）
        packets = [(text, y) for text, (x, y, bbox) in text_coords.items() if any(kw in text for kw in ["FIN=1", "ACK=1", "seq=", "ack="])]
        if len(packets) >= 4:
            sorted_packets = sorted(packets, key=lambda p: p[1])
            if "FIN=1" in sorted_packets[0][0] and "ACK=1" in sorted_packets[-1][0]:
                struct_result["order"]["pass"] = True
                struct_score += 1
            else:
                struct_result["order"]["reason"] = f"顺序错误：{[p[0] for p in sorted_packets]}"
        else:
            struct_result["order"]["reason"] = f"报文数不足：{len(packets)}"

        return struct_result, min(struct_score, 4)

    def check_detail(self, text_coords):
        """TCP四次挥手细节校验（2分）"""
        rules = self.get_standard_rules()
        detail_result = {
            "packet1": {"pass": False, "reason": ""},
            "packet2": {"pass": False, "reason": ""},
            "packet3": {"pass": False, "reason": ""},
            "flow": {"pass": False, "reason": ""}
        }
        detail_score = 0
        all_text = " ".join(text_coords.keys())

        if "FIN=1" in all_text and "seq=x" in all_text:
            detail_result["packet1"]["pass"] = True
            detail_score += 0.5
        if "ACK=1" in all_text and "ack=x+1" in all_text:
            detail_result["packet2"]["pass"] = True
            detail_score += 0.5
        if "FIN=1" in all_text and "seq=y" in all_text:
            detail_result["packet3"]["pass"] = True
            detail_score += 0.5
        if "关闭" in all_text or "连接释放" in all_text:
            detail_result["flow"]["pass"] = True
            detail_score += 0.5

        return detail_result, min(detail_score, 2)

    def calculate_score(self, kw_score, struct_score, detail_score):
        """TCP四次挥手评分计算"""
        total = kw_score + struct_score + detail_score
        return round(total, 1)