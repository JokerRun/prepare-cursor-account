import logging
import threading
import time
import sys
import os
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.gui import RegistrationGUI
from src.automation import EmailRegistration
from src.utils import setup_logging, generate_email_range, save_account
from src.config import SELECTORS

def register_emails(prefix_start, prefix_end, password, phone_number, gui):
    """注册邮箱的主函数"""
    logger = setup_logging()
    logger.info(f"开始注册邮箱: 从 {prefix_start} 到 {prefix_end}, 密码: {password}, 手机号: {phone_number}")
    
    # 生成邮箱列表
    email_list = generate_email_range(prefix_start, prefix_end)
    total_emails = len(email_list)
    logger.info(f"待注册邮箱数量: {total_emails}")
    
    # 初始化自动化模块
    registration = EmailRegistration()
    if not registration.initialize():
        logger.error("初始化自动化模块失败")
        messagebox.showerror("错误", "初始化自动化模块失败")
        gui.registration_complete()
        return
    
    # 将注册实例设置到GUI中，以便GUI可以访问其方法
    gui.registration_instance = registration
    
    # 当前处理的邮箱索引
    current_index = 0
    
    try:
        # 使用索引变量而不是for循环，以便能更灵活地控制流程
        while current_index < len(email_list):
            email = email_list[current_index]
            
            # 检查是否暂停
            while not gui.is_registering:
                time.sleep(0.5)
                # 如果程序已经关闭，则退出
                if not tk._default_root:
                    return
                
                # 在暂停状态下，仍然处理标签页切换请求
                if hasattr(gui, "switch_tab_request") and gui.switch_tab_request is not None:
                    tab_index = gui.switch_tab_request
                    registration.switch_to_tab(tab_index)
                    gui.switch_tab_request = None
            
            # 检查是否请求开始下一个账号
            if hasattr(gui, "next_account_request") and gui.next_account_request:
                gui.next_account_request = False  # 重置标志
                current_index += 1  # 直接增加索引，跳到下一个账号
                if current_index >= len(email_list):
                    logger.info("所有邮箱已处理完毕")
                    break
                email = email_list[current_index]  # 更新当前邮箱
                logger.info(f"根据用户请求，直接开始下一个邮箱 {email} 的注册")
            
            # 处理标签页切换请求
            if hasattr(gui, "switch_tab_request") and gui.switch_tab_request is not None:
                tab_index = gui.switch_tab_request
                registration.switch_to_tab(tab_index)
                gui.switch_tab_request = None
            
            logger.info(f"开始注册邮箱: {email}")
            
            # 更新GUI状态
            gui.status_label.config(text=f"正在注册: {email}")
            gui.update_progress(current_index, total_emails)
            gui.current_email = email
            
            # 为每个新邮箱创建一个新标签页（第一个邮箱除外，因为已经有一个初始标签页）
            if current_index > 0:
                logger.info(f"为邮箱 {email} 创建新标签页")
                if not registration.create_new_tab():
                    logger.error(f"为邮箱 {email} 创建新标签页失败")
                    current_index += 1
                    continue
            
            # 记录标签页与邮箱的映射关系
            current_tab_index = len(registration.pages) - 1
            if hasattr(gui, "tab_emails"):
                gui.tab_emails[current_tab_index] = email
            
            # 访问注册页面（包括选择普通注册模式）
            if not registration.navigate_to_register_page():
                logger.error(f"访问注册页面或选择注册类型失败: {email}")
                current_index += 1
                continue
            
            # 填写注册表单
            if not registration.fill_registration_form(email, password):
                logger.error(f"填写注册表单失败: {email}")
                current_index += 1
                continue
            
            # 填写手机号（如果表单中有这一项）
            if registration.page.locator(SELECTORS["phone_input"]).count() > 0:
                if not registration.fill_phone_number(phone_number):
                    logger.warning(f"填写手机号失败: {email}")
            
            # 此时已经自动填写了表单，用户需要手动完成剩余操作（如checkbox或验证码）
            # 我们等待用户的标记（手动完成或继续下一个）
            logger.info(f"已自动填写 {email} 的注册表单，等待用户完成剩余操作并标记结果")
            
            # 通知用户需要手动操作
            messagebox.showinfo(
                "需要手动操作", 
                f"已为 {email} 自动填写账号、密码和手机号。\n\n"
                f"请在浏览器中手动完成以下操作：\n"
                f"1. 勾选协议/条款复选框\n"
                f"2. 完成验证码验证（如有）\n"
                f"3. 点击注册按钮\n"
                f"4. 完成任何其他验证步骤\n\n"
                f"完成后请回到此界面点击'当前账号已人工注册成功'按钮。"
            )
            
            # 等待用户操作的循环
            while gui.is_registering:
                # 检查是否已被手动标记为完成
                if hasattr(gui, "current_account_done") and gui.current_account_done:
                    gui.current_account_done = False  # 重置标志
                    logger.info(f"用户已标记邮箱 {email} 注册成功，准备进入下一个")
                    break
                
                # 处理标签页切换请求
                if hasattr(gui, "switch_tab_request") and gui.switch_tab_request is not None:
                    tab_index = gui.switch_tab_request
                    registration.switch_to_tab(tab_index)
                    gui.switch_tab_request = None
                
                # 检查是否请求开始下一个账号
                if hasattr(gui, "next_account_request") and gui.next_account_request:
                    gui.next_account_request = False  # 重置标志
                    logger.info(f"接收到开始下一个账号的请求，准备进入下一个")
                    break  # 跳出等待循环，会进入下一个账号的注册
                
                time.sleep(0.5)
                # 如果程序已经关闭，则退出
                if not tk._default_root:
                    return
            
            # 进入下一个邮箱
            current_index += 1
    
    except Exception as e:
        logger.error(f"注册过程中发生错误: {e}")
        messagebox.showerror("错误", f"注册过程中发生错误: {e}")
    finally:
        # 清理资源
        registration.cleanup()
        
        # 完成注册
        gui.registration_complete()
        gui.registration_instance = None
        logger.info("注册流程结束")

def main():
    """主函数"""
    # 创建并启动GUI
    gui = RegistrationGUI(register_emails)
    gui.run()

if __name__ == "__main__":
    main() 