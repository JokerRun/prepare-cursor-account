import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import logging
import queue
import sys
import os
from datetime import datetime
import csv

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils import save_account

class RegistrationGUI:
    """注册工具GUI界面"""
    
    def __init__(self, register_callback):
        self.logger = logging.getLogger("163_register.gui")
        self.register_callback = register_callback
        self.log_queue = queue.Queue()
        self.is_registering = False
        self.current_email = None
        self.next_account_request = False  # 新增：请求开始下一个账号注册的标志
        
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
        self.prefix_start.insert(0, "cursorjr5")
        
        # 邮箱前缀结束
        ttk.Label(settings_frame, text="邮箱前缀结束:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.prefix_end = ttk.Entry(settings_frame, width=20)
        self.prefix_end.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.prefix_end.insert(0, "cursorjr10")
        
        # 统一密码
        ttk.Label(settings_frame, text="统一密码:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.password = ttk.Entry(settings_frame, width=20, show="*")
        self.password.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.password.insert(0, "Bitezhi666")
        
        # 显示密码复选框
        self.show_password_var = tk.BooleanVar()
        self.show_password_check = ttk.Checkbutton(
            settings_frame, 
            text="显示密码", 
            variable=self.show_password_var,
            command=self.toggle_password_visibility
        )
        self.show_password_check.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        
        # 手机号码
        ttk.Label(settings_frame, text="手机号码:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.phone_number = ttk.Entry(settings_frame, width=20)
        self.phone_number.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.phone_number.insert(0, "19921680956")
        
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
        
        # 标签页控制区域
        tabs_frame = ttk.Frame(self.root)
        tabs_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(tabs_frame, text="标签页:").pack(side="left", padx=5, pady=5)
        
        # 标签页下拉框
        self.tabs_var = tk.StringVar()
        self.tabs_combobox = ttk.Combobox(tabs_frame, textvariable=self.tabs_var, state="readonly", width=40)
        self.tabs_combobox.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        self.tabs_combobox["values"] = ["无标签页"]
        self.tabs_combobox.current(0)
        
        # 切换标签页按钮
        self.switch_tab_button = ttk.Button(tabs_frame, text="切换到所选标签页", command=self.switch_tab, state="disabled")
        self.switch_tab_button.pack(side="left", padx=5, pady=5)
        
        # 刷新标签页列表按钮
        self.refresh_tabs_button = ttk.Button(tabs_frame, text="刷新标签页列表", command=self.refresh_tabs, state="disabled")
        self.refresh_tabs_button.pack(side="left", padx=5, pady=5)
        
        # 手动标记成功按钮
        self.mark_success_button = ttk.Button(
            tabs_frame, 
            text="当前账号已人工注册成功", 
            command=self.mark_current_success, 
            state="disabled"
        )
        self.mark_success_button.pack(side="left", padx=5, pady=5)
        
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
        
        # 账号列表控制区域
        accounts_ctrl_frame = ttk.Frame(accounts_frame)
        accounts_ctrl_frame.pack(fill="x", padx=5, pady=5)
        
        # 导出按钮
        self.export_button = ttk.Button(accounts_ctrl_frame, text="导出已注册账号", command=self.export_accounts)
        self.export_button.pack(side="right", padx=5)
        
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
        phone_number = self.phone_number.get().strip()
        
        # 验证输入
        if not prefix_start or not prefix_end or not password or not phone_number:
            messagebox.showerror("输入错误", "请填写所有必填字段")
            return
        
        if len(password) < 6:
            messagebox.showerror("密码错误", "密码长度不能少于6个字符")
            return
        
        if not phone_number.isdigit() or len(phone_number) != 11:
            messagebox.showerror("手机号错误", "请输入有效的11位手机号码")
            return
        
        # 更新UI状态
        self.start_button.config(state="disabled")
        self.pause_button.config(state="normal")
        self.continue_button.config(state="disabled")
        self.switch_tab_button.config(state="normal")
        self.refresh_tabs_button.config(state="normal")
        self.mark_success_button.config(state="normal")
        self.manual_verify_button.config(state="normal")  # 允许用户点击完成验证按钮
        
        # 初始化标签页邮箱映射
        self.tab_emails = {}
        self.switch_tab_request = None
        self.registration_instance = None
        self.current_account_done = False
        self.next_account_request = False
        
        # 标记为正在注册
        self.is_registering = True
        
        # 启动注册线程
        self.registration_thread = threading.Thread(
            target=self.register_callback,
            args=(prefix_start, prefix_end, password, phone_number, self)
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
        # 如果当前账号已完成，标记为继续下一个账号
        if hasattr(self, "current_account_done") and self.current_account_done:
            self.current_account_done = False
            self.status_label.config(text="继续下一个号码注册")
        
        self.is_registering = True
        self.pause_button.config(state="normal")
        self.continue_button.config(state="disabled")
        self.start_button.config(state="disabled")
        self.status_label.config(text="正在注册")
    
    def show_captcha_verification(self, email):
        """显示需要完成图形验证码的提示"""
        self.current_email = email
        self.manual_verify_button.config(state="normal")
        self.mark_success_button.config(state="normal")
        self.status_label.config(text=f"请为 {email} 完成图形验证码")
        messagebox.showinfo("需要完成验证码", 
                           f"请在浏览器中完成图形验证码挑战。\n\n"
                           f"按照提示点击指定的字符或图像。\n\n"
                           f"完成后点击'完成验证'按钮继续。")
    
    def show_manual_verification(self, email):
        """显示需要手机验证码验证的提示"""
        self.current_email = email
        self.manual_verify_button.config(state="normal")
        self.mark_success_button.config(state="normal")
        self.status_label.config(text=f"请为 {email} 完成手机或二维码验证")
        messagebox.showinfo("需要手动验证", 
                           f"请在浏览器中扫描二维码或输入收到的短信验证码（如果适用）。\n\n"
                           f"完成后点击'完成验证'按钮继续。\n\n"
                           f"如果已经知道注册成功，可点击'当前账号已人工注册成功'按钮。")
    
    def manual_verification_done(self):
        """用户完成手动验证后调用"""
        self.manual_verify_button.config(state="disabled")
        self.status_label.config(text=f"已完成 {self.current_email} 的验证，等待自动进入下一步...")
        
        # 由于我们现在由用户全程手动操作，当用户点击完成验证按钮时，
        # 我们应当提示用户继续完成剩余注册流程，然后在完成后点击"当前账号已人工注册成功"按钮
        messagebox.showinfo("验证已完成", 
                           f"验证已标记为完成。请继续完成剩余的注册步骤，包括勾选协议并点击注册等。\n\n"
                           f"注册完成后请回到此界面点击'当前账号已人工注册成功'按钮。")
    
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
        self.switch_tab_button.config(state="disabled")
        self.refresh_tabs_button.config(state="disabled")
        self.mark_success_button.config(state="disabled")
        self.is_registering = False
        self.status_label.config(text="注册完成")
        messagebox.showinfo("注册完成", "所有邮箱注册流程已完成")
    
    def run(self):
        """运行GUI主循环"""
        self.root.mainloop()

    def switch_tab(self):
        """切换到选定的标签页"""
        if not hasattr(self, "registration_instance") or self.registration_instance is None:
            return
            
        selected_index = self.tabs_combobox.current()
        if selected_index < 0:
            return
            
        # 通过主线程发送请求到注册线程
        self.switch_tab_request = selected_index
        
    def refresh_tabs(self):
        """刷新标签页列表"""
        if not hasattr(self, "registration_instance") or self.registration_instance is None:
            self.tabs_combobox["values"] = ["无标签页"]
            self.tabs_combobox.current(0)
            return
            
        # 获取当前标签页数量
        tab_count = self.registration_instance.get_tab_count()
        if tab_count == 0:
            self.tabs_combobox["values"] = ["无标签页"]
            self.tabs_combobox.current(0)
            return
            
        # 更新标签页列表
        values = [f"标签页 {i+1}: {self.tab_emails.get(i, '未知邮箱')}" for i in range(tab_count)]
        self.tabs_combobox["values"] = values
        
        # 保持当前选择（如果可能）
        current = self.tabs_combobox.current()
        if current >= 0 and current < tab_count:
            self.tabs_combobox.current(current)
        else:
            self.tabs_combobox.current(0)

    def mark_current_success(self):
        """标记当前账号已成功注册并立即开始下一个账号注册"""
        if not self.current_email:
            return
            
        # 记录成功状态
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        password = self.password.get()
        
        # 保存账号信息
        save_result = save_account(self.current_email, password, "success")
        
        # 更新GUI显示
        self.add_account(self.current_email, password, "手动标记成功", timestamp)
        
        # 提供保存状态反馈
        if save_result:
            self.status_label.config(text=f"{self.current_email} 已标记为成功注册并保存，正在准备下一个...")
            self.logger.info(f"邮箱 {self.current_email} 已成功保存到数据文件")
        else:
            self.status_label.config(text=f"{self.current_email} 已标记为成功注册，但保存数据时出错！正在准备下一个...")
            self.logger.error(f"邮箱 {self.current_email} 保存到数据文件时出错")
            messagebox.showwarning("数据保存警告", f"邮箱 {self.current_email} 标记成功，但保存数据时出错，请检查日志")
        
        # 禁用手动验证按钮
        self.manual_verify_button.config(state="disabled")
        
        # 设置标志，通知注册线程开始下一个账号
        self.current_account_done = True
        self.next_account_request = True  # 设置标志，请求注册下一个账号
        
        # 确保注册流程处于运行状态
        self.is_registering = True
        self.pause_button.config(state="normal")
        self.continue_button.config(state="disabled")
        self.start_button.config(state="disabled")

    def export_accounts(self):
        """导出当前已注册账号列表"""
        # 确认导出
        if not messagebox.askyesno("确认导出", "是否确认导出当前已注册的账号列表？"):
            return
            
        # 获取所有显示的账号数据
        accounts = []
        for item_id in self.accounts_tree.get_children():
            values = self.accounts_tree.item(item_id, "values")
            accounts.append({
                "email": values[0],
                "password": values[1],
                "status": values[2],
                "timestamp": values[3]
            })
        
        if not accounts:
            messagebox.showinfo("导出结果", "当前没有已注册的账号数据可导出")
            return
        
        # 导出到CSV文件
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        export_file = f"../data/export_{timestamp}.csv"
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(export_file), exist_ok=True)
            
            with open(export_file, mode='w', newline='') as file:
                fieldnames = ["email", "password", "status", "timestamp"]
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                for account in accounts:
                    writer.writerow(account)
            
            self.logger.info(f"已将 {len(accounts)} 个账号导出到: {export_file}")
            messagebox.showinfo("导出成功", f"已成功导出 {len(accounts)} 个账号到文件:\n{export_file}")
        except Exception as e:
            self.logger.error(f"导出账号数据失败: {e}")
            messagebox.showerror("导出失败", f"导出账号数据失败: {e}")

# 自定义的日志处理器，将日志放入队列
class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
    
    def emit(self, record):
        self.log_queue.put(record) 