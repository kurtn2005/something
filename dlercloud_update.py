import requests
import os
import logging

# ================= 配置区域 =================
DLER_API_KEY = "YOUR API KEY"
DLER_BASE_ENDPOINT = "dler.cloud/api/v3/download.getFile"
DLER_LV_PARAM = "1|2|3"
DLER_FILE_EXT = ".mp4"

MESL_URL = "https://em.mesl.cloud/ems/get?token=YOUR TOKEN"

# 证书配置
CA_PASSPHRASE = "Dler"
CA_P12 = "MIIDGgIBAzCCAuAGCSqGSIb3DQEHAaCCAtEEggLNMIICyTCCAb8GCSqGSIb3DQEHBqCCAbAwggGsAgEAMIIBpQYJKoZIhvcNAQcBMBwGCiqGSIb3DQEMAQYwDgQI5e4W8st2yMMCAggAgIIBeBDhcB5oCpEtPyamF2QSSZMoKnIQ9idB7/spS4BgYMq/zDT8c7SDSKM746+4D98feqkJmAYFUWlXtXOHwSR8QlFad9dTYw4SulHDpDAVr/+da6iCX+LeQuducormCI6xVcmpfZ8qvHWzpfHy5mrKxkuyj5OHlehvYOedDZ9P9s9ME2qZFsffKC4kk398QPjoBMLCb73m7QcFdzdus7NuVAd/kYZRww7ODcXcb5a45Yv4NeRwRjnVT8eCgjGXjJXQgJPAtyAWPLW+o1uS132Qdkmg+8EjwuxL/lOu3rLKh0gWWUFHcxv2rg4OcezyoZuv70zs3A8Ju3wmQ6oZuakeRuRyKu6+9BtgOqxnoBwvTMCI4saY8E318DWZjBOzg9N2vPOhKDeoh8ES9TAbRlcp5Bnp5TWrPhae+XeHlHde5KCr3kjB15/DAhrlh7+ht18I/p1shnRKAd1tH6p62to51j9mSHNxOFFCbBPiFqBSnPmuV2SSOOYHcjUwggECBgkqhkiG9w0BBwGggfQEgfEwge4wgesGCyqGSIb3DQEMCgECoIG0MIGxMBwGCiqGSIb3DQEMAQMwDgQI/FfHqSBxFUoCAggABIGQIJa8eopsdqunR4ZwxWt/ThhdkRw2LFHTbgg5jWdAUQfK2b+I6+Wk9Dimdb2xGzAaYcAVt3ArbfuDTjDUTI4m3pzXBe/edyeXagr6i6DgM9TluB4OsG6hC/MFtF3rvqnCT3DGf5b48hSj0Y5OfJy+iFXmasxtwVIf4pFFylXOOJeJdQry1NgImb0nZwsS8NJAMSUwIwYJKoZIhvcNAQkVMRYEFHijHPCciGG5pbv+qBYZvjpHBIFnMDEwITAJBgUrDgMCGgUABBSxzZGBSpKB8R5FQ6wdiWxFka+xcgQIxB+kS2hfUpkCAggA"

IP_ADDRESS = "auto"  
PORT = "80"
SAVE_DIR = "/usr/share/dlercloud"
LOG_FILE = "/var/log/dler_update.log"

SOFTWARE_MAP = {
    "Surge": ["surge", "surge.conf", True],
    "Clash": ["clash", "clash.yaml", False],
    "Quantumult X": ["quantumultx", "quan.conf", False],
    "Shadowrocket": ["mu", "shadow.conf", False]
}
# ===========================================

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_public_ip():
    services = ['https://api.ipify.org', 'https://ifconfig.me/ip']
    for service in services:
        try:
            r = requests.get(service, timeout=10)
            if r.status_code == 200: return r.text.strip()
        except: continue
    return None

def process_and_save(url, file_name, is_surge, current_ip, add_cert=False):
    file_path = os.path.join(SAVE_DIR, file_name)
    headers = {"User-Agent": "Surge/2855 (Macintosh; Intel Mac OS X 14.4.1)"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            content = response.text
            
            # 1. 注入证书逻辑
            if add_cert:
                cert_content = f"skip-server-cert-verify = true\nh2 = true\nca-passphrase = {CA_PASSPHRASE}\nca-p12 = {CA_P12}"
                if "[MITM]" in content:
                    # 如果已有 [MITM] 段落，在段落标题下插入证书
                    content = content.replace("[MITM]", f"[MITM]\n{cert_content}")
                    logging.info(f"{file_name}: 已在原有 [MITM] 段落注入证书")
                else:
                    # 如果没有，在末尾追加
                    content += f"\n\n[MITM]\n{cert_content}"
                    logging.info(f"{file_name}: 已在文件末尾新建 [MITM] 并注入证书")

            # 2. 处理 Surge 托管首行
            if is_surge:
                lines = content.splitlines()
                managed_header = f"#!MANAGED-CONFIG http://{current_ip}:{PORT}/{file_name} interval=86400"
                if lines and (lines[0].startswith("#") or lines[0].startswith("!")):
                    lines[0] = managed_header
                else:
                    lines.insert(0, managed_header)
                content = "\n".join(lines)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            logging.info(f"保存成功: {file_name}")
    except Exception as e:
        logging.error(f"处理 {file_name} 异常: {str(e)}")

def run_update():
    global IP_ADDRESS
    if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)
    
    current_ip = get_public_ip() if IP_ADDRESS.lower() == "auto" else IP_ADDRESS
    if not current_ip: return

    # 处理 DlerCloud
    for soft_name, config in SOFTWARE_MAP.items():
        param, file_name, is_surge = config
        url = f"https://{DLER_BASE_ENDPOINT}/{DLER_API_KEY}?{param}=smart&lv={DLER_LV_PARAM}&type=latest{DLER_FILE_EXT}" if is_surge else f"https://{DLER_BASE_ENDPOINT}/{DLER_API_KEY}?{param}=smart&lv={DLER_LV_PARAM}{DLER_FILE_EXT}"
        # DlerCloud 建议也根据需要决定是否加证书，这里默认不加
        process_and_save(url, file_name, is_surge, current_ip, add_cert=False)

    # 处理 MESL (强制开启加证书)
    logging.info("开始处理 MESL 配置...")
    process_and_save(MESL_URL, "mesl.conf", True, current_ip, add_cert=True)

if __name__ == "__main__":
    run_update()
