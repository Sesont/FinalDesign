# -*- coding: utf-8 -*-
"""
TCP三次握手辅助批改系统（适配标准时序图）
核心：关键词+结构+报文细节校验 + 自动评分建议
"""
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from paddleocr import PaddleOCR
from PIL import Image, ImageTk
import math
import re

# ===================== 1. 标准规则定义（适配提供的标准答案图） =====================
STANDARD_RULES = {
    # 关键词库（按类别）
    "keywords": {
        "subject": ["客户端", "服务端", "A", "B"],       # 主体
        "state": ["CLOSED", "SYN-SENT", "LISTEN", "SYN-RCVD", "ESTABLISHED"],  # 状态
        "packet": ["SYN=1", "ACK=1", "seq=x", "seq=y", "ack=x+1", "ack=y+1"],  # 报文
        "flow": ["主动打开", "被动打开", "数据传输"]       # 流程
    },
    # 核心关键词（权重最高）
    "core_keywords": ["SYN=1", "ACK=1", "客户端", "服务端", "ESTABLISHED"],
    # 状态顺序规则（从上到下）
    "state_order": {
        "client": ["CLOSED", "SYN-SENT", "ESTABLISHED"],
        "server": ["CLOSED", "LISTEN", "SYN-RCVD", "ESTABLISHED"]
    },
    # 报文交互顺序（从上到下）
    "packet_order": [
        "SYN=1,seq=x",          # 第一次握手
        "SYN=1,ACK=1,seq=y,ack=x+1",  # 第二次握手
        "ACK=1,seq=x+1,ack=y+1" # 第三次握手
    ],
    # 评分标准（10分制）
    "score_rules": {
        "keyword": 4,   # 关键词完整性
        "structure": 4, # 结构正确性
        "packet_detail": 2 # 报文细节正确性
    }
}

# ===================== 2. 初始化核心组件 =====================
# PaddleOCR（开启角度分类，支持倾斜/竖排文字）
ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)

# ===================== 3. 核心工具函数 =====================
def extract_text_with_coords(img_path):
    """
    识别图片文字+坐标，兼容符号/斜体/竖排
    返回：dict{文本: (中心x, 中心y, 原始bbox)}, list[所有识别结果]
    """
    try:
        result = ocr.ocr(img_path, cls=True)[0]
        text_coords = {}
        all_results = []
        for line in result:
            bbox = line[0]
            text = line[1][0].strip()
            score = line[1][1]
            # 计算中心坐标
            center_x = (bbox[0][0] + bbox[2][0]) / 2
            center_y = (bbox[0][1] + bbox[2][1]) / 2
            text_coords[text] = (center_x, center_y, bbox)
            all_results.append((text, center_x, center_y, score))
        return text_coords, all_results
    except Exception as e:
        messagebox.showerror("错误", f"OCR识别失败：{str(e)}")
        return {}, []

def match_keywords(text_coords):
    """
    关键词匹配：统计各类关键词的命中数
    返回：匹配结果dict，关键词得分（0-4分）
    """
    match_result = {
        "subject": {"hit": [], "miss": []},    # 主体
        "state": {"hit": [], "miss": []},      # 状态
        "packet": {"hit": [], "miss": []},     # 报文
        "flow": {"hit": [], "miss": []},       # 流程
        "core": {"hit": [], "miss": []}        # 核心关键词
    }
    # 扁平化所有识别文本（便于模糊匹配）
    all_text = " ".join(text_coords.keys()).upper()
    
    # 1. 匹配核心关键词
    for kw in STANDARD_RULES["core_keywords"]:
        if kw in all_text or re.search(kw.replace("=", "\="), all_text):
            match_result["core"]["hit"].append(kw)
        else:
            match_result["core"]["miss"].append(kw)
    
    # 2. 匹配各类关键词
    for key in ["subject", "state", "packet", "flow"]:
        for kw in STANDARD_RULES["keywords"][key]:
            if kw in all_text or re.search(kw.replace("=", "\="), all_text):
                match_result[key]["hit"].append(kw)
            else:
                match_result[key]["miss"].append(kw)
    
    # 计算关键词得分（满分4分）
    keyword_score = 0
    # 主体关键词（1分）
    if len(match_result["subject"]["hit"]) >= 1:
        keyword_score += 1
    # 状态关键词（1分）
    if len(match_result["state"]["hit"]) >= 3:
        keyword_score += 1
    # 报文关键词（2分）
    packet_hit = len(match_result["packet"]["hit"])
    if packet_hit >= 2:
        keyword_score += 2
    elif packet_hit == 1:
        keyword_score += 1
    
    return match_result, min(keyword_score, 4)

def check_structure(text_coords):
    """
    结构校验：左右位置+状态顺序+报文顺序
    返回：结构结果dict，结构得分（0-4分）
    """
    struct_result = {
        "pos": {"pass": False, "reason": ""},       # 客户端/服务端位置
        "client_state": {"pass": False, "reason": ""}, # 客户端状态顺序
        "server_state": {"pass": False, "reason": ""}, # 服务端状态顺序
        "packet_order": {"pass": False, "reason": ""}  # 报文顺序
    }
    struct_score = 0
    
    # 1. 校验客户端/服务端左右位置（1分）
    client_x = []
    server_x = []
    for text, (x, y, bbox) in text_coords.items():
        if any(kw in text for kw in ["客户端", "A"]):
            client_x.append(x)
        elif any(kw in text for kw in ["服务端", "B"]):
            server_x.append(x)
    if client_x and server_x:
        avg_client_x = sum(client_x) / len(client_x)
        avg_server_x = sum(server_x) / len(server_x)
        if avg_client_x < avg_server_x:
            struct_result["pos"]["pass"] = True
            struct_score += 1
        else:
            struct_result["pos"]["reason"] = "客户端在右，服务端在左（位置颠倒）"
    else:
        struct_result["pos"]["reason"] = "未识别到客户端/服务端"
    
    # 2. 校验客户端状态顺序（1分）
    client_states = []
    for text, (x, y, bbox) in text_coords.items():
        if text in STANDARD_RULES["state_order"]["client"]:
            client_states.append((text, y))
    if len(client_states) >= 3:
        # 按y坐标排序（从上到下）
        client_states_sorted = sorted(client_states, key=lambda s: s[1])
        sorted_text = [s[0] for s in client_states_sorted]
        if sorted_text == STANDARD_RULES["state_order"]["client"]:
            struct_result["client_state"]["pass"] = True
            struct_score += 1
        else:
            struct_result["client_state"]["reason"] = f"顺序错误：{sorted_text}"
    else:
        struct_result["client_state"]["reason"] = f"识别到状态数不足：{len(client_states)}"
    
    # 3. 校验服务端状态顺序（1分）
    server_states = []
    for text, (x, y, bbox) in text_coords.items():
        if text in STANDARD_RULES["state_order"]["server"]:
            server_states.append((text, y))
    if len(server_states) >= 4:
        server_states_sorted = sorted(server_states, key=lambda s: s[1])
        sorted_text = [s[0] for s in server_states_sorted]
        if sorted_text == STANDARD_RULES["state_order"]["server"]:
            struct_result["server_state"]["pass"] = True
            struct_score += 1
        else:
            struct_result["server_state"]["reason"] = f"顺序错误：{sorted_text}"
    else:
        struct_result["server_state"]["reason"] = f"识别到状态数不足：{len(server_states)}"
    
    # 4. 校验报文顺序（1分）
    packets = []
    for text, (x, y, bbox) in text_coords.items():
        if any(kw in text for kw in ["SYN=1", "ACK=1", "seq=", "ack="]):
            packets.append((text, y))
    if len(packets) >= 3:
        packets_sorted = sorted(packets, key=lambda p: p[1])
        # 简化校验：只要包含SYN=1的报文在最上，ACK=1在最下
        first_packet = packets_sorted[0][0]
        last_packet = packets_sorted[-1][0]
        if "SYN=1" in first_packet and "ACK=1" in last_packet:
            struct_result["packet_order"]["pass"] = True
            struct_score += 1
        else:
            struct_result["packet_order"]["reason"] = f"报文顺序错误：{[p[0] for p in packets_sorted]}"
    else:
        struct_result["packet_order"]["reason"] = f"识别到报文数不足：{len(packets)}"
    
    return struct_result, min(struct_score, 4)

def check_packet_detail(text_coords):
    """
    报文细节校验（满分2分）
    返回：细节结果dict，细节得分（0-2分）
    """
    detail_result = {
        "packet1": {"pass": False, "reason": ""},  # 第一次握手
        "packet2": {"pass": False, "reason": ""},  # 第二次握手
        "packet3": {"pass": False, "reason": ""},  # 第三次握手
        "flow": {"pass": False, "reason": ""}      # 数据传输
    }
    detail_score = 0
    all_text = " ".join(text_coords.keys())
    
    # 1. 第一次握手（0.5分）：SYN=1 + seq=x
    if "SYN=1" in all_text and "seq=x" in all_text:
        detail_result["packet1"]["pass"] = True
        detail_score += 0.5
    else:
        detail_result["packet1"]["reason"] = "缺失SYN=1或seq=x"
    
    # 2. 第二次握手（0.5分）：SYN=1 + ACK=1 + ack=x+1
    if all(kw in all_text for kw in ["SYN=1", "ACK=1", "ack=x+1"]):
        detail_result["packet2"]["pass"] = True
        detail_score += 0.5
    else:
        detail_result["packet2"]["reason"] = "缺失SYN=1/ACK=1/ack=x+1"
    
    # 3. 第三次握手（0.5分）：ACK=1 + ack=y+1
    if "ACK=1" in all_text and "ack=y+1" in all_text:
        detail_result["packet3"]["pass"] = True
        detail_score += 0.5
    else:
        detail_result["packet3"]["reason"] = "缺失ACK=1或ack=y+1"
    
    # 4. 数据传输（0.5分）
    if any(kw in all_text for kw in ["数据传输", "数据通信"]):
        detail_result["flow"]["pass"] = True
        detail_score += 0.5
    else:
        detail_result["flow"]["reason"] = "未识别到数据传输"
    
    return detail_result, min(detail_score, 2)

def load_image(img_path, canvas):
    """加载图片到Canvas，支持缩放"""
    try:
        img = Image.open(img_path)
        canvas_w = canvas.winfo_width() or 600
        canvas_h = canvas.winfo_height() or 800
        img.thumbnail((canvas_w, canvas_h), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(img)
        canvas.delete("all")
        canvas.create_image(canvas_w/2, canvas_h/2, image=tk_img)
        canvas.img = tk_img
        return True
    except Exception as e:
        messagebox.showerror("错误", f"图片加载失败：{str(e)}")
        return False

# ===================== 4. 界面设计 =====================
class TCPHandshakeCorrection:
    def __init__(self, root):
        self.root = root
        self.root.title("TCP三次握手辅助批改系统（标准图适配版）")
        self.root.geometry("1200x800")

        # 变量定义
        self.img_path = tk.StringVar()
        self.total_score_var = tk.StringVar(value="10.0")  # 自动评分建议
        self.match_result = None
        self.struct_result = None
        self.detail_result = None

        # 主布局：左右分栏
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=BOTH, expand=YES, padx=10, pady=10)

        # ---------------- 左侧：图片展示区 ----------------
        left_frame = ttk.Frame(main_frame, bootstyle=PRIMARY)
        left_frame.pack(side=LEFT, fill=BOTH, expand=YES, padx=5, pady=5)
        ttk.Label(left_frame, text="标准答案/学生答案图片", font=("微软雅黑", 12, "bold"), bootstyle=PRIMARY).pack(side=TOP, fill=X, padx=5, pady=3)
        
        self.img_canvas = tk.Canvas(left_frame, bg="white", bd=1, relief=tk.SOLID)
        self.img_canvas.pack(fill=BOTH, expand=YES, padx=5, pady=5)

        # 按钮区
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=X, padx=5, pady=5)
        ttk.Button(btn_frame, text="选择图片", command=self.select_img, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="开始校验&评分", command=self.start_check, bootstyle=INFO).pack(side=LEFT, padx=5)

        # ---------------- 右侧：辅助批改面板 ----------------
        right_frame = ttk.Frame(main_frame, bootstyle=PRIMARY)
        right_frame.pack(side=RIGHT, fill=BOTH, expand=YES, padx=5, pady=5)
        ttk.Label(right_frame, text="辅助批改&评分面板", font=("微软雅黑", 12, "bold"), bootstyle=PRIMARY).pack(side=TOP, fill=X, padx=5, pady=3)

        # 1. 自动评分区
        score_frame = ttk.Frame(right_frame, bootstyle=SECONDARY)
        score_frame.pack(fill=X, padx=5, pady=5)
        ttk.Label(score_frame, text="自动评分建议：", font=("微软雅黑", 10, "bold"), bootstyle=SECONDARY).pack(side=LEFT, padx=5, pady=5)
        ttk.Entry(score_frame, textvariable=self.total_score_var, width=10, font=("微软雅黑", 10)).pack(side=LEFT, padx=5, pady=5)
        ttk.Label(score_frame, text="/ 10.0 分", font=("微软雅黑", 10)).pack(side=LEFT, padx=5, pady=5)

        # 2. 关键词校验区
        kw_frame = ttk.Frame(right_frame, bootstyle=SECONDARY)
        kw_frame.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        ttk.Label(kw_frame, text="关键词校验（4分）", font=("微软雅黑", 10, "bold"), bootstyle=SECONDARY).pack(side=TOP, fill=X, padx=5, pady=2)
        
        self.kw_label = scrolledtext.ScrolledText(kw_frame, width=60, height=6, font=("微软雅黑", 9))
        self.kw_label.pack(fill=BOTH, expand=YES, padx=5, pady=5)

        # 3. 结构校验区
        struct_frame = ttk.Frame(right_frame, bootstyle=SECONDARY)
        struct_frame.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        ttk.Label(struct_frame, text="结构校验（4分）", font=("微软雅黑", 10, "bold"), bootstyle=SECONDARY).pack(side=TOP, fill=X, padx=5, pady=2)
        
        self.struct_label = scrolledtext.ScrolledText(struct_frame, width=60, height=8, font=("微软雅黑", 9))
        self.struct_label.pack(fill=BOTH, expand=YES, padx=5, pady=5)

        # 4. 报文细节校验区
        detail_frame = ttk.Frame(right_frame, bootstyle=SECONDARY)
        detail_frame.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        ttk.Label(detail_frame, text="报文细节校验（2分）", font=("微软雅黑", 10, "bold"), bootstyle=SECONDARY).pack(side=TOP, fill=X, padx=5, pady=2)
        
        self.detail_label = scrolledtext.ScrolledText(detail_frame, width=60, height=6, font=("微软雅黑", 9))
        self.detail_label.pack(fill=BOTH, expand=YES, padx=5, pady=5)

        # 5. 老师注释&保存区
        note_frame = ttk.Frame(right_frame, bootstyle=SECONDARY)
        note_frame.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        ttk.Label(note_frame, text="老师注释", font=("微软雅黑", 10, "bold"), bootstyle=SECONDARY).pack(side=TOP, fill=X, padx=5, pady=2)
        
        self.note_text = scrolledtext.ScrolledText(note_frame, width=60, height=3, font=("微软雅黑", 9))
        self.note_text.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        
        ttk.Button(note_frame, text="保存批改结果", command=self.save_result, bootstyle=SUCCESS).pack(side=RIGHT, padx=5, pady=5)

    def select_img(self):
        """选择图片"""
        path = filedialog.askopenfilename(filetypes=[("图片文件", "*.png;*.jpg;*.jpeg")])
        if path:
            self.img_path.set(path)
            load_image(path, self.img_canvas)

    def start_check(self):
        """开始校验+评分"""
        if not self.img_path.get():
            messagebox.showwarning("警告", "请先选择图片！")
            return

        # 1. OCR识别
        text_coords, _ = extract_text_with_coords(self.img_path.get())
        if not text_coords:
            return

        # 2. 关键词匹配
        self.match_result, kw_score = match_keywords(text_coords)
        
        # 3. 结构校验
        self.struct_result, struct_score = check_structure(text_coords)
        
        # 4. 报文细节校验
        self.detail_result, detail_score = check_packet_detail(text_coords)
        
        # 5. 总分计算
        total_score = kw_score + struct_score + detail_score
        self.total_score_var.set(f"{total_score:.1f}")

        # 6. 更新界面显示
        self.update_kw_display()
        self.update_struct_display()
        self.update_detail_display()

    def update_kw_display(self):
        """更新关键词校验显示"""
        self.kw_label.delete('1.0', tk.END)
        content = "【核心关键词】\n"
        content += f"命中：{', '.join(self.match_result['core']['hit']) or '无'}\n"
        content += f"缺失：{', '.join(self.match_result['core']['miss']) or '无'}\n\n"
        
        content += "【分类关键词】\n"
        for key in ["subject", "state", "packet", "flow"]:
            content += f"{key}：命中{len(self.match_result[key]['hit'])}个，缺失{len(self.match_result[key]['miss'])}个\n"
            content += f"  命中：{', '.join(self.match_result[key]['hit']) or '无'}\n"
            content += f"  缺失：{', '.join(self.match_result[key]['miss']) or '无'}\n"
        
        self.kw_label.insert('1.0', content)

    def update_struct_display(self):
        """更新结构校验显示"""
        self.struct_label.delete('1.0', tk.END)
        content = "【客户端/服务端位置】\n"
        content += f"结果：{'✅ 正确' if self.struct_result['pos']['pass'] else '❌ 错误'}\n"
        content += f"原因：{self.struct_result['pos']['reason'] or '客户端在左，服务端在右'}\n\n"
        
        content += "【客户端状态顺序】\n"
        content += f"结果：{'✅ 正确' if self.struct_result['client_state']['pass'] else '❌ 错误'}\n"
        content += f"原因：{self.struct_result['client_state']['reason'] or 'CLOSED→SYN-SENT→ESTABLISHED'}\n\n"
        
        content += "【服务端状态顺序】\n"
        content += f"结果：{'✅ 正确' if self.struct_result['server_state']['pass'] else '❌ 错误'}\n"
        content += f"原因：{self.struct_result['server_state']['reason'] or 'CLOSED→LISTEN→SYN-RCVD→ESTABLISHED'}\n\n"
        
        content += "【报文交互顺序】\n"
        content += f"结果：{'✅ 正确' if self.struct_result['packet_order']['pass'] else '❌ 错误'}\n"
        content += f"原因：{self.struct_result['packet_order']['reason'] or '三次报文从上到下顺序正确'}\n"
        
        self.struct_label.insert('1.0', content)

    def update_detail_display(self):
        """更新报文细节校验显示"""
        self.detail_label.delete('1.0', tk.END)
        content = "【第一次握手（SYN=1,seq=x）】\n"
        content += f"结果：{'✅ 正确' if self.detail_result['packet1']['pass'] else '❌ 错误'}\n"
        content += f"原因：{self.detail_result['packet1']['reason'] or '包含SYN=1和seq=x'}\n\n"
        
        content += "【第二次握手（SYN=1,ACK=1,ack=x+1）】\n"
        content += f"结果：{'✅ 正确' if self.detail_result['packet2']['pass'] else '❌ 错误'}\n"
        content += f"原因：{self.detail_result['packet2']['reason'] or '包含SYN=1、ACK=1、ack=x+1'}\n\n"
        
        content += "【第三次握手（ACK=1,ack=y+1）】\n"
        content += f"结果：{'✅ 正确' if self.detail_result['packet3']['pass'] else '❌ 错误'}\n"
        content += f"原因：{self.detail_result['packet3']['reason'] or '包含ACK=1和ack=y+1'}\n\n"
        
        content += "【数据传输】\n"
        content += f"结果：{'✅ 正确' if self.detail_result['flow']['pass'] else '❌ 错误'}\n"
        content += f"原因：{self.detail_result['flow']['reason'] or '识别到数据传输'}\n"
        
        self.detail_label.insert('1.0', content)

    def save_result(self):
        """保存批改结果"""
        if not self.match_result:
            messagebox.showwarning("警告", "请先完成校验！")
            return
        
        try:
            with open("TCP三次握手批改结果.txt", "a", encoding="utf-8") as f:
                f.write(f"===== 批改结果 - {self.img_path.get()} =====\n")
                f.write(f"自动评分建议：{self.total_score_var.get()}分\n")
                f.write(f"老师注释：{self.note_text.get('1.0', tk.END).strip()}\n")
                f.write("-"*80 + "\n\n")
            messagebox.showinfo("成功", "结果已保存到「TCP三次握手批改结果.txt」！")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{str(e)}")

# ===================== 5. 主程序 =====================
if __name__ == "__main__":
    root = ttk.Window(themename="litera")
    app = TCPHandshakeCorrection(root)
    root.mainloop()