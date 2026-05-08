# -*- coding: utf-8 -*-
"""
网络协议主观题辅助批改系统 - 主界面
支持8类典型题型：TCP三次握手/四次挥手、OSI七层、子网划分、HTTP/HTTPS、交换机vs路由器、TCP拥塞控制、DNS解析
"""
# ========== 基础依赖导入 ==========
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
import csv
from datetime import datetime

# ========== 路径配置 ==========
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

# ========== 核心模块导入 ==========
from core.tcp_handshake import TCPHandshakeCorrection
from core.tcp_wave import TCPWaveCorrection
from core.osi_seven_layer import OSISevenLayerCorrection
from core.ip_subnet import IPSubnetCorrection
from core.http_https import HTTPHTTPSCorrection
from core.switch_router import SwitchRouterCorrection
from core.tcp_congestion import TCPCongestionCorrection
from core.dns_resolve import DNSResolveCorrection

# ========== 题型枚举 ==========
class QuestionType:
    TCP_HANDSHAKE = "TCP三次握手"
    TCP_WAVE = "TCP四次挥手"
    OSI_SEVEN_LAYER = "OSI七层模型"
    IP_SUBNET = "子网划分/IP计算"
    HTTP_HTTPS = "HTTP与HTTPS区别"
    SWITCH_ROUTER = "交换机vs路由器"
    TCP_CONGESTION = "TCP拥塞控制"
    DNS_RESOLVE = "DNS解析过程"

# ========== 主界面类 ==========
class MainUI:
    def __init__(self, root, question_type=QuestionType.TCP_HANDSHAKE):
        self.root = root
        self.root.title("网络协议主观题辅助批改系统")
        self.root.geometry("1200x850")

        self.correction = self._init_correction(question_type)
        if not self.correction:
            self.root.quit()
            return

        self.img_path = tk.StringVar()
        self.total_score_var = tk.StringVar(value=f"{self.correction.total_score:.1f}")
        self.match_result = None
        self.struct_result = None
        self.detail_result = None

        self.batch_paths = []
        self.batch_index = 0
        self.export_records = []

        self._init_main_layout()

    def _init_correction(self, question_type):
        try:
            correction_map = {
                QuestionType.TCP_WAVE: TCPWaveCorrection(),
                QuestionType.OSI_SEVEN_LAYER: OSISevenLayerCorrection(),
                QuestionType.IP_SUBNET: IPSubnetCorrection(),
                QuestionType.HTTP_HTTPS: HTTPHTTPSCorrection(),
                QuestionType.SWITCH_ROUTER: SwitchRouterCorrection(),
                QuestionType.TCP_CONGESTION: TCPCongestionCorrection(),
                QuestionType.DNS_RESOLVE: DNSResolveCorrection(),
                QuestionType.TCP_HANDSHAKE: TCPHandshakeCorrection()
            }
            return correction_map.get(question_type, TCPHandshakeCorrection())
        except Exception as e:
            messagebox.showerror("初始化失败", f"题型加载失败：{e}")
            return None

    def _init_main_layout(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=BOTH, expand=YES, padx=10, pady=10)

        type_frame = ttk.Frame(main_frame, bootstyle=PRIMARY)
        type_frame.pack(fill=X, padx=5, pady=5)

        ttk.Label(type_frame, text="题型选择：", font=("微软雅黑",11,"bold")).pack(side=LEFT,padx=5,pady=3)
        self.question_type_var = tk.StringVar(value=self.correction.question_type)
        self.type_combo = ttk.Combobox(
            type_frame, textvariable=self.question_type_var,
            values=[
                QuestionType.TCP_HANDSHAKE, QuestionType.TCP_WAVE,
                QuestionType.OSI_SEVEN_LAYER, QuestionType.IP_SUBNET,
                QuestionType.HTTP_HTTPS, QuestionType.SWITCH_ROUTER,
                QuestionType.TCP_CONGESTION, QuestionType.DNS_RESOLVE
            ],
            state="readonly", font=("微软雅黑",10), width=20
        )
        self.type_combo.pack(side=LEFT,padx=5,pady=3)
        ttk.Button(type_frame, text="切换题型", command=self._switch_question_type, bootstyle=WARNING, width=10).pack(side=LEFT,padx=5,pady=3)
        ttk.Button(type_frame, text="批量选择", command=self._batch_select_images, bootstyle=WARNING, width=10).pack(side=RIGHT,padx=5)
        ttk.Button(type_frame, text="导出CSV", command=self._export_results_csv, bootstyle=SUCCESS, width=10).pack(side=RIGHT,padx=5)

        left_frame = ttk.Frame(main_frame, bootstyle=PRIMARY)
        left_frame.pack(side=LEFT,fill=BOTH,expand=YES,padx=5,pady=5)
        self.left_title_label = ttk.Label(left_frame, text=f"{self.correction.question_type} - 答案图片", font=("微软雅黑",12,"bold"))
        self.left_title_label.pack(side=TOP,fill=X,padx=5,pady=3)
        self.img_canvas = tk.Canvas(left_frame,bg="white",bd=1,relief=tk.SOLID)
        self.img_canvas.pack(fill=BOTH,expand=YES,padx=5,pady=5)
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=X,padx=5,pady=5)
        ttk.Button(btn_frame,text="选择图片",command=self._select_img,bootstyle=SUCCESS,width=10).pack(side=LEFT,padx=5)
        ttk.Button(btn_frame,text="开始批改",command=self._start_check,bootstyle=INFO,width=12).pack(side=LEFT,padx=5)
        ttk.Button(btn_frame,text="下一张",command=self._batch_next_image,bootstyle=SECONDARY,width=10).pack(side=LEFT,padx=5)

        right_frame = ttk.Frame(main_frame,bootstyle=PRIMARY)
        right_frame.pack(side=RIGHT,fill=BOTH,expand=YES,padx=5,pady=5)
        self.right_title_label = ttk.Label(right_frame,text=f"{self.correction.question_type} - 辅助批改面板",font=("微软雅黑",12,"bold"))
        self.right_title_label.pack(side=TOP,fill=X,padx=5,pady=3)

        score_frame = ttk.Frame(right_frame,bootstyle=SECONDARY)
        score_frame.pack(fill=X,padx=5,pady=5)
        ttk.Label(score_frame,text="得分：",font=("微软雅黑",10,"bold")).pack(side=LEFT,padx=5,pady=5)
        ttk.Entry(score_frame,textvariable=self.total_score_var,width=10,font=("微软雅黑",10)).pack(side=LEFT,padx=5,pady=5)
        self.score_total_label = ttk.Label(score_frame,text=f"/ {self.correction.total_score:.1f}",font=("微软雅黑",10)).pack(side=LEFT,padx=5,pady=5)

        kw_frame = ttk.Frame(right_frame,bootstyle=SECONDARY)
        kw_frame.pack(fill=BOTH,expand=YES,padx=5,pady=5)
        self.kw_title_label = ttk.Label(kw_frame,text=self._get_kw_title(),font=("微软雅黑",10,"bold"))
        self.kw_title_label.pack(side=TOP,fill=X,padx=5,pady=2)
        self.kw_text = scrolledtext.ScrolledText(kw_frame,width=60,height=6,font=("微软雅黑",9))
        self.kw_text.pack(fill=BOTH,expand=YES,padx=5,pady=5)

        struct_frame = ttk.Frame(right_frame,bootstyle=SECONDARY)
        struct_frame.pack(fill=BOTH,expand=YES,padx=5,pady=5)
        self.struct_title_label = ttk.Label(struct_frame,text=self._get_struct_title(),font=("微软雅黑",10,"bold"))
        self.struct_title_label.pack(side=TOP,fill=X,padx=5,pady=2)
        self.struct_text = scrolledtext.ScrolledText(struct_frame,width=60,height=8,font=("微软雅黑",9))
        self.struct_text.pack(fill=BOTH,expand=YES,padx=5,pady=5)

        detail_frame = ttk.Frame(right_frame,bootstyle=SECONDARY)
        detail_frame.pack(fill=BOTH,expand=YES,padx=5,pady=5)
        self.detail_title_label = ttk.Label(detail_frame,text=self._get_detail_title(),font=("微软雅黑",10,"bold"))
        self.detail_title_label.pack(side=TOP,fill=X,padx=5,pady=2)
        self.detail_text = scrolledtext.ScrolledText(detail_frame,width=60,height=6,font=("微软雅黑",9))
        self.detail_text.pack(fill=BOTH,expand=YES,padx=5,pady=5)

        note_frame = ttk.Frame(right_frame,bootstyle=SECONDARY)
        note_frame.pack(fill=BOTH,expand=YES,padx=5,pady=5)
        ttk.Label(note_frame,text="评语",font=("微软雅黑",10,"bold")).pack(side=TOP,fill=X,padx=5,pady=2)
        self.note_text = scrolledtext.ScrolledText(note_frame,width=60,height=3,font=("微软雅黑",9))
        self.note_text.pack(fill=BOTH,expand=YES,padx=5,pady=5)
        ttk.Button(note_frame,text="保存结果",command=self._save_result,bootstyle=SUCCESS,width=12).pack(side=RIGHT,padx=5,pady=5)

    def _get_kw_title(self):
        return {"TCP三次握手":"关键词（4分）"}.get(self.correction.question_type,"关键词")
    def _get_struct_title(self):
        return {"TCP三次握手":"结构（4分）"}.get(self.correction.question_type,"结构")
    def _get_detail_title(self):
        return {"TCP三次握手":"细节（2分）"}.get(self.correction.question_type,"细节")

    def _switch_question_type(self):
        new_type = self.question_type_var.get()
        self.correction = self._init_correction(new_type)
        self._clear_all_states()
        self.left_title_label.config(text=f"{new_type} - 答案图片")
        self.right_title_label.config(text=f"{new_type} - 辅助批改面板")

    def _clear_all_states(self):
        self.img_path.set("")
        self.total_score_var.set(f"{self.correction.total_score:.1f}")
        self.img_canvas.delete("all")
        self.kw_text.delete('1.0',tk.END)
        self.struct_text.delete('1.0',tk.END)
        self.detail_text.delete('1.0',tk.END)
        self.note_text.delete('1.0',tk.END)

    def _select_img(self):
        path = filedialog.askopenfilename(filetypes=[("图片","*.png;*.jpg;*.jpeg")])
        if not path: return
        self.img_path.set(path)
        self._display_image(path)

    def _display_image(self, path):
        img = Image.open(path)
        img.thumbnail((600,500))
        tkimg = ImageTk.PhotoImage(img)
        self.img_canvas.delete("all")
        self.img_canvas.image = tkimg
        self.img_canvas.create_image(self.img_canvas.winfo_width()//2, self.img_canvas.winfo_height()//2, image=tkimg, anchor=tk.CENTER)

    def _batch_select_images(self):
        paths = filedialog.askopenfilenames(filetypes=[("图片","*.png;*.jpg;*.jpeg")])
        if not paths: return
        self.batch_paths = list(paths)
        self.batch_index = 0
        self._batch_next_image()

    def _batch_next_image(self):
        if not self.batch_paths or self.batch_index >= len(self.batch_paths):
            messagebox.showinfo("完成","全部完成")
            return
        path = self.batch_paths[self.batch_index]
        self.img_path.set(path)
        self._display_image(path)
        self.batch_index +=1

    def _start_check(self):
        if not self.img_path.get():
            messagebox.showwarning("提示","请选图片")
            return
        try:
            ocr_items, processed = self.correction.extract_text_with_coords(self.img_path.get())
            res = self.correction.correct(ocr_items)

            # 保存结果用于显示
            self.match_result = {"core":{"hit":res["hit_keywords"],"miss":res["miss_keywords"]}}
            self.struct_result = {"log":res["structure_log"]}
            self.detail_result = {"log":res["detail_log"]}

            self.total_score_var.set(f"{res['score']:.1f}")

            # 更新三个文本框
            self._update_kw_display(res)
            self._update_struct_display(res)
            self._update_detail_display(res)

            messagebox.showinfo("完成","批改成功")
        except Exception as e:
            messagebox.showerror("错误",str(e))

    def _update_kw_display(self, res):
        self.kw_text.delete('1.0',tk.END)
        self.kw_text.insert(tk.END, f"【OCR原始文本】\n{res['original_text']}\n\n")
        self.kw_text.insert(tk.END, f"【修正后文本】\n{res['fixed_text']}\n\n")
        self.kw_text.insert(tk.END, f"命中关键词：{res['hit_keywords']}\n")
        self.kw_text.insert(tk.END, f"缺失关键词：{res['miss_keywords']}\n")

    def _update_struct_display(self, res):
        self.struct_text.delete('1.0',tk.END)
        self.struct_text.insert(tk.END, "【结构校验过程】\n")
        for line in res["structure_log"]:
            self.struct_text.insert(tk.END, line + "\n")

    def _update_detail_display(self, res):
        self.detail_text.delete('1.0',tk.END)
        self.detail_text.insert(tk.END, "【细节校验过程】\n")
        for line in res["detail_log"]:
            self.detail_text.insert(tk.END, line + "\n")

    def _save_result(self):
        messagebox.showinfo("保存","已保存（演示版）")
    def _export_results_csv(self):
        messagebox.showinfo("导出","已导出（演示版）")

if __name__ == "__main__":
    root = ttk.Window(themename="flatly")
    app = MainUI(root)
    root.mainloop()