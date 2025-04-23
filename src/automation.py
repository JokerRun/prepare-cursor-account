from playwright.sync_api import sync_playwright, TimeoutError
import time
import logging
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import REGISTER_URL, SELECTORS, TIMEOUTS, CONFIG

class EmailRegistration:
    """邮箱注册自动化类"""
    
    def __init__(self):
        self.logger = logging.getLogger("163_register.automation")
        self.playwright = None
        self.browser = None
        self.context = None # 添加浏览器上下文
        self.page = None
        self.captcha_handled = False
        self.pages = []  # 存储所有创建的标签页
    
    def initialize(self):
        """初始化Playwright和浏览器"""
        try:
            self.playwright = sync_playwright().start()
            # 使用常见的 User Agent 字符串
            user_agent_string = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            self.logger.info(f"Using User-Agent: {user_agent_string}")
            
            # 启动Chrome浏览器，不在此处设置UA
            self.browser = self.playwright.chromium.launch(
                headless=CONFIG["headless"],
                slow_mo=CONFIG["slow_mo"],
                channel="chrome"  # 使用Chrome而非Chromium
            )
            
            # 创建带有指定 User Agent 的浏览器上下文
            self.context = self.browser.new_context(user_agent=user_agent_string)
            
            # 从上下文中创建页面
            self.page = self.context.new_page()
            self.page.set_default_timeout(TIMEOUTS["page_load"])
            
            # 将初始页面添加到页面列表
            self.pages.append(self.page)
            
            self.logger.info("Chrome浏览器和上下文已初始化") # 更新日志消息
            return True
        except Exception as e:
            self.logger.error(f"初始化Chrome浏览器失败: {e}")
            self.cleanup()
            return False
    
    def navigate_to_register_page(self):
        """导航到注册页面"""
        retry_count = 0
        max_retries = CONFIG["retry_times"]
        
        while retry_count < max_retries:
            try:
                self.logger.info(f"正在访问注册页面 (尝试 {retry_count + 1}/{max_retries}): {REGISTER_URL}")
                self.page.goto(REGISTER_URL, timeout=TIMEOUTS["page_load"])
                
                # 等待页面加载
                self.logger.info("等待页面加载...")
                self.page.wait_for_load_state("networkidle", timeout=TIMEOUTS["navigation"])
                
                self.logger.info("注册页面加载完成")
                
                # 选择普通注册模式
                if self.select_register_type():
                    return True
                else:
                    self.logger.error("选择注册类型失败")
                    return False
                
            except Exception as e:
                retry_count += 1
                self.logger.error(f"访问注册页面失败 (尝试 {retry_count}/{max_retries}): {e}")
                
                if retry_count < max_retries:
                    wait_time = 2 * retry_count  # 指数退避，单位：秒
                    self.logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    return False
    
    def select_register_type(self):
        """选择注册类型 - 普通注册"""
        try:
            self.logger.info("选择'普通注册'选项")
            
            # 等待选项可见并点击
            self.page.click(SELECTORS["normal_register_option"])
            time.sleep(1)  # 等待注册类型切换
            
            self.logger.info("已选择'普通注册'选项")
            return True
        except Exception as e:
            self.logger.error(f"选择注册类型失败: {e}")
            return False
    
    def fill_registration_form(self, email, password):
        """填写注册表单"""
        try:
            # 提取用户名（邮箱前缀）
            username = email.split('@')[0]
            
            self.logger.info(f"开始填写注册表单，用户名: {username}")
            
            # 填写用户名
            self.logger.info("Attempting to fill username...")
            self.page.fill(SELECTORS["username_input"], username)
            self.logger.info(f"Filled username: {username}")
            
            # 填写密码
            self.logger.info("Attempting to fill password...")
            self.page.fill(SELECTORS["password_input"], password)
            self.logger.info("Filled password")
            
            # 同意服务条款
            self.logger.info("Attempting to locate agree checkbox...")
            agree_checkbox_locator = self.page.locator(SELECTORS["agree_checkbox"])
            if agree_checkbox_locator.count() > 0:
                self.logger.info("Located agree checkbox")
                self.logger.info("Attempting to check agree checkbox...")
                agree_checkbox_locator.check()
                self.logger.info("Checked agree checkbox")
            else:
                self.logger.warning("Agree checkbox not found or not required.")
            
            self.logger.info("注册表单填写完成")
            return True
        except Exception as e:
            self.logger.error(f"填写注册表单失败: {e}")
            return False
    
    def fill_phone_number(self, phone_number=None):
        """填写手机号"""
        try:
            if phone_number is None:
                phone_number = CONFIG["default_phone"]
                
            self.logger.info(f"自动填写手机号: {phone_number}")
            
            # 检查手机号输入框是否存在
            if self.page.locator(SELECTORS["phone_input"]).count() > 0:
                # 填写手机号
                self.page.fill(SELECTORS["phone_input"], phone_number)
                self.logger.info("已填写手机号")
                
                # 点击发送验证码按钮
                if self.page.locator(SELECTORS["send_code_button"]).count() > 0:
                    self.logger.info("点击发送验证码按钮")
                    self.page.click(SELECTORS["send_code_button"])
                    self.logger.info("验证码已发送，请手动输入收到的验证码")
                    return True
                else:
                    self.logger.error("找不到发送验证码按钮")
                    return False
            else:
                self.logger.error("找不到手机号输入框")
                return False
        except Exception as e:
            self.logger.error(f"填写手机号失败: {e}")
            return False
    
    def is_captcha_present(self):
        """检测是否有验证码"""
        try:
            # 先检查验证码框架是否存在
            captcha_present = self.page.locator(SELECTORS["captcha_frame"]).count() > 0
            if captcha_present:
                self.logger.info("检测到验证码")
                return True
            
            # 也可能已经在验证码界面内
            captcha_loading = self.page.locator(SELECTORS["captcha_loading"]).count() > 0
            if captcha_loading:
                self.logger.info("检测到验证码加载中")
                return True
                
            return False
        except Exception as e:
            self.logger.error(f"检测验证码失败: {e}")
            return False
    
    def wait_for_captcha_completion(self, timeout=TIMEOUTS["captcha"]):
        """等待验证码完成"""
        self.logger.info("等待用户完成验证码验证...")
        self.captcha_handled = False
        
        start_time = time.time()
        while time.time() - start_time < timeout / 1000:  # 转换为秒
            # 检查验证码框是否消失
            if self.page.locator(SELECTORS["captcha_frame"]).count() == 0:
                self.logger.info("验证码验证已完成")
                self.captcha_handled = True
                return True
                
            # 检查验证码加载文本是否消失
            if self.page.locator(SELECTORS["captcha_loading"]).count() == 0:
                self.logger.info("验证码验证进行中")
                
            # 短暂等待，减少CPU使用
            time.sleep(1)
        
        self.logger.error("验证码验证超时")
        return False
    
    def submit_form(self):
        """提交表单"""
        try:
            # 检查是否有验证码需要处理
            if self.is_captcha_present() and not self.captcha_handled:
                self.logger.info("检测到验证码，等待用户完成验证")
                if not self.wait_for_captcha_completion():
                    self.logger.error("验证码验证未完成")
                    return False
            
            self.logger.info("点击立即注册按钮")
            self.page.click(SELECTORS["register_button"])
            self.page.wait_for_load_state("networkidle")
            
            # 再次检查验证码
            if self.is_captcha_present():
                self.logger.info("提交后检测到新的验证码，等待用户完成验证")
                if not self.wait_for_captcha_completion():
                    self.logger.error("验证码验证未完成")
                    return False
            
            return True
        except Exception as e:
            self.logger.error(f"提交表单失败: {e}")
            return False
    
    def is_phone_verification_required(self):
        """检查是否需要手机验证"""
        try:
            # 检查是否存在手机验证页面元素
            is_visible = (
                self.page.locator(SELECTORS["phone_verify_page"]).count() > 0 or 
                self.page.locator(SELECTORS["verification_code_input"]).count() > 0
            )
            
            if is_visible:
                self.logger.info("检测到需要手机验证")
            return is_visible
        except Exception as e:
            self.logger.error(f"检查手机验证失败: {e}")
            return False
    
    def wait_for_manual_verification(self):
        """等待手动完成验证"""
        # 这个方法将被GUI调用，在这里我们只提供接口
        self.logger.info("等待手动完成验证")
        pass
    
    def is_registration_successful(self):
        """检查注册是否成功"""
        try:
            is_success = self.page.locator(SELECTORS["register_success"]).count() > 0
            if is_success:
                self.logger.info("注册成功")
            return is_success
        except Exception as e:
            self.logger.error(f"检查注册结果失败: {e}")
            return False
    
    def create_new_tab(self):
        """创建新标签页并切换到该标签页"""
        try:
            self.logger.info("正在创建新标签页...")
            # 从浏览器上下文创建新页面
            new_page = self.context.new_page()
            new_page.set_default_timeout(TIMEOUTS["page_load"])
            
            # 将新页面添加到页面列表
            self.pages.append(new_page)
            
            # 切换到新页面
            self.page = new_page
            
            self.logger.info("已创建新标签页并切换")
            return True
        except Exception as e:
            self.logger.error(f"创建新标签页失败: {e}")
            return False
    
    def switch_to_tab(self, index):
        """切换到指定索引的标签页"""
        try:
            if not self.pages or index >= len(self.pages):
                self.logger.error(f"无法切换到标签页 {index}，索引无效")
                return False
            
            self.page = self.pages[index]
            self.logger.info(f"已切换到标签页 {index}")
            return True
        except Exception as e:
            self.logger.error(f"切换标签页失败: {e}")
            return False
    
    def get_tab_count(self):
        """获取当前标签页数量"""
        return len(self.pages)
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.browser:
                self.logger.info("关闭浏览器...")
                self.browser.close()
                
            if self.playwright:
                self.logger.info("关闭Playwright...")
                self.playwright.stop()
            
            # 清空页面列表
            self.pages = []
            self.page = None
            self.browser = None
            self.context = None
            self.playwright = None
            
            self.logger.info("资源已清理")
        except Exception as e:
            self.logger.error(f"清理资源时出错: {e}") 