import ttkbootstrap as ttk

root = ttk.Window(themename="litera")
root.title("测试界面")
root.geometry("400x300")

ttk.Label(root, text="Hello, 界面正常！", font=("微软雅黑", 16)).pack(pady=50)
ttk.Button(root, text="点我", bootstyle="success").pack(pady=10)

root.mainloop()