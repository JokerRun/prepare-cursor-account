import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import logging
import queue
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class RegistrationGUI:
    """注册工具GUI界面"""
    
    def __init__(self, register_callback):
        self.logger = logging.getLogger("163_register.gui")
        self.register_callback = register_callback
        self.log_queue = queue.Queue()
        self.is_registering = False
        self.current_email = None
        
        self.root = tk.Tk()
        self.setup_ui()
        
        # 启动日志处理线程
        self.setup_logging()
        
    def setup_ui(self):
        """设置UI界面"""
        self.root.title("163邮箱自动注册工具")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 设置区域 - 邮箱范围和密码
        settings_frame = ttk.LabelFrame(self.root, text="注册设置")
        settings_frame.pack(fill="x", padx=10, pady=10)
        
        # 邮箱前缀起始
        ttk.Label(settings_frame, text="邮箱前缀起始:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.prefix_start = ttk.Entry(settings_frame, width=20)
        self.prefix_start.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.prefix_start.insert(0, "CursorJR001")
        
        # 邮箱前缀结束
        ttk.Label(settings_frame, text="邮箱前缀结束:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.prefix_end = ttk.Entry(settings_frame, width=20)
        self.prefix_end.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.prefix_end.insert(0, "CursorJR010")
        
        # 统一密码
        ttk.Label(settings_frame, text="统一密码:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.password = ttk.Entry(settings_frame, width=20, show="*")
        self.password.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # 显示密码复选框
        self.show_password_var = tk.BooleanVar()
        self.show_password_check = ttk.Checkbutton(
            settings_frame, 
            text="显示密码", 
            variable=self.show_password_var,
            command=self.toggle_password_visibility
        )
        self.show_password_check.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        
        # 操作按钮区域
        buttons_frame = ttk.Frame(self.root)
        buttons_frame.pack(fill="x", padx=10, pady=5)
        
        self.start_button = ttk.Button(buttons_frame, text="开始注册", command=self.start_registration)
        self.start_button.pack(side="left", padx=5)
        
        self.pause_button = ttk.Button(buttons_frame, text="暂停", command=self.pause_registration, state="disabled")
        self.pause_button.pack(side="left", padx=5)
        
        self.continue_button = ttk.Button(buttons_frame, text="继续", command=self.continue_registration, state="disabled")
        self.continue_button.pack(side="left", padx=5)
        
        self.manual_verify_button = ttk.Button(buttons_frame, text="完成验证", command=self.manual_verification_done, state="disabled")
        self.manual_verify_button.pack(side="left", padx=5)
        
        # 状态显示区域
        status_frame = ttk.LabelFrame(self.root, text="注册状态")
        status_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 当前操作状态
        self.status_label = ttk.Label(status_frame, text="就绪")
        self.status_label.pack(anchor="w", padx=5, pady=5)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill="x", padx=5, pady=5)
        
        # 日志显示区域
        self.log_text = scrolledtext.ScrolledText(status_frame, height=15)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_text.config(state="disabled")
        
        # 已注册账号列表
        accounts_frame = ttk.LabelFrame(self.root, text="已注册账号")
        accounts_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 使用Treeview显示已注册账号
        columns = ("邮箱", "密码", "状态", "时间")
        self.accounts_tree = ttk.Treeview(accounts_frame, columns=columns, show="headings")
        
        # 设置列标题
        for col in columns:
            self.accounts_tree.heading(col, text=col)
            self.accounts_tree.column(col, width=100)
        
        self.accounts_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
    def setup_logging(self):
        """设置日志处理"""
        # 创建一个自定义的日志处理器，将日志发送到队列
        log_handler = QueueHandler(self.log_queue)
        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # 添加到根日志记录器
        root_logger = logging.getLogger()
        root_logger.addHandler(log_handler)
        
        # 开始周期性检查日志队列
        self.process_logs()
    
    def process_logs(self):
        """处理日志队列中的消息"""
        try:
            while True:
                record = self.log_queue.get_nowait()
                self.update_log(record)
        except queue.Empty:
            # 如果队列为空，则等待100ms后再次检查
            self.root.after(100, self.process_logs)
    
    def update_log(self, record):
        """更新日志显示"""
        self.log_text.config(state="normal")
        self.log_text.insert("end", record.getMessage() + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")
    
    def toggle_password_visibility(self):
        """切换密码显示/隐藏"""
        if self.show_password_var.get():
            self.password.config(show="")
        else:
            self.password.config(show="*")
    
    def start_registration(self):
        """开始注册流程"""
        # 获取用户输入
        prefix_start = self.prefix_start.get().strip()
        prefix_end = self.prefix_end.get().strip()
        password = self.password.get()
        
        # 验证输入
        if not prefix_start or not prefix_end or not password:
            messagebox.showerror("输入错误", "请填写所有必填字段")
            return
        
        if len(password) < 6:
            messagebox.showerror("密码错误", "密码长度不能少于6个字符")
            return
        
        # 更新UI状态
        self.start_button.config(state="disabled")
        self.pause_button.config(state="normal")
        self.continue_button.config(state="disabled")
        
        # 标记为正在注册
        self.is_registering = True
        
        # 启动注册线程
        self.registration_thread = threading.Thread(
            target=self.register_callback,
            args=(prefix_start, prefix_end, password, self)
        )
        self.registration_thread.daemon = True
        self.registration_thread.start()
    
    def pause_registration(self):
        """暂停注册流程"""
        self.is_registering = False
        self.pause_button.config(state="disabled")
        self.continue_button.config(state="normal")
        self.start_button.config(state="normal")
        self.status_label.config(text="已暂停")
    
    def continue_registration(self):
        """继续注册流程"""
        self.is_registering = True
        self.pause_button.config(state="normal")
        self.continue_button.config(state="disabled")
        self.start_button.config(state="disabled")
        self.status_label.config(text="正在注册")
    
    def show_captcha_verification(self, email):
        """显示需要完成图形验证码的提示"""
        self.current_email = email
        self.manual_verify_button.config(state="normal")
        self.status_label.config(text=f"请为 {email} 完成图形验证码")
        messagebox.showinfo("需要完成验证码", 
                           f"请在浏览器中完成图形验证码挑战。\n\n"
                           f"按照提示点击指定的字符或图像。\n\n"
                           f"完成后点击'完成验证'按钮继续。")
    
    def show_manual_verification(self, email):
        """显示需要手机验证码验证的提示"""
        self.current_email = email
        self.manual_verify_button.config(state="normal")
        self.status_label.config(text=f"请为 {email} 完成手机或二维码验证")
        messagebox.showinfo("需要手动验证", 
                           f"请在浏览器中扫描二维码或输入收到的短信验证码（如果适用）。\n\n"
                           f"完成后点击'完成验证'按钮。")
    
    def manual_verification_done(self):
        """用户完成手动验证后调用"""
        self.manual_verify_button.config(state="disabled")
        self.status_label.config(text="继续自动注册流程")
    
    def update_progress(self, current, total):
        """更新进度条"""
        progress_value = (current / total) * 100
        self.progress_var.set(progress_value)
    
    def add_account(self, email, password, status, timestamp):
        """添加一个注册成功的账号到列表"""
        self.accounts_tree.insert("", "end", values=(email, password, status, timestamp))
    
    def registration_complete(self):
        """注册流程完成"""
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled")
        self.continue_button.config(state="disabled")
        self.manual_verify_button.config(state="disabled")
        self.is_registering = False
        self.status_label.config(text="注册完成")
        messagebox.showinfo("注册完成", "所有邮箱注册流程已完成")
    
    def run(self):
        """运行GUI主循环"""
        self.root.mainloop()

# 自定义的日志处理器，将日志放入队列
class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
    
    def emit(self, record):
        self.log_queue.put(record) 