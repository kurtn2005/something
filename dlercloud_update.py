import requests
import os
import logging
import datetime

# ================= 配置区域 =================
API_KEY = "你的_API_KEY_在这里"
IP_ADDRESS = "192.168.1.100"  # 用于 Surge 托管首行
PORT = "5888"                 # 用于 Surge 托管首行

# 存储目录和日志路径
SAVE_DIR = "/usr/share/dlercloud"
LOG_FILE = "/var/log/dler_update.log"

# 软件配置映射: {软件名: [API参数名, 保存文件名, 是否为Surge]}
SOFTWARE_MAP = {
    "Surge": ["surge", "surge.conf", True],
    "Clash": ["clash", "clash.yaml", False],
    "Quantumult X": ["quantumultx", "quan.conf", False],
    "Shadowrocket": ["mu", "shadow.conf", False]
}
# ===========================================

# 初始化日志
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def update_dlercloud():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
        logging.info(f"创建目录: {SAVE_DIR}")

    for soft_name, config in SOFTWARE_MAP.items():
        param_name, file_name, is_surge = config
        
        # 构造 URL
        url = f"https://dler.cloud/api/v3/download.getFile/{API_KEY}?{param_name}=smart&lv=2"
        if is_surge:
            url += "&type=latest"
        
        file_path = os.path.join(SAVE_DIR, file_name)
        
        try:
            logging.info(f"正在更新 {soft_name}...")
            response = requests.get(url, timeout=30)
            
            # 检查 HTTP 状态码
            if response.status_code == 200:
                content = response.text
                
                # 特殊处理 Surge 首行
                if is_surge:
                    lines = content.splitlines()
                    managed_header = f"#!MANAGED-CONFIG http://{IP_ADDRESS}:{PORT}/surge.conf interval=86400"
                    if lines:
                        lines[0] = managed_header
                    else:
                        lines.append(managed_header)
                    content = "\n".join(lines)
                    logging.info("Surge 配置文件首行修改成功。")
                
                # 写入文件
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                logging.info(f"{soft_name} 更新成功，保存在: {file_path}")
            else:
                logging.error(f"{soft_name} 更新失败，错误码: {response.status_code}")
                
        except Exception as e:
            logging.error(f"{soft_name} 更新时发生异常: {str(e)}")

if __name__ == "__main__":
    update_dlercloud()
