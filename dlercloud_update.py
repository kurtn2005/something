import requests
import os
import logging
from urllib.parse import urlparse

# ================= 配置区域 =================
API_KEY = "你的_API_KEY_在这里"
# IP_ADDRESS 现在支持手动填入，或者填入 "auto" 来自动获取公网 IP
IP_ADDRESS = "auto"  
PORT = "80"

# --- URL 组成部分配置 ---
BASE_ENDPOINT = "dler.cloud/api/v3/download.getFile"
LV_PARAM = "1|2|3"
FILE_EXT = ".mp4"

SAVE_DIR = "/usr/share/dlercloud"
LOG_FILE = "/var/log/dler_update.log"

SOFTWARE_MAP = {
    "Surge": ["surge", "surge.conf", True],
    "Clash": ["clash", "clash.yaml", False],
    "Quantumult X": ["quantumultx", "quan.conf", False],
    "Shadowrocket": ["mu", "shadow.conf", False]
}
# ===========================================

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_public_ip():
    """获取当前服务器的公网 IP"""
    # 备选的 IP 获取服务，增加脚本的健壮性
    services = [
        'https://api.ipify.org',
        'https://ifconfig.me/ip',
        'https://ident.me',
        'http://ip.42.pl/raw'
    ]
    for service in services:
        try:
            response = requests.get(service, timeout=10)
            if response.status_code == 200:
                ip = response.text.strip()
                logging.info(f"成功获取公网 IP: {ip} (来源: {service})")
                return ip
        except Exception as e:
            logging.warn(f"无法从 {service} 获取 IP: {e}")
            continue
    return None

def update_dlercloud():
    global IP_ADDRESS
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    # 如果配置为 auto，则尝试获取公网 IP
    if IP_ADDRESS.lower() == "auto":
        fetched_ip = get_public_ip()
        if fetched_ip:
            IP_ADDRESS = fetched_ip
        else:
            logging.error("无法获取公网 IP，脚本停止运行")
            return

    for soft_name, config in SOFTWARE_MAP.items():
        param, file_name, is_surge = config
        
        # 构造 URL
        if is_surge:
            url = f"https://{BASE_ENDPOINT}/{API_KEY}?{param}=smart&lv={LV_PARAM}&type=latest{FILE_EXT}"
        else:
            url = f"https://{BASE_ENDPOINT}/{API_KEY}?{param}=smart&lv={LV_PARAM}{FILE_EXT}"
        
        file_path = os.path.join(SAVE_DIR, file_name)
        
        try:
            response = requests.get(url, timeout=30)
            status_code = response.status_code
            
            if status_code == 200:
                content = response.text
                
                if is_surge:
                    lines = content.splitlines()
                    # 关键修改：此时 IP_ADDRESS 已经是动态获取到的公网 IP
                    managed_header = f"#!MANAGED-CONFIG http://{IP_ADDRESS}:{PORT}/surge.conf interval=86400"
                    
                    if lines and lines[0].startswith("#"):
                        lines[0] = managed_header
                        surge_mod_msg = "成功替换首行内容"
                    else:
                        lines.insert(0, managed_header)
                        surge_mod_msg = "首行非注释，已在顶部插入托管行"
                    
                    content = "\n".join(lines)
                    logging.info(f"Surge 特殊处理: {surge_mod_msg} (使用 IP: {IP_ADDRESS})")
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                logging.info(f"{soft_name} 更新状态: 成功 | 保存路径: {file_path}")
            else:
                logging.error(f"{soft_name} 更新状态: 失败 | 错误码: {status_code} | URL: {url}")
                
        except Exception as e:
            logging.error(f"{soft_name} 更新状态: 异常 | 错误信息: {str(e)}")

if __name__ == "__main__":
    update_dlercloud()
