import requests
import os
import logging
from urllib.parse import urlparse

# ================= 配置区域 =================
API_KEY = "你的_API_KEY_在这里"
IP_ADDRESS = "192.168.1.100"  # Surge 托管地址
PORT = "5888"

SAVE_DIR = "/usr/share/dlercloud"
LOG_FILE = "/var/log/dler_update.log"

# {软件名: [参数名, 文件名, 是否Surge]}
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

def update_dlercloud():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    for soft_name, config in SOFTWARE_MAP.items():
        param, file_name, is_surge = config
        
        # 构造基础 URL，结尾强制加 .png
        if is_surge:
            # Surge 特殊处理：增加 type=latest
            url = f"https://dler.cloud/api/v3/download.getFile/{API_KEY}?{param}=smart&lv=2&type=latest.png"
        else:
            url = f"https://dler.cloud/api/v3/download.getFile/{API_KEY}?{param}=smart&lv=2.png"
        
        file_path = os.path.join(SAVE_DIR, file_name)
        
        try:
            response = requests.get(url, timeout=30)
            status_code = response.status_code
            
            if status_code == 200:
                content = response.text
                
                # 修改 Surge 首行逻辑
                if is_surge:
                    lines = content.splitlines()
                    managed_header = f"#!MANAGED-CONFIG http://{IP_ADDRESS}:{PORT}/surge.conf interval=86400"
                    
                    if lines and lines[0].startswith("#"):
                        lines[0] = managed_header
                        surge_mod_msg = "成功替换首行内容"
                    else:
                        lines.insert(0, managed_header)
                        surge_mod_msg = "首行非注释，已在顶部插入托管行"
                    
                    content = "\n".join(lines)
                    logging.info(f"Surge 特殊处理: {surge_mod_msg}")
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                logging.info(f"{soft_name} 更新状态: 成功 | 保存路径: {file_path}")
            else:
                logging.error(f"{soft_name} 更新状态: 失败 | 错误码: {status_code} | URL: {url}")
                
        except Exception as e:
            logging.error(f"{soft_name} 更新状态: 异常 | 错误信息: {str(e)}")

if __name__ == "__main__":
    update_dlercloud()
