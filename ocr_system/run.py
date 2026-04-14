# -*- coding: utf-8 -*-
import os
import sys
import traceback
import ttkbootstrap as ttk

# 添加根目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

# 选择题型：TCP三次握手 / OSI七层模型/TCP四次挥手
SELECTED_QUESTION_TYPE = "TCP三次握手"

if __name__ == "__main__":
    try:
        from ui.main_ui import MainUI, QuestionType
        root = ttk.Window(themename="litera")
        app = MainUI(root, question_type=SELECTED_QUESTION_TYPE)
        root.mainloop()
    except Exception as e:
        print("="*50)
        print("启动失败！详细错误：")
        traceback.print_exc()
        print("="*50)
        input("按回车退出...")