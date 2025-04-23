import csv
import logging
import os
import sys
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_logging():
    """设置日志系统"""
    log_dir = "./data/logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = f"{log_dir}/registration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("163_register")

def generate_email_range(prefix_start, prefix_end, domain="@163.com"):
    """生成指定范围的邮箱列表"""
    # 提取数字部分
    start_num = int(''.join(filter(str.isdigit, prefix_start)))
    end_num = int(''.join(filter(str.isdigit, prefix_end)))
    
    # 提取前缀字母部分
    alpha_part = ''.join(filter(str.isalpha, prefix_start))
    
    # 生成邮箱列表
    emails = []
    for i in range(start_num, end_num + 1):
        # 保持相同的数字长度格式（如001, 002等）
        num_str = str(i).zfill(len(str(start_num)))
        email = f"{alpha_part}{num_str}{domain}"
        emails.append(email)
    
    return emails

def save_account(email, password, status="success", extra_info=None):
    """保存注册成功的账号信息"""
    data_file = "./data/registered_accounts.csv"
    backup_file = "./data/registered_accounts_backup.csv"
    file_exists = os.path.isfile(data_file)
    
    # 创建data目录（如果不存在）
    os.makedirs(os.path.dirname(data_file), exist_ok=True)
    
    try:
        with open(data_file, mode='a', newline='') as file:
            fieldnames = ['email', 'password', 'status', 'timestamp', 'extra_info']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            # 写入当前账号
            row_data = {
                'email': email,
                'password': password,
                'status': status,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'extra_info': extra_info or ''
            }
            writer.writerow(row_data)
            
            # 立即刷新文件到磁盘
            file.flush()
            os.fsync(file.fileno())
        
        # 创建备份文件
        if os.path.isfile(data_file):
            import shutil
            shutil.copy2(data_file, backup_file)
            
        print(f"账号 {email} 的数据已成功保存并备份")
        return True
    except Exception as e:
        print(f"保存账号 {email} 数据时出错: {e}")
        return False 