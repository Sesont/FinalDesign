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
from PIL import ImageTk

# ========== 路径配置 ==========
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

# ========== 核心模块导入 ==========
try:
    from ocr_system.core import (
        TCPHandshakeCorrection, TCPWaveCorrection,
        OSISevenLayerCorrection, IPSubnetCorrection,
        HTTPHTTPSCorrection, SwitchRouterCorrection,
        TCPCongestionCorrection, DNSResolveCorrection
    )
except ImportError:
    # 备用导入（直接导入，兼容无init.py的情况）
    try:
        from core.tcp_handshake import TCPHandshakeCorrection
        from core.tcp_wave import TCPWaveCorrection
        from core.osi_seven_layer import OSISevenLayerCorrection
        from core.ip_subnet import IPSubnetCorrection
        from core.http_https import HTTPHTTPSCorrection
        from core.switch_router import SwitchRouterCorrection
        from core.tcp_congestion import TCPCongestionCorrection
        from core.dns_resolve import DNSResolveCorrection
    except ImportError as e:
        raise Exception(f"核心模块导入失败：{e}\n请检查core目录下的文件是否完整！")

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
        self.root.geometry("1200x800")

        # 初始化核心校正类
        self.correction = self._init_correction(question_type)
        if not self.correction:
            self.root.quit()
            return

        # 界面变量
        self.img_path = tk.StringVar()
        self.total_score_var = tk.StringVar(value=f"{self.correction.total_score:.1f}")
        self.match_result = None
        self.struct_result = None
        self.detail_result = None

        # 初始化布局
        self._init_main_layout()

    def _init_correction(self, question_type):
        """初始化校正类（适配所有8类题型）"""
        try:
            correction_map = {
                QuestionType.TCP_WAVE: TCPWaveCorrection(),
                QuestionType.OSI_SEVEN_LAYER: OSISevenLayerCorrection(),
                QuestionType.IP_SUBNET: IPSubnetCorrection(),
                QuestionType.HTTP_HTTPS: HTTPHTTPSCorrection(),
                QuestionType.SWITCH_ROUTER: SwitchRouterCorrection(),
                QuestionType.TCP_CONGESTION: TCPCongestionCorrection(),
                QuestionType.DNS_RESOLVE: DNSResolveCorrection(),
                QuestionType.TCP_HANDSHAKE: TCPHandshakeCorrection()  # 默认
            }
            return correction_map.get(question_type, TCPHandshakeCorrection())
        except Exception as e:
            messagebox.showerror("初始化失败", f"题型加载失败：{e}")
            return None

    def _init_main_layout(self):
        """初始化主布局（含可更新标题+全题型适配）"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=BOTH, expand=YES, padx=10, pady=10)

        # ---------------- 顶部：题型选择区 ----------------
        type_frame = ttk.Frame(main_frame, bootstyle=PRIMARY)
        type_frame.pack(fill=X, padx=5, pady=5)
        
        # 题型选择标签
        ttk.Label(
            type_frame, 
            text="题型选择：", 
            font=("微软雅黑", 11, "bold"), 
            bootstyle=PRIMARY
        ).pack(side=LEFT, padx=5, pady=3)
        
        # 题型下拉框（8类题型）
        self.question_type_var = tk.StringVar(value=self.correction.question_type)
        self.type_combo = ttk.Combobox(
            type_frame,
            textvariable=self.question_type_var,
            values=[
                QuestionType.TCP_HANDSHAKE,
                QuestionType.TCP_WAVE,
                QuestionType.OSI_SEVEN_LAYER,
                QuestionType.IP_SUBNET,
                QuestionType.HTTP_HTTPS,
                QuestionType.SWITCH_ROUTER,
                QuestionType.TCP_CONGESTION,
                QuestionType.DNS_RESOLVE
            ],
            state="readonly",
            font=("微软雅黑", 10),
            width=20
        )
        self.type_combo.pack(side=LEFT, padx=5, pady=3)
        
        # 切换题型按钮
        ttk.Button(
            type_frame,
            text="切换题型",
            command=self._switch_question_type,
            bootstyle=WARNING,
            width=10
        ).pack(side=LEFT, padx=5, pady=3)

        # ---------------- 左侧：图片展示区 ----------------
        left_frame = ttk.Frame(main_frame, bootstyle=PRIMARY)
        left_frame.pack(side=LEFT, fill=BOTH, expand=YES, padx=5, pady=5)
        
        # 左侧标题（可更新）
        self.left_title_label = ttk.Label(
            left_frame, 
            text=f"{self.correction.question_type} - 答案图片", 
            font=("微软雅黑", 12, "bold"), 
            bootstyle=PRIMARY
        )
        self.left_title_label.pack(side=TOP, fill=X, padx=5, pady=3)
        
        # 图片显示画布
        self.img_canvas = tk.Canvas(left_frame, bg="white", bd=1, relief=tk.SOLID)
        self.img_canvas.pack(fill=BOTH, expand=YES, padx=5, pady=5)

        # 左侧功能按钮
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=X, padx=5, pady=5)
        ttk.Button(
            btn_frame, 
            text="选择图片", 
            command=self._select_img, 
            bootstyle=SUCCESS,
            width=10
        ).pack(side=LEFT, padx=5)
        ttk.Button(
            btn_frame, 
            text="开始校验&评分", 
            command=self._start_check, 
            bootstyle=INFO,
            width=12
        ).pack(side=LEFT, padx=5)

        # ---------------- 右侧：辅助批改面板 ----------------
        right_frame = ttk.Frame(main_frame, bootstyle=PRIMARY)
        right_frame.pack(side=RIGHT, fill=BOTH, expand=YES, padx=5, pady=5)
        
        # 右侧标题（可更新）
        self.right_title_label = ttk.Label(
            right_frame, 
            text=f"{self.correction.question_type} - 辅助批改面板", 
            font=("微软雅黑", 12, "bold"), 
            bootstyle=PRIMARY
        )
        self.right_title_label.pack(side=TOP, fill=X, padx=5, pady=3)

        # 1. 自动评分区（修复总分标签引用）
        score_frame = ttk.Frame(right_frame, bootstyle=SECONDARY)
        score_frame.pack(fill=X, padx=5, pady=5)
        ttk.Label(
            score_frame, 
            text="自动评分建议：", 
            font=("微软雅黑", 10, "bold")
        ).pack(side=LEFT, padx=5, pady=5)
        ttk.Entry(
            score_frame, 
            textvariable=self.total_score_var, 
            width=10, 
            font=("微软雅黑", 10),
            state="readonly"  # 设为只读，防止手动修改
        ).pack(side=LEFT, padx=5, pady=5)
        # 总分标签（改为变量引用）
        self.score_total_label = ttk.Label(
            score_frame, 
            text=f"/ {self.correction.total_score:.1f} 分", 
            font=("微软雅黑", 10)
        )
        self.score_total_label.pack(side=LEFT, padx=5, pady=5)

        # 2. 关键词校验区（可更新标题）
        kw_frame = ttk.Frame(right_frame, bootstyle=SECONDARY)
        kw_frame.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        self.kw_title_label = ttk.Label(
            kw_frame, 
            text=self._get_kw_title(), 
            font=("微软雅黑", 10, "bold")
        )
        self.kw_title_label.pack(side=TOP, fill=X, padx=5, pady=2)
        self.kw_text = scrolledtext.ScrolledText(
            kw_frame, 
            width=60, 
            height=6, 
            font=("微软雅黑", 9)
        )
        self.kw_text.pack(fill=BOTH, expand=YES, padx=5, pady=5)

        # 3. 结构/计算/流程校验区（可更新标题）
        struct_frame = ttk.Frame(right_frame, bootstyle=SECONDARY)
        struct_frame.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        self.struct_title_label = ttk.Label(
            struct_frame, 
            text=self._get_struct_title(), 
            font=("微软雅黑", 10, "bold")
        )
        self.struct_title_label.pack(side=TOP, fill=X, padx=5, pady=2)
        self.struct_text = scrolledtext.ScrolledText(
            struct_frame, 
            width=60, 
            height=8, 
            font=("微软雅黑", 9)
        )
        self.struct_text.pack(fill=BOTH, expand=YES, padx=5, pady=5)

        # 4. 细节校验区（可更新标题）
        detail_frame = ttk.Frame(right_frame, bootstyle=SECONDARY)
        detail_frame.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        self.detail_title_label = ttk.Label(
            detail_frame, 
            text=self._get_detail_title(), 
            font=("微软雅黑", 10, "bold")
        )
        self.detail_title_label.pack(side=TOP, fill=X, padx=5, pady=2)
        self.detail_text = scrolledtext.ScrolledText(
            detail_frame, 
            width=60, 
            height=6, 
            font=("微软雅黑", 9)
        )
        self.detail_text.pack(fill=BOTH, expand=YES, padx=5, pady=5)

        # 5. 老师注释&保存区
        note_frame = ttk.Frame(right_frame, bootstyle=SECONDARY)
        note_frame.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        ttk.Label(
            note_frame, 
            text="老师注释", 
            font=("微软雅黑", 10, "bold")
        ).pack(side=TOP, fill=X, padx=5, pady=2)
        self.note_text = scrolledtext.ScrolledText(
            note_frame, 
            width=60, 
            height=3, 
            font=("微软雅黑", 9)
        )
        self.note_text.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        ttk.Button(
            note_frame, 
            text="保存批改结果", 
            command=self._save_result, 
            bootstyle=SUCCESS,
            width=12
        ).pack(side=RIGHT, padx=5, pady=5)

    # ========== 标题生成方法（适配所有题型） ==========
    def _get_kw_title(self):
        """根据题型生成关键词校验标题（带分值）"""
        type_kw_title = {
            QuestionType.TCP_HANDSHAKE: "关键词校验结果（4分）",
            QuestionType.TCP_WAVE: "关键词校验结果（4分）",
            QuestionType.OSI_SEVEN_LAYER: "关键词校验结果（5分）",
            QuestionType.IP_SUBNET: "关键词校验结果（3分）",
            QuestionType.HTTP_HTTPS: "关键词校验结果（5分）",
            QuestionType.SWITCH_ROUTER: "关键词校验结果（5分）",
            QuestionType.TCP_CONGESTION: "关键词校验结果（4分）",
            QuestionType.DNS_RESOLVE: "关键词校验结果（4分）"
        }
        return type_kw_title.get(self.correction.question_type, "关键词校验结果")

    def _get_struct_title(self):
        """根据题型生成结构/计算/流程校验标题（带分值）"""
        type_struct_title = {
            QuestionType.TCP_HANDSHAKE: "结构校验结果（4分）",
            QuestionType.TCP_WAVE: "结构校验结果（4分）",
            QuestionType.OSI_SEVEN_LAYER: "结构校验结果（3分）",
            QuestionType.IP_SUBNET: "计算结果校验（5分）",
            QuestionType.HTTP_HTTPS: "核心对比校验（3分）",
            QuestionType.SWITCH_ROUTER: "核心对比校验（3分）",
            QuestionType.TCP_CONGESTION: "阶段顺序校验（4分）",
            QuestionType.DNS_RESOLVE: "流程顺序校验（4分）"
        }
        return type_struct_title.get(self.correction.question_type, "结构校验结果")

    def _get_detail_title(self):
        """根据题型生成细节校验标题（带分值）"""
        type_detail_title = {
            QuestionType.TCP_HANDSHAKE: "报文细节校验结果（2分）",
            QuestionType.TCP_WAVE: "细节校验结果（2分）",
            QuestionType.OSI_SEVEN_LAYER: "功能细节校验结果（2分）",
            QuestionType.IP_SUBNET: "细节校验结果（2分）",
            QuestionType.HTTP_HTTPS: "细节校验结果（2分）",
            QuestionType.SWITCH_ROUTER: "细节校验结果（2分）",
            QuestionType.TCP_CONGESTION: "细节校验结果（2分）",
            QuestionType.DNS_RESOLVE: "细节校验结果（2分）"
        }
        return type_detail_title.get(self.correction.question_type, "细节校验结果")

    # ========== 核心交互方法 ==========
    def _switch_question_type(self):
        """切换题型（标题+分值+逻辑全同步，修复所有Bug）"""
        new_type = self.question_type_var.get()
        if new_type == self.correction.question_type:
            messagebox.showinfo("提示", "当前已是该题型，无需切换！")
            return

        # 确认切换
        if not messagebox.askyesno("确认切换", f"确定切换到「{new_type}」吗？\n当前所有结果将被清空！"):
            return

        # 重新初始化校正类
        self.correction = self._init_correction(new_type)
        if not self.correction:
            return

        # 清空所有界面状态
        self._clear_all_states()

        # ========== 同步更新所有标题和分值 ==========
        # 窗口标题
        self.root.title(f"网络协议主观题辅助批改系统 - {new_type}")
        # 左右侧主标题
        self.left_title_label.config(text=f"{new_type} - 答案图片")
        self.right_title_label.config(text=f"{new_type} - 辅助批改面板")
        # 分块标题（按题型适配）
        self.kw_title_label.config(text=self._get_kw_title())
        self.struct_title_label.config(text=self._get_struct_title())
        self.detail_title_label.config(text=self._get_detail_title())
        # 总分标签（同步更新总分值）
        self.score_total_label.config(text=f"/ {self.correction.total_score:.1f} 分")

        messagebox.showinfo("切换成功", f"已切换到「{new_type}」题型！所有配置已同步更新。")

    def _clear_all_states(self):
        """清空所有界面状态（切换题型专用）"""
        # 清空变量
        self.img_path.set("")
        self.total_score_var.set(f"{self.correction.total_score:.1f}")
        self.match_result = None
        self.struct_result = None
        self.detail_result = None

        # 清空画布（图片）
        self.img_canvas.delete("all")

        # 清空所有文本框
        self.kw_text.delete('1.0', tk.END)
        self.struct_text.delete('1.0', tk.END)
        self.detail_text.delete('1.0', tk.END)
        self.note_text.delete('1.0', tk.END)

    def _select_img(self):
        """选择并显示图片（兼容所有题型）"""
        path = filedialog.askopenfilename(
            title="选择答案图片",
            filetypes=[("图片文件", "*.png;*.jpg;*.jpeg"), ("所有文件", "*.*")]
        )
        if not path:
            return
        
        self.img_path.set(path)
        try:
            # 调用对应题型的图片加载方法
            img = self.correction.load_image(path, self.img_canvas)
            tk_img = ImageTk.PhotoImage(img)
            self.img_canvas.delete("all")
            self.img_canvas.create_image(
                self.img_canvas.winfo_width()/2, 
                self.img_canvas.winfo_height()/2, 
                image=tk_img
            )
            self.img_canvas.img = tk_img  # 防止图片被GC回收
        except Exception as e:
            messagebox.showerror("图片加载失败", f"错误原因：{str(e)}\n请选择清晰的图片文件！")

    def _start_check(self):
        """开始校验&评分（适配所有题型的校验逻辑）"""
        if not self.img_path.get():
            messagebox.showwarning("提示", "请先选择答案图片！")
            return
        
        try:
            # 1. OCR识别（调用对应题型的识别方法）
            text_coords, raw_text = self.correction.extract_text_with_coords(self.img_path.get())
            if not text_coords or not raw_text:
                messagebox.showwarning("提示", "未识别到任何文字！请检查图片清晰度。")
                return

            # 2. 三级校验（关键词+结构/计算+细节）
            self.match_result, kw_score = self.correction.match_keywords(text_coords)
            self.struct_result, struct_score = self.correction.check_structure(text_coords)
            self.detail_result, detail_score = self.correction.check_detail(text_coords)

            # 3. 总分计算
            total_score = self.correction.calculate_score(kw_score, struct_score, detail_score)
            self.total_score_var.set(f"{total_score:.1f}")

            # 4. 更新结果显示（适配所有题型）
            self._update_kw_display()
            self._update_struct_display()
            self._update_detail_display()

            messagebox.showinfo("成功", "校验完成！请查看右侧批改结果。")
        except Exception as e:
            messagebox.showerror("校验失败", f"错误原因：{str(e)}\n请检查图片或题型配置！")

    def _save_result(self):
        """保存批改结果（按题型分类保存）"""
        if not self.match_result:
            messagebox.showwarning("提示", "请先完成校验！")
            return
        
        try:
            # 按题型生成保存文件名
            filename = f"{self.correction.question_type}_批改结果.txt"
            with open(filename, "a", encoding="utf-8") as f:
                f.write(f"\n===== 批改结果 - {self.correction.question_type} =====\n")
                f.write(f"图片路径：{self.img_path.get()}\n")
                f.write(f"自动评分：{self.total_score_var.get()} / {self.correction.total_score:.1f} 分\n")
                f.write(f"老师注释：{self.note_text.get('1.0', tk.END).strip()}\n")
                f.write("-" * 80 + "\n")
            
            messagebox.showinfo("保存成功", f"结果已保存到：\n{os.path.abspath(filename)}")
        except Exception as e:
            messagebox.showerror("保存失败", f"错误原因：{str(e)}\n请检查文件是否被占用！")

    # ========== 结果显示更新方法（适配所有8类题型） ==========
    def _update_kw_display(self):
        """更新关键词校验结果（通用逻辑，适配所有题型）"""
        self.kw_text.delete('1.0', tk.END)
        if not self.match_result or "core" not in self.match_result:
            self.kw_text.insert('1.0', "【核心关键词】\n暂无校验结果\n")
            return
        
        content = "【核心关键词】\n"
        content += f"命中：{', '.join(self.match_result['core']['hit']) or '无'}\n"
        content += f"缺失：{', '.join(self.match_result['core']['miss']) or '无'}\n\n"
        
        # 补充其他关键词分类（如TCP的stage、OSI的layer等）
        for key in self.match_result.keys():
            if key == "core":
                continue
            content += f"【{key}关键词】\n"
            content += f"命中：{', '.join(self.match_result[key].get('hit', []))[:80] or '无'}\n"
            content += f"缺失：{', '.join(self.match_result[key].get('miss', []))[:80] or '无'}\n\n"
        
        self.kw_text.insert('1.0', content)

    def _update_struct_display(self):
        """更新结构/计算/流程校验结果（适配所有8类题型）"""
        self.struct_text.delete('1.0', tk.END)
        if not self.struct_result:
            self.struct_text.insert('1.0', "【结构/计算校验】\n暂无校验结果\n")
            return
        
        qt = self.correction.question_type
        content = ""

        # 1. TCP三次握手
        if qt == QuestionType.TCP_HANDSHAKE:
            content = "【客户端/服务端位置】\n"
            content += f"结果：{'✅ 正确' if self.struct_result['pos']['pass'] else '❌ 错误'}\n"
            content += f"原因：{self.struct_result['pos']['reason']}\n\n"
            content += "【客户端状态顺序】\n"
            content += f"结果：{'✅ 正确' if self.struct_result['client_state']['pass'] else '❌ 错误'}\n"
            content += f"原因：{self.struct_result['client_state']['reason']}\n\n"
            content += "【服务端状态顺序】\n"
            content += f"结果：{'✅ 正确' if self.struct_result['server_state']['pass'] else '❌ 错误'}\n"
            content += f"原因：{self.struct_result['server_state']['reason']}\n\n"
            content += "【报文交互顺序】\n"
            content += f"结果：{'✅ 正确' if self.struct_result['packet_order']['pass'] else '❌ 错误'}\n"
            content += f"原因：{self.struct_result['packet_order']['reason']}\n"
        
        # 2. TCP四次挥手
        elif qt == QuestionType.TCP_WAVE:
            content = "【四次挥手顺序】\n"
            content += f"结果：{'✅ 正确' if self.struct_result['order']['pass'] else '❌ 错误'}\n"
            content += f"原因：{self.struct_result['order']['reason']}\n\n"
            content += "【客户端/服务端位置】\n"
            content += f"结果：{'✅ 正确' if self.struct_result['pos']['pass'] else '❌ 错误'}\n"
            content += f"原因：{self.struct_result['pos']['reason']}\n"
        
        # 3. OSI七层模型
        elif qt == QuestionType.OSI_SEVEN_LAYER:
            content = "【七层顺序】\n"
            content += f"结果：{'✅ 正确' if self.struct_result['order']['pass'] else '❌ 错误'}\n"
            content += f"原因：{self.struct_result['order']['reason']}\n\n"
            content += "【顺序方向描述】\n"
            content += f"结果：{'✅ 正确' if self.struct_result['direction']['pass'] else '❌ 错误'}\n"
            content += f"原因：{self.struct_result['direction']['reason']}\n"
        
        # 4. 子网划分/IP计算
        elif qt == QuestionType.IP_SUBNET:
            content = "【IP计算结果】\n"
            content += f"结果：{'✅ 正确' if self.struct_result['calculate']['pass'] else '❌ 错误'}\n"
            content += f"原因：{self.struct_result['calculate']['reason']}\n"
        
        # 5. HTTP/HTTPS区别 & 交换机vs路由器
        elif qt in [QuestionType.HTTP_HTTPS, QuestionType.SWITCH_ROUTER]:
            content = "【核心对比项】\n"
            content += f"结果：{'✅ 正确' if self.struct_result['compare']['pass'] else '❌ 错误'}\n"
            content += f"原因：{self.struct_result['compare']['reason']}\n"
        
        # 6. TCP拥塞控制
        elif qt == QuestionType.TCP_CONGESTION:
            content = "【阶段顺序校验】\n"
            content += f"结果：{'✅ 正确' if self.struct_result['order']['pass'] else '❌ 错误'}\n"
            content += f"原因：{self.struct_result['order']['reason']}\n"
        
        # 7. DNS解析过程
        elif qt == QuestionType.DNS_RESOLVE:
            content = "【解析流程校验】\n"
            content += f"结果：{'✅ 正确' if self.struct_result['flow']['pass'] else '❌ 错误'}\n"
            content += f"原因：{self.struct_result['flow']['reason']}\n"
        
        # 通用兜底
        else:
            content = "【结构/计算校验】\n"
            content += f"结果：{'✅ 正确' if list(self.struct_result.values())[0]['pass'] else '❌ 错误'}\n"
            content += f"原因：{list(self.struct_result.values())[0]['reason']}\n"
        
        self.struct_text.insert('1.0', content)

    def _update_detail_display(self):
        """更新细节校验结果（通用逻辑，适配所有题型）"""
        self.detail_text.delete('1.0', tk.END)
        if not self.detail_result or "detail" not in self.detail_result:
            self.detail_text.insert('1.0', "【细节校验结果】\n暂无校验结果\n")
            return
        
        content = "【细节校验结果】\n"
        content += f"结果：{'✅ 正确' if self.detail_result['detail']['pass'] else '❌ 错误'}\n"
        content += f"原因：{self.detail_result['detail']['reason']}\n"
        
        self.detail_text.insert('1.0', content)

# ========== 程序入口 ==========
if __name__ == "__main__":
    root = ttk.Window(themename="flatly")  # 使用ttkbootstrap的窗口
    app = MainUI(root)
    root.mainloop()