import torch
import cv2
import matplotlib.pyplot as plt
import tkinter
import matplotlib

# 打印环境和库信息
print("Python版本：", __import__('sys').version)
print("PyTorch是否可用：", "CPU模式（正常）" if not torch.cuda.is_available() else "GPU模式")
print("OpenCV版本：", cv2.__version__)

print("matplotlib版本：", matplotlib.__version__)
print("tkinter可用：", tkinter is not None)
print("✅ 所有依赖测试通过！")

print("hello raoshen")