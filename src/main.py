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

def register_emails(prefix_start, prefix_end, password, gui):
    """注册邮箱的主函数"""
    logger = setup_logging()
    logger.info(f"开始注册邮箱: 从 {prefix_start} 到 {prefix_end}")
    
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
    
    try:
        for i, email in enumerate(email_list):
            # 检查是否暂停
            while not gui.is_registering:
                time.sleep(0.5)
                # 如果程序已经关闭，则退出
                if not tk._default_root:
                    return
            
            logger.info(f"开始注册邮箱: {email}")
            
            # 更新GUI状态
            gui.status_label.config(text=f"正在注册: {email}")
            gui.update_progress(i, total_emails)
            gui.current_email = email
            
            # 访问注册页面（包括选择普通注册模式）
            if not registration.navigate_to_register_page():
                logger.error(f"访问注册页面或选择注册类型失败: {email}")
                continue
            
            # 填写注册表单
            if not registration.fill_registration_form(email, password):
                logger.error(f"填写注册表单失败: {email}")
                continue
            
            # 填写手机号（如果表单中有这一项）
            if registration.page.locator(SELECTORS["phone_input"]).count() > 0:
                if not registration.fill_phone_number():
                    logger.warning(f"填写手机号失败: {email}")
            
            # 检查是否有验证码需要处理
            if registration.is_captcha_present():
                logger.info("检测到需要图形验证码")
                
                # 提示用户输入验证码
                gui.show_captcha_verification(email)
                
                # 等待用户完成验证码输入
                waiting_for_captcha = True
                while waiting_for_captcha and gui.is_registering:
                    # 检查验证码是否已经完成
                    if gui.manual_verify_button["state"] == "disabled" or registration.captcha_handled:
                        waiting_for_captcha = False
                        break
                    
                    time.sleep(0.5)
                    # 如果程序已经关闭，则退出
                    if not tk._default_root:
                        return
            
            # 提交表单
            if not registration.submit_form():
                logger.error(f"提交注册表单失败: {email}")
                continue
            
            # 检查是否需要手机验证码验证
            if registration.is_phone_verification_required():
                logger.info(f"需要手机验证码验证: {email}")
                
                # 提示用户输入手机验证码
                gui.show_manual_verification(email)
                
                # 等待用户完成验证码输入和验证
                while gui.manual_verify_button["state"] != "disabled" and gui.is_registering:
                    time.sleep(0.5)
                    # 如果程序已经关闭，则退出
                    if not tk._default_root:
                        return
            
            # 检查注册是否成功
            if registration.is_registration_successful():
                logger.info(f"注册成功: {email}")
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 保存账号信息
                save_account(email, password, "success")
                
                # 更新GUI显示
                gui.add_account(email, password, "成功", timestamp)
            else:
                logger.warning(f"注册失败或状态未知: {email}")
                save_account(email, password, "failed", "可能的原因: 验证未完成或其他错误")
            
            # 暂停一下，避免过快操作
            time.sleep(1)
    
    except Exception as e:
        logger.error(f"注册过程中发生错误: {e}")
        messagebox.showerror("错误", f"注册过程中发生错误: {e}")
    finally:
        # 清理资源
        registration.cleanup()
        
        # 完成注册
        gui.registration_complete()
        logger.info("注册流程结束")

def main():
    """主函数"""
    # 创建并启动GUI
    gui = RegistrationGUI(register_emails)
    gui.run()

if __name__ == "__main__":
    main() 