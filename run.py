#!/usr/bin/env python3
"""
163邮箱自动注册工具启动脚本
"""
import os
import sys
import argparse

# 添加src目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

def main():
    """主函数，解析命令行参数并启动相应功能"""
    parser = argparse.ArgumentParser(description="163邮箱自动注册工具")
    parser.add_argument("-e", "--email", help="要注册的单个邮箱前缀，如'cursorjr002'")
    parser.add_argument("-p", "--password", help="注册密码")
    parser.add_argument("-m", "--phone", help="手机号码")
    
    args = parser.parse_args()
    
    # 如果提供了邮箱参数，则使用命令行模式
    if args.email:
        # 导入需要的模块
        from src.automation import EmailRegistration
        from src.config import CONFIG
        import logging
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger("163_register")
        
        # 设置参数
        email_prefix = args.email
        password = args.password or "Bitezhi666"
        phone = args.phone or CONFIG["default_phone"]
        
        logger.info(f"准备注册邮箱: {email_prefix}@163.com，密码: {password}, 手机号: {phone}")
        
        # 执行注册
        register_single_email(email_prefix, password, phone, logger)
    else:
        # 使用GUI模式
        from src.main import main as gui_main
        gui_main()

def register_single_email(email_prefix, password, phone, logger):
    """注册单个邮箱"""
    from src.automation import EmailRegistration
    from src.utils import save_account
    from datetime import datetime
    import time
    
    # 完整邮箱
    email = f"{email_prefix}@163.com"
    
    # 初始化自动化模块
    registration = EmailRegistration()
    if not registration.initialize():
        logger.error("初始化自动化模块失败")
        return False
    
    try:
        # 访问注册页面
        if not registration.navigate_to_register_page():
            logger.error("访问注册页面或选择注册类型失败")
            return False
        
        # 填写注册表单
        if not registration.fill_registration_form(email, password):
            logger.error("填写注册表单失败")
            return False
        
        # 填写手机号
        if not registration.fill_phone_number(phone):
            logger.warning("填写手机号失败")
        
        # 检查是否有验证码
        if registration.is_captcha_present():
            logger.info("检测到需要图形验证码，请在浏览器中完成验证码")
            
            # 等待用户手动完成验证码
            if not registration.wait_for_captcha_completion():
                logger.error("验证码验证未完成")
                return False
        
        # 提交表单
        if not registration.submit_form():
            logger.error("提交注册表单失败")
            return False
        
        # 检查是否需要手机验证
        if registration.is_phone_verification_required():
            logger.info(f"需要手机验证（可能是短信或二维码），请在浏览器中操作")
            
            # 等待用户手动输入验证码或扫描二维码
            input("请在浏览器中扫描二维码或完成短信验证（如果适用），完成后按Enter键继续...")
        
        # 检查注册是否成功
        if registration.is_registration_successful():
            logger.info(f"注册成功: {email}")
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 保存账号信息
            save_account(email, password, "success")
            return True
        else:
            logger.warning(f"注册失败或状态未知: {email}")
            save_account(email, password, "failed", "可能的原因: 验证未完成或其他错误")
            return False
            
    except Exception as e:
        logger.error(f"注册过程中发生错误: {e}")
        return False
    finally:
        # 给用户查看结果的时间
        logger.info("注册流程结束，5秒后关闭浏览器...")
        time.sleep(5)
        
        # 清理资源
        registration.cleanup()

if __name__ == "__main__":
    main() 