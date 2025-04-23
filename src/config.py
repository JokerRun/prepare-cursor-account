# 163邮箱注册页面的URL
REGISTER_URL = "https://mail.163.com/register/#/normal"

# 页面元素选择器
SELECTORS = {
    # 注册类型选择
    "normal_register_option": "text=普通注册",  # 普通注册选项
    
    # 表单填写
    "username_input": "input[placeholder='邮箱地址']",  # 邮箱地址输入框 (基于 placeholder)
    "password_input": "input[type=password]",  # 密码输入框
    "phone_input": "input[placeholder='手机号码']",  # 手机号输入框
    "agree_checkbox": "input.j-agree[type=checkbox]",  # 同意条款复选框 (更精确)
    "register_button": "text=立即注册",  # 立即注册按钮
    
    # 验证码相关
    "captcha_frame": "iframe[name*='captcha']",  # 验证码iframe
    "captcha_loading": "text=加载中...",  # 验证码加载提示
    "captcha_close_button": "button:has-text('关闭')",  # 验证码关闭按钮
    
    # 手机验证相关
    "phone_verify_page": ".verify-panel",
    "send_code_button": "text=发送验证码",  # 发送验证码按钮
    "verification_code_input": "input[placeholder='验证码']",  # 验证码输入框
    "verify_button": "text=验证",  # 验证按钮
    
    # 结果确认
    "register_success": ".register-success"  # 注册成功提示
}

# 超时设置（毫秒）
TIMEOUTS = {
    "page_load": 60000,   # 60秒
    "element_visible": 10000,  # 10秒
    "navigation": 60000,   # 60秒
    "captcha": 120000      # 验证码等待超时，2分钟
}

# 其他配置
CONFIG = {
    "headless": False,  # 是否隐藏浏览器界面
    "slow_mo": 100,     # 操作间隔时间（毫秒）
    "retry_times": 3,   # 重试次数
    "data_file": "./data/registered_accounts.csv",  # 账号保存路径
    "default_phone": "19921680956"  # 默认手机号
} 